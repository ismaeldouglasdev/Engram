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

function Patch-McpServersUrl {  # Cursor, Kiro, Trae, Amazon Q
    param([string]$f)
    & $py -c "import json,os;f=r'$f';u='$McpUrl';k='$InviteKey';c=json.load(open(f)) if os.path.exists(f) else {};os.makedirs(os.path.dirname(f),exist_ok=True);c.setdefault('mcpServers',{});e={'url':u};k and e.update({'headers':{'Authorization':'Bearer '+k}});c['mcpServers']['engram']=e;json.dump(c,open(f,'w'),indent=2);print('  + '+f)"
}

function Patch-Windsurf {  # serverUrl not url
    param([string]$f)
    & $py -c "import json,os;f=r'$f';u='$McpUrl';k='$InviteKey';c=json.load(open(f)) if os.path.exists(f) else {};os.makedirs(os.path.dirname(f),exist_ok=True);c.setdefault('mcpServers',{});e={'serverUrl':u};k and e.update({'headers':{'Authorization':'Bearer '+k}});c['mcpServers']['engram']=e;json.dump(c,open(f,'w'),indent=2);print('  + '+f)"
}

function Patch-VSCode {  # {servers: {type: "http", url}}
    param([string]$f)
    & $py -c "import json,os;f=r'$f';u='$McpUrl';k='$InviteKey';c=json.load(open(f)) if os.path.exists(f) else {};os.makedirs(os.path.dirname(f),exist_ok=True);c.setdefault('servers',{});e={'type':'http','url':u};k and e.update({'headers':{'Authorization':'Bearer '+k}});c['servers']['engram']=e;json.dump(c,open(f,'w'),indent=2);print('  + '+f)"
}

function Patch-ClaudeCode {  # {type: "http", url} in ~/.claude.json
    param([string]$f)
    & $py -c "import json,os;f=r'$f';u='$McpUrl';k='$InviteKey';c=json.load(open(f)) if os.path.exists(f) else {};c.setdefault('mcpServers',{});e={'type':'http','url':u};k and e.update({'headers':{'Authorization':'Bearer '+k}});c['mcpServers']['engram']=e;json.dump(c,open(f,'w'),indent=2);print('  + '+f)"
}

function Patch-ClaudeDesktop {  # npx mcp-remote bridge
    param([string]$f)
    & $py -c "import json,os;f=r'$f';u='$McpUrl';k='$InviteKey';c=json.load(open(f)) if os.path.exists(f) else {};os.makedirs(os.path.dirname(f),exist_ok=True);c.setdefault('mcpServers',{});a=['-y','mcp-remote@latest',u];k and a.extend(['--header','Authorization: Bearer '+k]);c['mcpServers']['engram']={'command':'npx','args':a};json.dump(c,open(f,'w'),indent=2);print('  + '+f)"
}

function Patch-OpenCode {  # {mcp: {engram: {type: "remote", url}}}
    param([string]$f)
    & $py -c "import json,os;f=r'$f';u='$McpUrl';k='$InviteKey';c=json.load(open(f)) if os.path.exists(f) else {};os.makedirs(os.path.dirname(f),exist_ok=True);c.setdefault('mcp',{});e={'type':'remote','url':u,'enabled':True};k and e.update({'headers':{'Authorization':'Bearer '+k}});c['mcp']['engram']=e;json.dump(c,open(f,'w'),indent=2);print('  + '+f)"
}

# ── Detect and patch MCP clients ──────────────────────────────────
Write-Host "`nDetecting MCP clients..."
$patched = 0

# Claude Desktop
if (Test-Path "$env:APPDATA\Claude") {
    Patch-ClaudeDesktop "$env:APPDATA\Claude\claude_desktop_config.json"
    $patched++
}

# Claude Code (~/.claude.json)
if ((Test-Path "$env:USERPROFILE\.claude.json") -or (Test-Path "$env:USERPROFILE\.claude")) {
    Patch-ClaudeCode "$env:USERPROFILE\.claude.json"
    $patched++
}

# Cursor
if (Test-Path "$env:USERPROFILE\.cursor") {
    Patch-McpServersUrl "$env:USERPROFILE\.cursor\mcp.json"
    $patched++
}

# VS Code
if (Test-Path "$env:APPDATA\Code") {
    Patch-VSCode "$env:APPDATA\Code\User\mcp.json"
    $patched++
}

# Windsurf
if (Test-Path "$env:USERPROFILE\.codeium\windsurf") {
    Patch-Windsurf "$env:USERPROFILE\.codeium\windsurf\mcp_config.json"
    $patched++
}

# Kiro
if (Test-Path "$env:USERPROFILE\.kiro") {
    Patch-McpServersUrl "$env:USERPROFILE\.kiro\settings\mcp.json"
    $patched++
}

# Amazon Q Developer
if (Test-Path "$env:USERPROFILE\.aws\amazonq") {
    Patch-McpServersUrl "$env:USERPROFILE\.aws\amazonq\mcp.json"
    $patched++
}

# Trae (ByteDance)
if (Test-Path "$env:APPDATA\Trae") {
    Patch-McpServersUrl "$env:APPDATA\Trae\User\mcp.json"
    $patched++
}

# JetBrains / Junie
if (Test-Path "$env:USERPROFILE\.junie") {
    Patch-McpServersUrl "$env:USERPROFILE\.junie\mcp\mcp.json"
    $patched++
}

# Cline (VS Code extension)
$clineMcp = "$env:USERPROFILE\Documents\Cline\MCP\cline_mcp_settings.json"
if (Test-Path "$env:USERPROFILE\Documents\Cline") {
    Patch-McpServersUrl $clineMcp
    $patched++
}

# Roo Code (VS Code extension)
$rooStorage = "$env:APPDATA\Code\User\globalStorage\rooveterinaryinc.roo-cline"
if (Test-Path $rooStorage) {
    Patch-McpServersUrl "$rooStorage\settings\cline_mcp_settings.json"
    $patched++
}

# OpenCode
if (Test-Path "$env:USERPROFILE\.config\opencode") {
    Patch-OpenCode "$env:USERPROFILE\.config\opencode\config.json"
    $patched++
}

# ── Result ─────────────────────────────────────────────────────────
Write-Host ''
if ($patched -eq 0) {
    Write-Host 'No MCP clients detected. Manually add to your IDE''s MCP config:'
    Write-Host ''
    Write-Host "  Remote MCP URL: $McpUrl"
    if ($InviteKey) { Write-Host "  Header: Authorization: Bearer $InviteKey" }
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
