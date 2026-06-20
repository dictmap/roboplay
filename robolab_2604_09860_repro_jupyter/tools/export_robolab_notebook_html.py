#!/usr/bin/env python3
"""Export the RoboLab learning notebook to a lightweight static HTML page.

This intentionally avoids Jupyter nbconvert so the docs package can be refreshed
on a minimal Python environment. It renders markdown cells, code cells, and any
existing text outputs; it does not execute the notebook.
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path

import markdown
import nbformat


STYLE = """
:root {
  color-scheme: light dark;
  --bg: #f7f8fa;
  --fg: #1f2328;
  --muted: #5f6b7a;
  --panel: #ffffff;
  --border: #d0d7de;
  --accent: #166534;
  --code-bg: #f6f8fa;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0d1117;
    --fg: #e6edf3;
    --muted: #9aa4b2;
    --panel: #161b22;
    --border: #30363d;
    --accent: #4ade80;
    --code-bg: #0b1220;
  }
}
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 20px 72px;
}
.cell {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 18px 22px;
  margin: 16px 0;
  overflow-x: auto;
}
.cell.markdown { border-left: 5px solid var(--accent); }
.cell.code { border-left: 5px solid #2563eb; }
h1, h2, h3 { line-height: 1.25; }
h1 { font-size: 2.1rem; }
h2 { margin-top: 1.6em; }
a { color: #0969da; }
blockquote {
  border-left: 4px solid var(--border);
  margin-left: 0;
  padding-left: 1rem;
  color: var(--muted);
}
pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
}
code {
  background: var(--code-bg);
  border-radius: 4px;
  padding: 0.12em 0.28em;
}
pre code { padding: 0; background: transparent; }
table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}
th, td {
  border: 1px solid var(--border);
  padding: 6px 8px;
  vertical-align: top;
}
th { background: var(--code-bg); }
.meta {
  color: var(--muted);
  margin-bottom: 24px;
}
"""


def render_markdown(source: str) -> str:
    return markdown.markdown(
        source,
        extensions=["extra", "tables", "fenced_code", "toc", "sane_lists"],
        output_format="html5",
    )


def render_outputs(outputs: list[dict]) -> str:
    parts: list[str] = []
    for output in outputs:
        output_type = output.get("output_type")
        if output_type == "stream":
            text = output.get("text", "")
            parts.append(f"<pre><code>{html.escape(text)}</code></pre>")
        elif output_type in {"execute_result", "display_data"}:
            data = output.get("data", {})
            if "text/html" in data:
                value = data["text/html"]
                parts.append("".join(value) if isinstance(value, list) else str(value))
            elif "text/plain" in data:
                value = data["text/plain"]
                text = "".join(value) if isinstance(value, list) else str(value)
                parts.append(f"<pre><code>{html.escape(text)}</code></pre>")
        elif output_type == "error":
            traceback = "\n".join(output.get("traceback", []))
            parts.append(f"<pre><code>{html.escape(traceback)}</code></pre>")
    return "\n".join(parts)


def export_notebook(notebook_path: Path, output_path: Path) -> None:
    nb = nbformat.read(notebook_path, as_version=4)
    body_parts = [
        "<main>",
        "<h1>RoboLab 4090 Reproduction Learning Record</h1>",
        f"<p class='meta'>Generated from <code>{html.escape(notebook_path.name)}</code>. This static page renders the latest markdown/code content without executing Isaac Sim.</p>",
    ]
    for index, cell in enumerate(nb.cells, start=1):
        if cell.cell_type == "markdown":
            body_parts.append(f"<section class='cell markdown' id='cell-{index}'>")
            body_parts.append(render_markdown(cell.source))
            body_parts.append("</section>")
        elif cell.cell_type == "code":
            body_parts.append(f"<section class='cell code' id='cell-{index}'>")
            body_parts.append(f"<pre><code>{html.escape(cell.source)}</code></pre>")
            outputs = render_outputs(cell.get("outputs", []))
            if outputs:
                body_parts.append(outputs)
            body_parts.append("</section>")
    body_parts.append("</main>")
    page = "\n".join([
        "<!doctype html>",
        "<html lang='zh-CN'>",
        "<head>",
        "<meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>RoboLab 4090 Reproduction Learning Record</title>",
        f"<style>{STYLE}</style>",
        "</head>",
        "<body>",
        *body_parts,
        "</body>",
        "</html>",
    ])
    output_path.write_text(page, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--notebook", default="RoboLab_4090_repro_learning_record.ipynb")
    parser.add_argument("--output", default="RoboLab_4090_repro_learning_record.html")
    args = parser.parse_args()
    export_notebook(Path(args.notebook), Path(args.output))


if __name__ == "__main__":
    main()
