"""Vercel ASGI entrypoint — serves the landing page only.

Self-contained — no dependency on the engram package — so
Vercel only needs starlette in requirements.txt.
"""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route


def _render_landing() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Engram — Shared memory for your team's agents</title>
  <meta name="description" content="Shared memory for your team's agents. Works with any MCP-compatible IDE. You own your data. Your agents handle everything else.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      line-height: 1.6;
      color: #0f172a;
      background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 50%, #dcfce7 100%);
      min-height: 100vh;
    }
    
    .container {
      max-width: 800px;
      margin: 0 auto;
      padding: 0 24px;
    }
    
    /* Header */
    header {
      padding: 24px 0;
      background: rgba(255, 255, 255, 0.8);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid rgba(5, 150, 105, 0.1);
    }
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .logo {
      font-size: 28px;
      font-weight: 700;
      color: #059669;
      text-decoration: none;
      letter-spacing: -0.02em;
    }
    
    .nav-links a {
      color: #059669;
      text-decoration: none;
      font-size: 15px;
      font-weight: 500;
      transition: opacity 0.2s;
    }
    
    .nav-links a:hover {
      opacity: 0.7;
    }
    
    /* Hero */
    .hero {
      padding: 80px 0 60px;
      text-align: center;
    }
    
    h1 {
      font-size: 48px;
      font-weight: 700;
      line-height: 1.2;
      margin-bottom: 20px;
      color: #064e3b;
      letter-spacing: -0.03em;
    }
    
    .subtitle {
      font-size: 18px;
      color: #047857;
      max-width: 600px;
      margin: 0 auto 40px;
      line-height: 1.6;
    }
    
    /* Install Section */
    .install-section {
      background: white;
      border-radius: 16px;
      padding: 40px;
      margin-bottom: 40px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
      border: 1px solid rgba(5, 150, 105, 0.1);
    }
    
    .section-title {
      font-size: 28px;
      font-weight: 700;
      margin-bottom: 24px;
      color: #064e3b;
      text-align: center;
    }
    
    .code-block {
      background: #064e3b;
      color: #d1fae5;
      padding: 20px;
      border-radius: 12px;
      font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
      font-size: 15px;
      margin-bottom: 16px;
      position: relative;
      border: 2px solid #059669;
    }
    
    .code-block .copy-btn {
      position: absolute;
      top: 12px;
      right: 12px;
      background: #059669;
      color: white;
      border: none;
      padding: 6px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 600;
      transition: background 0.2s;
    }
    
    .code-block .copy-btn:hover {
      background: #047857;
    }
    
    .step {
      font-size: 15px;
      color: #047857;
      margin-bottom: 12px;
      font-weight: 500;
    }
    
    .note {
      font-size: 14px;
      color: #047857;
      line-height: 1.6;
      text-align: center;
      margin-top: 20px;
    }
    
    /* What Happens Section */
    .what-happens {
      background: white;
      border-radius: 16px;
      padding: 40px;
      margin-bottom: 40px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
      border: 1px solid rgba(5, 150, 105, 0.1);
    }
    
    .what-happens p {
      font-size: 16px;
      color: #1e293b;
      line-height: 1.7;
      margin-bottom: 16px;
    }
    
    .what-happens strong {
      color: #059669;
      font-weight: 600;
    }
    
    /* Tools Section */
    .tools-section {
      background: white;
      border-radius: 16px;
      padding: 40px;
      margin-bottom: 40px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
      border: 1px solid rgba(5, 150, 105, 0.1);
    }
    
    .tools-grid {
      display: grid;
      gap: 12px;
      margin-top: 24px;
    }
    
    .tool-item {
      padding: 16px;
      background: #f0fdf4;
      border-radius: 10px;
      border-left: 4px solid #059669;
    }
    
    .tool-item code {
      font-family: 'SF Mono', monospace;
      font-size: 14px;
      color: #059669;
      font-weight: 600;
    }
    
    .tool-item p {
      margin-top: 6px;
      font-size: 14px;
      color: #1e293b;
      line-height: 1.5;
    }
    
    /* Footer */
    footer {
      padding: 40px 0;
      text-align: center;
    }
    
    .footer-links {
      display: flex;
      gap: 24px;
      justify-content: center;
      margin-bottom: 12px;
    }
    
    .footer-links a {
      color: #059669;
      text-decoration: none;
      font-size: 14px;
      font-weight: 500;
    }
    
    .footer-links a:hover {
      opacity: 0.7;
    }
    
    .footer-tagline {
      font-size: 13px;
      color: #047857;
      font-style: italic;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
      h1 { font-size: 32px; }
      .subtitle { font-size: 16px; }
      .hero { padding: 60px 0 40px; }
      .install-section, .what-happens, .tools-section { padding: 28px 20px; }
      .section-title { font-size: 22px; }
    }
  </style>
</head>
<body>
  <!-- Header -->
  <header>
    <div class="container">
      <div class="header-content">
        <a href="/" class="logo">engram</a>
        <nav class="nav-links">
          <a href="https://github.com/Agentscreator/Engram" target="_blank">GitHub →</a>
        </nav>
      </div>
    </div>
  </header>

  <!-- Hero -->
  <section class="hero">
    <div class="container">
      <h1>Shared memory for your team's agents</h1>
      <p class="subtitle">
        Works with any MCP-compatible IDE. You own your data. Your agents handle everything else.
      </p>
    </div>
  </section>

  <!-- Install -->
  <section>
    <div class="container">
      <div class="install-section">
        <h2 class="section-title">Quick Start</h2>
        
        <div class="step">1. Install Engram</div>
        <div class="code-block">
          <button class="copy-btn" onclick="copyCode('install-cmd')">Copy</button>
          <div id="install-cmd">pip install engram-team && engram install</div>
        </div>
        
        <div class="step">2. Restart your editor</div>
        
        <div class="step">3. Ask your agent</div>
        <div class="code-block">
          <button class="copy-btn" onclick="copyCode('setup-prompt')">Copy</button>
          <div id="setup-prompt">"Set up Engram for my team"</div>
        </div>
        
        <p class="note">
          Supports Claude Code, Claude Desktop, Cursor, Windsurf, VS Code, and any MCP-compatible IDE
        </p>
      </div>
    </div>
  </section>

  <!-- What happens -->
  <section>
    <div class="container">
      <div class="what-happens">
        <h2 class="section-title">What It Does</h2>
        <p>
          When one agent discovers something important — a hidden side effect, a failed approach, 
          an undocumented constraint — it commits that fact. Every other agent on your team can query it instantly.
        </p>
        <p>
          When two agents develop incompatible beliefs, Engram detects the contradiction and surfaces it for review.
        </p>
        <p>
          <strong>You own your data.</strong> Engram connects to your PostgreSQL database. 
          Your facts live in your database, not ours.
        </p>
      </div>
    </div>
  </section>

  <!-- Tools -->
  <section>
    <div class="container">
      <div class="tools-section">
        <h2 class="section-title">MCP Tools</h2>
        <div class="tools-grid">
          <div class="tool-item">
            <code>engram_commit</code>
            <p>Persist a verified discovery</p>
          </div>
          <div class="tool-item">
            <code>engram_query</code>
            <p>Pull what your team's agents know</p>
          </div>
          <div class="tool-item">
            <code>engram_conflicts</code>
            <p>Surface contradictions</p>
          </div>
          <div class="tool-item">
            <code>engram_resolve</code>
            <p>Settle disagreements</p>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer>
    <div class="container">
      <div class="footer-links">
        <span style="font-weight: 600; color: #064e3b;">engram</span>
        <a href="https://github.com/Agentscreator/Engram" target="_blank">GitHub</a>
        <a href="https://github.com/Agentscreator/Engram/blob/main/LICENSE" target="_blank">Apache 2.0</a>
      </div>
      <p class="footer-tagline">An engram is the physical trace a memory leaves in the brain</p>
    </div>
  </footer>

  <script>
    function copyCode(id) {
      const el = document.getElementById(id);
      const text = el.textContent.trim();
      navigator.clipboard.writeText(text).then(() => {
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = originalText, 2000);
      }).catch(err => {
        console.error('Failed to copy:', err);
      });
    }
  </script>
</body>
</html>"""


def _render_dashboard_placeholder() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard — Engram</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #f9fafb;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 24px;
    }
    .card {
      max-width: 500px;
      background: white;
      padding: 48px;
      border-radius: 12px;
      border: 1px solid #e5e5e5;
      text-align: center;
    }
    h1 {
      font-size: 24px;
      margin-bottom: 16px;
      color: #1a1a1a;
    }
    p {
      color: #666;
      line-height: 1.6;
      margin-bottom: 24px;
    }
    .code-box {
      background: #1a1a1a;
      color: #e5e5e5;
      padding: 16px;
      border-radius: 8px;
      font-family: 'Courier New', monospace;
      font-size: 14px;
      text-align: left;
      margin-bottom: 24px;
    }
    a {
      color: #059669;
      text-decoration: none;
      font-weight: 500;
    }
    a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>Dashboard needs a running server</h1>
    <p>Start your local Engram instance, then open the dashboard there.</p>
    <div class="code-box">
      pip install engram-team
    </div>
    <div class="code-box" style="margin-top: 8px;">
      engram install
    </div>
    <div class="code-box" style="margin-top: 8px;">
      engram serve --http
    </div>
    <p>Then visit <a href="http://localhost:7474/dashboard">localhost:7474/dashboard</a></p>
    <p><a href="/">← Back to home</a></p>
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
