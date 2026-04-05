# Engram installer for Windows PowerShell
# Usage: irm https://engram-us.com/install.ps1 | iex
#   or:  & { $env:ENGRAM_JOIN='ek_live_...'; irm https://engram-us.com/install.ps1 | iex }

$ErrorActionPreference = 'Stop'
$McpUrl = 'https://mcp.engram-us.com/mcp'
$InviteKey = $env:ENGRAM_JOIN

# ── Require Python 3 ───────────────────────────────────────────────
if (-not (Get-Command python3 -ErrorAction SilentlyContinue) -and
    -not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host 'Python 3 is required but not found. Please install it first.' -ForegroundColor Red
    exit 1
}
$py = if (Get-Command python3 -ErrorAction SilentlyContinue) { 'python3' } else { 'python' }

# ── Ask for invite key if not provided ─────────────────────────────
if (-not $InviteKey) {
    $hasKey = Read-Host "`nDo you have an invite key from a teammate? (y/n)"
    if ($hasKey -eq 'y' -or $hasKey -eq 'Y') {
        $InviteKey = Read-Host 'Paste your invite key'
    }
}

# ── Per-IDE JSON patchers ──────────────────────────────────────────

# Generic: mcpServers.engram = {url, headers?}  (Cursor, Kiro)
function Patch-McpServersUrl {
    param([string]$ConfigFile)
    & $py -c @"
import json, sys, os
config_file = r'$ConfigFile'
mcp_url     = '$McpUrl'
invite_key  = '$InviteKey'
if os.path.exists(config_file):
    try:
        with open(config_file) as f: config = json.load(f)
    except Exception: config = {}
else:
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    config = {}
config.setdefault('mcpServers', {})
entry = {'url': mcp_url}
if invite_key: entry['headers'] = {'Authorization': f'Bearer {invite_key}'}
config['mcpServers']['engram'] = entry
with open(config_file, 'w') as f: json.dump(config, f, indent=2)
print(f'  + {config_file}')
"@
}

# Windsurf: mcpServers.engram = {serverUrl, headers?}
function Patch-Windsurf {
    param([string]$ConfigFile)
    & $py -c @"
import json, sys, os
config_file = r'$ConfigFile'
mcp_url     = '$McpUrl'
invite_key  = '$InviteKey'
if os.path.exists(config_file):
    try:
        with open(config_file) as f: config = json.load(f)
    except Exception: config = {}
else:
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    config = {}
config.setdefault('mcpServers', {})
entry = {'serverUrl': mcp_url}
if invite_key: entry['headers'] = {'Authorization': f'Bearer {invite_key}'}
config['mcpServers']['engram'] = entry
with open(config_file, 'w') as f: json.dump(config, f, indent=2)
print(f'  + {config_file}')
"@
}

# VS Code: servers.engram = {type: "http", url, headers?}
function Patch-VSCode {
    param([string]$ConfigFile)
    & $py -c @"
import json, sys, os
config_file = r'$ConfigFile'
mcp_url     = '$McpUrl'
invite_key  = '$InviteKey'
if os.path.exists(config_file):
    try:
        with open(config_file) as f: config = json.load(f)
    except Exception: config = {}
else:
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    config = {}
config.setdefault('servers', {})
entry = {'type': 'http', 'url': mcp_url}
if invite_key: entry['headers'] = {'Authorization': f'Bearer {invite_key}'}
config['servers']['engram'] = entry
with open(config_file, 'w') as f: json.dump(config, f, indent=2)
print(f'  + {config_file}')
"@
}

# Claude Code: mcpServers.engram = {type: "http", url, headers?} in ~/.claude.json
function Patch-ClaudeCode {
    param([string]$ConfigFile)
    & $py -c @"
import json, sys, os
config_file = r'$ConfigFile'
mcp_url     = '$McpUrl'
invite_key  = '$InviteKey'
if os.path.exists(config_file):
    try:
        with open(config_file) as f: config = json.load(f)
    except Exception: config = {}
else:
    config = {}
config.setdefault('mcpServers', {})
entry = {'type': 'http', 'url': mcp_url}
if invite_key: entry['headers'] = {'Authorization': f'Bearer {invite_key}'}
config['mcpServers']['engram'] = entry
with open(config_file, 'w') as f: json.dump(config, f, indent=2)
print(f'  + {config_file}')
"@
}

# Claude Desktop: must use npx mcp-remote bridge for remote servers
function Patch-ClaudeDesktop {
    param([string]$ConfigFile)
    & $py -c @"
import json, sys, os
config_file = r'$ConfigFile'
mcp_url     = '$McpUrl'
invite_key  = '$InviteKey'
if os.path.exists(config_file):
    try:
        with open(config_file) as f: config = json.load(f)
    except Exception: config = {}
else:
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    config = {}
config.setdefault('mcpServers', {})
args = ['-y', 'mcp-remote@latest', mcp_url]
if invite_key: args.extend(['--header', f'Authorization: Bearer {invite_key}'])
config['mcpServers']['engram'] = {'command': 'npx', 'args': args}
with open(config_file, 'w') as f: json.dump(config, f, indent=2)
print(f'  + {config_file}')
"@
}

# ── Detect and patch MCP clients ──────────────────────────────────
Write-Host "`nDetecting MCP clients..."
$patched = 0

# Claude Desktop (Windows) — uses npx mcp-remote bridge
$claudeDesktop = "$env:APPDATA\Claude\claude_desktop_config.json"
if (Test-Path "$env:APPDATA\Claude") {
    Patch-ClaudeDesktop $claudeDesktop
    $patched++
}

# Claude Code — config lives in ~/.claude.json
$claudeCode = "$env:USERPROFILE\.claude.json"
if ((Test-Path $claudeCode) -or (Test-Path "$env:USERPROFILE\.claude")) {
    Patch-ClaudeCode $claudeCode
    $patched++
}

# Cursor (~/.cursor/mcp.json)
$cursor = "$env:USERPROFILE\.cursor\mcp.json"
if (Test-Path "$env:USERPROFILE\.cursor") {
    Patch-McpServersUrl $cursor
    $patched++
}

# VS Code (Windows) — uses {servers: {type: "http", url}} in mcp.json
$vscode = "$env:APPDATA\Code\User\mcp.json"
if (Test-Path "$env:APPDATA\Code") {
    Patch-VSCode $vscode
    $patched++
}

# Windsurf — uses {serverUrl}
$windsurf = "$env:USERPROFILE\.codeium\windsurf\mcp_config.json"
if (Test-Path "$env:USERPROFILE\.codeium\windsurf") {
    Patch-Windsurf $windsurf
    $patched++
}

# Kiro (~/.kiro/settings/mcp.json)
$kiro = "$env:USERPROFILE\.kiro\settings\mcp.json"
if (Test-Path "$env:USERPROFILE\.kiro") {
    Patch-McpServersUrl $kiro
    $patched++
}

# ── Result ─────────────────────────────────────────────────────────
Write-Host ''
if ($patched -eq 0) {
    Write-Host 'No MCP clients detected. Manually add to your IDE''s MCP config:'
    Write-Host ''
    Write-Host "  Remote MCP URL: $McpUrl"
    if ($InviteKey) {
        Write-Host "  Header: Authorization: Bearer $InviteKey"
    }
    Write-Host ''
    Write-Host 'Then restart your IDE.'
} else {
    Write-Host 'Done! Restart your IDE, then ask your agent:'
    if (-not $InviteKey) {
        Write-Host ''
        Write-Host '  "Set up Engram for my team"    - to create a new workspace'
        Write-Host '  "Join Engram with key ek_live_..."  - to join a teammate''s workspace'
    } else {
        Write-Host ''
        Write-Host '  "Set up Engram"  - your agent will connect to your workspace'
    }
}
Write-Host ''
