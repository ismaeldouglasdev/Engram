#!/bin/sh
# Engram installer — adds Engram to your MCP config
# Usage: curl -fsSL https://engram-us.com/install | sh
#   or:  curl -fsSL https://engram-us.com/install | sh -s -- --join ek_live_...

set -e

MCP_URL="https://mcp.engram-us.com/mcp"
INVITE_KEY=""

# Parse --join flag
while [ $# -gt 0 ]; do
  case "$1" in
    --join) INVITE_KEY="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# ── Detect OS ──────────────────────────────────────────────────────
OS="$(uname -s)"
if [ "$OS" != "Darwin" ] && [ "$OS" != "Linux" ]; then
  echo "Unsupported OS: $OS"
  echo "Manually add Engram to your MCP config:"
  echo "  url: $MCP_URL"
  exit 1
fi

# ── Require Python 3 ───────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required but not found. Please install it first."
  exit 1
fi

# ── Ask for invite key if not provided ─────────────────────────────
if [ -z "$INVITE_KEY" ]; then
  printf "\nDo you have an invite key from a teammate? (y/n): "
  read HAS_KEY
  if [ "$HAS_KEY" = "y" ] || [ "$HAS_KEY" = "Y" ]; then
    printf "Paste your invite key: "
    read INVITE_KEY
  fi
fi

# ── Per-IDE JSON patchers (Python) ─────────────────────────────────
# Each IDE has its own config format, key names, and file location.
# We use small Python scripts to patch each one correctly.

# Generic patcher for mcpServers.engram = {url, headers?}
# Used by: Cursor, Kiro, JetBrains
patch_mcpservers_url() {
  CONFIG_FILE="$1"
  python3 - "$CONFIG_FILE" "$MCP_URL" "$INVITE_KEY" << 'PYEOF'
import json, sys, os

config_file = sys.argv[1]
mcp_url     = sys.argv[2]
invite_key  = sys.argv[3]

if os.path.exists(config_file):
  try:
    with open(config_file) as f:
      config = json.load(f)
  except Exception:
    config = {}
else:
  os.makedirs(os.path.dirname(config_file), exist_ok=True)
  config = {}

if "mcpServers" not in config:
  config["mcpServers"] = {}

entry = {"url": mcp_url}
if invite_key:
  entry["headers"] = {"Authorization": f"Bearer {invite_key}"}

config["mcpServers"]["engram"] = entry

with open(config_file, "w") as f:
  json.dump(config, f, indent=2)

print(f"  ✓ {config_file}")
PYEOF
}

# Windsurf uses "serverUrl" instead of "url"
patch_windsurf() {
  CONFIG_FILE="$1"
  python3 - "$CONFIG_FILE" "$MCP_URL" "$INVITE_KEY" << 'PYEOF'
import json, sys, os

config_file = sys.argv[1]
mcp_url     = sys.argv[2]
invite_key  = sys.argv[3]

if os.path.exists(config_file):
  try:
    with open(config_file) as f:
      config = json.load(f)
  except Exception:
    config = {}
else:
  os.makedirs(os.path.dirname(config_file), exist_ok=True)
  config = {}

if "mcpServers" not in config:
  config["mcpServers"] = {}

entry = {"serverUrl": mcp_url}
if invite_key:
  entry["headers"] = {"Authorization": f"Bearer {invite_key}"}

config["mcpServers"]["engram"] = entry

with open(config_file, "w") as f:
  json.dump(config, f, indent=2)

print(f"  ✓ {config_file}")
PYEOF
}

# VS Code uses {servers: {name: {type, url, headers?}}} in mcp.json
patch_vscode() {
  CONFIG_FILE="$1"
  python3 - "$CONFIG_FILE" "$MCP_URL" "$INVITE_KEY" << 'PYEOF'
import json, sys, os

config_file = sys.argv[1]
mcp_url     = sys.argv[2]
invite_key  = sys.argv[3]

if os.path.exists(config_file):
  try:
    with open(config_file) as f:
      config = json.load(f)
  except Exception:
    config = {}
else:
  os.makedirs(os.path.dirname(config_file), exist_ok=True)
  config = {}

if "servers" not in config:
  config["servers"] = {}

entry = {"type": "http", "url": mcp_url}
if invite_key:
  entry["headers"] = {"Authorization": f"Bearer {invite_key}"}

config["servers"]["engram"] = entry

with open(config_file, "w") as f:
  json.dump(config, f, indent=2)

print(f"  ✓ {config_file}")
PYEOF
}

# Claude Code: patches ~/.claude.json (NOT ~/.claude/settings.json)
# Uses mcpServers.engram = {type: "http", url, headers?}
patch_claude_code() {
  CONFIG_FILE="$1"
  python3 - "$CONFIG_FILE" "$MCP_URL" "$INVITE_KEY" << 'PYEOF'
import json, sys, os

config_file = sys.argv[1]
mcp_url     = sys.argv[2]
invite_key  = sys.argv[3]

if os.path.exists(config_file):
  try:
    with open(config_file) as f:
      config = json.load(f)
  except Exception:
    config = {}
else:
  config = {}

if "mcpServers" not in config:
  config["mcpServers"] = {}

entry = {"type": "http", "url": mcp_url}
if invite_key:
  entry["headers"] = {"Authorization": f"Bearer {invite_key}"}

config["mcpServers"]["engram"] = entry

with open(config_file, "w") as f:
  json.dump(config, f, indent=2)

print(f"  ✓ {config_file}")
PYEOF
}

# Claude Desktop: remote servers must use npx mcp-remote as a stdio bridge
# Direct {"url": ...} entries in claude_desktop_config.json are ignored.
patch_claude_desktop() {
  CONFIG_FILE="$1"
  python3 - "$CONFIG_FILE" "$MCP_URL" "$INVITE_KEY" << 'PYEOF'
import json, sys, os

config_file = sys.argv[1]
mcp_url     = sys.argv[2]
invite_key  = sys.argv[3]

if os.path.exists(config_file):
  try:
    with open(config_file) as f:
      config = json.load(f)
  except Exception:
    config = {}
else:
  os.makedirs(os.path.dirname(config_file), exist_ok=True)
  config = {}

if "mcpServers" not in config:
  config["mcpServers"] = {}

args = ["-y", "mcp-remote@latest", mcp_url]
if invite_key:
  args.extend(["--header", f"Authorization: Bearer {invite_key}"])

config["mcpServers"]["engram"] = {
  "command": "npx",
  "args": args
}

with open(config_file, "w") as f:
  json.dump(config, f, indent=2)

print(f"  ✓ {config_file}")
PYEOF
}

# ── Detect and patch MCP clients ──────────────────────────────────
echo ""
echo "Detecting MCP clients..."
PATCHED=0

# Claude Desktop (Mac) — uses npx mcp-remote bridge
CLAUDE_DESKTOP="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [ "$OS" = "Darwin" ] && [ -d "$HOME/Library/Application Support/Claude" ]; then
  patch_claude_desktop "$CLAUDE_DESKTOP"
  PATCHED=$((PATCHED + 1))
fi

# Claude Desktop (Linux) — uses npx mcp-remote bridge
CLAUDE_DESKTOP_LINUX="$HOME/.config/Claude/claude_desktop_config.json"
if [ "$OS" = "Linux" ] && [ -d "$HOME/.config/Claude" ]; then
  patch_claude_desktop "$CLAUDE_DESKTOP_LINUX"
  PATCHED=$((PATCHED + 1))
fi

# Claude Code — config lives in ~/.claude.json (not ~/.claude/settings.json)
CLAUDE_CODE="$HOME/.claude.json"
if [ -f "$CLAUDE_CODE" ] || [ -d "$HOME/.claude" ]; then
  patch_claude_code "$CLAUDE_CODE"
  PATCHED=$((PATCHED + 1))
fi

# Cursor (~/.cursor/mcp.json) — uses {url, headers?}
CURSOR="$HOME/.cursor/mcp.json"
if [ -f "$CURSOR" ] || [ -d "$HOME/.cursor" ]; then
  patch_mcpservers_url "$CURSOR"
  PATCHED=$((PATCHED + 1))
fi

# VS Code (Mac) — uses {servers: {type: "http", url}} in mcp.json
VSCODE_MAC="$HOME/Library/Application Support/Code/User/mcp.json"
if [ "$OS" = "Darwin" ] && [ -d "$HOME/Library/Application Support/Code" ]; then
  patch_vscode "$VSCODE_MAC"
  PATCHED=$((PATCHED + 1))
fi

# VS Code (Linux) — uses {servers: {type: "http", url}} in mcp.json
VSCODE_LINUX="$HOME/.config/Code/User/mcp.json"
if [ "$OS" = "Linux" ] && [ -d "$HOME/.config/Code" ]; then
  patch_vscode "$VSCODE_LINUX"
  PATCHED=$((PATCHED + 1))
fi

# Windsurf — uses {serverUrl} not {url}
WINDSURF="$HOME/.codeium/windsurf/mcp_config.json"
if [ -f "$WINDSURF" ] || [ -d "$HOME/.codeium/windsurf" ]; then
  patch_windsurf "$WINDSURF"
  PATCHED=$((PATCHED + 1))
fi

# Kiro (~/.kiro/settings/mcp.json) — uses {url, headers?}
KIRO="$HOME/.kiro/settings/mcp.json"
if [ -f "$KIRO" ] || [ -d "$HOME/.kiro" ]; then
  patch_mcpservers_url "$KIRO"
  PATCHED=$((PATCHED + 1))
fi

# Zed (~/.config/zed/mcp.json or ~/Library/Application Support/Zed/mcp.json)
if [ "$OS" = "Darwin" ]; then
  ZED_DIR="$HOME/Library/Application Support/Zed"
else
  ZED_DIR="$HOME/.config/zed"
fi
ZED_MCP="$ZED_DIR/mcp.json"
if [ -d "$ZED_DIR" ]; then
  patch_mcpservers_url "$ZED_MCP"
  PATCHED=$((PATCHED + 1))
fi

# ── Result ─────────────────────────────────────────────────────────
echo ""
if [ "$PATCHED" -eq 0 ]; then
  echo "No MCP clients detected. Manually add to your IDE's MCP config:"
  echo ""
  echo "  Remote MCP URL: $MCP_URL"
  if [ -n "$INVITE_KEY" ]; then
    echo "  Header: Authorization: Bearer $INVITE_KEY"
  fi
  echo ""
  echo "Then restart your IDE."
else
  echo "Done! Restart your IDE, then ask your agent:"
  if [ -z "$INVITE_KEY" ]; then
    echo ""
    echo "  \"Set up Engram for my team\"    — to create a new workspace"
    echo "  \"Join Engram with key ek_live_...\"  — to join a teammate's workspace"
  else
    echo ""
    echo "  \"Set up Engram\"  — your agent will connect to your workspace"
  fi
fi
echo ""
