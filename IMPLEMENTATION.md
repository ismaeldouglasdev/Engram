# Engram Implementation Plan

This plan is grounded in the papers in [`./papers/`](./papers/) and the adversarial literature review in [`LITERATURE.md`](./LITERATURE.md). The original design drew from Yu et al. (2026) and Hu et al. (2026). Two rounds of targeted falsification research have shaped this revision:

- **Round 1** exposed failure modes in embedding-based retrieval, LLM-as-judge contradiction detection, and multi-agent memory scaling.
- **Round 2** discovered a unifying architectural simplification: **NLI cross-encoders** (specifically `cross-encoder/nli-deberta-v3-base`, 92% accuracy, ~10ms/pair, runs locally) can replace the LLM-as-judge for the majority of contradiction checks. This eliminates the LLM API as a dependency for the core differentiating feature and makes conflict detection effectively synchronous.

The most significant architectural change from Round 2 is the **Tiered NLI Pipeline** (see Phase 3), which restructures conflict detection from an async LLM-dependent process into a fast, local, deterministic pipeline with LLM escalation only for ambiguous cases. This change was motivated by the discovery that production NLI models achieve 92% accuracy on contradiction detection at 200x the speed and zero marginal cost compared to LLM API calls, while also avoiding the agreeableness bias [12] that causes LLM judges to miss 75%+ of contradictions.

Additional Round 2 findings include: Letta (formerly MemGPT) already ships shared memory blocks for multi-agent systems but has no conflict detection [28]; Agent-MCP provides a shared knowledge graph MCP server [29]; CLAIRE demonstrates corpus-level inconsistency detection at Wikipedia scale [25]; and the Semantic Conflict Model [27] provides a principled foundation for Engram's federation layer based on replicated journals with semantic dependency tracking.

---

## Architecture overview

Engram maps directly onto the three-layer hierarchy from Yu et al.:

```
┌─────────────────────────────────────┐
│           I/O Layer (MCP)           │  ← agents connect here
│   engram_query / engram_commit /    │
│         engram_conflicts            │
├─────────────────────────────────────┤
│           Cache Layer               │  ← hot embeddings, recent facts
│   in-memory vector index,           │
│   LRU fact cache, conflict cache    │
├─────────────────────────────────────┤
│           Memory Layer              │  ← durable store
│   SQLite (facts + conflicts),       │
│   embedding store, agent registry   │
└─────────────────────────────────────┘
```

The consistency model sits across all three layers: it governs what writes become visible and when, and surfaces semantic contradictions as structured artifacts rather than errors.

---

## Phase 1 — Foundation: data model and storage

**Goal:** Define the core schema that everything else builds on. Get this right before writing any server code.

### Fact schema

Informed by A-Mem's note structure and Yu et al.'s consistency model requirements:

```sql
CREATE TABLE facts (
    id                   TEXT PRIMARY KEY,  -- uuid
    content              TEXT NOT NULL,     -- the raw fact as committed by the agent
    content_hash         TEXT NOT NULL,     -- SHA-256 of normalized content, for dedup
    scope                TEXT NOT NULL,     -- e.g. "auth", "payments/webhooks", "infra"
    confidence           REAL NOT NULL,     -- 0.0–1.0, agent-reported (treat as noisy signal)
    confidence_source    TEXT NOT NULL DEFAULT 'agent',  -- "agent" | "system" | "calibrated"
    agent_id             TEXT NOT NULL,     -- which agent committed this
    engineer             TEXT,              -- human owner of the agent session
    keywords             TEXT,              -- JSON array, LLM-generated
    tags                 TEXT,              -- JSON array, LLM-generated
    summary              TEXT,              -- one-sentence LLM-generated description
    entities             TEXT,              -- JSON array of extracted entities (services, APIs, config keys, numbers)
    embedding            BLOB,              -- float32 vector, serialized
    embedding_model      TEXT NOT NULL,     -- e.g. "all-MiniLM-L6-v2"
    embedding_model_ver  TEXT NOT NULL,     -- e.g. "2.3.1" from sentence-transformers
    committed_at         TEXT NOT NULL,     -- ISO8601 timestamp
    version              INTEGER NOT NULL DEFAULT 1,
    superseded_by        TEXT,              -- id of newer fact, null if current
    source_fact_id       TEXT,              -- if this fact was derived from another, link to origin
    utility_score        REAL DEFAULT 1.0   -- decayed utility for consolidation (see Phase 3b)
);

CREATE INDEX idx_facts_content_hash ON facts(content_hash);
CREATE INDEX idx_facts_scope ON facts(scope);
CREATE INDEX idx_facts_agent_id ON facts(agent_id);
```

**Design decisions grounded in the literature:**
- `agent_id` + `engineer` implement the "agent memory access protocol" Yu et al. identify as missing — every write is traceable to its source
- `scope` is the unit of access granularity (document, chunk, key-value record) that Yu et al. flag as under-specified
- `keywords`, `tags`, `summary` follow A-Mem's note enrichment approach — facts carry their own semantic metadata, not just raw content
- `entities` addresses the Orthogonality Constraint [7]: structured entity extraction provides hash-based retrieval keys that don't suffer from semantic interference, complementing embedding-based retrieval
- `content_hash` enables O(1) near-duplicate detection, addressing the duplication failure mode identified by Cemri et al. [9] — two agents committing semantically identical facts with different wording are caught before they bloat the store
- `superseded_by` enables the versioning Yu et al. require for read-time conflict handling under iterative revisions
- `source_fact_id` tracks derivation chains to detect the Mandela Effect [8] — when a cluster of facts all trace back to a single unverified source
- `confidence` is already in the public API; it feeds conflict resolution priority
- `utility_score` supports future consolidation (SEDM [16]) — facts that are never queried or frequently contradicted decay toward archival

### Conflict schema

```sql
CREATE TABLE conflicts (
    id           TEXT PRIMARY KEY,
    fact_a_id    TEXT NOT NULL REFERENCES facts(id),
    fact_b_id    TEXT NOT NULL REFERENCES facts(id),
    detected_at  TEXT NOT NULL,
    detection_method TEXT,              -- "embedding+llm" | "bm25+llm" | "entity_match" | "numeric"
    explanation  TEXT,                  -- LLM-generated description of the contradiction
    severity     TEXT,                  -- "high" | "medium" | "low"
    status       TEXT NOT NULL DEFAULT 'open',  -- "open" | "resolved" | "dismissed"
    resolved_by  TEXT,                  -- agent_id that resolved
    resolved_at  TEXT,
    resolution   TEXT                   -- how it was resolved
);
```

### Agent registry

Implements the "permissions, scope, and access granularity" protocol Yu et al. identify as missing:

```sql
CREATE TABLE agents (
    agent_id       TEXT PRIMARY KEY,
    engineer       TEXT NOT NULL,
    label          TEXT,                  -- human-readable name, e.g. "alice-claude-code"
    registered_at  TEXT NOT NULL,
    last_seen      TEXT,
    total_commits  INTEGER DEFAULT 0,
    contradicted_commits INTEGER DEFAULT 0  -- facts later found contradictory
);
```

The `contradicted_commits / total_commits` ratio provides an agent reliability signal used in query scoring (MMA [18]). Agents whose facts are frequently contradicted have their results downweighted.

---

## Phase 2 — Core MCP server

**Goal:** A working MCP server exposing the three public tools. No conflict detection yet — just commit, store, and query.

### Stack

- **Python 3.11+** with `fastmcp` (or `mcp` SDK directly)
- **SQLite** via `aiosqlite` for async I/O (WAL mode mandatory — see SQLite concurrency note below)
- **`sentence-transformers`** for local embeddings (default: `all-MiniLM-L6-v2`, ~80MB, no API key required)
- **`cross-encoder/nli-deberta-v3-base`** for local NLI-based contradiction detection (~400MB, 92% accuracy on SNLI/MNLI, ~10ms/pair on CPU) — this is the primary contradiction judge, replacing the LLM-as-judge for the majority of checks [23]
- **`rank_bm25`** for lexical retrieval — addresses the Semantic Collapse problem [6] where embedding-based retrieval fails on negation
- **`numpy`** for cosine similarity

**SQLite concurrency note:** SQLite uses database-level locks that serialize all writes. Under concurrent multi-agent commits, this becomes a bottleneck. Mitigations: (1) WAL mode is mandatory (`PRAGMA journal_mode=WAL`), enabling concurrent reads during writes; (2) busy timeout set to 5000ms (`PRAGMA busy_timeout=5000`); (3) if write contention becomes measurable, the storage layer is designed to be swappable to PostgreSQL without changing the MCP interface. This is a known scaling ceiling, not a design flaw — SQLite is the right choice for local-first single-team use, but federation (Phase 6) will require a migration path.

### `engram_commit(fact, scope, confidence, agent_id?, source_fact_id?)`

1. Validate inputs
2. Compute `content_hash` (SHA-256 of lowercased, whitespace-normalized content)
3. **Near-duplicate check:** query `facts` for matching `content_hash` in same scope. If found and not superseded, return the existing fact_id with a `duplicate: true` flag instead of creating a new row. This prevents the duplication failure mode identified by Cemri et al. [9].
4. Generate embedding for `content`
5. Use LLM (or lightweight local model) to generate `keywords`, `tags`, `summary`, and `entities` — following A-Mem's note construction step. Entity extraction should identify: service names, API endpoints, config keys, numeric values with units, version numbers, and temporal references.
6. Write to `facts` table (append-only: never update or delete rows)
7. Trigger async conflict scan against existing facts in the same scope (Phase 3)
8. Return `{fact_id, committed_at, duplicate}`

**Append-only is non-negotiable.** Yu et al. require that versioning and traceability be explicit. Every fact that has ever been committed must remain readable. Supersession is expressed via `superseded_by`, not deletion. However, append-only does not mean append-forever: Phase 3b introduces periodic consolidation to prevent unbounded growth (SEDM [16]).

### `engram_query(topic, scope?, limit?)`

1. Generate embedding for `topic`
2. Retrieve all current (non-superseded) facts, optionally filtered by `scope`
3. **Dual retrieval:** Score facts using both embedding similarity and BM25 lexical match, then fuse results via Reciprocal Rank Fusion (RRF). This addresses the Semantic Collapse problem [6] — embedding retrieval misses negation-based contradictions, while BM25 catches exact keyword matches that embeddings blur together.
4. Compute final score incorporating four signals:
   - `relevance` — RRF-fused rank from embedding + BM25
   - `recency` — `exp(-λ * days_since_commit)`, `λ = 0.05`
   - `agent_reliability` — `1.0 - (contradicted_commits / total_commits)` for the committing agent (MMA [18])
   - `confidence` — agent-reported, but downweighted if the agent has low reliability
   - Final: `score = 0.5 * relevance + 0.2 * recency + 0.15 * agent_reliability + 0.15 * confidence` (tunable)
5. Return top-`limit` facts (default 10), ordered by score
6. Include `agent_id`, `confidence`, `committed_at`, `source_fact_id` in each result — agents need provenance
7. **CRITICAL:** Join with `conflicts` table to flag `has_open_conflict: true` if the fact is currently disputed. (Mitigates the "Blind Read" failure mode where agents unknowingly act on contested information).

The dual retrieval approach is informed by Bharti et al. [6], who showed that a Decoupled Lexical Architecture using BM25 as backbone outperformed dense retrieval for contradiction-aware tasks. Pure embedding similarity misses temporally important recent facts (MIRIX insight), but it also misses negation-differentiated facts (Semantic Collapse). The hybrid addresses both.

### `engram_conflicts(scope?)`

Initially: return all rows from `conflicts` table with `status = 'open'`, optionally filtered by scope. Conflict detection itself is Phase 3.

### Server entrypoint

```
engram serve [--host HOST] [--port PORT] [--db PATH] [--embedding-model MODEL]
```

- Default: `localhost:7474`, `~/.engram/knowledge.db`
- MCP endpoint: `http://HOST:PORT/mcp`
- Health check: `http://HOST:PORT/health`

---

## Phase 3 — Conflict detection

**Goal:** Implement the core consistency mechanism. This is what no existing system does — including Letta [28], Agent-MCP [29], mem0, and every other shared memory system in the current landscape.

The literature distinguishes two types of consistency violation (Yu et al.):
1. **Read-time conflict** — a stale fact remains visible alongside a newer contradicting fact (versioning problem)
2. **Update-time conflict** — two agents write contradictory facts concurrently or sequentially (semantic contradiction problem)

Both are handled here.

### Tiered Detection Pipeline (Revised Architecture)

The original design used an LLM-as-judge for all contradiction checks. Round 2 research [23, 24, 25] revealed that NLI cross-encoders achieve 92% accuracy on contradiction detection at ~10ms/pair (vs. ~2000ms for LLM calls), with zero marginal cost and no agreeableness bias. This enables a **tiered pipeline** where the fast, deterministic NLI model handles the majority of checks, and the LLM is reserved for ambiguous cases requiring explanation text.

Triggered after every `engram_commit`:

**Tier 0 — Deterministic pre-checks (< 1ms, every commit)**

Before any model inference:
- **Content hash dedup:** If `content_hash` matches an existing non-superseded fact in the same scope, return `duplicate: true`. O(1) lookup. Catches the duplication failure mode [9].
- **Entity overlap check:** If `f_new.entities` overlaps with any existing fact's `entities` (same service name, API endpoint, or config key with different values), flag as a candidate. Hash-based, immune to the Orthogonality Constraint [7].

**Tier 1 — NLI Cross-Encoder (< 500ms total, every commit)**

For the newly committed fact `f_new`, retrieve candidates via three parallel paths:

*Path A — Embedding similarity:*
- Retrieve the top-20 most embedding-similar facts in the same scope
- Use relative ranking (top-k) rather than an absolute cosine threshold. Absolute thresholds are unreliable due to anisotropy [14].

*Path B — BM25 lexical match:*
- Retrieve top-10 BM25 matches for `f_new.content` in the same scope
- Catches negation-differentiated contradictions that embeddings miss [6].

*Path C — Entity overlap:*
- Include any fact whose `entities` overlap with `f_new.entities`, regardless of embedding or BM25 score.

Union all three candidate sets, deduplicate, cap at 30 candidates.

For each candidate pair `(f_new, f_candidate)`, run the NLI cross-encoder (`cross-encoder/nli-deberta-v3-base`):

```python
from sentence_transformers import CrossEncoder

nli_model = CrossEncoder('cross-encoder/nli-deberta-v3-base')
scores = nli_model.predict([(f_new.content, f_candidate.content)])
# scores = [contradiction_score, entailment_score, neutral_score]
```

Classification:
- If `contradiction_score > 0.85`: **flag as conflict** (high confidence). Write to `conflicts` table with `detection_method = "nli"`.
- If `contradiction_score` between 0.5 and 0.85: **escalate to Tier 3** (LLM judge) for confirmation and explanation generation.
- If `entailment_score > 0.85`: candidate for corroboration link (see Tier 1b).
- Otherwise: no conflict detected.

At 30 candidates × ~10ms/pair, Tier 1 completes in ~300ms. This makes conflict detection **effectively synchronous** — the committing agent can optionally wait for the result rather than requiring a fully async pipeline.

**Tier 1b — Corroboration detection**

If `f_new` and `f_candidate` are from *different* agents, the NLI model returns `entailment_score > 0.85`, and entity overlap is high: mark `f_new` with a `corroborates: f_candidate.id` link. This addresses duplication [9] without deleting either fact.

**Tier 2 — Specialized numeric/temporal checks (< 5ms, every commit)**

Run in parallel with Tier 1:

*Numeric contradiction check:*
- Extract numeric values with units from both facts (using the `entities` field)
- If both facts reference the same entity + attribute but with different numeric values, flag as a candidate contradiction with `detection_method = "numeric"`
- This catches order-of-magnitude errors that both NLI models and LLMs systematically miss [13]

*Temporal contradiction check:*
- Extract temporal references and resolve them against `committed_at` timestamps
- If both facts reference the same entity with conflicting temporal claims, flag as candidate

**Tier 3 — LLM Judge (escalation only, ~2000ms/pair)**

Invoked ONLY when:
- Tier 1 NLI score is ambiguous (contradiction_score between 0.5 and 0.85)
- An explanation is needed for a high-confidence Tier 1 detection (for the dashboard)
- A scope is configured as "high-stakes" requiring LLM confirmation

```
System: You are an adversarial fact-checker. Your job is to find contradictions
        between two facts about a codebase. You should be skeptical and look for
        ANY way these facts could be incompatible.

        The NLI model has flagged these facts as potentially contradictory
        (score: {nli_contradiction_score}).

        First, list all ways these two facts COULD contradict each other.
        Then, for each potential contradiction, assess whether it is real.
        Finally, give your verdict.

        Respond with JSON:
        {
          "potential_contradictions": ["..."],
          "verdict": {"contradicts": true/false, "explanation": "...", "severity": "high/medium/low"}
        }

Fact A (committed by {agent_a}, scope: {scope}, confidence: {conf_a}, date: {date_a}):
{content_a}

Fact B (committed by {agent_b}, scope: {scope}, confidence: {conf_b}, date: {date_b}):
{content_b}
```

Key design choices:
- **Adversarial framing** counteracts agreeableness bias [12]
- **NLI score is included** in the prompt to anchor the LLM's judgment
- **Minority-veto ensemble** for high-stakes scopes: run 3 times, flag if any says yes
- Use a fast, cheap model (e.g., `claude-haiku-4-5`)

**Step 5 — Stale supersession check**

If `f_new` and `f_candidate` are from the same agent, same scope, and high similarity (NLI entailment > 0.85 OR high entity overlap): mark `f_candidate.superseded_by = f_new.id`. Uses atomic `UPDATE ... WHERE superseded_by IS NULL` to prevent race conditions.

### Conflict severity heuristic

| Condition | Severity |
|---|---|
| Contradicting facts from different engineers, both high-confidence (> 0.8), NLI contradiction > 0.9 | high |
| NLI contradiction > 0.85 but same engineer | medium |
| NLI contradiction between 0.5–0.85 (escalated to LLM, confirmed) | medium |
| Numeric/temporal contradiction detected by Tier 2 | high (numeric values in code are rarely ambiguous) |
| One or both facts low-confidence (< 0.5) | low |
| Different scopes (detected despite filtering) | low |

### Performance characteristics of the tiered pipeline

| Metric | Old (LLM-only) | New (Tiered NLI) |
|---|---|---|
| Latency per commit (30 candidates) | 60–150s (async) | ~500ms (sync-capable) |
| Cost per commit | ~$0.01–0.05 (API) | ~$0 (local) + $0.01 for Tier 3 escalations |
| LLM API dependency | Hard (every commit) | Soft (escalation only, ~10-20% of commits) |
| Determinism | No (LLM varies per call) | Yes for Tiers 0-2, No for Tier 3 |
| Agreeableness bias exposure | Every check | Only Tier 3 escalations |

---

## Phase 3b — Consolidation and memory hygiene

**Goal:** Prevent unbounded growth of the facts table. SEDM [16] demonstrates that append-only without consolidation leads to noise accumulation, degraded retrieval, and scaling failure. This phase adds a periodic background process.

### Utility decay

Every fact has a `utility_score` (default 1.0) that decays over time:
- Each time a fact is returned by `engram_query`, its utility is boosted: `utility_score = min(1.0, utility_score + 0.1)`
- A daily background job decays all facts: `utility_score *= 0.995`
- Facts with `utility_score < 0.1` and `committed_at` older than 90 days are candidates for archival

### Archival

Archived facts are moved to a separate `facts_archive` table with the same schema. They are excluded from `engram_query` results and conflict detection, but remain queryable via a separate `engram_query_archive` tool for audit purposes. This preserves the append-only audit trail while keeping the active store lean.

### Consolidation

When a scope accumulates more than 100 active (non-superseded, non-archived) facts, a consolidation job runs:
1. Cluster facts by entity overlap
2. For each cluster with 5+ facts, generate a summary fact that synthesizes the cluster
3. Mark original facts as `superseded_by` the summary
4. The summary fact carries `source_fact_id` links to all originals

This is aggressive and lossy — it should be opt-in per scope and require human approval via the dashboard (Phase 7) before executing.

---

## Phase 4 — Conflict resolution workflow

**Goal:** Make conflicts actionable, not just detectable. The survey (Hu et al., Section 7.5) calls for "learning-driven conflict resolution" and "agent-aware shared memory where R/W are conditioned on agent roles." This phase implements the deterministic baseline before any learning.

### New MCP tool: `engram_resolve(conflict_id, resolution, winning_fact_id?)`

```python
engram_resolve(
    conflict_id: str,
    resolution: str,          # human-readable explanation
    winning_fact_id: str | None  # if one fact wins, mark the other superseded
)
```

Behavior:
- Sets `conflicts.status = 'resolved'`, records `resolved_by`, `resolved_at`, `resolution`
- If `winning_fact_id` is provided: sets the losing fact's `superseded_by = winning_fact_id`
- If no winner: marks both facts with `confidence *= 0.5` (both remain, both downweighted)

### New MCP tool: `engram_dismiss(conflict_id, reason)`

For conflicts that are not actual contradictions (false positives from the LLM check):
- Sets `conflicts.status = 'dismissed'`
- Feeds into a false-positive training log for future prompt refinement

### Resolution strategies (informed by Yu et al.'s consistency model)

Three strategies agents or engineers can apply:

1. **Last-writer-wins** — the more recent fact supersedes the older. Appropriate when the newer fact is a correction (agent re-investigated and updated its belief).

2. **Higher-confidence-wins** — the fact with higher reported confidence supersedes. Appropriate when one agent had better information at commit time.

3. **Explicit merge** — a new fact is committed that synthesizes both, and both originals are marked superseded. Appropriate for complementary (not truly contradictory) facts that were incorrectly flagged.

---

## Phase 5 — Agent identity and access control

**Goal:** Implement the "agent memory access protocol" Yu et al. identify as missing — permissions, scope, and granularity.

### Agent registration

On first connection, an agent registers with:
```json
{
  "agent_id": "alice-claude-code-session-abc123",
  "engineer": "alice@company.com",
  "label": "Claude Code / alice"
}
```

`agent_id` is included in every `engram_commit` call. If omitted, the server generates one per session (unauthenticated mode).

### Scope-based access control

Scopes are hierarchical: `payments/webhooks` is a child of `payments`, which is a child of the root.

```sql
CREATE TABLE scope_permissions (
    agent_id   TEXT NOT NULL,
    scope      TEXT NOT NULL,           -- e.g. "payments" or "*"
    can_read   BOOLEAN NOT NULL DEFAULT TRUE,
    can_write  BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (agent_id, scope)
);
```

- Unauthenticated mode (default local): all agents can read/write all scopes
- Team mode: admins assign scope permissions per engineer or agent
- Read-only agents: useful for review workflows where an agent audits the knowledge base without writing

**Extensibility note:** Zhao et al. [15] (Collaborative Memory) demonstrate that real team deployments require time-evolving, asymmetric policies encoded as bipartite graphs — not just static scope permissions. The `scope_permissions` table is the MVP; the schema is designed to be extended with `valid_from`/`valid_until` timestamps and role-based policies without breaking the existing API.

### Token auth

Simple bearer token per engineer. Tokens stored hashed in the DB. Passed in MCP connection headers.

**Security note:** The MCP ecosystem has documented vulnerabilities including token audience confusion, CSRF-style attacks, and lack of transport encryption. Engram's auth implementation must: (1) bind tokens to specific server instances (audience claim), (2) require HTTPS for any non-localhost deployment, (3) implement token rotation. See the MCP security landscape analysis for current best practices — the 2025-06-18 MCP specification mandates OAuth 2.1 for remote servers.

```
engram serve --auth  # enables token verification
engram token create --engineer alice@company.com
```

---

## Phase 6 — Cross-team federation

**Goal:** Allow multiple Engram instances to share facts without centralizing everything. Yu et al. flag this as an open protocol gap (the "agent memory access protocol" problem at the inter-server level).

### Federation model — informed by Semantic Conflict Model [27] and CodeCRDT [26]

The Semantic Conflict Model [27] demonstrates that collaborative data structures can achieve explicit, local-first conflict resolution without central coordination by using a replicated journal with semantic dependency tracking. Engram's append-only facts table is already a replicated journal — this phase formalizes the replication semantics.

Each Engram instance is a **node**. Nodes can be configured as peers:

```yaml
# ~/.engram/config.yaml
federation:
  peers:
    - url: https://engram.teamb.internal
      token: <bearer>
      scopes: ["shared/*"]   # only sync facts in shared/ scope
      sync_interval: 60      # seconds
```

### Sync protocol

Pull-based (simpler than push, easier to reason about consistency):

1. Node A periodically fetches `/facts/since?timestamp=T&scope=shared/*` from Node B
2. Facts from remote nodes are written locally with their original `agent_id` and `committed_at`; `origin_node` field added
3. Conflicts are detected across nodes using the same tiered NLI pipeline as Phase 3 — the NLI cross-encoder runs locally on each node, so no cross-node LLM calls are needed
4. Resolution is local: each node tracks its own conflict table

This is an **eventually consistent** model — exactly the "eventual consistency paradigm" the survey (Hu et al.) describes as the practical direction for multi-agent memory. CodeCRDT [26] demonstrates that CRDT-based approaches achieve 100% convergence with zero merge failures for multi-agent LLM systems, validating this direction. Future work: model the facts table as a grow-only set CRDT for stronger convergence guarantees.

---

## Phase 7 — Dashboard

**Goal:** Make the knowledge base inspectable by humans, not just agents.

### Views

- **Knowledge base** — all current (non-superseded) facts, filterable by scope, agent, engineer, date range
- **Conflict queue** — open conflicts grouped by scope, sortable by severity. Each conflict shows both facts side by side with the LLM-generated explanation.
- **Timeline** — fact commits over time, colored by agent/engineer. Makes it visible when different agents were active in the same scope.
- **Agent activity** — per-engineer breakdown of commits, conflict rate, resolution rate

### Stack

- **Backend:** FastAPI, same process as the MCP server (separate router)
- **Frontend:** minimal — server-rendered HTML with HTMX or a single-page Vue/React app
- **Endpoint:** `http://HOST:PORT/dashboard`

---

## Delivery sequence

**Competitive context:** Letta [28] already ships shared memory blocks for multi-agent systems. Agent-MCP [29] provides a shared knowledge graph MCP server. Neither has conflict detection. This is Engram's moat, but the window is narrowing. Phases 1-3 must ship fast.

| Phase | Deliverable | Unlocks |
|---|---|---|
| 1 | Schema + migrations | All subsequent phases |
| 2 | MCP server: commit + query (dual retrieval) | Usable by agents today |
| 3 | Conflict detection (tiered NLI pipeline) | Core differentiator — **ship this before Letta adds it** |
| 3b | Consolidation + memory hygiene | Long-term scalability |
| 4 | Resolution workflow | Conflicts become actionable |
| 5 | Auth + access control | Team deployment |
| 6 | Federation (replicated journal model) | Multi-team / org-wide |
| 7 | Dashboard | Human oversight (CLAIRE [25] shows this is critical — best automated systems reach only 75.1% AUROC) |

Phases 1–3 are the minimum viable Engram. The tiered NLI pipeline (Phase 3) is now significantly simpler to implement than the original LLM-only design: no async job queue needed for the primary detection path, no LLM API dependency for the core feature, and the NLI model ships as a pip dependency alongside the embedding model. Phase 3b should ship shortly after — without it, the system degrades over weeks of team use. Phase 7 (dashboard) is more critical than originally assessed: CLAIRE [25] demonstrates that human-in-the-loop review is essential because fully automated consistency detection has a hard ceiling around 75% AUROC.

---

## Key design constraints from the literature

**1. Graph-Based Memory as the Unifying Abstraction**
- *Insight:* A relational database is insufficient for capturing the rich, interconnected nature of knowledge. A graph-based memory, where facts are nodes and relationships are edges, is a more powerful and flexible representation.
- *Implementation:* Engram will use a graph database as its primary storage layer. This will enable more sophisticated reasoning and retrieval, and will provide a more natural way to represent the complex dependencies between facts.

**2. Hybrid Retrieval is Essential**
- *Insight:* Embedding-based retrieval alone is not sufficient. It is vulnerable to semantic collapse, negation blindness, and the orthogonality constraint. A hybrid approach that combines embedding-based, lexical, and structured retrieval is necessary.
- *Implementation:* Engram will implement a hybrid retrieval pipeline that uses a combination of embedding similarity, BM25, and graph-based queries to retrieve candidate facts.

**3. Adversarial Prompting and Ensembles for Contradiction Detection**
- *Insight:* LLM-as-judge systems are prone to an "agreeableness bias" that leads to a high rate of false negatives in contradiction detection. Adversarial prompting and ensemble methods can mitigate this bias.
- *Implementation:* Engram will use adversarial prompting and a minority-veto ensemble to improve the accuracy of its contradiction detection mechanism.

**4. Quorum-Based Commit and Source Corroboration for Security**
- *Insight:* Shared memory systems are vulnerable to memory poisoning attacks (e.g., MINJA). A quorum-based commit process and source corroboration can help to mitigate this threat.
- *Implementation:* Engram will implement a quorum-based commit process for sensitive scopes, and will track the source and corroboration of all facts.

**5. Byzantine Fault Tolerance for Consensus**
- *Insight:* In a multi-agent system, it is essential to have a consensus mechanism that is resilient to Byzantine failures.
- *Implementation:* Engram will implement a Byzantine Fault-Tolerant (BFT) consensus protocol for all writes to the shared memory.

**6. Append-Only with Consolidation**
- *Insight:* An append-only architecture is essential for auditability and traceability, but it can lead to unbounded growth of the knowledge base. A consolidation mechanism is needed to manage this growth.
- *Implementation:* Engram will use an append-only architecture, but will also implement a periodic consolidation process to archive and summarize old or low-utility facts.

---

## Failure Modes & Architectural Mitigations

Based on an extensive adversarial literature review, the following failure modes have been identified. The Engram implementation plan has been revised to mitigate these threats.

**1. Memory Injection & Poisoning (MINJA)**
- *Failure Mode:* An adversary with query-only access injects malicious facts into the shared memory. These facts are designed to be retrieved by other agents, leading them to perform incorrect or harmful actions. The append-only nature of the memory makes these attacks persistent.
- *Mitigation:*
    - **Quorum-Based Commit:** For sensitive scopes, require a quorum of `n` independent agents to commit a fact before it is considered "trusted."
    - **Source Corroboration:** Track the number of independent agents that have corroborated a fact. Single-source facts are flagged and down-weighted in query results.
    - **Rate Limiting:** Implement rate limiting on `engram_commit` to prevent bulk injection of malicious facts.
    - **Derivation Tracking:** Use `source_fact_id` to track the derivation of facts. Clusters of facts derived from a single, unverified source are flagged as suspicious.

**2. LLM-as-Judge Agreeableness Bias**
- *Failure Mode:* The LLM used for contradiction detection exhibits a strong "agreeableness bias," leading it to miss a significant percentage of actual contradictions (high false-negative rate).
- *Mitigation:*
    - **Adversarial Prompting:** Frame the contradiction detection prompt to be adversarial (e.g., "Find any possible contradiction between these two facts").
    - **Minority-Veto Ensemble:** For high-stakes scopes, run the contradiction check with multiple LLM judges. If any judge detects a contradiction, the conflict is flagged.
    - **Deterministic Pre-Checks:** Implement deterministic checks for numeric and temporal contradictions before invoking the LLM judge.

**3. Embedding Retrieval Degradation (Semantic Collapse & Orthogonality Constraint)**
- *Failure Mode:* Embedding-based retrieval degrades as more semantically similar facts are added to the knowledge base. Contradictory facts may have very similar embeddings, making them difficult to distinguish.
- *Mitigation:*
    - **Hybrid Retrieval:** Use a hybrid retrieval approach that combines embedding-based similarity with lexical (BM25) and structured (entity-based) retrieval.
    - **Knowledge Graph Representation:** Represent facts and their relationships in a knowledge graph. This allows for more sophisticated and robust retrieval methods that are not solely reliant on embedding similarity.
    - **Consolidation & Archival:** Periodically archive and consolidate low-utility facts to reduce the size of the active knowledge base and mitigate the effects of semantic density.

**4. Lack of a Unifying Abstraction for Memory (Relational vs. Graph)**
- *Failure Mode:* A relational database schema is not expressive enough to capture the complex relationships between facts, leading to a loss of information and a less powerful reasoning capability.
- *Mitigation:*
    - **Graph-Based Memory:** Replace the relational database with a graph database. This will allow for the representation of facts as nodes and their relationships as edges, enabling more powerful graph-based reasoning and retrieval.
    - **Schema Evolution:** Design a flexible graph schema that can evolve as new types of facts and relationships are added to the knowledge base.

**5. Insufficient Protection Against Consensus Failures (Byzantine Faults)**
- *Failure Mode:* Malicious or faulty agents can disrupt the consensus process, leading to an inconsistent state in the shared memory.
- *Mitigation:*
    - **Byzantine Fault-Tolerant Consensus:** Implement a Byzantine Fault-Tolerant (BFT) consensus protocol for all writes to the shared memory. This will ensure that the system can reach a consistent state even in the presence of malicious agents.
    - **Agent Reputation:** Track the reputation of each agent based on its past behavior. Agents with a history of malicious or faulty behavior will be given less weight in the consensus process.

**6. Silent Retrieval Corruption from Embedding Model Upgrade**
- *Failure Mode:* Upgrading the embedding model can lead to silent retrieval corruption, where the new model is incompatible with the old embeddings, resulting in meaningless similarity scores and a failure to detect contradictions.
- *Mitigation:*
    - **Embedding Model Versioning:** Store the embedding model and version with each fact.
    - **Re-indexing:** Provide a mechanism to re-index all facts with the new embedding model.
    - **Validation:** At startup, validate the configured embedding model against the model used for the most recent facts in the database.

**7. Confidence Field Inflation (LLM Calibration Failure)**
- *Failure Mode:* LLMs tend to report high confidence scores regardless of their actual epistemic state, which can lead to an over-reliance on incorrect information.
- *Mitigation:*
    - **Confidence Calibration:** Implement a confidence calibration mechanism that adjusts the confidence scores reported by LLMs based on their historical performance.
    - **Agent Reliability:** Track the reliability of each agent based on the accuracy of its past contributions. This can be used to weight the confidence of new facts committed by the agent.

---

## What Engram is not building

The research landscape for agent memory is vast. To maintain focus, Engram is intentionally *not* building the following:

- **Parametric Memory:** Engram does not alter the weights of the LLMs it interacts with. It is a purely token-level system.
- **Cache-Level Protocols:** Engram does not implement protocols for sharing or reusing the internal cache of LLMs.
- **Episodic or Procedural Memory:** Engram is focused on storing and managing factual knowledge about a codebase, not on tracking the history of agent interactions or learning procedural skills.
- **RL-Driven Memory Management:** While reinforcement learning is a promising direction for optimizing memory systems, it is out of scope for the initial implementation of Engram.
- **Multimodal Memory:** The initial version of Engram will only support text-based facts. Support for images, diagrams, and other modalities is a potential future extension.
- **General Agent Orchestration:** Agent-MCP [29] handles task management, agent lifecycle, and visualization. Engram focuses exclusively on the consistency layer.
- **Full Knowledge Graph:** Letta [28] and Agent-MCP provide graph-based memory. Engram's data model is a flat fact store with entity links, optimized for conflict detection rather than graph traversal.

### Strategic positioning

Engram should be thought of as a **consistency layer** that could sit on top of existing shared memory systems (Letta, Agent-MCP) rather than replacing them. The long-term play is: other systems handle storage and retrieval; Engram handles "are these facts consistent?" This framing makes Engram complementary rather than competitive with the broader ecosystem, and focuses development effort on the one thing no other system does.
