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

# ── JSON patcher (Python) ──────────────────────────────────────────
function Patch-McpJson {
    param([string]$ConfigFile)
    & $py -c @"
import json, sys, os

config_file = r'$ConfigFile'
mcp_url     = '$McpUrl'
invite_key  = '$InviteKey'

if os.path.exists(config_file):
    try:
        with open(config_file) as f:
            config = json.load(f)
    except Exception:
        config = {}
else:
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    config = {}

if 'mcpServers' not in config:
    config['mcpServers'] = {}

entry = {'url': mcp_url}
if invite_key:
    entry['headers'] = {'Authorization': f'Bearer {invite_key}'}

config['mcpServers']['engram'] = entry

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print(f'  Patched: {config_file}')
"@
}

# ── Detect and patch MCP clients ──────────────────────────────────
Write-Host "`nDetecting MCP clients..."
$patched = 0

# Claude Desktop (Windows)
$claudeDesktop = "$env:APPDATA\Claude\claude_desktop_config.json"
if (Test-Path "$env:APPDATA\Claude") {
    Patch-McpJson $claudeDesktop
    $patched++
}

# Claude Code (~/.claude/settings.json)
$claudeCode = "$env:USERPROFILE\.claude\settings.json"
if (Test-Path "$env:USERPROFILE\.claude") {
    Patch-McpJson $claudeCode
    $patched++
}

# Cursor (~/.cursor/mcp.json)
$cursor = "$env:USERPROFILE\.cursor\mcp.json"
if (Test-Path "$env:USERPROFILE\.cursor") {
    Patch-McpJson $cursor
    $patched++
}

# VS Code (Windows)
$vscode = "$env:APPDATA\Code\User\settings.json"
if (Test-Path $vscode) {
    Patch-McpJson $vscode
    $patched++
}

# Windsurf
$windsurf = "$env:USERPROFILE\.codeium\windsurf\mcp_config.json"
if (Test-Path "$env:USERPROFILE\.codeium\windsurf") {
    Patch-McpJson $windsurf
    $patched++
}

# ── Result ─────────────────────────────────────────────────────────
Write-Host ''
if ($patched -eq 0) {
    Write-Host 'No MCP clients detected. Manually add to your config:'
    Write-Host ''
    if ($InviteKey) {
        Write-Host "  `"mcpServers`": { `"engram`": { `"url`": `"$McpUrl`", `"headers`": { `"Authorization`": `"Bearer $InviteKey`" } } }"
    } else {
        Write-Host "  `"mcpServers`": { `"engram`": { `"url`": `"$McpUrl`" } }"
    }
    Write-Host ''
    Write-Host 'Then restart your IDE.'
} else {
    Write-Host 'Done. Restart your IDE, then ask your agent:'
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
