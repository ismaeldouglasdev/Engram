# Literature

PDFs are in [`./papers/`](./papers/).

---

## [1] Multi-Agent Memory from a Computer Architecture Perspective: Visions and Challenges Ahead

**Authors:** Zhongming Yu, Naicheng Yu, Hejia Zhang, Wentao Ni, Mingrui Yin, Jiaying Yang, Yujie Zhao, Jishen Zhao
**Affiliations:** UC San Diego, Georgia Tech
**Venue:** Architecture 2.0 Workshop, March 23, 2026, Pittsburgh, PA
**ArXiv:** [2603.10062](https://arxiv.org/abs/2603.10062)
**File:** [`papers/2603.10062v1.pdf`](papers/2603.10062v1.pdf)

### Summary

This position paper — the direct intellectual foundation for Engram — frames multi-agent memory as a **computer architecture problem**. The central observation is that LLM agent systems are hitting a wall that looks exactly like the memory bottleneck in classical hardware: performance limited not by compute but by bandwidth, hierarchy, and consistency.

**Three-layer memory hierarchy:**
- *I/O layer* — interfaces ingesting audio, text, images, network calls (e.g., MCP)
- *Cache layer* — fast, limited-capacity short-term storage: compressed context, recent tool calls, KV caches, embeddings
- *Memory layer* — large-capacity long-term storage: full dialogue history, vector DBs, graph DBs

**Two missing protocols:**
1. *Agent cache sharing* — no principled protocol exists for one agent's cached artifacts to be transformed and reused by another (analogous to cache transfers in multiprocessors)
2. *Agent memory access control* — permissions, scope, and granularity for reading/writing another agent's memory remain under-specified

**Central claim:** The most pressing open challenge is **multi-agent memory consistency**. In single-agent settings, consistency means temporal coherence — new facts must not contradict established ones. In multi-agent settings, the problem compounds: multiple agents read from and write to shared memory concurrently, raising classical challenges of *visibility*, *ordering*, and *conflict resolution*. The difficulty is harder than hardware because memory artifacts are semantic and heterogeneous (evidence, tool traces, plans), and conflicts are often semantic and coupled to environment state.

**Relevance to Engram:** Engram directly implements the consistency layer this paper identifies as the field's most urgent gap. `engram_commit` is the shared write; `engram_query` is the read; `engram_conflicts` is the conflict detection mechanism. The paper's vocabulary — shared vs. distributed memory, hierarchy layers, consistency models — is the conceptual language of this project.

---

## [2] A-Mem: Agentic Memory for LLM Agents

**Authors:** Wujiang Xu, Zujie Liang, Kai Mei, Hang Gao, Juntao Tan, Yongfeng Zhang
**Affiliations:** Rutgers University, Independent Researcher, AIOS Foundation
**ArXiv:** [2502.12110](https://arxiv.org/abs/2502.12110) (v11, Oct 2025)
**File:** [`papers/2502.12110v11.pdf`](papers/2502.12110v11.pdf)

### Summary

A-Mem proposes a **Zettelkasten-inspired agentic memory system** that dynamically organizes memories without predefined schemas or fixed workflows. Its core contribution is that memory is not static storage — it actively evolves as new experiences arrive.

**Architecture:** Each memory is stored as a structured note:
```
mᵢ = {cᵢ, tᵢ, Kᵢ, Gᵢ, Xᵢ, eᵢ, Lᵢ}
```
where `c` = content, `t` = timestamp, `K` = LLM-generated keywords, `G` = tags, `X` = contextual description, `e` = embedding vector, `L` = links to related memories.

**Three-phase operation:**
1. *Note Construction* — LLM generates rich semantic attributes from raw interaction content
2. *Link Generation* — cosine similarity retrieves top-k neighbors; LLM determines whether semantic links should be established
3. *Memory Evolution* — when a new memory arrives, existing linked memories are updated: their context, keywords, and tags are revised to reflect the new knowledge

The result is a living knowledge graph where memories continuously deepen their connections and semantic representations as the agent accumulates experience.

**Results:** Outperforms MemGPT, MemoryBank, and ReadAgent on the LoCoMo long-form conversation QA benchmark across six foundation models (Llama 3.2, Qwen2.5, GPT-4o).

**Relevance to Engram:** A-Mem solves *single-agent* memory organization. It has no notion of shared state or cross-agent consistency. Engram operates at the layer above: once facts are committed to shared memory, Engram manages what happens when two agents' committed facts contradict each other — a problem A-Mem is not designed to address. A-Mem's note structure is instructive for how Engram might enrich committed facts with semantic metadata.

---

## [3] MIRIX: Multi-Agent Memory System for LLM-Based Agents

**Authors:** Yu Wang, Xi Chen
**Affiliation:** MIRIX AI (Yu Wang: UCSD, Xi Chen: NYU Stern)
**ArXiv:** [2507.07957](https://arxiv.org/abs/2507.07957) (v1, Jul 2025)
**File:** [`papers/2507.07957v1.pdf`](papers/2507.07957v1.pdf)

### Summary

MIRIX proposes a **modular, multi-agent memory system** organized around six specialized memory types — each managed by a dedicated agent — with a Meta Memory Manager handling routing.

**Six memory components:**
| Component | What it stores |
|---|---|
| Core Memory | High-priority persistent facts about user identity and agent persona |
| Episodic Memory | Time-stamped events, activities, interactions (a structured log) |
| Semantic Memory | Abstract concepts, entities, relationships independent of time |
| Procedural Memory | Step-by-step workflows and how-to guides |
| Resource Memory | Full documents, transcripts, multimedia files |
| Knowledge Vault | Sensitive verbatim facts: credentials, contacts, addresses (access-controlled) |

**Active Retrieval:** Rather than requiring explicit retrieval triggers, the system first generates a *topic* from the current query, then retrieves across all six components, injecting results into the system prompt. This eliminates the failure mode where LLMs default to stale parametric knowledge.

**Multi-agent workflow:** A Meta Memory Manager routes incoming data to the appropriate Memory Managers in parallel. On read, the Chat Agent performs coarse retrieval across all components, then targeted retrieval using whichever strategy (embedding_match, bm25_match, string_match) fits.

**Results:** SOTA 85.4% on LOCOMO (long-form conversation QA), outperforming prior best by 8 points. On a new multimodal benchmark (ScreenshotVQA, ~20K high-res screenshots), MIRIX achieves 35% higher accuracy than RAG baseline while using 99.9% less storage.

**Relevance to Engram:** MIRIX is the state-of-the-art in comprehensive single-user memory architecture. Its six-component taxonomy provides a rich vocabulary for what *kinds* of facts agents might commit. However, MIRIX is fundamentally single-user: its multi-agent architecture is internal (multiple agents managing one user's memory), not cross-team. Engram addresses what MIRIX does not: what happens when two engineers' agents independently commit contradictory facts about the same codebase to a shared store.

---

## [4] Memory in the Age of AI Agents: A Survey — Forms, Functions and Dynamics

**Authors:** Yuyang Hu, Shichun Liu, Yanwei Yue, Guibin Zhang, et al. (large collaborative team)
**Affiliations:** NUS, Renmin University of China, Fudan University, Peking University, NTU, Tongji University, UCSD, HKUST(GZ), Griffith University, Georgia Tech, OPPO, Oxford
**ArXiv:** [2512.13564](https://arxiv.org/abs/2512.13564) (v2, Jan 2026)
**File:** [`papers/2512.13564v2.pdf`](papers/2512.13564v2.pdf)

### Summary

The most comprehensive survey of agent memory as of early 2026. Proposes a unified taxonomy organized along three axes: **Forms** (what carries memory), **Functions** (why agents need memory), and **Dynamics** (how memory operates and evolves).

**Forms — three realizations:**
- *Token-level memory* — explicit discrete units (text, visual tokens): flat (1D), planar/graph (2D), or hierarchical (3D)
- *Parametric memory* — information encoded in model weights (fine-tuning, adapters, LoRA)
- *Latent memory* — information in internal hidden states, KV caches, continuous representations

**Functions — three purposes:**
- *Factual memory* — user facts and environment facts that sustain interaction consistency
- *Experiential memory* — case-based, strategy-based, skill-based knowledge accumulated through task execution
- *Working memory* — transient workspace information managed within a single task instance

**Dynamics — three lifecycle operators:**
- *Formation* — extracting and encoding information worth preserving
- *Evolution* — consolidation, updating, forgetting
- *Retrieval* — timing, query construction, strategy selection, post-processing

**Key distinctions:**
- Agent memory ≠ LLM memory (which concerns KV cache management and architecture-level context handling)
- Agent memory ≠ RAG (which retrieves from static external knowledge for single-task inference)
- Agent memory ≠ context engineering (which optimizes the context window as a resource)

**Multi-agent shared memory (Section 7.5):** Identified as a critical frontier. Early MAS used isolated local memories + message passing, suffering from redundancy and high communication overhead. Centralized shared stores helped but introduced *write contention* and *lack of permission-aware access control*. The survey calls for:
- *Agent-aware shared memory* — R/W conditioned on agent roles, expertise, and trust
- *Learning-driven conflict resolution* — training agents when/what/how to contribute based on team performance
- Shared memory that can abstract across heterogeneous signals while maintaining *temporal and semantic coherence*

**RL frontier (Section 7.3):** The field is moving from heuristic/prompt-driven memory management toward fully RL-driven systems where memory architecture and control policy are learned end-to-end.

**Relevance to Engram:** This survey provides the broadest context. It confirms that shared memory for multi-agent systems is an open frontier (Section 7.5) and that conflict detection and resolution are unsolved (referenced alongside RAMDocs, MADAM-RAG, and Zep). Engram's `engram_conflicts()` addresses exactly what this survey identifies as "write contention" and the need for "governance." The survey's taxonomy also gives Engram a precise vocabulary: Engram stores *factual memory* (environment facts about the codebase) in a *flat token-level* form with *append-only formation* and *explicit conflict evolution*.

---

## Landscape at a Glance

| Paper | Scope | Consistency | Conflict Detection | Year |
|---|---|---|---|---|
| Yu et al. [1] | Architecture framing | Named as #1 open problem | Not implemented | 2026 |
| Xu et al. [2] (A-Mem) | Single-agent memory organization | Temporal coherence only | No | 2025 |
| Wang & Chen [3] (MIRIX) | Single-user multi-component memory | Within one user's store | No | 2025 |
| Hu et al. [4] (Survey) | Full landscape | Flagged as unsolved frontier | No | 2026 |
| **Engram** | **Multi-agent shared memory** | **Cross-agent fact consistency** | **Yes (`engram_conflicts`)** | **2026** |

The gap Engram fills is visible in every row of the right two columns: every existing system either does not address cross-agent consistency or names it as unsolved. Engram is the first working implementation of the detection layer.


---

# Adversarial Literature: Failure Modes and Falsification Risks

The following papers and sources were identified through targeted search for research that could falsify or expose critical weaknesses in Engram's implementation plan. They are organized by the specific assumption they threaten.

---

## [5] Foundations of Global Consistency Checking with Noisy LLM Oracles

**Authors:** Paul He et al.
**ArXiv:** [2601.13600](https://arxiv.org/abs/2601.13600) (Jan 2026)

### Summary

This paper formalizes the problem Engram's conflict detection attempts to solve — and proves it is exponentially hard in the worst case. The authors show that verifying global consistency across a collection of natural-language facts requires exponentially many oracle queries when the oracle (LLM) is noisy. Pairwise checks are provably insufficient to guarantee global coherence. They propose an adaptive divide-and-conquer algorithm that identifies minimal inconsistent subsets (MUSes) with polynomial query complexity.

### Threat to Engram

Engram's Phase 3 conflict detection relies on pairwise LLM contradiction checks between a new fact and its embedding-similar neighbors. This paper proves that pairwise checking cannot guarantee global consistency. Three facts A, B, C may each be pairwise consistent while being jointly inconsistent (e.g., A: "service X uses PostgreSQL", B: "service X uses the same DB as service Y", C: "service Y uses MySQL"). Engram would miss this entirely. The paper's MUS-finding algorithm should inform a future revision of the detection pipeline.

---

## [6] Negation is Not Semantic: Diagnosing Dense Retrieval Failure Modes for Contradiction-Aware Biomedical QA

**Authors:** Divya Bharti et al.
**ArXiv:** [2603.17580](https://arxiv.org/abs/2603.17580) (Mar 2026)

### Summary

Demonstrates a "Simplicity Paradox" and "Semantic Collapse" in dense retrieval for contradiction detection. Complex adversarial dense retrieval strategies failed catastrophically at contradiction detection (MRR 0.023) because negation signals become indistinguishable in vector space. The authors also identify a "Retrieval Asymmetry": filtering dense embeddings improves contradiction detection but degrades support recall. Their solution is a Decoupled Lexical Architecture using BM25 as a backbone.

### Threat to Engram

Engram's candidate retrieval (Phase 3, Step 1) uses cosine similarity on embeddings to find facts that might contradict a new commit. But this paper shows that contradictory facts — which often differ only by negation or a single changed predicate — produce nearly identical embeddings. "The auth service uses JWT tokens" and "The auth service does not use JWT tokens" will have very high cosine similarity, which is correct for retrieval but means the 0.65 similarity threshold is meaningless as a filter for contradiction candidates. Worse, truly contradictory facts about different aspects of the same system may have *lower* similarity than non-contradictory facts about the same topic, causing them to be missed entirely. The implementation should add BM25/lexical retrieval as a parallel candidate retrieval path.

---

## [7] Attention Is Not Retention: The Orthogonality Constraint in Infinite-Context Architectures

**Authors:** Simran Chana et al.
**ArXiv:** [2601.15313](https://arxiv.org/abs/2601.15313) (Jan 2026)

### Summary

Identifies a fundamental geometric limit called the "Orthogonality Constraint": reliable memory retrieval requires orthogonal keys, but semantic embeddings cannot be orthogonal because training clusters similar concepts together. The result is "Semantic Interference" — neural systems writing facts into shared continuous parameters collapse to near-random accuracy within tens of semantically related facts. At high semantic density (ρ > 0.6), collapse occurs at just N=5 facts. The authors propose "Knowledge Objects" (KOs): structured facts with hash-based identity, controlled vocabularies, and explicit version chains. Hash-based retrieval maintains 100% accuracy where embedding-based retrieval collapses to near-zero.

### Threat to Engram

Engram stores codebase facts that are inherently high semantic density — many facts about the same services, APIs, and architectural decisions. The Orthogonality Constraint predicts that as facts accumulate within a scope, embedding-based retrieval will degrade. A scope like "auth" with 50+ facts about authentication will have high pairwise cosine similarity (ρ likely > 0.6), making it increasingly difficult to retrieve the *right* fact vs. any fact in that scope. The Knowledge Objects proposal — hash-based identity with controlled vocabularies — aligns with adding structured metadata (entity extraction, relation triples) to complement pure embedding retrieval.

---

## [8] When Agents "Misremember" Collectively: Exploring the Mandela Effect in LLM-based Multi-Agent Systems

**Authors:** Naen Xu et al.
**ArXiv:** [2602.00428](https://arxiv.org/abs/2602.00428) (Jan 2026)

### Summary

Demonstrates that LLM-based multi-agent systems are susceptible to collective false memory — the "Mandela Effect" — where agents reinforce each other's incorrect beliefs through social influence and internalized misinformation. The authors propose MANBENCH, a benchmark for evaluating this across four task types and five interaction protocols. Mitigation strategies (cognitive anchoring, source scrutiny, alignment-based defense) achieve 74.40% reduction in the effect.

### Threat to Engram

Engram's shared memory could become a vector for the Mandela Effect at scale. If Agent A commits an incorrect fact with high confidence, Agent B queries it, incorporates it into its reasoning, and then commits a *derived* fact that reinforces the original error, the knowledge base develops a self-reinforcing false belief. Engram's conflict detection only catches *contradictions* — it cannot detect *corroborating errors* where multiple agents agree on something false. The confidence field and agent provenance help, but there is no mechanism to flag when a cluster of facts all trace back to a single unverified source. A "citation depth" or "independent corroboration" metric should be considered.

---

## [9] Why Do Multi-Agent LLM Systems Fail?

**Authors:** Mert Cemri, Melissa Z. Pan, Shuyi Yang, et al. (UC Berkeley, Stanford)
**ArXiv:** [2503.13657](https://arxiv.org/abs/2503.13657) (Mar 2025)

### Summary

Introduces MAST, the first Multi-Agent System Failure Taxonomy, based on analysis of 1600+ annotated traces across 7 popular MAS frameworks. Identifies 14 unique failure modes in 3 categories: (i) system design issues, (ii) inter-agent misalignment, and (iii) task verification. Inter-agent misalignment accounts for 36.9% of failures, including agents ignoring, duplicating, or contradicting each other's work.

### Threat to Engram

Engram addresses contradiction (one failure mode) but the taxonomy reveals that inter-agent misalignment is broader: agents may *duplicate* work (committing semantically identical facts with different wording, bloating the knowledge base), *ignore* shared knowledge (querying but not incorporating results), or *misinterpret* facts from other agents (reading a fact correctly but applying it in the wrong context). Engram's current design has no deduplication mechanism — two agents committing "the payments service uses Stripe" and "Stripe is the payment processor for the payments module" would create two separate facts with no link between them, despite being the same knowledge. Near-duplicate detection should be added alongside contradiction detection.

---

## [10] Knowledge Conflicts for LLMs: A Survey

**Authors:** Rongwu Xu et al.
**ArXiv:** [2403.08319](https://arxiv.org/abs/2403.08319) (Mar 2024)

### Summary

Comprehensive survey of knowledge conflicts in LLMs, categorizing three types: context-memory conflict (retrieved context vs. parametric knowledge), inter-context conflict (contradictions between retrieved documents), and intra-memory conflict (inconsistencies within the model's own parameters). The survey documents that LLMs exhibit unpredictable behavior when faced with conflicting information — sometimes favoring context, sometimes parametric knowledge, with no reliable pattern.

### Threat to Engram

When `engram_query` returns facts that conflict with an agent's parametric knowledge, the agent's behavior is unpredictable. An agent might ignore a high-confidence Engram fact in favor of its training data, or vice versa. This means Engram's carefully curated knowledge base may be overridden silently by the consuming agent's own biases. The implementation cannot control what agents *do* with retrieved facts, but it can surface confidence signals and provenance more aggressively to help agents make informed decisions about which knowledge source to trust.

---

## [11] Common Sense vs. Morality: The Curious Case of Narrative Focus Bias in LLMs

**Authors:** Sukannya Purkayastha et al.
**ArXiv:** [2603.09434](https://arxiv.org/abs/2603.09434) (Mar 2026)

### Summary

Reveals that LLMs exhibit "narrative focus bias" — they more readily detect contradictions attributed to secondary characters/entities than to the primary narrator/subject. Across ten LLMs of different sizes, models consistently struggle to identify contradictions without prior signal.

### Threat to Engram

Engram's conflict detection prompt (Phase 3, Step 2) presents two facts and asks the LLM whether they contradict. The narrative focus bias suggests the LLM may be systematically worse at detecting contradictions in facts about the *primary* system under discussion (e.g., the main service being developed) vs. peripheral systems. Since most Engram facts will be about the primary codebase, this bias directly degrades detection accuracy on the most important facts. The prompt should be designed to mitigate this — potentially by reframing facts in a neutral, third-person structure.

---

## [12] Beyond Consensus: Mitigating the Agreeableness Bias in LLM Judge Evaluations

**Authors:** Umair Z. Ahmed et al.
**ArXiv:** [2510.11822](https://arxiv.org/abs/2510.11822) (Oct 2025)

### Summary

Demonstrates that LLMs used as judges exhibit strong positive bias: True Positive Rate > 96% but True Negative Rate < 25%. They are good at confirming valid outputs but remarkably poor at identifying invalid ones. Ensemble methods help but are insufficient; the authors propose minority-veto and regression-based debiasing.

### Threat to Engram

Engram uses an LLM (claude-haiku) as a judge to determine whether two facts contradict. The agreeableness bias predicts that the LLM will be biased toward saying facts are *not* contradictory (the "agreeable" answer). With a True Negative Rate potentially below 25%, Engram could miss 75%+ of actual contradictions. This is the single most dangerous failure mode for the core differentiator. Mitigation: use a minority-veto ensemble (run the contradiction check N times, flag as contradictory if *any* run says yes), or fine-tune the prompt to counteract the bias by asking "in what ways could these facts be contradictory?" before asking for a yes/no judgment.

---

## [13] The Messy Reality of Contradiction Detection in NLP

**Source:** [httphangar.com/blog/nlp-contradiction-deep-dive](https://httphangar.com/blog/nlp-contradiction-deep-dive) (2025)

### Summary

Practical analysis of contradiction detection accuracy across LLMs. Key findings: self-contradictions within a single document are detected at 0.6%–45.6% accuracy. Pairwise contradictions between documents reach ~89% with chain-of-thought prompting. Numeric contradictions (unit mismatches, order-of-magnitude errors) are systematically missed by embedding models. Temporal contradictions require anchor resolution that LLMs cannot perform without explicit date context. Negation scope is the messiest category — "not ruled out" vs. "confirmed" requires deep pragmatic understanding.

### Threat to Engram

Codebase facts are rich in numeric values (port numbers, timeout values, version numbers, rate limits) and temporal references ("deprecated since v3", "migrated last sprint"). These are exactly the contradiction types that LLMs handle worst. "The rate limit is 100 req/s" vs. "The rate limit is 1000 req/s" — an order-of-magnitude contradiction — will likely be missed because the embedding similarity is high and the LLM judge may not flag a numeric difference as a contradiction. The implementation should add specialized numeric and temporal extraction as a pre-processing step before the LLM contradiction check.

---

## [14] Semantics at an Angle: When Cosine Similarity Works Until It Doesn't

**Authors:** Kisung You et al.
**ArXiv:** [2504.16318](https://arxiv.org/abs/2504.16318) (Apr 2025)

### Summary

Examines the limitations of cosine similarity for embedding comparison. Key finding: when embedding norms carry meaningful semantic information (e.g., specificity, confidence, or frequency), cosine similarity discards this signal by normalizing vectors. Additionally, anisotropy in pretrained embedding spaces causes scores to concentrate in a narrow high-similarity band regardless of actual semantic relatedness, limiting interpretability as a quantitative measure.

### Threat to Engram

Engram uses cosine similarity with a fixed threshold (0.65) to filter contradiction candidates and a weighted score (α=0.7) for query ranking. If the embedding space is anisotropic (which `all-MiniLM-L6-v2` is known to be), most fact pairs will cluster in a narrow similarity band (e.g., 0.6–0.8), making the 0.65 threshold nearly meaningless — it will either admit almost everything or almost nothing depending on the domain. The scoring function should use calibrated similarity or relative ranking rather than absolute thresholds.

---

## [15] Collaborative Memory: Multi-User Memory Sharing in LLM Agents with Dynamic Access Control

**Authors:** Yuying Zhao et al.
**ArXiv:** [2505.18279](https://arxiv.org/abs/2505.18279) (May 2025)

### Summary

Introduces a framework for multi-user, multi-agent environments with asymmetric, time-evolving access controls encoded as bipartite graphs. Maintains two memory tiers: private fragments (visible only to originating user) and shared fragments (selectively shared). Each fragment carries immutable provenance attributes. Granular read/write policies enforce user-agent-resource constraints with context-aware transformations.

### Threat to Engram

This paper implements a more sophisticated version of Engram's Phase 5 (access control). Engram's scope-based permissions (Phase 5) are static and coarse — an agent either can or cannot read/write a scope. Collaborative Memory's bipartite graph model supports time-evolving, asymmetric policies where access depends on the relationship between the requesting agent, the originating user, and the resource. Engram's simple `scope_permissions` table may be insufficient for real team deployments where, e.g., a junior engineer's agent should be able to read but not write to architecture-level scopes, or where access should change based on project phase. The access control model should be designed with extensibility toward graph-based policies.

---

## [16] SEDM: Scalable Self-Evolving Distributed Memory for Agents

**Authors:** Haoran Xu et al.
**ArXiv:** [2509.09498](https://arxiv.org/abs/2509.09498) (Sep 2025)

### Summary

Addresses the unbounded growth problem in multi-agent memory. SEDM integrates verifiable write admission (based on reproducible replay), a self-scheduling memory controller that dynamically ranks and consolidates entries according to empirical utility, and cross-domain knowledge diffusion. Key insight: memory must be an active, self-optimizing component, not a passive repository.

### Threat to Engram

Engram's append-only design means the facts table grows without bound. There is no consolidation, no forgetting, no utility-based ranking. Over months of team use, the knowledge base will accumulate thousands of facts, many outdated or low-value. Query performance degrades (more candidates to score), conflict detection becomes slower (more pairwise comparisons), and the signal-to-noise ratio drops. SEDM's "verifiable write admission" — requiring that a fact's value be demonstrable before it is stored — is a direct challenge to Engram's "commit everything, sort it out later" philosophy. The implementation should plan for a consolidation phase that periodically merges, summarizes, or archives low-utility facts.

---

## [17] Learning to Share: Selective Memory for Efficient Parallel Agentic Systems

**Authors:** Joseph Fioresi et al.
**ArXiv:** [2602.05965](https://arxiv.org/abs/2602.05965) (Feb 2026)

### Summary

Proposes a learned shared-memory mechanism for parallel agent frameworks. A lightweight controller trained via stepwise RL decides whether intermediate agent steps should be added to a global memory bank. The controller learns to identify information that is globally useful across parallel executions, significantly reducing runtime while matching or improving task performance.

### Threat to Engram

Engram treats all committed facts equally — any agent can commit anything. LTS demonstrates that *learned admission control* (deciding what is worth sharing) dramatically improves efficiency. Without admission control, Engram will accumulate low-value facts that dilute retrieval quality. The confidence field is agent-reported and unreliable (agents tend to report high confidence). A learned or heuristic admission gate — even a simple one based on novelty relative to existing facts — would improve the signal-to-noise ratio.

---

## [18] MMA: Multimodal Memory Agent

**Authors:** Zeyu Zhang et al.
**ArXiv:** [2602.16493](https://arxiv.org/abs/2602.16493) (Feb 2026)

### Summary

Proposes dynamic reliability scoring for retrieved memory items by combining source credibility, temporal decay, and conflict-aware network consensus. Introduces the concept of abstaining when support is insufficient. Uncovers the "Visual Placebo Effect" where RAG-based agents inherit latent biases from foundation models.

### Threat to Engram

Engram's query scoring (Phase 2) uses a simple `α * cosine_similarity + (1-α) * recency_decay` formula. MMA demonstrates that source credibility and conflict-aware consensus are critical additional signals. A fact from an agent that has historically committed many later-contradicted facts should be scored lower. Engram has the data to compute this (agent_id + conflict history) but doesn't use it in the scoring function. The query ranking should incorporate agent reliability as a signal.

---

## Existing Competitive Implementations

Several existing projects occupy adjacent space and should be monitored:

- **[mem0](https://github.com/mem0ai/mem0)** — Universal memory layer for AI agents. 40k+ GitHub stars. Handles single-user memory well but has no cross-agent conflict detection. The most likely project to add this feature and compete directly.
- **[SAMEP](https://arxiv.org/abs/2507.10562)** — Secure Agent Memory Exchange Protocol. Implements persistent, secure, semantically searchable memory sharing with AES-256-GCM encryption and MCP/A2A compatibility. More mature security model than Engram's planned Phase 5.
- **[shared-memory-mcp](https://github.com/haasonsaas/shared-memory-mcp)** — Shared memory MCP server for agentic teams. Focuses on token efficiency and context deduplication rather than consistency, but occupies the same "shared MCP memory" niche.
- **[Memorix](https://github.com/AVIDS2/memorix)** — Cross-agent memory bridge for 10+ IDEs. Team collaboration features, workspace sync. No conflict detection but broad IDE integration.

---

## [19] MINJA: A Practical Memory Injection Attack against LLM Agents

**Authors:** Anonymous / Researcher team
**ArXiv:** [2503.03704](https://arxiv.org/abs/2503.03704) (Mar 2025)

### Summary

MINJA demonstrates that an adversary can poison a shared agent memory system **without any direct access to the memory store** — using only normal query interactions. The attack has three stages: (1) *Bridging steps* — the attacker crafts a malicious reasoning chain that connects a likely future victim query to a harmful conclusion; (2) *Indication prompts* — the attacker sends queries that cause the agent to store the malicious chain as a memory record; (3) *Progressive shortening* — the explicit attack prompts are gradually removed so the stored record appears benign. When a victim later queries the system with a matching term, the poisoned record is retrieved and the agent follows the malicious reasoning. Success rates exceed 95% across healthcare and web-automation task domains.

### Threat to Engram

Engram's shared memory is a textbook target for MINJA-style attacks. Any agent (or external actor impersonating an agent) can call `engram_commit` with carefully crafted `content` that looks like a legitimate fact but is semantically optimized to be retrieved by future queries and steer subsequent agents toward wrong conclusions. Because Engram's conflict detection only checks for *contradictions*, it will not flag a fact that is internally coherent but subtly false. There is currently no write-admission gate, no content anomaly detection, no rate-limiting per agent, and no cryptographic signing of committed facts. The append-only design means a poisoned fact, once committed, is permanent. A "source integrity" metric — tracking how many independent agents corroborate a fact vs. how many derive from a single agent — should be added to the scoring function.

---

## [20] SQLite WAL Mode: Single-Writer Serialization Under Concurrent Agent Load

**Source:** SQLite official documentation; "SQLite and Concurrent Writes" analysis by berthub.eu and tenthousandmeters.com (2024–2025)

### Summary

SQLite in WAL mode (Write-Ahead Logging) allows unlimited concurrent *readers* but enforces a **global single-writer lock**: regardless of the number of processes or async tasks, all write operations are serialized through a single mutex. In multi-process deployments, write contention manifests as `SQLITE_BUSY` errors. A particularly dangerous failure pattern occurs when a transaction begins as a read (`BEGIN`), performs a `SELECT`, and then attempts an upgrade to a write (`INSERT`/`UPDATE`): if another writer has acquired the lock in the interim, the upgrade fails and must restart. In agentic systems where LLM inference (multiple seconds) occurs between a read and its dependent write — a common pattern in Engram's conflict pipeline — this window of lock contention is wide rather than narrow.

### Threat to Engram

Engram's conflict detection pipeline (Phase 3) has a critical read-then-write pattern: it reads candidate facts, calls an LLM to check for contradictions (which takes 1–5 seconds), and then writes a conflict record. Under concurrent agent commits from multiple engineers, this multi-second LLM call will hold an open transaction or cause repeated `SQLITE_BUSY` retries. The implementation plan mentions atomic transactions for the `superseded_by` update but does not address the broader write-contention problem across the full conflict pipeline. **Concrete risks:** (a) under load, `engram_commit` latency spikes to seconds; (b) without `PRAGMA busy_timeout`, writes will fail immediately with `SQLITE_BUSY` rather than retrying; (c) the WAL file can grow unboundedly if frequent long-read transactions ("checkpoint starvation") prevent checkpointing. The implementation should explicitly set `PRAGMA busy_timeout`, use `BEGIN IMMEDIATE` for all write transactions, perform LLM calls *outside* of open transactions, and include monitoring for WAL file size. Long-term scaling (>10 concurrent engineers) will likely require migrating write coordination to a centralized writer process or switching to PostgreSQL.

---

## [21] Silent Index Corruption from Embedding Model Upgrades

**Sources:** "On the Theoretical Limitations of Embedding-Based Retrieval" (arXiv, 2025), production RAG engineering reports (Weaviate, Medium, Reddit, 2024–2025)

### Summary

When the model used to encode stored embeddings is upgraded — even a minor version change — the geometry of the vector space changes. Old stored embeddings and new query embeddings live in **incompatible coordinate systems**. Crucially, the system does not error: it silently returns lower-quality or semantically incorrect results. This "silent degradation" is one of the most common production failures in RAG systems. Partial re-embedding (indexing new documents with the new model while leaving old ones in the original space) is especially dangerous: retrieval becomes unpredictable because the same index contains two incompatible coordinate systems. Studies show that relevance scores drop dramatically and top-k hits are often semantically wrong, but users and agents receive no signal that anything is wrong.

### Threat to Engram

Engram stores `embedding BLOB` directly in the SQLite `facts` table as serialized `float32` vectors. There is no metadata recording *which embedding model and version* produced each vector. If a user upgrades `all-MiniLM-L6-v2` to a newer `sentence-transformers` release, or switches to a better model (e.g., `all-mpnet-base-v2`), all queries will generate vectors in a different space from the stored ones. `engram_query` will continue to return results — with confidently-scored similarity values — but those results will be semantically meaningless. The conflict detection pipeline will also silently fail: candidate retrieval will miss real contradictions because old and new embeddings are incommensurable. **Mitigations required:** (a) Store `embedding_model` and `embedding_model_version` alongside every fact; (b) Add an admin command `engram reindex --model NEW_MODEL` that re-embeds all facts and updates the stored blobs; (c) Raise a startup warning if the configured model differs from the model recorded in the most recent facts.

---

## [22] LLM Self-Reported Confidence is Systematically Overconfident

**Sources:** "Holistic Trajectory Calibration for LLM Agents" (arXiv, 2025); "LLM Confidence Calibration Survey" (arXiv, 2025); NeurIPS 2024 calibration workshop papers

### Summary

All major LLMs exhibit systematic overconfidence: their self-reported or behavior-derived confidence estimates substantially overstate their actual accuracy. This effect intensifies in multi-step agentic contexts, where errors compound over trajectories. Post-training alignment (RLHF) further inflates confidence by incentivizing "decisive" answers. Studies measuring calibration — how well reported confidence correlates with empirical accuracy — consistently find gaps of 15–40 percentage points. LLMs also exhibit "heightened suggestibility": they will absorb incorrect facts from their context and then report high confidence in those facts in subsequent queries, creating a dangerous loop when operating against a shared memory store.

### Threat to Engram

Engram's schema includes a `confidence REAL NOT NULL` field described as "agent-reported, 0.0–1.0." This value is used in: (a) conflict severity classification (high-confidence facts from two different engineers = high severity); (b) conflict resolution (higher-confidence fact wins); (c) query scoring in Phase 8's proposed "agent reliability" signal (MMA). But if LLMs systematically report high confidence — as the literature shows — then: the severity classifier will fire "high" for nearly every cross-agent conflict (inflating the conflict queue); the higher-confidence-wins resolution strategy will be effectively random (since both facts will report near-1.0 confidence); and the agent reliability score will be flat and uninformative. The implementation must treat agent-reported confidence as a noisy signal, not a ground truth. **Mitigations:** (a) Normalize confidence using historical calibration per agent (divide reported confidence by that agent's empirical contradiction rate); (b) Add a `confidence_source` field distinguishing agent-self-reported vs. system-computed; (c) Make the severity classifier primarily dependent on structural signals (same vs. different engineer, scope overlap) rather than confidence values.

---

## Revised Landscape at a Glance

| Paper/System | Scope | Consistency | Conflict Detection | Threat Level to Engram |
|---|---|---|---|---|
| He et al. [5] (Global Consistency) | Theory | Proves pairwise insufficient | Proposes MUS algorithm | **Critical** — undermines core detection approach |
| Bharti et al. [6] (Semantic Collapse) | Retrieval | Shows embedding failure for negation | N/A | **Critical** — candidate retrieval will miss contradictions |
| Chana et al. [7] (Orthogonality) | Retrieval | Shows embedding degradation at scale | N/A | **High** — retrieval degrades as facts accumulate |
| Xu et al. [8] (Mandela Effect) | Multi-agent | Shows collective false memory | N/A | **High** — Engram could amplify errors |
| Cemri et al. [9] (MAS Failures) | Multi-agent | 36.9% failures from misalignment | N/A | **Medium** — contradiction is only one failure mode |
| Ahmed et al. [12] (Agreeableness) | LLM-as-Judge | Shows 75%+ false negative rate | N/A | **Critical** — LLM judge will miss most contradictions |
| httphangar [13] (Messy Reality) | Detection | 0.6%–45.6% accuracy on self-contradictions | N/A | **High** — numeric/temporal contradictions missed |
| Zhao et al. [15] (Collaborative Memory) | Access control | Dynamic asymmetric policies | N/A | **Medium** — more sophisticated than Engram's Phase 5 |
| Xu et al. [16] (SEDM) | Scalability | Self-evolving consolidation | N/A | **High** — append-only will not scale |
| mem0 | Production | Single-user | No | **Medium** — could add conflict detection |
| SAMEP | Protocol | Secure sharing | No | **Medium** — better security model |
| arXiv:2503.03704 (MINJA) | Security | Memory injection via queries | N/A | **Critical** — Engram has no write-admission defense |
| SQLite WAL docs | Storage | Single-writer serialization | N/A | **High** — parallel agent commits will stall under load |
| Embedding drift (arXiv:2025) | Storage | Silent index corruption on upgrade | N/A | **High** — stored blobs become stale after model swap |
| Confidence calibration (arXiv:2025) | Epistemics | LLM self-reported confidence unreliable | N/A | **High** — `confidence` field is systematically inflated |

---

# Round 2: Falsification Research — Unifying Abstractions and Competitive Threats

The following papers, systems, and open-source projects were identified through a second round of targeted adversarial research. The goal was to find evidence that could force a major architectural change or reveal a simplifying abstraction that the current implementation plan misses. Several findings meet that bar.

---

## [23] NLI Cross-Encoders as a Replacement for LLM-as-Judge Contradiction Detection

**Model:** `cross-encoder/nli-deberta-v3-base` (Microsoft DeBERTa-v3, fine-tuned on SNLI + MultiNLI)
**Source:** [Hugging Face](https://huggingface.co/cross-encoder/nli-deberta-v3-base)
**Performance:** 92.38% accuracy on SNLI test set, 90.04% on MNLI mismatched set

### Summary

A cross-encoder NLI model that takes a sentence pair and outputs three scores: contradiction, entailment, neutral. Runs locally via `sentence-transformers` or raw `transformers`. Inference is ~10ms per pair on CPU, ~2ms on GPU. The model is ~400MB (DeBERTa-v3-base). No API calls, no cost per invocation, deterministic output.

### Threat to Engram — **CRITICAL (Simplifying)**

This is the single most important finding in this research round. Engram's Phase 3 conflict detection pipeline currently relies on an LLM (claude-haiku) as the contradiction judge — a design that is slow (~1-5s per pair), expensive (API cost per commit), non-deterministic, and subject to the agreeableness bias documented in [12] (75%+ false negative rate). The NLI cross-encoder offers a fundamentally different approach:

- **Speed:** ~10ms per pair vs. ~2000ms for an LLM call. This means Engram could check a new fact against 30 candidates in ~300ms total, making conflict detection effectively synchronous rather than requiring an async pipeline.
- **Cost:** Zero marginal cost per check (model runs locally). Eliminates the LLM API dependency for the core differentiating feature.
- **Determinism:** Same input always produces the same output. No agreeableness bias, no prompt sensitivity, no ensemble needed for consistency.
- **Accuracy:** 92% on general NLI benchmarks. While this is on general text (not codebase-specific facts), it provides a strong baseline that can be improved with domain-specific fine-tuning.

The architectural implication is profound: the entire Phase 3 pipeline could be restructured as a **tiered detection system** where the NLI cross-encoder serves as a fast, cheap first pass, and the LLM judge is reserved only for cases where the NLI model returns ambiguous scores (e.g., contradiction score between 0.3 and 0.7). This eliminates the LLM-as-judge as a single point of failure and reduces the async complexity that drives several of the identified failure modes (race conditions, SQLite write contention during LLM calls, etc.).

**Limitations:** NLI models trained on SNLI/MNLI may not generalize perfectly to technical codebase facts. "The auth service uses JWT" vs. "The auth service does not use JWT" should be caught (simple negation), but "The rate limit is 100 req/s" vs. "The rate limit is 1000 req/s" may still require the numeric pre-check. Domain-specific fine-tuning on a small dataset of codebase contradiction pairs would likely close this gap.

---

## [24] SummaC: Sentence-Level NLI Aggregation for Document Consistency

**Authors:** Philippe Laban et al.
**Venue:** TACL 2022
**ArXiv:** [2111.09525](https://arxiv.org/abs/2111.09525)
**GitHub:** Referenced in Hugging Face ecosystem

### Summary

SummaC demonstrates that NLI models, which are trained on sentence pairs, can be effectively applied to document-level consistency checking through a segmentation-and-aggregation strategy called SummaCConv. The approach segments documents into sentences, computes pairwise NLI scores between all sentence pairs, bins the scores into histograms, and applies a learned convolutional aggregator to produce a document-level consistency score. Achieves 74.4% balanced accuracy on a benchmark of six inconsistency detection datasets.

### Threat to Engram — **High (Simplifying)**

SummaC's architecture maps directly onto Engram's problem. Engram facts are short text statements (typically 1-3 sentences). The SummaCConv pattern — pairwise NLI scoring between a new fact and all candidates, followed by aggregation — is exactly what Engram's conflict detection pipeline needs. Combined with finding [23], this suggests a concrete architecture:

1. New fact arrives → segment into atomic claims
2. Retrieve candidates (embedding + BM25 + entity, as currently planned)
3. Run NLI cross-encoder on all (new_claim, candidate_claim) pairs (~300ms total)
4. Aggregate scores: if max contradiction score > threshold, flag as conflict
5. Only escalate to LLM judge for ambiguous cases or when explanation text is needed

This eliminates the LLM from the hot path entirely.

---

## [25] CLAIRE: Corpus-Level Inconsistency Detection at Scale

**Authors:** Sina Semnani et al.
**Venue:** EMNLP 2025
**ArXiv:** [2509.23233](https://arxiv.org/abs/2509.23233)

### Summary

CLAIRE is an agentic system for corpus-level inconsistency detection in Wikipedia. It combines LLM reasoning with retrieval to surface potentially inconsistent claims with contextual evidence. In a user study with experienced Wikipedia editors, 87.5% reported higher confidence when using CLAIRE, and participants identified 64.7% more inconsistencies. Key finding: at least 3.3% of English Wikipedia facts contradict another fact. The best fully automated system achieves only 75.1% AUROC on the WIKICOLLIDE benchmark.

### Threat to Engram — **High (Calibrating)**

CLAIRE provides the first empirical baseline for what Engram should expect: even in a well-curated corpus like Wikipedia, ~3.3% of facts are inconsistent. In a less-curated multi-agent knowledge base, the rate will be higher. More importantly, the 75.1% AUROC ceiling for fully automated detection means Engram should not promise perfect conflict detection — it should be designed as a human-in-the-loop system from the start, with the dashboard (Phase 7) being more critical than previously assumed. CLAIRE's architecture (retrieval + LLM reasoning + human review) validates Engram's general approach but suggests the detection pipeline should be optimized for recall over precision, surfacing more candidates for human review rather than trying to be a perfect automated judge.

---

## [26] CodeCRDT: CRDT-Based Coordination for Multi-Agent LLM Systems

**Authors:** Sergey Pugachev et al.
**ArXiv:** [2510.18893](https://arxiv.org/abs/2510.18893) (Oct 2025)

### Summary

CodeCRDT applies Conflict-Free Replicated Data Types (CRDTs) to multi-agent LLM code generation. Instead of explicit message passing, agents coordinate by monitoring a shared state with observable updates and deterministic convergence. Evaluation across 600 trials shows 100% convergence with zero merge failures, though with mixed performance results (up to 21.1% speedup on some tasks, up to 39.4% slowdown on others). Semantic conflict rates of 5-10% were observed.

### Threat to Engram — **Medium (Architectural Alternative)**

CodeCRDT demonstrates that CRDTs can provide strong eventual consistency for multi-agent LLM systems without centralized coordination. This challenges Engram's centralized SQLite-based architecture for Phase 6 (federation). If Engram's fact store were modeled as a CRDT (specifically, a grow-only set with metadata), federation would get strong eventual consistency for free — no custom sync protocol needed. The 5-10% semantic conflict rate observed in CodeCRDT aligns with CLAIRE's 3.3% finding and provides a useful baseline for Engram's expected conflict volume.

However, CRDTs resolve conflicts automatically through deterministic merge rules, which is the opposite of Engram's philosophy (conflicts are structured artifacts for human review). The CRDT approach would need to be adapted: use CRDTs for the replication/sync layer, but surface semantic conflicts as a separate concern on top.

---

## [27] Semantic Conflict Model for Collaborative Data Structures

**Authors:** Georgii Semenov et al.
**ArXiv:** [2602.19231](https://arxiv.org/abs/2602.19231) (Feb 2026)

### Summary

Introduces a conflict model for collaborative data structures that enables explicit, local-first conflict resolution without central coordination. The model identifies conflicts using semantic dependencies between operations and resolves them by rebasing conflicting operations onto a reconciling operation via a three-way merge over a replicated journal. Demonstrates the approach on collaborative registers including an explicit Last-Writer-Wins Register and a multi-register entity supporting semi-automatic reconciliation.

### Threat to Engram — **High (Unifying Abstraction)**

This paper describes almost exactly what Engram needs for its federation layer (Phase 6) and conflict resolution workflow (Phase 4). The "replicated journal" maps to Engram's append-only facts table. The "semantic dependencies between operations" maps to Engram's conflict detection. The "three-way merge via reconciling operation" maps to Engram's `engram_resolve` with explicit merge. The key insight is that Engram's fact store is essentially a replicated journal already — it just doesn't formalize the replication semantics. Adopting this model would give Engram a principled foundation for federation rather than the ad-hoc pull-based sync currently planned.

---

## [28] Letta (formerly MemGPT): Shared Memory Blocks for Multi-Agent Systems

**Source:** [Letta Documentation](https://docs.letta.com/guides/core-concepts/memory/shared-memory/), [GitHub](https://github.com/letta-ai/letta)
**Status:** Production, actively maintained, VC-funded (Felicis seed)

### Summary

Letta (evolved from the UC Berkeley MemGPT research project) provides stateful agents with tiered memory systems. Its shared memory feature allows multiple agents to access and update the same memory blocks. When one agent updates a block, all others see the change immediately. Concurrency model: `memory_insert` is append-only and concurrent-safe; `memory_replace` is mostly safe (fails if target string changed); `memory_rethink` (full rewrite) uses last-writer-wins. No conflict detection, no contradiction surfacing, no structured consistency model.

### Threat to Engram — **Critical (Competitive)**

Letta is the closest existing system to Engram's vision. It already has:
- Shared memory blocks attached to multiple agents
- Append-only insert operations
- Read-only blocks for reference data
- Agent identity and access control
- A production-grade platform with SDK, dashboard, and cloud deployment

What Letta does NOT have:
- Semantic conflict detection between shared memory entries
- Structured contradiction artifacts
- Cross-agent consistency checking
- Provenance tracking and derivation chains

This validates Engram's core thesis (the gap exists) but dramatically narrows the competitive window. If Letta adds conflict detection to their shared memory blocks, Engram's differentiation evaporates. Engram's strategy should be: (a) ship conflict detection fast, (b) consider whether Engram should be a layer on top of Letta rather than a standalone system, (c) focus on the consistency model as the moat, not the memory storage.

---

## [29] Agent-MCP: Shared Knowledge Graph MCP Server

**Source:** [GitHub](https://github.com/rinadelph/Agent-MCP)
**Status:** Open source, active development

### Summary

Agent-MCP is an MCP server framework for multi-agent AI development that provides a persistent shared knowledge graph, intelligent task management, and real-time visualization via a web dashboard. Multiple specialized agents work simultaneously on different parts of a codebase, coordinated through shared memory. The knowledge graph is searchable and persistent across sessions.

### Threat to Engram — **Medium (Competitive)**

Agent-MCP occupies the same "shared MCP memory for coding agents" niche as Engram. It has a working knowledge graph, task management, and a dashboard — features Engram plans for Phases 5-7. However, Agent-MCP has no conflict detection, no consistency model, and no contradiction surfacing. It's a coordination tool, not a consistency tool. The threat is that Agent-MCP's broader feature set (task management, agent lifecycle, visualization) may be more immediately useful to teams than Engram's focused consistency model, making it harder for Engram to gain adoption even if its core feature is more novel.

---

## [30] MAGIC: Multi-Hop Contradictions Are Dramatically Harder

**Authors:** (Multi-institution team)
**Venue:** EMNLP 2025 Findings
**ArXiv:** [2507.21544](https://arxiv.org/abs/2507.21544)

### Summary

MAGIC is a benchmark for inter-context conflicts in RAG systems that specifically tests multi-hop reasoning. Key finding: both open-source and proprietary LLMs struggle with conflict detection when multi-hop reasoning is required, and often fail to pinpoint the exact source of contradictions. This extends He et al.'s [5] theoretical result (pairwise checks are insufficient) with empirical evidence that the problem is not just theoretical — real LLMs fail at it in practice.

### Threat to Engram — **High (Confirms Known Limitation)**

Reinforces that Engram's pairwise detection will miss multi-hop contradictions. Example: Fact A says "Service X uses the same database as Service Y." Fact B says "Service Y uses PostgreSQL." Fact C says "Service X uses MySQL." Facts A+B and A+C are each pairwise consistent, but the triple is jointly inconsistent. MAGIC shows this isn't just a theoretical concern — it's a practical failure mode that current LLMs cannot reliably detect even when given all three facts together. The entity-based retrieval (Phase 3, Path C) partially mitigates this by ensuring facts about the same entities are compared, but the LLM judge still needs to reason over the transitive chain.

---

## [31] Debate Collapse in Multi-Agent Systems

**Authors:** Luoxi Tang et al.
**ArXiv:** [2602.07186](https://arxiv.org/abs/2602.07186) (Feb 2026)

### Summary

Multi-agent debate systems are vulnerable to "debate collapse" — a failure mode where agents converge on erroneous reasoning through iterative deliberation. The authors propose uncertainty metrics at three levels (intra-agent, inter-agent, system-level) and show that uncertainty-driven policy optimization can mitigate the problem. Key insight: confident-sounding but incorrect responses mislead other agents, creating cascading failures.

### Threat to Engram — **Medium (Amplification Risk)**

Debate collapse is the multi-agent version of the Mandela Effect [8]. When agents query Engram, incorporate retrieved facts into their reasoning, and then commit derived facts back, they create a feedback loop. If the initial fact is wrong but confidently stated, subsequent agents will build on it, and the knowledge base will accumulate a cluster of mutually-reinforcing incorrect facts. Engram's conflict detection cannot catch this because the facts agree with each other — they're just all wrong. The uncertainty metrics proposed in this paper (particularly the inter-agent disagreement signal) could inform a "confidence calibration" feature: if all facts in a cluster trace back to a single source agent, flag the cluster as "single-source, uncorroborated."

---

## [32] SCALE: Fast NLI-Based Inconsistency Detection Over Long Documents

**Authors:** (Research team)
**Venue:** EMNLP 2023
**ArXiv:** [2310.13189](https://arxiv.org/abs/2310.13189)

### Summary

SCALE is an NLI-based model that uses large text chunks to condition over long texts for factual inconsistency detection. Achieves state-of-the-art performance across diverse tasks and long inputs. The key architectural insight is chunking: rather than comparing individual sentences, SCALE compares chunks of text, preserving context that sentence-level approaches lose.

### Threat to Engram — **Medium (Architectural Refinement)**

SCALE's chunking approach is relevant because Engram facts are not always atomic sentences — they can be multi-sentence descriptions of architectural decisions, API behaviors, or configuration details. A sentence-level NLI approach (as in SummaC [24]) might miss contradictions that span multiple sentences within a fact. SCALE suggests that Engram's NLI-based detection should operate on full fact content rather than decomposing facts into sentences, at least for the initial pass.

---

## Revised Competitive Landscape

| System | Shared Memory | Conflict Detection | MCP Compatible | Consistency Model | Status |
|---|---|---|---|---|---|
| **Letta** | Yes (blocks) | No | Via adapters | Last-writer-wins | Production |
| **Agent-MCP** | Yes (knowledge graph) | No | Yes (native) | None | Active OSS |
| **mem0** | No (single-user) | No | Via MCP wrapper | None | Production (40k+ stars) |
| **shared-memory-mcp** | Yes | No | Yes | None | Early OSS |
| **Memorix** | Yes (cross-IDE) | No | Partial | None | Active OSS |
| **SAMEP** | Yes (encrypted) | No | Yes | Secure sharing | Research |
| **Engram** | Yes (planned) | **Yes** | Yes (native) | **Append-only + semantic conflicts** | **Early development** |

The consistency model remains Engram's unique differentiator across all known systems. But the window is narrowing — Letta in particular has the infrastructure, funding, and user base to add conflict detection quickly if they choose to.

---

## Key Unifying Insight: The Tiered NLI Pipeline

The most important finding across this entire research round is that Engram's conflict detection pipeline should be restructured around a **tiered NLI architecture** rather than an LLM-as-judge architecture:

| Tier | Method | Speed | Cost | Accuracy | When Used |
|---|---|---|---|---|---|
| 0 | Content hash + entity overlap | <1ms | Free | 100% (exact match) | Every commit |
| 1 | NLI cross-encoder (DeBERTa-v3) | ~10ms/pair | Free (local) | ~92% | Every commit |
| 2 | Numeric/temporal pre-checks | <5ms | Free | High for specific types | Every commit |
| 3 | LLM judge (adversarial prompt) | ~2000ms/pair | API cost | Variable (bias-prone) | Ambiguous Tier 1 scores only |

This tiered approach:
- Makes conflict detection effectively synchronous (Tiers 0-2 complete in <500ms for 30 candidates)
- Eliminates the LLM API as a dependency for the core feature
- Reduces the async complexity that drives failure modes 2, 9, and 20
- Provides deterministic, reproducible results for the majority of checks
- Reserves the expensive, non-deterministic LLM call for edge cases where explanation text is needed

This is the major architectural change this research round was looking for.
