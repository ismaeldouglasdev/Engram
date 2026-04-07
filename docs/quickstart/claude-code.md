# Claude Code Quickstart

This guide helps you install Engram in Claude Code and verify that the MCP connection is working.

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
  ✓ ~/.claude.json

Done! Restart your IDE, then ask your agent:

  "Set up Engram for my team"
  "Join Engram with key ek_live_..."
```

If you install with `--join`, the final line will instead look like:

```text
"Set up Engram"  — your agent will connect to your workspace
```

## Where Engram writes config

Claude Code is configured at:

```text
~/.claude.json
```

Engram is added under:

```json
{
  "mcpServers": {
    "engram": {
      "type": "http",
      "url": "https://mcp.engram.app/mcp"
    }
  }
}
```

If you install with an invite key, the installer also adds an `Authorization` header.

## Restart Claude Code

After the installer finishes, restart Claude Code before testing the connection.

## Verify the connection

Ask your agent to:

```text
call engram_status()
```

On first use, Engram should guide the agent through setup or joining a workspace. Once configured, `engram_status()` should return a ready state.

## Common failure

### Confusing Claude Code with Claude Desktop

Claude Code and Claude Desktop do not use the same config format.

- **Claude Code** uses `~/.claude.json`
- **Claude Desktop** uses `claude_desktop_config.json` and a `mcp-remote` bridge

If you are using Claude Code, make sure you are checking `~/.claude.json`, not the Claude Desktop config.

**Fix:**
1. Confirm you are using Claude Code
2. Open `~/.claude.json`
3. Verify the `engram` server entry exists
4. Restart Claude Code
5. Ask your agent to call `engram_status()` again

