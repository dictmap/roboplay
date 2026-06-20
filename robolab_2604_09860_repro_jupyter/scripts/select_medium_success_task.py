"""Select a medium-success task from a RoboLab output folder."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def read_rows(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(root.rglob("episode_results.jsonl")):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    row = json.loads(line)
                    row["_source"] = str(path)
                    rows.append(row)
    return rows


def load_matrix(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["task_name"]: row for row in data.get("tasks", [])}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--target-rate", type=float, default=0.5)
    args = parser.parse_args()

    rows = read_rows(args.output_root)
    if not rows:
        raise SystemExit(f"No episode_results.jsonl rows found under {args.output_root}")

    matrix = load_matrix(args.matrix)
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        task = row.get("task_name") or row.get("env_name")
        if task:
            by_task[str(task)].append(row)

    candidates = []
    for task, task_rows in by_task.items():
        successes = [1.0 if row.get("success") else 0.0 for row in task_rows]
        rate = mean(successes)
        score_values = [row.get("score") for row in task_rows if isinstance(row.get("score"), (int, float))]
        meta = matrix.get(task, {})
        candidates.append(
            {
                "task_name": task,
                "episodes": len(task_rows),
                "success_rate": rate,
                "score_mean": float(mean(score_values)) if score_values else None,
                "distance_to_target": abs(rate - args.target_rate),
                "difficulty_label": meta.get("difficulty_label"),
                "axes": meta.get("axes", []),
                "attributes": meta.get("attributes", []),
                "primary_objects_for_object_pose_variation": meta.get("primary_objects_for_object_pose_variation", []),
            }
        )

    non_degenerate = [row for row in candidates if 0.0 < row["success_rate"] < 1.0]
    pool = non_degenerate or candidates
    selected = sorted(pool, key=lambda row: (row["distance_to_target"], -row["episodes"], row["task_name"]))[0]
    payload = {
        "output_root": str(args.output_root),
        "target_rate": args.target_rate,
        "selected": selected,
        "candidates": sorted(candidates, key=lambda row: (row["distance_to_target"], row["task_name"])),
        "note": "If no task has 0<success_rate<1, this selects the closest task to target_rate as a fallback.",
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "selected": selected}, ensure_ascii=False))


if __name__ == "__main__":
    main()
