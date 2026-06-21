"""Read RoboLab episode results and produce paper-aligned summary tables.

This script is intentionally independent of Isaac Sim. It consumes the JSONL
files written by RoboLab rollouts and an optional task-matrix JSON that contains
paper metadata such as axes, difficulty and task length.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def load_task_matrix(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    tasks = payload.get("tasks", payload) if isinstance(payload, dict) else payload
    if not isinstance(tasks, list):
        return {}
    return {str(task.get("task_name")): task for task in tasks if task.get("task_name")}


def iter_episode_files(inputs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for item in inputs:
        if item.is_file() and item.name == "episode_results.jsonl":
            files.append(item)
        elif item.is_file() and item.suffix == ".jsonl":
            # Run manifests contain per-task artifact paths. Read them as a
            # convenience so the analysis can be driven from the manifest.
            for line in item.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                for key in ("episode_results", "episode_results_path", "results_path"):
                    value = row.get(key)
                    if value:
                        path = Path(value)
                        if path.exists() and path.name == "episode_results.jsonl":
                            files.append(path)
                output_dir = row.get("output_dir") or row.get("output_root")
                if output_dir:
                    files.extend(Path(output_dir).rglob("episode_results.jsonl"))
        elif item.is_dir():
            files.extend(item.rglob("episode_results.jsonl"))
    return sorted(set(path.resolve() for path in files if path.exists()))


def read_episode_rows(files: list[Path], task_meta: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for file in files:
        for line_no, line in enumerate(file.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{file}:{line_no}: invalid JSONL") from exc
            task_name = str(row.get("task_name") or row.get("env_name") or "unknown_task")
            meta = task_meta.get(task_name, {})
            row["_source_file"] = str(file)
            row["_task_name"] = task_name
            row["_axes"] = list(meta.get("axes") or infer_axes(row))
            row["_difficulty_label"] = str(meta.get("difficulty_label") or infer_difficulty(row))
            row["_difficulty_score"] = meta.get("difficulty_score")
            row["_num_subtasks"] = meta.get("num_subtasks")
            row["_num_atomic_conditions"] = meta.get("num_atomic_conditions")
            rows.append(row)
    return rows


def infer_axes(row: dict[str, Any]) -> list[str]:
    attrs = {str(item).lower() for item in row.get("attributes", []) if item}
    axes: list[str] = []
    if attrs & {"color", "semantics", "size"}:
        axes.append("visual")
    if attrs & {"affordance", "reorientation", "stacking", "sorting"}:
        axes.append("procedural")
    if attrs & {"spatial", "counting", "order", "conjunction", "disjunction"}:
        axes.append("relational")
    return axes or ["unknown"]


def infer_difficulty(row: dict[str, Any]) -> str:
    attrs = {str(item).lower() for item in row.get("attributes", []) if item}
    for label in ("simple", "moderate", "complex"):
        if label in attrs:
            return label
    steps = row.get("episode_step")
    if isinstance(steps, (int, float)):
        if steps <= 900:
            return "simple"
        if steps <= 2700:
            return "moderate"
        return "complex"
    return "unknown"


def mean_or_none(values: list[float]) -> float | None:
    return float(mean(values)) if values else None


def summarize_group(rows: list[dict[str, Any]], key_name: str, key_value: str) -> dict[str, Any]:
    success_count = sum(bool(row.get("success")) for row in rows)
    steps = [float(row["episode_step"]) for row in rows if isinstance(row.get("episode_step"), (int, float))]
    scores = [float(row["score"]) for row in rows if isinstance(row.get("score"), (int, float))]
    infer_ms = [
        float(row.get("timing", {}).get("policy_inference_avg_ms"))
        for row in rows
        if isinstance(row.get("timing"), dict)
        and isinstance(row.get("timing", {}).get("policy_inference_avg_ms"), (int, float))
    ]
    return {
        key_name: key_value,
        "episodes": len(rows),
        "successes": success_count,
        "success_rate": success_count / len(rows) if rows else None,
        "episode_step_mean": mean_or_none(steps),
        "score_mean": mean_or_none(scores),
        "policy_inference_avg_ms_mean": mean_or_none(infer_ms),
    }


def group_by_single(rows: list[dict[str, Any]], field: str, output_key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(field, "unknown"))].append(row)
    return [summarize_group(group_rows, output_key, key) for key, group_rows in sorted(groups.items())]


def group_by_axis(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for axis in row.get("_axes") or ["unknown"]:
            groups[str(axis)].append(row)
    return [summarize_group(group_rows, "axis", key) for key, group_rows in sorted(groups.items())]


def group_by_task_length(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        subtasks = row.get("_num_subtasks")
        atomics = row.get("_num_atomic_conditions")
        if subtasks is None:
            key = "unknown"
        else:
            key = f"{subtasks}_subtasks"
        groups[key].append(row)
        if atomics is not None:
            groups[f"{atomics}_atomic_conditions"].append(row)
    return [summarize_group(group_rows, "task_length", key) for key, group_rows in sorted(groups.items())]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", type=Path, required=True)
    parser.add_argument("--task-matrix", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--prefix", default="read_results")
    args = parser.parse_args()

    task_meta = load_task_matrix(args.task_matrix)
    episode_files = iter_episode_files(args.inputs)
    rows = read_episode_rows(episode_files, task_meta)

    by_axis = group_by_axis(rows)
    by_difficulty = group_by_single(rows, "_difficulty_label", "difficulty")
    by_task_length = group_by_task_length(rows)
    by_task = group_by_single(rows, "_task_name", "task_name")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "by_axis": args.out_dir / f"{args.prefix}_by_axis.csv",
        "by_difficulty": args.out_dir / f"{args.prefix}_by_difficulty.csv",
        "by_task_length": args.out_dir / f"{args.prefix}_by_task_length.csv",
        "by_task": args.out_dir / f"{args.prefix}_by_task.csv",
        "summary": args.out_dir / f"{args.prefix}_summary.json",
    }
    write_csv(outputs["by_axis"], by_axis)
    write_csv(outputs["by_difficulty"], by_difficulty)
    write_csv(outputs["by_task_length"], by_task_length)
    write_csv(outputs["by_task"], by_task)
    payload = {
        "inputs": [str(path) for path in args.inputs],
        "task_matrix": str(args.task_matrix) if args.task_matrix else None,
        "episode_files": [str(path) for path in episode_files],
        "episode_rows": len(rows),
        "successes": sum(bool(row.get("success")) for row in rows),
        "success_rate": sum(bool(row.get("success")) for row in rows) / len(rows) if rows else None,
        "tables": {key: str(path) for key, path in outputs.items() if key != "summary"},
        "by_axis": by_axis,
        "by_difficulty": by_difficulty,
        "by_task_length": by_task_length,
    }
    outputs["summary"].write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"episode_rows": len(rows), "successes": payload["successes"], "outputs": {k: str(v) for k, v in outputs.items()}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
