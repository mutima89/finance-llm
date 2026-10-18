"""Capture README screenshots of the running app.

Starts the FastAPI and Streamlit servers, screenshots them with Playwright,
and renders CLI output to PNG. No API keys are needed: these views only show
the interface, not model answers.

Usage:  python scripts/capture_screenshots.py
Output: docs/screenshots/*.png
"""

import html
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

ENV = {**os.environ, "PYTHONPATH": str(ROOT), "COLUMNS": "100", "TERM": "xterm-256color"}


def wait_for_port(port: int, timeout: float = 90) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.5)
    raise RuntimeError(f"port {port} did not open")


def cli_html(args: list[str], title: str) -> str:
    """Run a CLI command with colour forced and convert its ANSI output to HTML."""
    from rich.console import Console
    from rich.text import Text

    proc = subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=ROOT, env={**ENV, "FORCE_COLOR": "1"},
        capture_output=True, text=True, timeout=120,
    )
    console = Console(record=True, width=100, force_terminal=True, color_system="truecolor")
    console.print(Text.from_ansi(proc.stdout or proc.stderr))
    body = console.export_html(inline_styles=True, code_format="{code}")
    prompt = html.escape("$ python main.py " + " ".join(args))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
      body {{ margin:0; padding:32px; background:#e9edf2; font-family:-apple-system,Segoe UI,sans-serif; }}
      .win {{ width:fit-content; background:#0d1117; border-radius:10px; overflow:hidden;
              box-shadow:0 12px 32px rgba(0,0,0,.25); }}
      .bar {{ background:#21262d; padding:10px 14px; color:#8b949e; font-size:13px; display:flex; gap:8px; align-items:center; }}
      .dot {{ width:12px; height:12px; border-radius:50%; display:inline-block; }}
      pre {{ margin:0; padding:18px 22px; color:#e6edf3; font:14px/1.45 'DejaVu Sans Mono',Menlo,monospace; }}
      .p {{ color:#7ee787; }}
    </style></head><body><div class="win" id="win">
      <div class="bar"><span class="dot" style="background:#ff5f56"></span><span class="dot" style="background:#ffbd2e"></span>
      <span class="dot" style="background:#27c93f"></span><span style="margin-left:8px">{html.escape(title)}</span></div>
      <pre><span class="p">{prompt}</span>
{body}</pre></div></body></html>"""


def main() -> None:
    api = subprocess.Popen(
        [sys.executable, "-c", "from finance_llm.app import serve; serve(host='127.0.0.1', port=8000)"],
        cwd=ROOT, env=ENV,
    )
    ui = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "finance_llm/ui.py",
         "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false",
         "--theme.base=dark"],
        cwd=ROOT, env=ENV,
    )
    try:
        wait_for_port(8000)
        wait_for_port(8501)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)

            # Streamlit UI: wait for the sidebar and chat input to render
            page.goto("http://127.0.0.1:8501", wait_until="networkidle")
            page.wait_for_selector("[data-testid='stChatInput']", timeout=60000)
            page.wait_for_selector("[data-testid='stSidebar']", timeout=60000)
            page.wait_for_timeout(3000)
            page.screenshot(path=str(OUT / "web-ui.png"))

            # FastAPI Swagger docs with the /query operation expanded
            page.goto("http://127.0.0.1:8000/docs", wait_until="networkidle")
            page.wait_for_selector(".opblock", timeout=60000)
            try:
                page.click("#operations-default-query_endpoint_query_post .opblock-summary", timeout=5000)
                page.wait_for_timeout(1500)
            except Exception as exc:  # layout differences across Swagger versions
                print(f"could not expand /query: {exc}")
            page.screenshot(path=str(OUT / "api-docs.png"))

            # CLI views
            for args, name, title in [
                (["--help"], "cli-help.png", "Finance LLM — CLI"),
                (["stats"], "cli-stats.png", "Finance LLM — stats"),
            ]:
                page.set_content(cli_html(args, title))
                page.locator("#win").screenshot(path=str(OUT / name))

            browser.close()
    finally:
        api.terminate()
        ui.terminate()

    for f in sorted(OUT.glob("*.png")):
        print(f"wrote {f.relative_to(ROOT)} ({f.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
