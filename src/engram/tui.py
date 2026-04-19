"""Engram TUI — minimal box-style memory capture interface."""

from __future__ import annotations

import http.client
import json
import threading
import time
import urllib.parse
from typing import Any

from prompt_toolkit import Application, get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.formatted_text.utils import fragment_list_width
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.styles import Style

_LOCAL_SERVER = "http://localhost:7474"

_CATEGORIES = [
    ("About you", "Tell me something about yourself your agents should remember"),
    ("About the codebase", "Tell me something about this codebase worth knowing"),
    ("Goals", "What should your agents help you achieve?"),
]

_DEFAULT_QUESTION = "Tell me something your agents should always remember"

_STYLE = Style.from_dict(
    {
        "border": "#555555",
        "border.title": "bold #ffffff",
        "status.ok": "bold #00dd55",
        "status.warn": "bold #ffaa00",
        "status.loading": "#555555",
        "question": "#88ddff",
        "flash.ok": "bold #00dd55",
        "flash.err": "bold #ff5555",
        "tab": "#444444",
        "tab.selected": "bold #ffffff",
        "input.prefix": "#555555",
    }
)


# ── HTTP helpers ──────────────────────────────────────────────────────


def _http_get(url: str, timeout: int = 5) -> Any | None:
    try:
        parsed = urllib.parse.urlparse(url)
        use_https = parsed.scheme == "https"
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if use_https else 80)
        conn: http.client.HTTPConnection
        if use_https:
            conn = http.client.HTTPSConnection(host, port, timeout=timeout)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=timeout)
        conn.request("GET", parsed.path + (f"?{parsed.query}" if parsed.query else ""))
        resp = conn.getresponse()
        if resp.status == 200:
            return json.loads(resp.read())
    except Exception:
        pass
    return None


def _http_post(url: str, body: dict[str, Any], timeout: int = 5) -> tuple[int, Any]:
    try:
        parsed = urllib.parse.urlparse(url)
        raw = json.dumps(body).encode()
        use_https = parsed.scheme == "https"
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if use_https else 80)
        conn: http.client.HTTPConnection
        if use_https:
            conn = http.client.HTTPSConnection(host, port, timeout=timeout)
        else:
            conn = http.client.HTTPConnection(host, port, timeout=timeout)
        conn.request(
            "POST",
            parsed.path,
            raw,
            {"Content-Type": "application/json", "Content-Length": str(len(raw))},
        )
        resp = conn.getresponse()
        raw_body = resp.read()
        try:
            data = json.loads(raw_body) if raw_body.strip() else {}
        except Exception:
            data = {"error": raw_body.decode(errors="replace")[:200]}
        return resp.status, data
    except Exception as exc:
        return 0, {"error": str(exc)}


def _server_url(ws: Any) -> str:
    if ws and ws.server_url:
        return ws.server_url.rstrip("/")
    return _LOCAL_SERVER


# ── TUI ───────────────────────────────────────────────────────────────


def run_tui(ws: Any, ctx: Any) -> None:
    """Launch the Engram memory capture TUI."""
    state: dict[str, Any] = {
        "conflicts": [],
        "conflicts_loaded": False,
        "selected_category": -1,
        "flash": "",
        "flash_style": "class:flash.ok",
    }

    input_buf = Buffer(name="main_input", multiline=False)

    def _w() -> int:
        try:
            return get_app().output.get_size().columns
        except Exception:
            import shutil

            return shutil.get_terminal_size().columns

    def _content_line(parts: list[tuple[str, str]]) -> AnyFormattedText:
        w = _w()
        content_len = fragment_list_width(parts)
        pad = max(0, w - 4 - content_len)  # 4 = len("│  ") + len("│")
        return [("class:border", "│  "), *parts, ("", " " * pad), ("class:border", "│\n")]

    def top_border() -> AnyFormattedText:
        w = _w()
        title = "Engram"
        dashes = max(0, w - len(title) - 5)
        return [
            ("class:border", "┌─ "),
            ("class:border.title", title),
            ("class:border", " " + "─" * dashes + "┐\n"),
        ]

    def bottom_border() -> AnyFormattedText:
        w = _w()
        return [("class:border", "└" + "─" * (w - 2) + "┘\n")]

    def blank_line() -> AnyFormattedText:
        return _content_line([])

    def status_line() -> AnyFormattedText:
        if state["flash"]:
            return _content_line([(state["flash_style"], state["flash"])])
        if not state["conflicts_loaded"]:
            return _content_line([("class:status.loading", "Checking conflicts...")])
        n = len(state["conflicts"])
        if n == 0:
            return _content_line([("class:status.ok", "✓ No conflicts")])
        label = f"⚠  {n} conflict{'s' if n != 1 else ''}"
        return _content_line([("class:status.warn", label)])

    def question_line() -> AnyFormattedText:
        cat_idx = state["selected_category"]
        q = _CATEGORIES[cat_idx][1] if cat_idx >= 0 else _DEFAULT_QUESTION
        return _content_line([("class:question", f"💬  {q}")])

    def tabs_line() -> AnyFormattedText:
        parts: list[tuple[str, str]] = []
        for i, (name, _) in enumerate(_CATEGORIES):
            if i > 0:
                parts.append(("", "  "))
            style = "class:tab.selected" if i == state["selected_category"] else "class:tab"
            parts.append((style, f"[ {name} ]"))
        return _content_line(parts)

    # ── key bindings ──────────────────────────────────────────────────

    kb = KeyBindings()

    @kb.add("tab")
    def _next_cat(event: Any) -> None:
        n = len(_CATEGORIES)
        state["selected_category"] = (state["selected_category"] + 1) % n
        event.app.invalidate()

    @kb.add("s-tab")
    def _prev_cat(event: Any) -> None:
        n = len(_CATEGORIES)
        cur = state["selected_category"]
        state["selected_category"] = (cur - 1) % n if cur >= 0 else n - 1
        event.app.invalidate()

    @kb.add("enter")
    def _submit(event: Any) -> None:
        text = input_buf.text.strip()
        input_buf.reset()
        if not text:
            return

        cat_idx = state["selected_category"]
        scope = _CATEGORIES[cat_idx][0].lower().replace(" ", "_") if cat_idx >= 0 else "global"
        app = event.app

        def _do_commit() -> None:
            base = _server_url(ws)
            status, _ = _http_post(
                f"{base}/api/commit",
                {
                    "content": text,
                    "agent_id": "tui-user",
                    "scope": scope,
                    "confidence": 0.9,
                    "fact_type": "observation",
                },
                timeout=8,
            )
            if status == 200:
                state["flash"] = "✓ Saved"
                state["flash_style"] = "class:flash.ok"
            else:
                state["flash"] = "✗ Could not reach server — is `engram serve --http` running?"
                state["flash_style"] = "class:flash.err"
            app.invalidate()
            time.sleep(2)
            state["flash"] = ""
            app.invalidate()

        threading.Thread(target=_do_commit, daemon=True).start()

    @kb.add("c-c")
    @kb.add("c-d")
    def _exit(event: Any) -> None:
        event.app.exit()

    # ── layout ────────────────────────────────────────────────────────

    layout = Layout(
        HSplit(
            [
                Window(
                    FormattedTextControl(top_border), height=D.exact(1), dont_extend_height=True
                ),
                Window(
                    FormattedTextControl(status_line), height=D.exact(1), dont_extend_height=True
                ),
                Window(
                    FormattedTextControl(blank_line), height=D.exact(1), dont_extend_height=True
                ),
                Window(
                    FormattedTextControl(question_line),
                    height=D.exact(1),
                    dont_extend_height=True,
                ),
                Window(
                    BufferControl(
                        input_buf,
                        input_processors=[BeforeInput("│  > ", style="class:input.prefix")],
                    ),
                    height=D.exact(1),
                    dont_extend_height=True,
                ),
                Window(
                    FormattedTextControl(blank_line), height=D.exact(1), dont_extend_height=True
                ),
                Window(FormattedTextControl(tabs_line), height=D.exact(1), dont_extend_height=True),
                Window(
                    FormattedTextControl(bottom_border),
                    height=D.exact(1),
                    dont_extend_height=True,
                ),
                Window(),  # spacer fills remaining terminal height
            ]
        ),
        focused_element=input_buf,
    )

    app = Application(
        layout=layout,
        style=_STYLE,
        key_bindings=kb,
        full_screen=True,
        cursor=CursorShape.BLINKING_BLOCK,
        mouse_support=False,
    )

    def _load_conflicts() -> None:
        base = _server_url(ws)
        data = _http_get(f"{base}/api/conflicts?status=open", timeout=8)
        state["conflicts_loaded"] = True
        state["conflicts"] = data if isinstance(data, list) else []
        app.invalidate()

    threading.Thread(target=_load_conflicts, daemon=True).start()

    app.run()
