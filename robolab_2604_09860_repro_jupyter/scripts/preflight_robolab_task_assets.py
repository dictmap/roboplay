"""Static asset preflight for RoboLab task matrices.

This script checks whether scene USD files and their referenced assets exist on
disk. It intentionally does not import Isaac Sim or USD Python bindings, so it
can run quickly before expensive policy rollouts.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ASSET_REF_RE = re.compile(r"@([^@\n\r]+)@")
ASSET_EXTENSIONS = {
    ".usd",
    ".usda",
    ".usdc",
    ".mdl",
    ".png",
    ".jpg",
    ".jpeg",
    ".exr",
    ".hdr",
    ".tif",
    ".tiff",
    ".obj",
    ".mtl",
}


def load_matrix(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("tasks", []))


def looks_like_file_ref(ref: str) -> bool:
    """过滤掉非文件 asset path，避免把变量或内嵌标识误当缺失文件。"""
    clean = ref.split("?", 1)[0].split("#", 1)[0]
    return Path(clean).suffix.lower() in ASSET_EXTENSIONS


def resolve_ref(ref: str, owner: Path, robo_root: Path) -> Path:
    """把 USD 中的 asset 引用解析到当前机器上的候选路径。"""
    clean = ref.split("?", 1)[0].split("#", 1)[0]
    clean = clean.replace("\\", "/")
    if clean.startswith("file:"):
        clean = clean.replace("file://", "").replace("file:", "")

    path = Path(clean)
    if path.is_absolute():
        return path

    candidates = [
        (owner.parent / clean).resolve(),
        (robo_root / clean).resolve(),
        (robo_root / "assets" / clean).resolve(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def scan_file(path: Path, robo_root: Path, visited: set[Path], max_depth: int, depth: int = 0) -> dict[str, Any]:
    """递归扫描 USD/MDL/材质文件里的 @asset@ 引用并检查存在性。"""
    path = path.resolve()
    if path in visited:
        return {"refs": 0, "missing": []}
    visited.add(path)

    if not path.exists():
        return {"refs": 0, "missing": [{"owner": str(path), "ref": str(path), "resolved": str(path), "reason": "owner_missing"}]}

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return {"refs": 0, "missing": [{"owner": str(path), "ref": str(path), "resolved": str(path), "reason": f"read_error:{exc}"}]}

    refs = 0
    missing: list[dict[str, str]] = []
    for match in ASSET_REF_RE.finditer(text):
        ref = match.group(1).strip()
        if not looks_like_file_ref(ref):
            continue
        refs += 1
        resolved = resolve_ref(ref, path, robo_root)
        if not resolved.exists():
            missing.append({"owner": str(path), "ref": ref, "resolved": str(resolved), "reason": "missing_ref"})
            continue
        if depth < max_depth and resolved.suffix.lower() in {".usd", ".usda", ".usdc", ".mdl"}:
            child = scan_file(resolved, robo_root=robo_root, visited=visited, max_depth=max_depth, depth=depth + 1)
            refs += int(child["refs"])
            missing.extend(child["missing"])
    return {"refs": refs, "missing": missing}


def preflight_task(task: dict[str, Any], robo_root: Path, max_depth: int, max_examples: int) -> dict[str, Any]:
    scene_name = task.get("scene")
    scene_path = (robo_root / "assets" / "scenes" / str(scene_name)).resolve()
    visited: set[Path] = set()
    scan = scan_file(scene_path, robo_root=robo_root, visited=visited, max_depth=max_depth)
    missing = scan["missing"]
    return {
        "task_name": task.get("task_name"),
        "scene": scene_name,
        "scene_path": str(scene_path),
        "axes": task.get("axes", []),
        "attributes": task.get("attributes", []),
        "difficulty_label": task.get("difficulty_label"),
        "num_subtasks": task.get("num_subtasks"),
        "contact_objects": task.get("contact_objects", []),
        "scene_exists": scene_path.exists(),
        "refs_checked": scan["refs"],
        "missing_ref_count": len(missing),
        "missing_ref_examples": missing[:max_examples],
        "visited_file_count": len(visited),
        "asset_preflight_passed": scene_path.exists() and len(missing) == 0,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    axis_ready: Counter[str] = Counter()
    axis_total: Counter[str] = Counter()
    difficulty_ready: Counter[str] = Counter()
    difficulty_total: Counter[str] = Counter()
    for row in rows:
        axes = row.get("axes") or ["unknown_axis"]
        for axis in axes:
            axis_total[str(axis)] += 1
            if row["asset_preflight_passed"]:
                axis_ready[str(axis)] += 1
        difficulty = str(row.get("difficulty_label") or "unknown")
        difficulty_total[difficulty] += 1
        if row["asset_preflight_passed"]:
            difficulty_ready[difficulty] += 1
    return {
        "total_tasks": len(rows),
        "asset_ready_tasks": sum(1 for row in rows if row["asset_preflight_passed"]),
        "scene_missing_tasks": sum(1 for row in rows if not row["scene_exists"]),
        "tasks_with_missing_refs": sum(1 for row in rows if row["missing_ref_count"] > 0),
        "axis_total": dict(sorted(axis_total.items())),
        "axis_ready": dict(sorted(axis_ready.items())),
        "difficulty_total": dict(sorted(difficulty_total.items())),
        "difficulty_ready": dict(sorted(difficulty_ready.items())),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "task_name",
        "scene",
        "asset_preflight_passed",
        "scene_exists",
        "refs_checked",
        "missing_ref_count",
        "visited_file_count",
        "difficulty_label",
        "axes",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "task_name": row["task_name"],
                    "scene": row["scene"],
                    "asset_preflight_passed": row["asset_preflight_passed"],
                    "scene_exists": row["scene_exists"],
                    "refs_checked": row["refs_checked"],
                    "missing_ref_count": row["missing_ref_count"],
                    "visited_file_count": row["visited_file_count"],
                    "difficulty_label": row["difficulty_label"],
                    "axes": ",".join(row.get("axes") or []),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--robo-root", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, default=None)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--max-examples", type=int, default=8)
    args = parser.parse_args()

    tasks = load_matrix(args.matrix)
    rows = [
        preflight_task(task, robo_root=args.robo_root.resolve(), max_depth=args.max_depth, max_examples=args.max_examples)
        for task in tasks
    ]
    payload = {
        "matrix": str(args.matrix),
        "robo_root": str(args.robo_root),
        "max_depth": args.max_depth,
        "summary": summarize(rows),
        "tasks": rows,
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.out_csv:
        args.out_csv.parent.mkdir(parents=True, exist_ok=True)
        write_csv(args.out_csv, rows)
    print(
        json.dumps(
            {
                "out_json": str(args.out_json),
                "out_csv": str(args.out_csv) if args.out_csv else None,
                "summary": payload["summary"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
