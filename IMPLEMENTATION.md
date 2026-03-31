# Engram Implementation Plan

This plan is grounded in the papers in [`./papers/`](./papers/) and the adversarial literature review in [`LITERATURE.md`](./LITERATURE.md). The original design drew from Yu et al. (2026) and Hu et al. (2026). This revision incorporates findings from targeted falsification research — papers that expose failure modes in embedding-based retrieval, LLM-as-judge contradiction detection, and multi-agent memory scaling. Every major design decision below has been stress-tested against this adversarial literature; where the original plan was vulnerable, mitigations have been added.

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

**Goal:** Implement the core consistency mechanism. This is what no existing system does.

The literature distinguishes two types of consistency violation (Yu et al.):
1. **Read-time conflict** — a stale fact remains visible alongside a newer contradicting fact (versioning problem)
2. **Update-time conflict** — two agents write contradictory facts concurrently or sequentially (semantic contradiction problem)

Both are handled here.

### Detection pipeline

Triggered after every `engram_commit` (async, non-blocking to the committing agent):

**Step 1 — Candidate retrieval (dual-path)**

For the newly committed fact `f_new`, retrieve candidates via two parallel paths to address the Semantic Collapse problem [6]:

*Path A — Embedding similarity:*
- Retrieve the top-20 most embedding-similar facts in the same scope
- Use relative ranking (top-k) rather than an absolute cosine threshold. The original 0.65 threshold is unreliable because embedding spaces are anisotropic — scores concentrate in a narrow band regardless of actual relatedness [14]. Instead, take the top-20 by rank and let the LLM judge filter.

*Path B — BM25 lexical match:*
- Index fact content + keywords with BM25
- Retrieve top-10 BM25 matches for `f_new.content` in the same scope
- This catches contradictions that differ only by negation or a single changed predicate (e.g., "uses JWT" vs. "does not use JWT"), which embedding retrieval misses because negation signals collapse in vector space [6].

*Path C — Entity overlap:*
- If `f_new.entities` overlaps with any existing fact's `entities` (same service name, API endpoint, or config key), include that fact as a candidate regardless of embedding or BM25 score. This provides hash-based retrieval that doesn't suffer from the Orthogonality Constraint [7].

Union all three candidate sets, deduplicate, cap at 30 candidates.

Secondary fallback: if fewer than 5 candidates found in exact scope, retrieve globally with stricter filtering (top-10 by embedding, entity overlap only) to catch scope fragmentation.

**Step 2 — Specialized pre-checks (before LLM)**

Before invoking the LLM judge, run fast deterministic checks that catch contradiction types LLMs handle poorly [13]:

*Numeric contradiction check:*
- Extract numeric values with units from both facts (using the `entities` field)
- If both facts reference the same entity + attribute but with different numeric values (e.g., "rate limit is 100 req/s" vs. "rate limit is 1000 req/s"), flag as a candidate contradiction with `detection_method = "numeric"`
- This catches order-of-magnitude errors that LLMs systematically miss [13]

*Temporal contradiction check:*
- Extract temporal references and resolve them against `committed_at` timestamps
- If both facts reference the same entity with conflicting temporal claims, flag as candidate

**Step 3 — LLM contradiction check (adversarial prompting)**

For each candidate pair `(f_new, f_candidate)`:

```
System: You are an adversarial fact-checker. Your job is to find contradictions
        between two facts about a codebase. You should be skeptical and look for
        ANY way these facts could be incompatible.

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

Key changes from the original prompt, informed by the adversarial literature:
- **Adversarial framing** ("find contradictions") counteracts the agreeableness bias [12] where LLMs default to saying things are consistent. By asking the LLM to first enumerate *potential* contradictions before judging, we force it past the agreeable default.
- **Narrative focus bias mitigation** [11]: facts are presented in a neutral, third-person structure with explicit entity labels rather than as a narrative.
- **Ensemble check**: For high-stakes scopes (configurable), run the contradiction check 3 times. Flag as contradictory if *any* run says yes (minority-veto strategy from Ahmed et al. [12]). This reduces the false-negative rate from ~75% to ~42% at the cost of 3x LLM calls for those scopes.

Use a fast, cheap model (e.g., `claude-haiku-4-5`) — this runs on every commit. The ensemble is optional and scope-configurable.

**Step 4 — Write conflict record**

If contradicts (from LLM, numeric check, or temporal check), insert into `conflicts` table with `detection_method` recorded. Do not deduplicate against existing open conflicts (facts evolve; the same logical conflict may be reported by different commit pairs).

**Step 5 — Stale supersession check**

If `f_new` and `f_candidate` are from the same agent, same scope, and high similarity (> 0.85 by embedding OR high entity overlap): mark `f_candidate.superseded_by = f_new.id`. This handles the read-time conflict case: an agent refining its own prior belief.
*Implementation Note:* To prevent race conditions from concurrent identical commits, this step must use an atomic SQLite `UPDATE ... WHERE superseded_by IS NULL` transaction.

**Step 6 — Near-duplicate detection**

If `f_new` and `f_candidate` are from *different* agents but have very high similarity (> 0.92 by embedding AND high entity overlap), and the LLM does not flag a contradiction, mark `f_new` with a `corroborates: f_candidate.id` link. This addresses the duplication problem [9] without deleting either fact — both remain, but the system knows they represent the same knowledge from independent sources.

### Conflict severity heuristic

| Condition | Severity |
|---|---|
| Contradicting facts from different engineers, both high-confidence (> 0.8) | high |
| One or both facts low-confidence (< 0.5) | low |
| Same engineer, different sessions | medium |
| Different scopes (detected despite filtering) | low |

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

### Federation model

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
3. Conflicts are detected across nodes using the same pipeline as Phase 3
4. Resolution is local: each node tracks its own conflict table

This is a **eventually consistent** model — exactly the "eventual consistency paradigm" the survey (Hu et al.) describes as the practical direction for multi-agent memory.

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

| Phase | Deliverable | Unlocks |
|---|---|---|
| 1 | Schema + migrations | All subsequent phases |
| 2 | MCP server: commit + query (dual retrieval) | Usable by agents today |
| 3 | Conflict detection (multi-path + adversarial prompting) | Core differentiator |
| 3b | Consolidation + memory hygiene | Long-term scalability |
| 4 | Resolution workflow | Conflicts become actionable |
| 5 | Auth + access control | Team deployment |
| 6 | Federation | Multi-team / org-wide |
| 7 | Dashboard | Human oversight |

Phases 1–3 are the minimum viable Engram. Phase 3b should ship shortly after — without it, the system degrades over weeks of team use. Everything after that extends the consistency model further along the axes the literature identifies: governance, access control, federation, human review.

---

## Key design constraints from the literature

**1. Append-only writes (with planned consolidation)**
Yu et al. require explicit versioning for read-time conflict handling. Deletions would break the audit trail. Facts are superseded, not deleted. However, SEDM [16] demonstrates that pure append-only without consolidation leads to unbounded growth and retrieval degradation. Phase 3b adds utility-based archival and opt-in consolidation to balance auditability with scalability.

**2. Semantic conflicts are structured artifacts, not errors**
The survey (Hu et al., §7.5) and Yu et al. both frame conflicts as something to detect, surface, and resolve — not prevent. `engram_conflicts()` returns a structured list, not an exception. This is intentional.

**3. Embeddings are necessary but insufficient**
A-Mem demonstrates that embedding-based retrieval without semantic enrichment misses connections. But the adversarial literature reveals deeper problems: the Orthogonality Constraint [7] shows embedding retrieval degrades as semantically similar facts accumulate, Semantic Collapse [6] shows negation is invisible in vector space, and anisotropy [14] makes absolute similarity thresholds unreliable. Engram therefore uses embeddings as *one of three* retrieval paths (alongside BM25 and entity-based lookup), never as the sole signal.

**4. Agent identity is mandatory for consistency**
Yu et al.'s consistency model requires knowing *which agent* wrote what and *when*. The survey (§7.7) warns that memory systems without attribution enable privacy leaks and untraceable hallucinations. `agent_id` is required on every write path. Additionally, agent reliability tracking (MMA [18]) uses historical contradiction rates to weight query results.

**5. Scope is the unit of isolation**
MIRIX's six memory types and A-Mem's box structure both point to the same principle: organizing memory by *topic domain* makes retrieval and conflict detection tractable. In Engram, `scope` plays this role. It should be hierarchical (path-like) and queryable at any level.

**6. Conflict detection must be async and non-blocking**
Committing a fact should return immediately. Detection runs in the background. Blocking commits on LLM inference would make the write path unusable in practice.

**7. LLM-as-judge is unreliable by default**
The agreeableness bias [12] means LLM judges miss 75%+ of contradictions in single-shot evaluation. The narrative focus bias [11] means contradictions about the primary subject are harder to detect than peripheral ones. Engram mitigates this through adversarial prompting (asking the LLM to enumerate potential contradictions before judging), minority-veto ensembles for high-stakes scopes, and deterministic pre-checks for numeric/temporal contradictions that LLMs handle poorly [13].

**8. Pairwise checking cannot guarantee global consistency**
He et al. [5] prove that pairwise consistency checks are insufficient — three facts can be pairwise consistent but jointly inconsistent. This is a known limitation of the current design. Future work should implement the MUS-finding algorithm from [5] as a periodic batch job that checks for multi-fact inconsistencies across the knowledge base.

---

## Failure Modes & Architectural Mitigations

Based on adversarial literature review (see LITERATURE.md §5–22) and analysis of multi-agent memory constraints, the following failure modes have been identified and addressed:

**1. The "Blind Read" (Stale Facts / Knowledge Decay)**
- *Failure Mode:* Vector databases natively treat all stored records as equally valid. An agent might query a fact that is currently disputed by another agent, and unknowingly use it as ground truth.
- *Mitigation:* `engram_query` guarantees it surfaces `has_open_conflict` for every returned fact, forcing the reading agent to acknowledge the dispute, wait for resolution, or explicitly choose a side via `engram_resolve`.

**2. Async Race Conditions (Lost Updates)**
- *Failure Mode:* If two agents highly concurrently commit contradictory facts, the async conflict pipeline might interleave, causing incomplete supersession or dropping the conflict entirely.
- *Mitigation:* SQLite's explicit atomic transactions are used during the `superseded_by` update step. The `conflicts` table acts as a dead-letter queue for contradictory facts that bypass initial synchronous checks.

**3. Scope Fragmentation (Context drift)**
- *Failure Mode:* An agent commits a fact to `payment/webhook`, and another to `payments/webhooks`. Exact string matching filters out the conflict, creating two bifurcated realities.
- *Mitigation:* Candidate retrieval (Phase 3, Step 1) supplements precise scope filtering with entity-based cross-scope matching and a global high-similarity fallback.

**4. Semantic Collapse (Negation Blindness)** — from Bharti et al. [6]
- *Failure Mode:* "The auth service uses JWT" and "The auth service does not use JWT" produce nearly identical embeddings. Embedding-based candidate retrieval finds them (high similarity) but cannot distinguish agreement from contradiction. Worse, the LLM judge may also miss the negation due to agreeableness bias [12].
- *Mitigation:* BM25 lexical retrieval as a parallel candidate path catches negation keywords. Adversarial prompting forces the LLM to enumerate potential contradictions before judging. Entity-based matching ensures facts about the same service are always compared.

**5. Agreeableness Bias (Silent False Negatives)** — from Ahmed et al. [12]
- *Failure Mode:* The LLM contradiction judge has a True Negative Rate below 25% — it will say "not contradictory" for 75%+ of actual contradictions in single-shot evaluation.
- *Mitigation:* Adversarial prompt framing ("find contradictions" rather than "check if contradictory"). Minority-veto ensemble for high-stakes scopes (flag as contradictory if any of 3 runs says yes). Deterministic numeric/temporal pre-checks that bypass the LLM entirely for contradiction types it handles worst.

**6. The Mandela Effect (Corroborating Errors)** — from Xu et al. [8]
- *Failure Mode:* Agent A commits an incorrect fact. Agent B queries it, incorporates it, and commits a derived fact that reinforces the error. The knowledge base develops a self-reinforcing false belief that conflict detection cannot catch (because the facts *agree*, they just agree on something wrong).
- *Mitigation:* `source_fact_id` tracks derivation chains. The dashboard (Phase 7) should surface "citation depth" — clusters of facts that all trace back to a single source. Facts with no independent corroboration from different agents/engineers should be flagged as "single-source" in query results.

**7. Unbounded Growth (Retrieval Degradation)** — from SEDM [16]
- *Failure Mode:* Append-only means the facts table grows without bound. After months of team use, thousands of facts accumulate, many outdated or low-value. Query performance degrades, conflict detection becomes slower (more candidates), and signal-to-noise ratio drops.
- *Mitigation:* Phase 3b introduces utility-based decay, archival of low-utility old facts, and opt-in consolidation per scope.

**8. Pairwise Insufficiency (Missed Multi-Fact Inconsistencies)** — from He et al. [5]
- *Failure Mode:* Three facts A, B, C are each pairwise consistent but jointly inconsistent. Engram's pairwise detection misses this entirely.
- *Mitigation:* This is a known limitation. The current design accepts it as a tradeoff for tractability. Future work: implement the MUS-finding algorithm from He et al. [5] as a periodic batch job. For now, the dashboard should surface "fact clusters" within a scope to help humans spot multi-fact inconsistencies visually.

**9. SQLite Write Contention** — from operational analysis
- *Failure Mode:* SQLite serializes all writes with database-level locks. Under heavy concurrent agent commits, writes queue up and latency spikes.
- *Mitigation:* WAL mode + busy timeout for the MVP. The storage layer is abstracted behind an async interface so PostgreSQL can be swapped in for team deployments without changing the MCP API.

**10. Knowledge Conflict at the Consumer** — from Xu et al. [10]
- *Failure Mode:* Even when Engram returns correct, consistent facts, the consuming agent may ignore them in favor of its own parametric knowledge. LLMs exhibit unpredictable behavior when retrieved context conflicts with training data.
- *Mitigation:* Engram cannot control agent behavior, but it can help: query results include explicit confidence scores, provenance, and conflict status. The `engram_query` response format is designed to be unambiguous about what the shared knowledge base believes, even if the agent ultimately overrides it.

**11. Embedding Retrieval Degradation at Scale** — from Chana et al. [7]
- *Failure Mode:* The Orthogonality Constraint predicts that as semantically similar facts accumulate within a scope, embedding-based retrieval collapses. A scope like "auth" with 50+ facts will have high pairwise cosine similarity, making it increasingly difficult to retrieve the *right* fact.
- *Mitigation:* Entity-based retrieval (Path C in Phase 3) provides hash-based lookup that doesn't suffer from semantic interference. BM25 provides keyword-based retrieval that degrades gracefully. Consolidation (Phase 3b) keeps per-scope fact counts manageable.

**12. Numeric and Temporal Contradiction Blindness** — from [13]
- *Failure Mode:* "The rate limit is 100 req/s" vs. "The rate limit is 1000 req/s" — an order-of-magnitude contradiction — will likely be missed because embeddings are similar and LLMs systematically fail on numeric comparison. Temporal contradictions ("deprecated since v3" vs. "still supported in v4") require anchor resolution.
- *Mitigation:* Deterministic numeric/temporal pre-checks in Phase 3, Step 2 extract and compare values before the LLM is invoked. The `entities` field stores extracted numeric values with units for structured comparison.

**13. Memory Injection / Poisoning (MINJA-style attacks)** *(New — from arXiv:2503.03704 [19])*
- *Failure Mode:* An adversary calls `engram_commit` with content that appears legitimate but is semantically crafted to be retrieved by future queries and steer subsequent agents toward harmful or incorrect conclusions. The attack requires no special access — only normal agent interactions. Conflict detection cannot catch this because the poisoned fact is internally coherent (it doesn't contradict anything; it simply asserts something false). The append-only design makes the committed fact permanent. Success rates for MINJA-style attacks exceed 95%.
- *Mitigation:* (a) Add a `source_corroboration` count to `engram_query` results: facts corroborated by ≥2 *independent* agents (different `engineer` field) score higher; single-source facts in sensitive scopes are flagged. (b) Rate-limit `engram_commit` per `agent_id` to prevent bulk injection (default: 100 commits/hour). (c) For sensitive scopes (`infra/*`, `auth/*`, `secrets/*`), require a quorum of ≥2 engineers before a fact is indexed as current. (d) Track `source_fact_id` so derivation chains can be audited — a cluster of facts all derived from one unverified source is a poisoning signal.

**14. Silent Retrieval Corruption from Embedding Model Upgrade** *(New — from production RAG research [21])*
- *Failure Mode:* When `all-MiniLM-L6-v2` is upgraded or swapped for another model, stored embedding BLOBs are in an incompatible vector space. `engram_query` continues to return results with seemingly valid similarity scores, but the rankings are semantically meaningless. The conflict detection pipeline silently stops finding candidates across the version boundary. Users get no error — just silently wrong answers. The schema previously had no way to detect this had happened.
- *Mitigation:* (a) `embedding_model` and `embedding_model_ver` are now stored with every fact (added to schema). (b) At startup, validate the configured model against the model in the most recent facts; emit a warning and refuse to serve if they differ without explicit `--force-mismatch`. (c) Implement `engram reindex --model NEW_MODEL` to atomically re-embed all facts. (d) Before any embedding-model upgrade, document the reindex procedure in the ops runbook.

**15. Confidence Field Inflation (LLM Calibration Failure)** *(New — from calibration research [22])*
- *Failure Mode:* LLMs systematically report near-maximum confidence regardless of epistemic state (calibration gap of 15–40 percentage points). Engram uses `confidence` for severity classification, resolution priority, and agent reliability scoring. With uniformly high confidence, the severity classifier fires "high" for nearly every cross-agent conflict, flooding the queue; the higher-confidence-wins resolution strategy becomes effectively random; and agent reliability scores flatten to uninformative constants.
- *Mitigation:* (a) `confidence_source` field now distinguishes `'agent'` (raw self-report), `'system'` (computed from calibration), and `'calibrated'` (adjusted by historical contradiction rate). (b) Build a per-agent calibration table: `(agent_id, reported_confidence_bucket, empirical_contradiction_rate)` — updated whenever a conflict is resolved, using the loser's original confidence. (c) The conflict severity classifier should weight structural signals primarily (cross-engineer, same scope, both facts current) and treat `confidence` as a tiebreaker only when structural signals are ambiguous.

---

## What Engram is not building

The literature covers a large space. Several things are intentionally out of scope:

- **Parametric memory** (fine-tuning, LoRA adapters) — out of scope; Engram is a token-level system
- **Latent/KV-cache sharing** — the "cache sharing protocol" Yu et al. identify as missing; too deep in model internals
- **Episodic/procedural memory** (MIRIX's six types) — Engram stores *factual* memory about a shared codebase, not personal user history
- **RL-driven memory management** (Hu et al., §7.3) — the right long-term direction but requires evaluation infrastructure first
- **Multimodal memory** — text facts only in initial implementation; images and diagrams are a later extension
