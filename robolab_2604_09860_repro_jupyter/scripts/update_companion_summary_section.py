"""Append an idempotent final summary section to RoboLab companion docs."""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path


START = "<!-- ROBOPLAY_COMPANION_FINAL_SUMMARY_START -->"
END = "<!-- ROBOPLAY_COMPANION_FINAL_SUMMARY_END -->"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def count_outputs(root: Path) -> dict[str, int]:
    return {
        "hdf5": len(glob.glob(str(root / "**" / "*.hdf5"), recursive=True)),
        "mp4": len(glob.glob(str(root / "**" / "*.mp4"), recursive=True)),
        "subtask_logs": len(glob.glob(str(root / "**" / "log_0_env0.json"), recursive=True)),
    }


def strip_existing(text: str) -> str:
    if START in text and END in text:
        before = text.split(START, 1)[0].rstrip()
        after = text.split(END, 1)[1].lstrip()
        return (before + "\n\n" + after).strip() + "\n"
    return text.rstrip() + "\n"


def csv_path(artifact_dir: Path, prefix: str, suffix: str) -> Path:
    return artifact_dir / f"{prefix}_{suffix}.csv"


def build_section(base: Path) -> str:
    artifact_dir = base / "robolab_repro_artifacts"
    qid = (artifact_dir / "current_companion_queue_id.txt").read_text(encoding="utf-8").strip()
    output_base = Path("/home/yjl/codex_robolab_4090_20260619/RoboLab/output")

    full_prefix = "robolab120_pi05_full_assetsfixed_20260620_170411_read_results"
    baseline_prefix = f"{qid}_pi05_baseline_read_results"
    camera_prefix = f"{qid}_camera_angle_read_results"
    wrist_prefix = f"{qid}_wrist_blackout_read_results"
    robot_prefix = f"{qid}_robot_base_shift_read_results"
    combined_prefix = f"{qid}_combined120_read_results"

    summaries = {
        "Pi05 RoboLab-120": read_json(artifact_dir / f"{full_prefix}_summary.json"),
        "Pi05 20-task baseline": read_json(artifact_dir / f"{baseline_prefix}_summary.json"),
        "Camera angle variants": read_json(artifact_dir / f"{camera_prefix}_summary.json"),
        "Wrist camera blackout": read_json(artifact_dir / f"{wrist_prefix}_summary.json"),
        "Robot base shift": read_json(artifact_dir / f"{robot_prefix}_summary.json"),
        "Companion combined": read_json(artifact_dir / f"{combined_prefix}_summary.json"),
    }

    roots = {
        "Pi05 20-task baseline": None,
        "Camera angle variants": output_base / f"{qid}_camera_angle_camera_pose_variation",
        "Wrist camera blackout": output_base / f"{qid}_wrist_blackout_wrist_blackout",
        "Robot base shift": output_base / f"{qid}_robot_base_shift",
    }

    robot_ep = output_base / f"{qid}_robot_base_shift" / "episode_results.jsonl"
    robot_rows = []
    if robot_ep.exists():
        for line in robot_ep.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip():
                robot_rows.append(json.loads(line))

    rows = []
    prefix_map = {
        "Pi05 RoboLab-120": full_prefix,
        "Pi05 20-task baseline": baseline_prefix,
        "Camera angle variants": camera_prefix,
        "Wrist camera blackout": wrist_prefix,
        "Robot base shift": robot_prefix,
        "Companion combined": combined_prefix,
    }
    for name, summary in summaries.items():
        episodes = summary.get("episode_rows", 0)
        successes = summary.get("successes", 0)
        rate = summary.get("success_rate")
        rate_text = f"{rate:.1%}" if isinstance(rate, (int, float)) else "n/a"
        counts = count_outputs(roots[name]) if roots.get(name) else {"hdf5": "-", "mp4": "-", "subtask_logs": "-"}
        prefix = prefix_map[name]
        rows.append(
            "| "
            + " | ".join(
                [
                    name,
                    str(episodes),
                    str(successes),
                    rate_text,
                    str(counts["hdf5"]),
                    str(counts["mp4"]),
                    str(counts["subtask_logs"]),
                    f"`{artifact_dir / (prefix + '_summary.json')}`",
                ]
            )
            + " |"
        )

    robot_task_lines = []
    for row in robot_rows:
        robot_task_lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("task_name")),
                    "success" if row.get("success") else "fail",
                    str(row.get("episode_step")),
                    str(row.get("reason", "")).replace("|", "/")[:120],
                ]
            )
            + " |"
        )

    return f"""
{START}

## 2026-06-21 22:05 - 最终核验与重试补录

> 重要说明：上方日志里 `05_wrist_blackout_20` 和 `06_robot_base_shift_20` 的 `failed_or_blocked`
> 是第一次尝试的失败记录。后续已完成 retry：`05_wrist_blackout_20_retry` 与
> `06_robot_base_shift_20_retry2`，下面表格是以最终 retry 产物为准的核验结果。

### 总结果

| 实验 | episode rows | successes | success rate | HDF5 | MP4 | subtask logs | summary |
|---|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(rows)}

### 分组统计表

- 120 任务：`{csv_path(artifact_dir, full_prefix, 'by_axis')}`，`{csv_path(artifact_dir, full_prefix, 'by_difficulty')}`，`{csv_path(artifact_dir, full_prefix, 'by_task_length')}`
- Pi05 20 基线：`{csv_path(artifact_dir, baseline_prefix, 'by_axis')}`，`{csv_path(artifact_dir, baseline_prefix, 'by_difficulty')}`，`{csv_path(artifact_dir, baseline_prefix, 'by_task_length')}`
- 相机角度：`{csv_path(artifact_dir, camera_prefix, 'by_axis')}`，`{csv_path(artifact_dir, camera_prefix, 'by_difficulty')}`，`{csv_path(artifact_dir, camera_prefix, 'by_task_length')}`
- 取消腕部相机：`{csv_path(artifact_dir, wrist_prefix, 'by_axis')}`，`{csv_path(artifact_dir, wrist_prefix, 'by_difficulty')}`，`{csv_path(artifact_dir, wrist_prefix, 'by_task_length')}`
- 机器人基座偏移：`{csv_path(artifact_dir, robot_prefix, 'by_axis')}`，`{csv_path(artifact_dir, robot_prefix, 'by_difficulty')}`，`{csv_path(artifact_dir, robot_prefix, 'by_task_length')}`

### 机器人基座偏移 20 任务逐条记录

| task | result | steps | reason |
|---|---|---:|---|
{chr(10).join(robot_task_lines)}

### 当前边界

- RoboChallenge pi、ReKep、GR00T、PaliGemma、Cosmos、阿里/Qwen 目前已有 probe/adapter-required 记录，但还不是 RoboLab action-policy 真实 20 任务 rollout。
- 真实对照需要补齐 `observation -> action` 适配器：接收 RoboLab 多相机观测和语言指令，输出 Franka/Robotiq 控制动作，并接入同一套 `episode_results.jsonl + HDF5 + video + subtask log` 记录链路。
- 以上边界已写入 `robolab_repro_artifacts/{qid}_other_models_probe_summary.json`，后续不能把 probe 结果当成功率对比。

{END}
""".strip()


def update_doc(path: Path, section: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else f"# {path.stem}\n"
    path.write_text(strip_existing(text) + "\n" + section + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    args = parser.parse_args()
    section = build_section(args.base)
    for name in ["COMPANION_QUEUE_LIVE_PROGRESS.md", "EXPERIMENT_21_companion_experiment_queue.md"]:
        update_doc(args.base / name, section)
    print(json.dumps({"updated": ["COMPANION_QUEUE_LIVE_PROGRESS.md", "EXPERIMENT_21_companion_experiment_queue.md"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
