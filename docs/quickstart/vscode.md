# VS Code Quickstart

This guide helps you install Engram in Visual Studio Code and verify that the MCP connection is working.

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
  ✓ ~/Library/Application Support/Code/User/mcp.json

Done! Restart your IDE, then ask your agent:

  "Set up Engram for my team"    — to create a new workspace
  "Join Engram with key ek_live_..."  — to join a teammate's workspace
```

If you install with `--join`, the final line will instead look like:

```text
"Set up Engram"  — your agent will connect to your workspace
```

## Where Engram writes config

On macOS, the installer writes to:

```text
~/Library/Application Support/Code/User/mcp.json
```

On Linux, it writes to:

```text
~/.config/Code/User/mcp.json
```

VS Code uses the `servers` format, not Cursor’s `mcpServers` format.

Engram is added as:

```json
{
  "servers": {
    "engram": {
      "type": "http",
      "url": "https://mcp.engram.app/mcp"
    }
  }
}
```

If you install with an invite key, the installer also adds an `Authorization` header.

## Restart VS Code

After the installer finishes, fully restart VS Code before testing the connection.

## Verify the connection

Ask your agent to:

```text
call engram_status()
```

On first use, Engram should guide the agent through setup or joining a workspace. Once configured, `engram_status()` should return a ready state.

## Common failure

### VS Code was patched, but the MCP connection still does not appear

A common issue is checking for the wrong config shape. VS Code uses:

```text
servers.engram
```

not:

```text
mcpServers.engram
```

Another common issue is not restarting VS Code after installation.

**Fix:**
1. Open the VS Code MCP config file
2. Confirm Engram was written under `servers`
3. Restart VS Code
4. Ask your agent to call `engram_status()` again