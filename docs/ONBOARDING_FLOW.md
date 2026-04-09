# Onboarding Flow Documentation

This document maps all `next_prompt` strings in the Engram MCP server — these are the exact messages agents display to users during the onboarding flow.

## Overview

Engram uses a state machine approach for onboarding. The agent calls `engram_status()` first, then follows the `next_prompt` instructions to guide users through setup.

## States

### 1. No Workspace Configured (`awaiting_db`)

**When:** No `workspace.json` exists and no `ENGRAM_DB_URL` environment variable.

**Agent says:**
```
To set up Engram, add your database connection string to your environment.

Create a .env file in your project root with:
  ENGRAM_DB_URL='postgres://user:password@host:port/database'

Or set it in your shell config (.bashrc, .zshrc, etc.):
  export ENGRAM_DB_URL='postgres://user:password@host:port/database'

IMPORTANT: Don't paste your database URL in this chat for security reasons.

You can:
  • Use your existing app database (Engram creates a separate 'engram' schema)
  • Get a free dedicated database at neon.tech, supabase.com, or railway.app

Once set, restart this chat and I'll detect it automatically.
```

**User action:** Set up database connection and restart.

---

### 2. Workspace Exists, No Storage (`awaiting_setup`)

**When:** `workspace.json` exists but storage not initialized.

**Agent says:**
```
This workspace has a configuration but isn't initialized yet.
I can't read from or write to the database until setup completes.

Options:
  • If you're the workspace creator: I can run the full setup now.
  • If you joined via invite key: The workspace creator needs to complete setup first.
  • If this is unexpected: Check workspace.json and ensure the database is accessible.

What would you like to do?
```

**User action:** Confirm they're the creator or wait for creator setup.

---

### 3. Ready to Use (`ready`)

**When:** Workspace configured and storage initialized.

**Agent says:**
```
Your workspace is ready. The memory is empty — a clean slate.

Guidelines for what to remember:
  • Architectural decisions and the reasoning behind them
  • What approaches already failed and why
  • Non-negotiable constraints (deadlines, budgets, APIs, etc.)
  • Team conventions and patterns
  • Anything you'd want another agent to know

When you need to check what the team already knows:
  • Call `engram_query("<topic>")` to search memory before starting tasks
  • Call `engram_query("<topic>")` again if your approach changes

Do not call `engram_query` more than 3 times per task.
```

**User action:** Start using Engram by committing facts and querying.

---

### 4. Disconnected (`disconnected`)

**When:** Key generation mismatch between local config and database.

**Agent says:**
```
This workspace is disconnected from the database.

The local key generation (X) doesn't match the database (Y).
This usually happens when:
  • The workspace was re-initialized by the team admin
  • You're using an old invite key
  • The database was reset

To reconnect:
  • Ask the workspace admin for a fresh invite key
  • Or delete ~/.engram/workspace.json and re-join with a new key

Your local memory is preserved but can't sync until reconnected.
```

**User action:** Get fresh invite key from admin or re-join.

---

### 5. Team Founder Setup (`engram_init`)

**When:** User calls `engram_init` to create new workspace.

**Prompt before DB:**
```
To set up Engram, add your database connection string to your environment.

[Same as awaiting_db prompt]
```

**Prompt after successful init:**
```
Your team workspace is ready.

Engram tables are in the 'engram' schema in your database — completely isolated from your application tables.

Share this with teammates via iMessage, WhatsApp, Slack, or any channel:

  Invite Key: [key]

That's all they need. They install Engram, start a chat, paste the key, and their agent handles the rest.

Next steps:
  1. Share the invite key with your team
  2. Install Engram in your IDE: https://github.com/Agentscreator/Engram#installation
  3. Your team can start committing facts and building shared memory
```

---

### 6. Team Member Join (`engram_join`)

**When:** User calls `engram_join` with invite key.

**If key invalid/expired:**
```
That invite key is invalid or expired.
Ask your team admin for a fresh key, then try again.
```

**If key valid:**
```
Successfully joined workspace [engram_id].

Your agent is now connected to the team's shared memory.

When you need to check what the team already knows:
  • Call `engram_query("<topic>")` to search memory before starting tasks

Do not call `engram_query` more than 3 times per task.
```

---

## State Transition Diagram

```
┌─────────────────┐
│ No workspace   │
│ (no workspace. │
│    json)       │
└────────┬────────┘
         │ engram_init / engram_join
         ▼
┌─────────────────┐
│ Awaiting setup  │ (workspace.json exists,
│ (no storage)    │  storage not initialized)
└────────┬────────┘
         │ engram_init (creator)
         ▼
┌─────────────────┐
│     Ready       │
│  (initialized)  │
└────────┬────────┘
         │ key mismatch
         ▼
┌─────────────────┐
│  Disconnected  │
└─────────────────┘
```

## Contributing to Onboarding

To improve the onboarding flow:

1. **Review this document** to understand the full conversation tree
2. **Make changes** to the `next_prompt` strings in `server.py`
3. **Update this document** to reflect any changes
4. **Test manually** by going through the flow with a fresh workspace

This makes onboarding improvements accessible to non-engineers (PMs, writers, UX contributors) who can review the flow without reading Python code.