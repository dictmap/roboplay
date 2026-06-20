"""Diagnose RoboLab task-run logs without importing Isaac Sim.

The full RoboLab runner may continue after a per-task failure, so the shell
exit code alone is not enough. This script joins three evidence streams:

1. The tmux/run log, which contains missing USD assets and runtime tracebacks.
2. The task manifest, which records per-task run and artifact-check exit codes.
3. Per-task artifact-check JSON files, which verify episode JSONL/HDF5/video/logs.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TASK_START_RE = re.compile(r"\[robolab120\] \[(\d+)/(\d+)\] ([A-Za-z0-9_]+) -> ([^\s]+)")
MISSING_ASSET_RE = re.compile(r"Could not open asset @([^@]+)@")
CONTACT_REPORTER_RE = re.compile(r"Sensor at path '([^']+)' could not find any bodies with contact reporter API")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """读取 JSONL manifest；空行会被跳过，坏行会直接报出文件和行号。"""
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL") from exc
    return rows


def load_artifact_checks(patterns: list[str]) -> dict[str, dict[str, Any]]:
    """把 `*_Task_artifact_check.json` 按任务名索引起来。"""
    checks: dict[str, dict[str, Any]] = {}
    for pattern in patterns:
        for file_name in glob.glob(pattern):
            path = Path(file_name)
            data = json.loads(path.read_text(encoding="utf-8"))
            for task_row in data.get("tasks", []):
                task = task_row.get("task")
                if task:
                    checks[task] = {
                        "file": str(path),
                        "root_passed": bool(data.get("passed")),
                        "episode_results_jsonl_nonempty": bool(data.get("episode_results_jsonl_nonempty")),
                        "task_passed": bool(task_row.get("passed")),
                        "hdf5_count": len(task_row.get("hdf5") or []),
                        "video_count": len(task_row.get("videos") or []),
                        "event_log_count": len(task_row.get("subtask_or_event_logs") or []),
                        "env_cfg_count": len(task_row.get("env_cfg") or []),
                    }
    return checks


def parse_log(path: Path, max_examples: int) -> dict[str, Any]:
    """按当前正在运行的任务聚合日志信号。"""
    tasks: dict[str, dict[str, Any]] = {}
    current_task: str | None = None
    global_missing_assets: Counter[str] = Counter()

    def task_bucket(task: str) -> dict[str, Any]:
        return tasks.setdefault(
            task,
            {
                "task": task,
                "missing_asset_count": 0,
                "missing_asset_examples": [],
                "contact_reporter_errors": [],
                "traceback_count": 0,
                "runtime_error_count": 0,
                "line_start": None,
                "line_end": None,
            },
        )

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, 1):
            start = TASK_START_RE.search(line)
            if start:
                current_task = start.group(3)
                bucket = task_bucket(current_task)
                bucket["line_start"] = line_no
                bucket["line_end"] = line_no
                continue

            if current_task:
                task_bucket(current_task)["line_end"] = line_no

            missing = MISSING_ASSET_RE.search(line)
            if missing:
                asset = missing.group(1)
                global_missing_assets[asset] += 1
                if current_task:
                    bucket = task_bucket(current_task)
                    bucket["missing_asset_count"] += 1
                    examples = bucket["missing_asset_examples"]
                    if len(examples) < max_examples and asset not in examples:
                        examples.append(asset)

            contact = CONTACT_REPORTER_RE.search(line)
            if contact and current_task:
                bucket = task_bucket(current_task)
                errors = bucket["contact_reporter_errors"]
                if len(errors) < max_examples:
                    errors.append({"line": line_no, "sensor_path": contact.group(1)})

            if "Traceback (most recent call last):" in line and current_task:
                task_bucket(current_task)["traceback_count"] += 1

            if "RuntimeError:" in line and current_task:
                task_bucket(current_task)["runtime_error_count"] += 1

    return {
        "tasks": tasks,
        "missing_assets_total": sum(global_missing_assets.values()),
        "missing_assets_unique": len(global_missing_assets),
        "top_missing_assets": [
            {"asset": asset, "count": count}
            for asset, count in global_missing_assets.most_common(max_examples)
        ],
    }


def classify_task(task: dict[str, Any]) -> str:
    """给每个任务一个可读的状态，避免把环境失败误写成 policy 失败。"""
    artifact = task.get("artifact_check") or {}
    if artifact.get("task_passed"):
        return "complete_scored_episode"
    if task.get("contact_reporter_errors"):
        return "env_init_failed_contact_sensor"
    if task.get("missing_asset_count", 0) > 0:
        return "artifact_missing_or_asset_incomplete"
    if artifact and not artifact.get("task_passed"):
        return "artifact_check_failed_no_episode"
    return "unknown_or_log_incomplete"


def build_report(
    log_path: Path,
    manifest_path: Path | None,
    artifact_patterns: list[str],
    max_examples: int,
) -> dict[str, Any]:
    parsed = parse_log(log_path, max_examples=max_examples)
    tasks = parsed["tasks"]

    manifest_rows = read_jsonl(manifest_path) if manifest_path else []
    for row in manifest_rows:
        task_name = row.get("task_name")
        if not task_name:
            continue
        bucket = tasks.setdefault(task_name, {"task": task_name})
        bucket["manifest"] = {
            "created_at": row.get("created_at"),
            "output_root": row.get("output_root"),
            "run_returncode": row.get("run_returncode"),
            "verify_returncode": row.get("verify_returncode"),
        }

    artifact_checks = load_artifact_checks(artifact_patterns)
    for task_name, artifact in artifact_checks.items():
        bucket = tasks.setdefault(task_name, {"task": task_name})
        bucket["artifact_check"] = artifact

    for bucket in tasks.values():
        bucket["diagnosis"] = classify_task(bucket)

    diagnosis_counts = Counter(bucket["diagnosis"] for bucket in tasks.values())
    return {
        "log": str(log_path),
        "manifest": str(manifest_path) if manifest_path else None,
        "num_tasks_observed": len(tasks),
        "diagnosis_counts": dict(sorted(diagnosis_counts.items())),
        "missing_assets_total": parsed["missing_assets_total"],
        "missing_assets_unique": parsed["missing_assets_unique"],
        "top_missing_assets": parsed["top_missing_assets"],
        "tasks": [tasks[name] for name in sorted(tasks)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--artifact-check-glob", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-examples", type=int, default=15)
    args = parser.parse_args()

    report = build_report(
        log_path=args.log,
        manifest_path=args.manifest,
        artifact_patterns=args.artifact_check_glob,
        max_examples=args.max_examples,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "num_tasks_observed": report["num_tasks_observed"],
                "diagnosis_counts": report["diagnosis_counts"],
                "missing_assets_unique": report["missing_assets_unique"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
