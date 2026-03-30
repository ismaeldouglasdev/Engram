# Engram

**Persistent, shared agent memory as MCP infrastructure.**

Every agent session starts from zero. It has no memory of why a decision was made last week, which approaches already failed, or what constraints are non-negotiable. Another engineer's agent re-discovered the same things the day before. That knowledge evaporated when the session ended.

Engram fixes that.

---

## What it does

Engram is an MCP server that gives your agents a shared, versioned knowledge base that persists across sessions. When an agent discovers something real during work — a hidden side effect, a failed approach, an undocumented constraint — it commits that to Engram. The next engineer's agent, in a separate session days later, pulls that fact before touching the relevant code.

It does not re-discover. It builds on.

## How it works

Engram exposes three tools any MCP-compatible agent can call:

```
query(topic)
```
Before beginning work, the agent pulls relevant facts, past decisions, and known constraints about what it is about to touch.

```
commit(fact, context)
```
When an agent discovers something worth preserving, it writes a structured entry — the fact, what triggered the discovery, the relevant scope, a confidence level, and a timestamp. Entries are append-only and never deleted.

```
conflicts()
```
Returns pairs of facts that semantically contradict each other, flagged automatically when a new commit's embedding similarity score crosses a contradiction threshold. A structured artifact you can review and resolve — not an error that blocks you.

## Works with your existing tools

Engram is MCP-native. If your agent supports MCP — Claude Code, Cursor, Windsurf, or anything compatible — you connect to the server and it works. No changes to how you work. Just every session starting with accumulated team intelligence instead of nothing.

## Current status

Engram is in early development. The core design is solid — the architecture, API surface, and storage model are defined. Implementation is underway.

If you're interested in what's being built and want to follow along, star the repo. If you want to help shape it, open an issue or start a discussion. Early feedback on the design is especially welcome.

## Roadmap

- [ ] MCP server with `query`, `commit`, and `conflicts` tools
- [ ] SQLite backend with append-only fact store
- [ ] Semantic search over committed facts
- [ ] Embedding-based conflict detection
- [ ] Two-engineer reproducible demo

## Contributing

Engram is being built in the open. If the problem resonates with you — if you've felt the pain of agents re-discovering things that were already known — contributions are welcome.

Check [`CONTRIBUTING.md`](./CONTRIBUTING.md) for how to get involved. If you're not sure where to start, open a discussion and say what you're thinking. That counts.

## Feedback

If you have thoughts on the design, the API surface, or the problem itself — open an issue or reach out directly at joshnathbrown884@gmail.com. This is early enough that real feedback changes real decisions.

---

*A biological engram is the physical trace a memory leaves in the brain. That's the idea.*
