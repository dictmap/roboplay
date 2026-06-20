"""Summarize RoboLab ablation output folders.

This parser is intentionally lightweight: it reads episode_results.jsonl files
from RoboLab output folders and produces grouped JSON/CSV summaries. It does not
require Isaac Sim.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


def iter_episode_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.name == "episode_results.jsonl":
            files.append(path)
        elif path.is_dir():
            files.extend(path.rglob("episode_results.jsonl"))
    return sorted(set(files))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL") from exc
            row["_episode_results_file"] = str(path)
            rows.append(row)
    return rows


def infer_variant(row: dict[str, Any], source: Path) -> str:
    text = " ".join(
        str(value)
        for value in [
            row.get("env_name"),
            row.get("run_name"),
            row.get("policy"),
            source.parent.name,
            source.parent.parent.name if source.parent.parent else "",
        ]
    )
    mapping = [
        ("randomize_wrist_and_external_cam", "camera_external_and_wrist_randomized"),
        ("randomize_external_camera", "camera_external_randomized"),
        ("randomize_wrist_cam", "camera_wrist_randomized"),
        ("camera_pose_variation", "camera_pose_variation"),
        ("wrist_blackout", "wrist_blackout"),
        ("baseline", "baseline"),
    ]
    for needle, variant in mapping:
        if needle in text:
            return variant
    return "unlabeled"


def numeric_mean(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [row.get(key) for row in rows if isinstance(row.get(key), (int, float))]
    return float(mean(values)) if values else None


def nested_numeric_mean(rows: list[dict[str, Any]], parent: str, key: str) -> float | None:
    values = [
        row.get(parent, {}).get(key)
        for row in rows
        if isinstance(row.get(parent), dict) and isinstance(row.get(parent, {}).get(key), (int, float))
    ]
    return float(mean(values)) if values else None


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        source = Path(row["_episode_results_file"])
        variant = infer_variant(row, source)
        key = (
            str(row.get("task_name") or row.get("env_name") or "unknown_task"),
            str(row.get("env_name") or "unknown_env"),
            str(row.get("policy") or "unknown_policy"),
            variant,
        )
        groups[key].append(row)

    output: list[dict[str, Any]] = []
    for (task_name, env_name, policy, variant), group_rows in sorted(groups.items()):
        events = Counter()
        for row in group_rows:
            if isinstance(row.get("events"), dict):
                events.update({str(k): int(v) for k, v in row["events"].items() if isinstance(v, int)})
        successes = [bool(row.get("success")) for row in group_rows]
        output.append(
            {
                "task_name": task_name,
                "env_name": env_name,
                "policy": policy,
                "variant": variant,
                "episodes": len(group_rows),
                "successes": sum(successes),
                "success_rate": sum(successes) / len(group_rows) if group_rows else None,
                "score_mean": numeric_mean(group_rows, "score"),
                "episode_step_mean": numeric_mean(group_rows, "episode_step"),
                "duration_mean": numeric_mean(group_rows, "duration"),
                "policy_inference_avg_ms_mean": nested_numeric_mean(group_rows, "timing", "policy_inference_avg_ms"),
                "env_step_avg_ms_mean": nested_numeric_mean(group_rows, "timing", "env_step_avg_ms"),
                "events": dict(events),
                "source_files": sorted({row["_episode_results_file"] for row in group_rows}),
            }
        )
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "task_name",
        "env_name",
        "policy",
        "variant",
        "episodes",
        "successes",
        "success_rate",
        "score_mean",
        "episode_step_mean",
        "duration_mean",
        "policy_inference_avg_ms_mean",
        "env_step_avg_ms_mean",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roots", nargs="+", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, default=None)
    args = parser.parse_args()

    episode_files = iter_episode_files(args.roots)
    rows: list[dict[str, Any]] = []
    for path in episode_files:
        rows.extend(read_jsonl(path))

    summary = summarize(rows)
    payload = {
        "episode_files": [str(path) for path in episode_files],
        "num_episode_rows": len(rows),
        "groups": summary,
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.out_csv:
        args.out_csv.parent.mkdir(parents=True, exist_ok=True)
        write_csv(args.out_csv, summary)

    print(json.dumps({"out_json": str(args.out_json), "out_csv": str(args.out_csv) if args.out_csv else None, "groups": len(summary)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
