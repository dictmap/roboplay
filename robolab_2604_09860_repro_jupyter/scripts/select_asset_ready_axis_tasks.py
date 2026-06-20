"""Select an asset-ready RoboLab task subset by competency axis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DIFFICULTY_ORDER = {"simple": 0, "moderate": 1, "complex": 2}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def task_sort_key(row: dict[str, Any]) -> tuple[int, float, int, str]:
    """优先选简单、短任务；同等条件下保留官方 metadata 顺序。"""
    difficulty = DIFFICULTY_ORDER.get(str(row.get("difficulty_label") or "unknown"), 99)
    score = row.get("difficulty_score")
    return (
        difficulty,
        float(score) if isinstance(score, (int, float)) else 99.0,
        int(row.get("index") or 9999),
        str(row.get("task_name") or ""),
    )


def select_tasks(
    matrix: dict[str, Any],
    preflight: dict[str, Any],
    axes: list[str],
    per_axis: int,
) -> list[dict[str, Any]]:
    ready_names = {row["task_name"] for row in preflight.get("tasks", []) if row.get("asset_preflight_passed")}
    matrix_tasks = {row["task_name"]: row for row in matrix.get("tasks", []) if row.get("task_name")}

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for axis in axes:
        candidates = [
            row
            for name, row in matrix_tasks.items()
            if name in ready_names and axis in (row.get("axes") or [])
        ]
        candidates.sort(key=task_sort_key)
        for row in candidates[:per_axis]:
            task_name = row["task_name"]
            if task_name in seen:
                continue
            item = dict(row)
            item["selection_axis"] = axis
            item["selection_reason"] = "asset_preflight_passed_and_axis_candidate"
            selected.append(item)
            seen.add(task_name)
    return selected


def axis_counts(tasks: list[dict[str, Any]], axes: list[str]) -> dict[str, int]:
    return {axis: sum(1 for row in tasks if axis in (row.get("axes") or [])) for axis in axes}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--axes", nargs="+", default=["visual", "procedural", "relational"])
    parser.add_argument("--per-axis", type=int, default=5)
    args = parser.parse_args()

    matrix = load_json(args.matrix)
    preflight = load_json(args.preflight)
    tasks = select_tasks(matrix=matrix, preflight=preflight, axes=args.axes, per_axis=args.per_axis)
    payload = {
        "source_matrix": str(args.matrix),
        "source_preflight": str(args.preflight),
        "selection_rule": (
            "From static asset-preflight-passed tasks, choose low-difficulty candidates per axis; "
            "task names are unique, but multi-label tasks can count for multiple axes."
        ),
        "per_axis": args.per_axis,
        "axes": args.axes,
        "num_tasks": len(tasks),
        "axis_counts": axis_counts(tasks, args.axes),
        "tasks": tasks,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "num_tasks": len(tasks),
                "axis_counts": payload["axis_counts"],
                "tasks": [row["task_name"] for row in tasks],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
