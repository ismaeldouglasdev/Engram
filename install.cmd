@echo off
REM Engram installer for Windows CMD
REM Usage: curl -fsSL https://engram-us.com/install.cmd -o install.cmd && install.cmd && del install.cmd

setlocal enabledelayedexpansion

set "MCP_URL=https://mcp.engram-us.com/mcp"
set "INVITE_KEY="

REM ── Require Python 3 ─────────────────────────────────────────────
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set "PY=python3"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY=python"
    ) else (
        echo Python 3 is required but not found. Please install it first.
        exit /b 1
    )
)

REM ── Ask for invite key ───────────────────────────────────────────
echo.
set /p "HAS_KEY=Do you have an invite key from a teammate? (y/n): "
if /i "%HAS_KEY%"=="y" (
    set /p "INVITE_KEY=Paste your invite key: "
)

REM ── Detect and patch MCP clients ────────────────────────────────
echo.
echo Detecting MCP clients...
set "PATCHED=0"

REM Claude Desktop (Windows)
if exist "%APPDATA%\Claude" (
    call :patch_json "%APPDATA%\Claude\claude_desktop_config.json"
    set /a PATCHED+=1
)

REM Claude Code
if exist "%USERPROFILE%\.claude" (
    call :patch_json "%USERPROFILE%\.claude\settings.json"
    set /a PATCHED+=1
)

REM Cursor
if exist "%USERPROFILE%\.cursor" (
    call :patch_json "%USERPROFILE%\.cursor\mcp.json"
    set /a PATCHED+=1
)

REM VS Code
if exist "%APPDATA%\Code\User\settings.json" (
    call :patch_json "%APPDATA%\Code\User\settings.json"
    set /a PATCHED+=1
)

REM Windsurf
if exist "%USERPROFILE%\.codeium\windsurf" (
    call :patch_json "%USERPROFILE%\.codeium\windsurf\mcp_config.json"
    set /a PATCHED+=1
)

REM ── Result ───────────────────────────────────────────────────────
echo.
if %PATCHED% equ 0 (
    echo No MCP clients detected. Manually add to your config:
    echo.
    echo   "mcpServers": { "engram": { "url": "%MCP_URL%" } }
    echo.
    echo Then restart your IDE.
) else (
    echo Done. Restart your IDE, then ask your agent:
    echo.
    if "%INVITE_KEY%"=="" (
        echo   "Set up Engram for my team"    - to create a new workspace
        echo   "Join Engram with key ek_live_..."  - to join a teammate's workspace
    ) else (
        echo   "Set up Engram"  - your agent will connect to your workspace
    )
)
echo.
goto :eof

:patch_json
set "CONFIG_FILE=%~1"
%PY% -c "import json,sys,os;f=r'%CONFIG_FILE%';u='%MCP_URL%';k='%INVITE_KEY%';c=json.load(open(f)) if os.path.exists(f) else {};c.setdefault('mcpServers',{});e={'url':u};k and e.update({'headers':{'Authorization':'Bearer '+k}});c['mcpServers']['engram']=e;os.makedirs(os.path.dirname(f),exist_ok=True);json.dump(c,open(f,'w'),indent=2);print('  Patched: '+f)"
goto :eof
