"""Vercel ASGI entrypoint — serves the landing page only.

The live dashboard (knowledge base, conflicts, etc.) requires a running
Engram server with a SQLite database. On Vercel we serve the marketing
landing page and redirect dashboard routes to a helpful message.

This file is self-contained — no dependency on the engram package — so
Vercel only needs starlette in requirements.txt.
"""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route


# ── Landing page (kept in sync with src/engram/dashboard.py) ─────────

def _render_landing() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Engram — Multi-agent memory consistency</title>
  <meta name="description" content="Give your AI agents shared, persistent memory that detects contradictions. Works with Claude Code, Cursor, Windsurf, Kiro, and any MCP client.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  {_LANDING_STYLE}
</head>
<body>
  <div class="grain"></div>

  <!-- Nav -->
  <nav class="topnav">
    <div class="topnav-inner">
      <a href="/" class="logo" aria-label="Engram home">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true">
          <circle cx="14" cy="14" r="12" stroke="url(#glow)" stroke-width="2" opacity="0.5"/>
          <circle cx="14" cy="14" r="6" fill="url(#glow)"/>
          <circle cx="14" cy="14" r="3" fill="#0a0a0b"/>
          <defs>
            <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
              <stop offset="0%" stop-color="#a78bfa"/>
              <stop offset="100%" stop-color="#6d28d9"/>
            </radialGradient>
          </defs>
        </svg>
        <span>engram</span>
      </a>
      <div class="topnav-links">
        <a href="https://github.com/Agentscreator/Engram" target="_blank" rel="noopener">GitHub</a>
        <a href="#get-started">Get Started</a>
        <a href="/dashboard" class="nav-btn">Dashboard</a>
      </div>
    </div>
  </nav>

  <!-- Hero -->
  <section class="hero">
    <div class="hero-glow" aria-hidden="true"></div>
    <div class="hero-content">
      <div class="hero-badge">Open source &middot; Apache 2.0</div>
      <h1>Shared memory for<br>your AI agents</h1>
      <p class="hero-sub">
        Engram gives every agent on your team a persistent knowledge base that
        detects contradictions. One install. Four MCP tools. Zero config.
      </p>
      <div class="hero-install" id="get-started">
        <div class="install-box">
          <div class="install-label">Install &amp; run</div>
          <div class="code-line">
            <code id="install-cmd">pip install engram-mcp &amp;&amp; engram serve --http</code>
            <button class="copy-btn" onclick="copyText('install-cmd')" aria-label="Copy install command">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="5" y="5" width="9" height="9" rx="1.5" stroke="currentColor" stroke-width="1.5"/><path d="M3 11V3a1 1 0 011-1h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              <span class="copy-label">Copy</span>
            </button>
          </div>
        </div>
        <div class="install-or">or use uvx (no install needed)</div>
        <div class="install-box">
          <div class="install-label">One-liner with uvx</div>
          <div class="code-line">
            <code id="uvx-cmd">uvx engram-mcp@latest serve --http</code>
            <button class="copy-btn" onclick="copyText('uvx-cmd')" aria-label="Copy uvx command">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="5" y="5" width="9" height="9" rx="1.5" stroke="currentColor" stroke-width="1.5"/><path d="M3 11V3a1 1 0 011-1h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              <span class="copy-label">Copy</span>
            </button>
          </div>
        </div>
      </div>
      <p class="hero-note">Requires Python 3.11+. Runs on localhost:7474. No API keys needed.</p>
    </div>
  </section>

  <!-- How it works -->
  <section class="section">
    <div class="section-inner">
      <h2>Four tools. That's the entire API.</h2>
      <p class="section-sub">Engram exposes four MCP tools. Your agents call them automatically.</p>
      <div class="tools-grid">
        <div class="tool-card">
          <div class="tool-icon" aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2"/><path d="M16 16l4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </div>
          <h3>engram_query</h3>
          <p>Pull what your team's agents collectively know about a topic. Structured facts, ranked by relevance.</p>
        </div>
        <div class="tool-card">
          <div class="tool-icon" aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          </div>
          <h3>engram_commit</h3>
          <p>Persist a verified discovery. Append-only, timestamped, traceable. Every commit is immediately available to every agent.</p>
        </div>
        <div class="tool-card">
          <div class="tool-icon" aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 9v4M12 17h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <h3>engram_conflicts</h3>
          <p>Surface pairs of facts that semantically contradict each other. Reviewable, resolvable, auditable.</p>
        </div>
        <div class="tool-card">
          <div class="tool-icon" aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M9 12l2 2 4-4M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <h3>engram_resolve</h3>
          <p>Settle a disagreement. Pick a winner, merge both sides, or dismiss a false positive.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Connect -->
  <section class="section section-dark" id="connect">
    <div class="section-inner">
      <h2>Connect your MCP client</h2>
      <p class="section-sub">Works with any MCP-compatible client. Pick your setup.</p>

      <div class="tabs" role="tablist">
        <button class="tab active" role="tab" aria-selected="true" onclick="switchTab(event, 'tab-http')">Streamable HTTP</button>
        <button class="tab" role="tab" aria-selected="false" onclick="switchTab(event, 'tab-stdio')">stdio (local)</button>
      </div>

      <div class="tab-panels">
        <div class="tab-panel active" id="tab-http">
          <div class="config-context">Add this to your MCP client config (Claude Code, Cursor, Windsurf, Kiro, VS Code):</div>
          <div class="code-block">
            <div class="code-block-header">
              <span>mcp.json</span>
              <button class="copy-btn" onclick="copyBlock('config-http')" aria-label="Copy HTTP config">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="5" y="5" width="9" height="9" rx="1.5" stroke="currentColor" stroke-width="1.5"/><path d="M3 11V3a1 1 0 011-1h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
                <span class="copy-label">Copy</span>
              </button>
            </div>
            <pre id="config-http"><code>{{
  "mcpServers": {{
    "engram": {{
      "url": "http://localhost:7474/mcp"
    }}
  }}
}}</code></pre>
          </div>
        </div>
        <div class="tab-panel" id="tab-stdio">
          <div class="config-context">For local-only mode without running a server. Add to your MCP client config:</div>
          <div class="code-block">
            <div class="code-block-header">
              <span>mcp.json</span>
              <button class="copy-btn" onclick="copyBlock('config-stdio')" aria-label="Copy stdio config">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="5" y="5" width="9" height="9" rx="1.5" stroke="currentColor" stroke-width="1.5"/><path d="M3 11V3a1 1 0 011-1h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
                <span class="copy-label">Copy</span>
              </button>
            </div>
            <pre id="config-stdio"><code>{{
  "mcpServers": {{
    "engram": {{
      "command": "uvx",
      "args": ["engram-mcp@latest"]
    }}
  }}
}}</code></pre>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Architecture -->
  <section class="section">
    <div class="section-inner">
      <h2>How it works under the hood</h2>
      <p class="section-sub">Three layers. Writes return in ~1ms. Conflict detection runs async.</p>
      <div class="arch-diagram" role="img" aria-label="Architecture diagram showing three layers: I/O Layer with MCP tools, Detection Layer with tiered pipeline, and Storage Layer with SQLite">
        <div class="arch-layer arch-layer-top">
          <div class="arch-label">I/O Layer (MCP)</div>
          <div class="arch-items">
            <span class="arch-chip">engram_commit</span>
            <span class="arch-chip">engram_query</span>
            <span class="arch-chip">engram_conflicts</span>
            <span class="arch-chip">engram_resolve</span>
          </div>
          <div class="arch-note">Agents connect here</div>
        </div>
        <div class="arch-arrow" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 5v14M7 14l5 5 5-5" stroke="#6d28d9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <div class="arch-layer arch-layer-mid">
          <div class="arch-label">Detection Layer</div>
          <div class="arch-items">
            <span class="arch-chip">Hash dedup</span>
            <span class="arch-chip">Entity match</span>
            <span class="arch-chip">NLI cross-encoder</span>
            <span class="arch-chip">LLM escalation</span>
          </div>
          <div class="arch-note">Runs asynchronously in background</div>
        </div>
        <div class="arch-arrow" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 5v14M7 14l5 5 5-5" stroke="#6d28d9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <div class="arch-layer arch-layer-bottom">
          <div class="arch-label">Storage Layer (SQLite)</div>
          <div class="arch-items">
            <span class="arch-chip">Append-only</span>
            <span class="arch-chip">Bitemporal</span>
            <span class="arch-chip">Zero config</span>
          </div>
          <div class="arch-note">~/.engram/knowledge.db</div>
        </div>
      </div>
    </div>
  </section>

  <!-- Clients -->
  <section class="section section-dark">
    <div class="section-inner">
      <h2>Works with your tools</h2>
      <p class="section-sub">Any MCP-compatible client. No vendor lock-in.</p>
      <div class="clients-row">
        <div class="client-badge">Claude Code</div>
        <div class="client-badge">Cursor</div>
        <div class="client-badge">Windsurf</div>
        <div class="client-badge">Kiro</div>
        <div class="client-badge">VS Code</div>
        <div class="client-badge">Any MCP Client</div>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="footer">
    <div class="footer-inner">
      <div class="footer-left">
        <span class="footer-logo">engram</span>
        <span class="footer-tagline">The physical trace a memory leaves in the brain.</span>
      </div>
      <div class="footer-links">
        <a href="https://github.com/Agentscreator/Engram" target="_blank" rel="noopener">GitHub</a>
        <a href="https://github.com/Agentscreator/Engram/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">Contributing</a>
        <a href="https://github.com/Agentscreator/Engram/blob/main/LICENSE" target="_blank" rel="noopener">Apache 2.0</a>
      </div>
    </div>
  </footer>

  <script>
  function copyText(id) {{
    const el = document.getElementById(id);
    const text = el.textContent.replace(/&amp;/g, '&');
    navigator.clipboard.writeText(text).then(() => {{
      const btn = el.closest('.code-line').querySelector('.copy-label');
      btn.textContent = 'Copied';
      setTimeout(() => btn.textContent = 'Copy', 2000);
    }});
  }}
  function copyBlock(id) {{
    const el = document.getElementById(id);
    navigator.clipboard.writeText(el.textContent).then(() => {{
      const btn = el.closest('.code-block').querySelector('.copy-label');
      btn.textContent = 'Copied';
      setTimeout(() => btn.textContent = 'Copy', 2000);
    }});
  }}
  function switchTab(e, panelId) {{
    document.querySelectorAll('.tab').forEach(t => {{
      t.classList.remove('active');
      t.setAttribute('aria-selected', 'false');
    }});
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    e.currentTarget.classList.add('active');
    e.currentTarget.setAttribute('aria-selected', 'true');
    document.getElementById(panelId).classList.add('active');
  }}
  </script>
</body>
</html>"""


_LANDING_STYLE = """
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0a0a0b; color: #e4e4e7; line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }
  .grain {
    position: fixed; inset: 0; z-index: 9999; pointer-events: none; opacity: 0.03;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  }
  .topnav { position: sticky; top: 0; z-index: 100; background: rgba(10,10,11,0.8);
            backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.06); }
  .topnav-inner { max-width: 1100px; margin: 0 auto; padding: 0.75rem 1.5rem;
                   display: flex; align-items: center; justify-content: space-between; }
  .logo { display: flex; align-items: center; gap: 0.5rem; text-decoration: none;
          color: #e4e4e7; font-weight: 600; font-size: 1.05rem; }
  .topnav-links { display: flex; align-items: center; gap: 1.25rem; }
  .topnav-links a { color: #a1a1aa; text-decoration: none; font-size: 0.875rem;
                     transition: color 0.15s; }
  .topnav-links a:hover { color: #e4e4e7; }
  .nav-btn { background: rgba(109,40,217,0.15); border: 1px solid rgba(109,40,217,0.3);
             border-radius: 8px; padding: 0.4rem 1rem; color: #c4b5fd !important;
             transition: all 0.15s; }
  .nav-btn:hover { background: rgba(109,40,217,0.25); border-color: rgba(109,40,217,0.5); }
  .hero { position: relative; padding: 6rem 1.5rem 4rem; text-align: center;
          overflow: hidden; }
  .hero-glow { position: absolute; top: -200px; left: 50%; transform: translateX(-50%);
               width: 800px; height: 600px; border-radius: 50%;
               background: radial-gradient(ellipse, rgba(109,40,217,0.15) 0%, transparent 70%);
               pointer-events: none; }
  .hero-content { position: relative; max-width: 720px; margin: 0 auto; }
  .hero-badge { display: inline-block; padding: 0.3rem 0.9rem; border-radius: 100px;
                background: rgba(109,40,217,0.1); border: 1px solid rgba(109,40,217,0.25);
                color: #c4b5fd; font-size: 0.8rem; font-weight: 500; margin-bottom: 1.5rem; }
  .hero h1 { font-size: clamp(2.2rem, 5vw, 3.5rem); font-weight: 700; line-height: 1.15;
             letter-spacing: -0.03em; color: #fafafa;
             background: linear-gradient(to bottom right, #fafafa, #a1a1aa);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent;
             background-clip: text; }
  .hero-sub { margin-top: 1.25rem; font-size: 1.1rem; color: #a1a1aa; max-width: 560px;
              margin-left: auto; margin-right: auto; line-height: 1.7; }
  .hero-install { margin-top: 2.5rem; display: flex; flex-direction: column;
                  align-items: center; gap: 0.75rem; }
  .install-box { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
                 border-radius: 12px; padding: 1rem 1.25rem; width: 100%; max-width: 520px; }
  .install-label { font-size: 0.75rem; color: #71717a; text-transform: uppercase;
                   letter-spacing: 0.05em; margin-bottom: 0.5rem; font-weight: 500; }
  .code-line { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; }
  .code-line code { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem;
                    color: #c4b5fd; white-space: nowrap; overflow-x: auto; }
  .copy-btn { display: flex; align-items: center; gap: 0.35rem; background: none;
              border: 1px solid rgba(255,255,255,0.1); border-radius: 6px;
              padding: 0.3rem 0.6rem; color: #71717a; cursor: pointer;
              font-size: 0.75rem; transition: all 0.15s; flex-shrink: 0;
              font-family: 'Inter', sans-serif; }
  .copy-btn:hover { color: #e4e4e7; border-color: rgba(255,255,255,0.2); }
  .install-or { color: #52525b; font-size: 0.8rem; }
  .hero-note { margin-top: 1rem; font-size: 0.8rem; color: #52525b; }
  .section { padding: 5rem 1.5rem; }
  .section-dark { background: rgba(255,255,255,0.02); }
  .section-inner { max-width: 1000px; margin: 0 auto; }
  .section h2 { font-size: 1.75rem; font-weight: 700; color: #fafafa; text-align: center;
                letter-spacing: -0.02em; }
  .section-sub { text-align: center; color: #a1a1aa; margin-top: 0.75rem;
                 margin-bottom: 2.5rem; font-size: 1rem; }
  .tools-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 1rem; }
  .tool-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
               border-radius: 12px; padding: 1.5rem; transition: border-color 0.2s; }
  .tool-card:hover { border-color: rgba(109,40,217,0.3); }
  .tool-icon { color: #8b5cf6; margin-bottom: 0.75rem; }
  .tool-card h3 { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem;
                  color: #c4b5fd; margin-bottom: 0.5rem; font-weight: 500; }
  .tool-card p { font-size: 0.85rem; color: #a1a1aa; line-height: 1.6; }
  .tabs { display: flex; gap: 0.25rem; justify-content: center; margin-bottom: 1.5rem;
          background: rgba(255,255,255,0.03); border-radius: 10px; padding: 0.25rem;
          width: fit-content; margin-left: auto; margin-right: auto; }
  .tab { background: none; border: none; color: #71717a; padding: 0.5rem 1.25rem;
         border-radius: 8px; cursor: pointer; font-size: 0.875rem; font-weight: 500;
         transition: all 0.15s; font-family: 'Inter', sans-serif; }
  .tab.active { background: rgba(109,40,217,0.15); color: #c4b5fd; }
  .tab:hover:not(.active) { color: #a1a1aa; }
  .tab-panels { max-width: 560px; margin: 0 auto; }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }
  .config-context { font-size: 0.85rem; color: #a1a1aa; margin-bottom: 1rem; text-align: center; }
  .code-block { background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px; overflow: hidden; }
  .code-block-header { display: flex; justify-content: space-between; align-items: center;
                       padding: 0.6rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.06);
                       font-size: 0.75rem; color: #52525b; }
  .code-block pre { padding: 1rem 1.25rem; overflow-x: auto; margin: 0; }
  .code-block code { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;
                     color: #c4b5fd; line-height: 1.7; }
  .arch-diagram { display: flex; flex-direction: column; align-items: center; gap: 0.5rem;
                  max-width: 600px; margin: 0 auto; }
  .arch-layer { width: 100%; padding: 1.25rem 1.5rem; border-radius: 12px; text-align: center; }
  .arch-layer-top { background: rgba(109,40,217,0.08); border: 1px solid rgba(109,40,217,0.2); }
  .arch-layer-mid { background: rgba(59,130,246,0.06); border: 1px solid rgba(59,130,246,0.15); }
  .arch-layer-bottom { background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.15); }
  .arch-label { font-weight: 600; font-size: 0.9rem; color: #e4e4e7; margin-bottom: 0.5rem; }
  .arch-items { display: flex; flex-wrap: wrap; gap: 0.4rem; justify-content: center;
                margin-bottom: 0.4rem; }
  .arch-chip { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
               padding: 0.2rem 0.6rem; border-radius: 6px;
               background: rgba(255,255,255,0.05); color: #a1a1aa; }
  .arch-note { font-size: 0.75rem; color: #52525b; }
  .arch-arrow { color: #6d28d9; }
  .clients-row { display: flex; flex-wrap: wrap; gap: 0.75rem; justify-content: center; }
  .client-badge { padding: 0.6rem 1.25rem; border-radius: 10px;
                  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
                  font-size: 0.875rem; color: #a1a1aa; font-weight: 500; }
  .footer { border-top: 1px solid rgba(255,255,255,0.06); padding: 2rem 1.5rem; }
  .footer-inner { max-width: 1100px; margin: 0 auto; display: flex;
                  justify-content: space-between; align-items: center; flex-wrap: wrap;
                  gap: 1rem; }
  .footer-left { display: flex; align-items: center; gap: 1rem; }
  .footer-logo { font-weight: 600; color: #71717a; }
  .footer-tagline { font-size: 0.8rem; color: #3f3f46; font-style: italic; }
  .footer-links { display: flex; gap: 1.25rem; }
  .footer-links a { color: #52525b; text-decoration: none; font-size: 0.8rem;
                    transition: color 0.15s; }
  .footer-links a:hover { color: #a1a1aa; }
  @media (max-width: 640px) {
    .hero { padding: 4rem 1rem 3rem; }
    .hero h1 { font-size: 2rem; }
    .hero-sub { font-size: 1rem; }
    .tools-grid { grid-template-columns: 1fr; }
    .topnav-links { gap: 0.75rem; }
    .footer-inner { flex-direction: column; text-align: center; }
    .footer-left { flex-direction: column; }
    .code-line code { font-size: 0.8rem; }
  }
</style>
"""


def _render_dashboard_placeholder() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard — Engram</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: #0a0a0b; color: #e4e4e7; min-height: 100vh;
      display: flex; align-items: center; justify-content: center;
      -webkit-font-smoothing: antialiased;
    }
    .card {
      max-width: 520px; text-align: center; padding: 3rem 2rem;
      background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
      border-radius: 16px;
    }
    h1 { font-size: 1.5rem; font-weight: 700; color: #fafafa; margin-bottom: 0.75rem; }
    p { color: #a1a1aa; line-height: 1.7; margin-bottom: 1.25rem; font-size: 0.95rem; }
    .code-box {
      background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.06);
      border-radius: 10px; padding: 1rem 1.25rem; text-align: left; margin-bottom: 1.5rem;
    }
    code {
      font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #c4b5fd;
    }
    a {
      color: #c4b5fd; text-decoration: none; font-weight: 500;
      transition: color 0.15s;
    }
    a:hover { color: #e4e4e7; }
    .back { margin-top: 0.5rem; font-size: 0.85rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Dashboard requires a running server</h1>
    <p>
      The live dashboard connects to your Engram instance's SQLite database.
      Start a local server to access it:
    </p>
    <div class="code-box">
      <code>pip install engram-mcp<br>engram serve --http</code>
    </div>
    <p>Then visit <a href="http://localhost:7474/dashboard">localhost:7474/dashboard</a></p>
    <div class="back"><a href="/">&larr; Back to home</a></div>
  </div>
</body>
</html>"""


async def landing(request: Request) -> HTMLResponse:
    return HTMLResponse(_render_landing())


async def dashboard_placeholder(request: Request) -> HTMLResponse:
    return HTMLResponse(_render_dashboard_placeholder())


app = Starlette(
    routes=[
        Route("/", landing, methods=["GET"]),
        Route("/dashboard", dashboard_placeholder, methods=["GET"]),
        Route("/dashboard/{path:path}", dashboard_placeholder, methods=["GET"]),
    ],
)
