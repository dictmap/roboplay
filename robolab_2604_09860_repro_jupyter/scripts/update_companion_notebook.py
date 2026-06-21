"""Create/update a companion Jupyter notebook from the live experiment log."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import nbformat as nbf


def load_status(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"raw": line})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--md", type=Path, required=True)
    parser.add_argument("--status-jsonl", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    nb = nbf.v4.new_notebook()
    md_text = args.md.read_text(encoding="utf-8") if args.md.exists() else "# Companion experiment queue\n\nNo markdown log yet."
    rows = load_status(args.status_jsonl)
    nb.cells = [
        nbf.v4.new_markdown_cell(md_text),
        nbf.v4.new_markdown_cell("## 机器可读状态 JSONL\n\n下面 cell 读取同目录 JSONL，方便后续继续分析。"),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import json\n"
            f"status_path = Path({str(args.status_jsonl)!r})\n"
            "rows = [json.loads(line) for line in status_path.read_text(encoding='utf-8').splitlines() if line.strip()] if status_path.exists() else []\n"
            "len(rows), rows[-5:] if rows else []"
        ),
        nbf.v4.new_markdown_cell("## 当前状态快照\n\n```json\n" + json.dumps(rows[-12:], ensure_ascii=False, indent=2) + "\n```"),
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, args.out)
    print(json.dumps({"out": str(args.out), "cells": len(nb.cells), "status_rows": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
