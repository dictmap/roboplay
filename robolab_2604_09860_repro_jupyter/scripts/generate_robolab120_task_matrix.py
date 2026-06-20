"""Generate a full RoboLab-120 task matrix from official task metadata."""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


METADATA_URL = "https://raw.githubusercontent.com/NVlabs/RoboLab/main/robolab/tasks/_metadata/task_metadata.json"

ATTRIBUTE_TO_AXIS = {
    "size": "visual",
    "color": "visual",
    "semantics": "visual",
    "spatial": "relational",
    "conjunction": "relational",
    "counting": "relational",
    "stacking": "procedural",
    "sorting": "procedural",
    "reorientation": "procedural",
    "affordance": "procedural",
}

CONTAINER_LIKE_OBJECTS = {
    "table",
    "grey_bin",
    "left_bin",
    "right_bin",
    "bin",
    "crate",
    "bowl",
    "plate",
    "tray",
}


def load_metadata(path_or_url: str) -> list[dict[str, Any]]:
    """Load RoboLab metadata from a local JSON file or the official raw URL."""
    if path_or_url.startswith(("http://", "https://")):
        with urllib.request.urlopen(path_or_url, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    return json.loads(Path(path_or_url).read_text(encoding="utf-8"))


def split_csv(value: str | None) -> list[str]:
    """Split RoboLab metadata comma fields while preserving original labels."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def axes_for_attributes(attrs: list[str]) -> list[str]:
    """Map fine-grained paper attributes to visual/procedural/relational axes."""
    return sorted({ATTRIBUTE_TO_AXIS[attr] for attr in attrs if attr in ATTRIBUTE_TO_AXIS})


def parse_primary_objects(subtasks: str | None, contact_objects: str | None) -> list[str]:
    """Extract likely target objects for later object-position perturbation tests."""
    objects: list[str] = []
    for group in re.findall(r"groups=\[([^\]]+)\]", subtasks or ""):
        for item in re.findall(r"'([^']+)'", group):
            if item != "conditions" and item not in objects:
                objects.append(item)
    if objects and not any(item.startswith("group") or "_and_" in item for item in objects):
        return objects

    fallback: list[str] = []
    for item in split_csv(contact_objects):
        if item not in CONTAINER_LIKE_OBJECTS and item not in fallback:
            fallback.append(item)
    return fallback[:4]


def build_task_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    """Normalize one official metadata row into the local experiment schema."""
    attrs = split_csv(row.get("attributes"))
    axes = axes_for_attributes(attrs)
    return {
        "index": index,
        "task_name": row.get("task_name"),
        "instruction": row.get("instruction"),
        "axes": axes,
        "attributes": attrs,
        "difficulty_label": row.get("difficulty_label"),
        "difficulty_score": row.get("difficulty_score"),
        "num_subtasks": row.get("num_subtasks"),
        "num_atomic_conditions": row.get("num_atomic_conditions"),
        "episode_s": row.get("episode_s"),
        "scene": row.get("scene"),
        "filename": row.get("filename"),
        "contact_objects": split_csv(row.get("contact_objects")),
        "primary_objects_for_object_pose_variation": parse_primary_objects(
            row.get("subtasks"),
            row.get("contact_objects"),
        ),
    }


def count_axes(tasks: list[dict[str, Any]]) -> dict[str, int]:
    """Count multi-label axis coverage; one task can contribute to multiple axes."""
    counter: Counter[str] = Counter()
    for task in tasks:
        for axis in task.get("axes", []) or ["unknown_axis"]:
            counter[axis] += 1
    return dict(sorted(counter.items()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", default=METADATA_URL)
    parser.add_argument("--out", type=Path, default=Path("robolab_repro_artifacts/robolab120_task_matrix.json"))
    parser.add_argument("--allow-count-mismatch", action="store_true")
    args = parser.parse_args()

    metadata = load_metadata(args.metadata)
    tasks = [build_task_row(row, index=i) for i, row in enumerate(metadata)]
    missing_names = [i for i, task in enumerate(tasks) if not task.get("task_name")]
    if missing_names:
        raise SystemExit(f"Metadata rows without task_name: {missing_names[:10]}")

    if len(tasks) != 120 and not args.allow_count_mismatch:
        raise SystemExit(f"Expected 120 RoboLab tasks, got {len(tasks)} from {args.metadata}")

    difficulty_counts = Counter(str(task.get("difficulty_label") or "unknown") for task in tasks)
    attribute_counts = Counter(attr for task in tasks for attr in task.get("attributes", []))
    payload = {
        "metadata_url": args.metadata,
        "selection_rule": "All official RoboLab task_metadata rows, preserving metadata order.",
        "num_tasks": len(tasks),
        "axis_counts": count_axes(tasks),
        "difficulty_counts": dict(sorted(difficulty_counts.items())),
        "attribute_counts": dict(sorted(attribute_counts.items())),
        "execution_contract": {
            "per_task_required_artifacts": [
                "episode_results.jsonl",
                "run_*.hdf5",
                "*.mp4",
                "log_*_env*.json",
                "env_cfg.json",
            ],
            "recommended_4090_defaults": {
                "num_envs": 1,
                "num_runs_first_pass": 1,
                "video_mode": "all",
                "record_image_data": False,
            },
        },
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
                "difficulty_counts": payload["difficulty_counts"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
