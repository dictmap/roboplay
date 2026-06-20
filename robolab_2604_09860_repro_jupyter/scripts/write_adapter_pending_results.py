"""Create explicit adapter-pending result rows for non-drop-in baselines."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_tasks(matrix: Path) -> list[dict[str, Any]]:
    data = json.loads(matrix.read_text(encoding="utf-8"))
    return data.get("tasks", [])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--status", default="adapter_required")
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()

    tasks = load_tasks(args.matrix)
    args.out_root.mkdir(parents=True, exist_ok=True)
    episode_path = args.out_root / "episode_results.jsonl"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with episode_path.open("w", encoding="utf-8") as f:
        for task in tasks:
            row = {
                "task_name": task["task_name"],
                "env_name": task["task_name"],
                "policy": args.policy,
                "status": args.status,
                "adapter_required": True,
                "success": None,
                "score": None,
                "episode_step": None,
                "reason": args.reason,
                "created_at": now,
                "axes": task.get("axes", []),
                "difficulty_label": task.get("difficulty_label"),
                "source_matrix": str(args.matrix),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "output_root": str(args.out_root),
        "episode_results_jsonl": str(episode_path),
        "policy": args.policy,
        "status": args.status,
        "reason": args.reason,
        "num_tasks": len(tasks),
        "boundary": "These rows are placeholders for comparison bookkeeping. They are not simulation rollouts.",
    }
    (args.out_root / "adapter_pending_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"out_root": str(args.out_root), "rows": len(tasks), "policy": args.policy}, ensure_ascii=False))


if __name__ == "__main__":
    main()
