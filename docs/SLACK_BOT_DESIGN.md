# Slack Bot Design — Query and Commit from Chat

> **Issue #40** — Design for Slack integration to surface Engram to non-agent team members.

## Problem Statement

Currently, Engram is designed for AI agents. PMs, designers, tech leads, and other team members who don't use Claude Code or Cursor have no way to access the team's knowledge base. The decisions get made in Slack — Engram should be there too.

## Proposed Solution

A Slack app with two slash commands:
- `/engram ask <question>` — Query workspace memory, returns top 5 facts
- `/engram learn <fact>` — Commit a human-written fact to the workspace

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Slack     │────▶│  Slack App  │────▶│   Engram    │
│  Workspace  │     │  (Python)   │     │  Workspace  │
└─────────────┘     └──────────────┘     └─────────────┘
      │                    │                    │
      │ /engram ask       │ Query API          │
      │◀─────────────────│◀──────────────────│
      │                   │                    │
      │ /engram learn     │ Commit API         │
      │─────────────────▶│───────────────────▶│
```

### Components

1. **Slack App** — Python Flask/bolt app running on Cloud Run or similar
2. **Engram API** — Uses existing REST API (`/api/query`, `/api/commit`)
3. **Auth** — Bot token + workspace-scoped API key

## Slash Commands

### `/engram ask <question>`

**Input:** Natural language question  
**Output:** Formatted Slack message with top 5 facts

```text
📚 Engram Answer for "what's the API timeout?"

1. **The API timeout is 30 seconds** (confidence: 90%)
   - Scope: backend/api
   - Last verified: 2 days ago

2. **Default timeout for external services is 60s** (confidence: 75%)
   - Scope: backend
   - Last verified: 1 week ago
```

### `/engram learn <fact>`

**Input:** Fact statement  
**Output:** Confirmation message

```text
✅ Fact learned!

"Design review happens every Thursday at 2pm"
- Scope: process/meetings
- Confidence: 80% (manual fact)
```

## Implementation Phases

### Phase 1: Basic Slash Commands (Low effort)
- `/engram ask` — Query via REST API
- `/engram learn` — Commit via REST API
- Simple formatting

### Phase 2: Rich UI (Medium effort)
- Interactive message buttons
- Threaded responses for multiple facts
- "Learn more" expandable sections

### Phase 3: Bot Mode (Higher effort)
- `@engram` mention in channels
- Proactive suggestions when relevant topics arise
- Daily/weekly knowledge digests

## Schema Changes

None required — uses existing REST API.

## Configuration

```python
# Environment variables
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
ENGRAM_API_URL=https://api.engram.app
ENGRAM_WORKSPACE_KEY=workspace-...
```

## Risk Assessment

- **Security**: Medium — need to validate workspace access
- **Spam**: Low — slash commands are explicit
- **Rate limits**: Low — Slack handles this

## Related Issues

- #41 — Linear and GitHub Issues linking (complementary integration)
- #43 — n8n and Zapier/Make nodes (similar automation pattern)

---

*Design by ismaeldouglasdev — 2026-04-12*