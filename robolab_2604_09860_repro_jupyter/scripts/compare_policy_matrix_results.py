"""Compare multiple RoboLab policy output folders on the same task matrix."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def load_matrix(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["task_name"]: row for row in data.get("tasks", [])}


def read_episode_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("episode_results.jsonl")):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                row["_output_root"] = str(root)
                row["_episode_results_file"] = str(path)
                rows.append(row)
    return rows


def infer_policy(root: Path, row: dict[str, Any]) -> str:
    policy = row.get("policy")
    if policy:
        return str(policy)
    name = root.name
    for prefix in ["axis5_", "pi05_", "policy_"]:
        if name.startswith(prefix):
            return name[len(prefix) :].split("_")[0]
    return name


def safe_mean(values: list[float]) -> float | None:
    return float(mean(values)) if values else None


def success_values(group_rows: list[dict[str, Any]]) -> list[float]:
    """Use only real boolean success values; adapter placeholders stay pending."""
    values: list[float] = []
    for row in group_rows:
        success = row.get("success")
        if isinstance(success, bool):
            values.append(1.0 if success else 0.0)
    return values


def aggregate(rows: list[dict[str, Any]], matrix: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_task_policy: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_axis_policy: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_difficulty_policy: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        root = Path(row["_output_root"])
        task = str(row.get("task_name") or row.get("env_name") or "unknown_task")
        policy = infer_policy(root, row)
        meta = matrix.get(task, {})
        by_task_policy[(policy, task)].append(row)
        for axis in meta.get("axes", []) or ["unknown_axis"]:
            by_axis_policy[(policy, axis)].append(row)
        by_difficulty_policy[(policy, meta.get("difficulty_label") or "unknown")].append(row)

    def summarize_group(key: tuple[str, str], group_rows: list[dict[str, Any]], label_name: str) -> dict[str, Any]:
        successes = success_values(group_rows)
        scores = [float(row["score"]) for row in group_rows if isinstance(row.get("score"), (int, float))]
        steps = [float(row["episode_step"]) for row in group_rows if isinstance(row.get("episode_step"), (int, float))]
        pending = [row for row in group_rows if row.get("adapter_required") or row.get("status") in {"adapter_required", "planner_adapter_required"}]
        return {
            "policy": key[0],
            label_name: key[1],
            "episodes": len(group_rows),
            "scored_episodes": len(successes),
            "pending_episodes": len(pending),
            "success_rate": safe_mean(successes),
            "score_mean": safe_mean(scores),
            "episode_step_mean": safe_mean(steps),
        }

    return {
        "by_task": [summarize_group(key, rows, "task_name") for key, rows in sorted(by_task_policy.items())],
        "by_axis": [summarize_group(key, rows, "axis") for key, rows in sorted(by_axis_policy.items())],
        "by_difficulty": [
            summarize_group(key, rows, "difficulty_label") for key, rows in sorted(by_difficulty_policy.items())
        ],
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = sorted({key for row in rows for key in row.keys()})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--roots", nargs="+", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, default=None)
    args = parser.parse_args()

    matrix = load_matrix(args.matrix)
    rows: list[dict[str, Any]] = []
    for root in args.roots:
        rows.extend(read_episode_rows(root))

    report = {
        "matrix": str(args.matrix),
        "roots": [str(root) for root in args.roots],
        "num_episode_rows": len(rows),
        "aggregates": aggregate(rows, matrix),
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.out_csv:
        write_csv(args.out_csv, report["aggregates"]["by_axis"])
    print(json.dumps({"out_json": str(args.out_json), "rows": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
