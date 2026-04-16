# Agent Identity and Trust Levels Design

> **Issue #33** — Design for agent identity, reputation, and trust scoring system.

## Problem Statement

Currently, Engram treats all agents equally. When Agent A and Agent B contradict each other, there's no way to weigh their credibility. A senior engineer's fact should carry more weight than a junior agent's. Similarly, agents with a history of accurate commits should be trusted more than agents with frequent retractions or conflicts.

## Design Goals

1. **Trust-weighted retrieval** — Facts from trusted agents should rank higher in query results
2. **Conflict resolution hints** — When resolving conflicts, trust scores should inform suggestions
3. **Incentivize quality** — Agents with good track records benefit; poor ones are flagged
4. **Privacy-preserving** — Trust is computed server-side; individual agents don't expose credentials

## Proposed Solution

### 1. Agent Trust Score

Each agent gets a trust score computed from:

- **Accuracy rate**: Percentage of commits that never got into a conflict
- **Corroboration count**: How many other agents queried and confirmed their facts
- **Conflict rate**: Percentage of commits that resulted in conflicts (negative signal)
- **Staleness**: Facts that were never superseded = positive signal
- **Recency decay**: Older track record counts less

```
trust_score = accuracy_rate * 0.4 + corroboration_rate * 0.3 + (1 - conflict_rate) * 0.3
```

### 2. Trust Tiers

| Tier | Score Range | Behavior |
|------|-------------|----------|
| `trusted` | 0.8 - 1.0 | Facts get +20% relevance boost in queries |
| `standard` | 0.4 - 0.79 | Default behavior |
| `flagged` | 0.0 - 0.39 | Facts get -20% relevance; conflicts trigger review |

### 3. Schema Changes

```python
# New migration (version 10+)
ALTER TABLE agents ADD COLUMN trust_score REAL DEFAULT 0.5
ALTER TABLE agents ADD COLUMN trust_tier TEXT DEFAULT 'standard'
ALTER TABLE agents ADD COLUMN total_commits INTEGER DEFAULT 0
ALTER TABLE agents ADD COLUMN conflict_count INTEGER DEFAULT 0
ALTER TABLE agents ADD COLUMN last_trust_calculated_at TEXT
```

### 4. Trust Update Process

Trust scores are recalculated:

- **On commit**: Increment agent's commit count
- **On conflict detection**: Increment agent's conflict count
- **On query**: Increment corroboration count when agent's fact is returned
- **Daily batch job**: Recalculate all trust scores with recency decay

### 5. Query Integration

In `engine.py`, when ranking results:

```python
def rank_fact(fact, agent_trust_scores):
    base_score = fact.relevance_score
    
    agent_score = agent_trust_scores.get(fact.agent_id, 0.5)
    if agent_score >= 0.8:
        base_score *= 1.2  # Trusted agent boost
    elif agent_score < 0.4:
        base_score *= 0.8  # Flagged agent penalty
    
    return base_score
```

### 6. Conflict Resolution Integration

When suggesting resolution:

```python
def suggest_resolution(conflict, agent_trust_scores):
    score_a = agent_trust_scores.get(conflict.fact_a.agent_id, 0.5)
    score_b = agent_trust_scores.get(conflict.fact_b.agent_id, 0.5)
    
    if score_a > score_b + 0.2:
        return suggest_winner(fact_a)
    elif score_b > score_a + 0.2:
        return suggest_winner(fact_b)
    # Else: keep neutral suggestion
```

## Implementation Phases

### Phase 1: Schema + Basic Tracking (Low effort)
- Add trust columns to agents table
- Track commit/conflict counts per agent

### Phase 2: Trust Calculation (Medium effort)
- Implement trust score algorithm
- Add daily batch job

### Phase 3: Query Integration (Medium effort)
- Apply trust weights to ranking
- Add tests

### Phase 4: Conflict Resolution (Higher effort)
- Use trust in suggestion generation

## Risk Assessment

- **Complexity**: Medium — requires changes to query ranking
- **Performance**: Low — trust lookup is O(1) per fact
- **Gaming risk**: Medium — agents could try to inflate trust (mitigate with corroboration requirement)

## Related Issues

- #18 — Fact confidence decay with corroboration boost (complementary)
- #30 — engram_promote (could use trust to auto-approve promotions)

---

*Design by ismaeldouglasdev — 2026-04-12*