"""Verify that RoboLab output folders contain required evidence artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_matrix(path: Path | None) -> list[str] | None:
    if path is None:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return [row["task_name"] for row in data.get("tasks", [])]


def find_task_dirs(root: Path, task: str) -> list[Path]:
    candidates = []
    if any(root.glob("run_*.hdf5")) or list(root.glob("*.mp4")):
        candidates.append(root)
    candidates.extend(path for path in root.iterdir() if path.is_dir() and task in path.name)
    return sorted(set(candidates))


def nonempty(paths: list[Path]) -> list[str]:
    return [str(path) for path in paths if path.is_file() and path.stat().st_size > 0]


def verify_task(root: Path, task: str) -> dict[str, Any]:
    dirs = find_task_dirs(root, task)
    hdf5 = []
    videos = []
    logs = []
    env_cfg = []
    for directory in dirs:
        hdf5.extend(directory.glob("run_*.hdf5"))
        videos.extend(directory.glob("*.mp4"))
        logs.extend(directory.glob("log_*_env*.json"))
        env_cfg.extend(directory.glob("env_cfg.json"))
    return {
        "task": task,
        "task_dirs": [str(path) for path in dirs],
        "hdf5": nonempty(hdf5),
        "videos": nonempty(videos),
        "subtask_or_event_logs": nonempty(logs),
        "env_cfg": nonempty(env_cfg),
        "passed": bool(nonempty(hdf5) and nonempty(videos) and nonempty(logs)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, default=None)
    parser.add_argument("--tasks", nargs="+", default=None)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = args.output_root
    tasks = args.tasks or load_matrix(args.matrix)
    if not tasks:
        tasks = sorted({path.name.split("_")[0] for path in root.iterdir() if path.is_dir()})

    root_episode = root / "episode_results.jsonl"
    report = {
        "output_root": str(root),
        "episode_results_jsonl": str(root_episode) if root_episode.exists() else None,
        "episode_results_jsonl_nonempty": root_episode.exists() and root_episode.stat().st_size > 0,
        "tasks": [verify_task(root, task) for task in tasks],
    }
    report["passed"] = report["episode_results_jsonl_nonempty"] and all(row["passed"] for row in report["tasks"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "passed": report["passed"]}, ensure_ascii=False))

    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
