# Cursor Quickstart

This guide helps you install Engram in Cursor and verify that the MCP connection is working.

## Install Engram

Run:

```bash
curl -fsSL https://engram-us.com/install | sh
```

If you are joining an existing workspace, run:

```bash
curl -fsSL https://engram-us.com/install | sh -s -- --join ek_live_YOUR_KEY
```

## Expected terminal output

A successful install should look similar to:

```text
Do you have an invite key from a teammate? (y/n):
Detecting MCP clients...
  ✓ ~/.cursor/mcp.json

Done! Restart your IDE, then ask your agent:

  "Set up Engram for my team"
  "Join Engram with key ek_live_..."
```

If you install with `--join`, the final line will instead look like:

```text
"Set up Engram"  — your agent will connect to your workspace
```

## Where Engram writes config

Cursor is configured at:

```text
~/.cursor/mcp.json
```

Engram is added under:

```json
{
  "mcpServers": {
    "engram": {
      "url": "https://mcp.engram.app/mcp"
    }
  }
}
```

If you install with an invite key, the installer also adds an `Authorization` header.

## Restart Cursor

After the installer finishes, fully restart Cursor before testing the connection.

## Verify the connection

Ask your agent to:

```text
call engram_status()
```

On first use, Engram should guide the agent through setup or joining a workspace. Once configured, `engram_status()` should return a ready state.

## Common failure

### Cursor was configured, but Engram still does not appear to work

The most common cause is that Cursor was not restarted after installation.

**Fix:**
1. Quit Cursor completely
2. Re-open Cursor
3. Ask your agent to call `engram_status()` again

If Cursor still does not connect, open `~/.cursor/mcp.json` and confirm that the `engram` entry exists and points to:

```text
https://mcp.engram.app/mcp
```
