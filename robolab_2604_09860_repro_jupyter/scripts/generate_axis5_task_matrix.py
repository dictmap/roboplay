"""Generate the Pi05 ability-axis task matrix from official RoboLab metadata."""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from collections import defaultdict
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

SELECTED_TASKS = [
    # Visual axis: color / semantics / size.
    "BananaInBowlTask",
    "BBQSauceInBinTask",
    "BigPumpkinInBinTask",
    "CannedFoodInBinTask",
    "RedItemsInBinTask",
    # Procedural axis: stacking / sorting / reorientation / affordance.
    "Stack3RubiksCubeTask",
    "ReorientAllMugsTask",
    "AppleAndYogurtInBowlTask",
    "BlocksInBinTask",
    "BlackItemsInBinTask",
    # Relational axis: spatial / conjunction / counting.
    "RubiksCubeLeftOfBowlTask",
    "BowlStackingLeftOnRightTask",
    "BananaThenRubiksCubeTask",
    "BananasInCrateTask",
    "ClampInRightBinTask",
    # Extra relational backup if one task hits an asset/contact issue.
    "ButterAboveRaisinTask",
]

KNOWN_EXCLUDED = {
    "BlockStackingSpecifiedOrderTask": "Earlier local/remote attempt hit contact reporter asset initialization failure.",
}


def load_metadata(path_or_url: str) -> list[dict[str, Any]]:
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        with urllib.request.urlopen(path_or_url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    return json.loads(Path(path_or_url).read_text(encoding="utf-8"))


def split_attributes(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def axes_for_attributes(attrs: list[str]) -> list[str]:
    return sorted({ATTRIBUTE_TO_AXIS[attr] for attr in attrs if attr in ATTRIBUTE_TO_AXIS})


def parse_primary_objects(subtasks: str | None, contact_objects: str | None) -> list[str]:
    contact_names = [
        item.strip() for item in (contact_objects or "").split(",") if item.strip()
    ]
    contact_set = set(contact_names)
    objects: list[str] = []
    for group in re.findall(r"groups=\[([^\]]+)\]", subtasks or ""):
        for item in re.findall(r"'([^']+)'", group):
            if item != "conditions" and item in contact_set and item not in objects:
                objects.append(item)
    if objects:
        return objects

    objects = []
    fallback_skip = {"table", "grey_bin", "left_bin", "right_bin", "bin", "crate", "bowl"}
    for name in contact_names:
        if name and name not in fallback_skip and name not in objects:
            objects.append(name)
    return objects[:3]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", default=METADATA_URL)
    parser.add_argument("--out", type=Path, default=Path("robolab_repro_artifacts/pi05_axis5_task_matrix.json"))
    args = parser.parse_args()

    metadata = load_metadata(args.metadata)
    by_name = {row["task_name"]: row for row in metadata}

    missing = [task for task in SELECTED_TASKS if task not in by_name]
    if missing:
        raise SystemExit(f"Missing tasks in metadata: {missing}")

    tasks = []
    axis_counts: dict[str, int] = defaultdict(int)
    for task_name in SELECTED_TASKS:
        row = by_name[task_name]
        attrs = split_attributes(row.get("attributes"))
        axes = axes_for_attributes(attrs)
        for axis in axes:
            axis_counts[axis] += 1
        tasks.append(
            {
                "task_name": task_name,
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
                "contact_objects": [item.strip() for item in (row.get("contact_objects") or "").split(",") if item.strip()],
                "primary_objects_for_object_pose_variation": parse_primary_objects(
                    row.get("subtasks"), row.get("contact_objects")
                ),
            }
        )

    required_axes = {"visual", "procedural", "relational"}
    failures = [axis for axis in required_axes if axis_counts.get(axis, 0) < 5]
    if failures:
        raise SystemExit(f"Axis coverage too small: {dict(axis_counts)}")

    payload = {
        "metadata_url": args.metadata,
        "policy": "pi05",
        "selection_rule": "At least 5 tasks per ability axis; avoid known contact-reporter failure task in first main matrix.",
        "axis_counts": dict(sorted(axis_counts.items())),
        "known_excluded": KNOWN_EXCLUDED,
        "tasks": tasks,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "axis_counts": payload["axis_counts"], "num_tasks": len(tasks)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
