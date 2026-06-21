"""Generate a deterministic 20-task RoboLab matrix for follow-up comparisons."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

AXIS_TARGET = {"visual": 9, "relational": 8, "procedural": 8}
DIFFICULTY_TARGET = {"simple": 8, "moderate": 7, "complex": 5}


def load_source(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def task_score(task: dict[str, Any], selected: list[dict[str, Any]], axis_counts: Counter[str], diff_counts: Counter[str], attr_counts: Counter[str]) -> float:
    axes = task.get("axes") or []
    attrs = task.get("attributes") or []
    difficulty = str(task.get("difficulty_label") or "unknown")
    score = 0.0
    for axis in axes:
        score += max(0, AXIS_TARGET.get(axis, 0) - axis_counts[axis]) * 4
    score += max(0, DIFFICULTY_TARGET.get(difficulty, 0) - diff_counts[difficulty]) * 3
    for attr in attrs:
        if attr_counts[attr] == 0:
            score += 2.0
    score += min(len(axes), 3) * 0.8
    score -= float(task.get("index", 0)) * 1e-4
    if any(t["task_name"] == task["task_name"] for t in selected):
        score = -1e9
    return score


def select_tasks(tasks: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    axis_counts: Counter[str] = Counter()
    diff_counts: Counter[str] = Counter()
    attr_counts: Counter[str] = Counter()
    remaining = list(tasks)
    while len(selected) < count and remaining:
        best = max(remaining, key=lambda t: task_score(t, selected, axis_counts, diff_counts, attr_counts))
        remaining.remove(best)
        selected.append(best)
        for axis in best.get("axes") or []:
            axis_counts[axis] += 1
        diff_counts[str(best.get("difficulty_label") or "unknown")] += 1
        for attr in best.get("attributes") or []:
            attr_counts[attr] += 1
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("robolab_repro_artifacts/robolab120_task_matrix.json"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()

    source = load_source(args.source)
    selected = select_tasks(source.get("tasks", []), args.count)
    axis_counts = Counter(axis for task in selected for axis in (task.get("axes") or []))
    diff_counts = Counter(str(task.get("difficulty_label") or "unknown") for task in selected)
    attr_counts = Counter(attr for task in selected for attr in (task.get("attributes") or []))
    payload = {
        "source_matrix": str(args.source),
        "selection_rule": "Greedy metadata-balanced selection over axes, difficulties, and attributes; deterministic official-order tie break.",
        "num_tasks": len(selected),
        "axis_counts": dict(sorted(axis_counts.items())),
        "difficulty_counts": dict(sorted(diff_counts.items())),
        "attribute_counts": dict(sorted(attr_counts.items())),
        "tasks": selected,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "num_tasks": len(selected), "axis_counts": payload["axis_counts"], "difficulty_counts": payload["difficulty_counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
