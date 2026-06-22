#!/usr/bin/env python3
"""Validate RoboLab adapter contracts without launching Isaac Sim.

这个脚本只做 shape/schema/门禁验证，不跑真实 episode。它的目标是防止把
RoboChallenge/ReKep 的 probe 或 placeholder 误写成 RoboLab 成功率。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
STUB_DIR = ROOT / "robolab_repro_artifacts" / "adapter_stubs"
sys.path.insert(0, str(STUB_DIR))

from robochallenge_robolab_adapter import (  # noqa: E402
    RetargetRequired,
    build_robochallenge_observation,
    retarget_robochallenge_actions,
    validate_franka_robotiq_action_chunk,
    validate_robolab_observation,
)
from rekep_robolab_adapter import (  # noqa: E402
    PlannerBridgeRequired,
    build_rekep_stage_plan_schema,
    eef_path_to_franka_action_chunk,
    extract_keypoint_inputs,
    inspect_rekep_observation_requirements,
)


def fake_robolab_obs(*, with_rekep_perception: bool = False) -> dict[str, Any]:
    """构造一个最小 RoboLab observation，避免依赖 Isaac/RoboLab 运行时。"""
    obs: dict[str, Any] = {
        "image_obs": {
            "over_shoulder_left_camera": np.zeros((224, 224, 3), dtype=np.uint8),
            "over_shoulder_right_camera": np.zeros((224, 224, 3), dtype=np.uint8),
            "wrist_cam": np.zeros((224, 224, 3), dtype=np.uint8),
        },
        "proprio_obs": {
            "arm_joint_pos": np.zeros((7,), dtype=np.float32),
            "gripper_pos": np.zeros((1,), dtype=np.float32),
            "ee_pos": np.zeros((3,), dtype=np.float32),
            "ee_quat": np.array([0, 0, 0, 1], dtype=np.float32),
        },
    }
    if with_rekep_perception:
        obs["depth_obs"] = {"over_shoulder_left_camera": np.ones((224, 224), dtype=np.float32)}
        obs["segmentation_obs"] = {"object_masks": np.zeros((4, 224, 224), dtype=np.uint8)}
        obs["camera_obs"] = {
            "intrinsics": np.eye(3, dtype=np.float32),
            "extrinsics": np.eye(4, dtype=np.float32),
        }
    return obs


def record_case(rows: list[dict[str, Any]], name: str, fn) -> None:
    """运行一个验证用例，把 pass/fail 和详情写入 rows。"""
    try:
        detail = fn()
        rows.append({"case": name, "status": "pass", "detail": detail})
    except Exception as exc:  # noqa: BLE001 - validation report wants exact failure
        rows.append({"case": name, "status": "fail", "error_type": type(exc).__name__, "error": str(exc)})


def record_expected_block(rows: list[dict[str, Any]], name: str, expected_exception: type[Exception], fn) -> None:
    """运行预期应被门禁拦截的用例。拦截成功记为 blocked_expected。"""
    try:
        detail = fn()
        rows.append({"case": name, "status": "unexpected_pass", "detail": detail})
    except expected_exception as exc:
        rows.append({"case": name, "status": "blocked_expected", "error_type": type(exc).__name__, "error": str(exc)})
    except Exception as exc:  # noqa: BLE001
        rows.append({"case": name, "status": "unexpected_fail", "error_type": type(exc).__name__, "error": str(exc)})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    obs = fake_robolab_obs()
    obs_rich = fake_robolab_obs(with_rekep_perception=True)

    record_case(rows, "robolab_observation_minimal", lambda: validate_robolab_observation(obs))
    record_case(
        rows,
        "franka_robotiq_Nx8_direct_contract",
        lambda: validate_franka_robotiq_action_chunk(np.zeros((4, 8), dtype=np.float32), source="pi05_or_gr00t_style"),
    )

    for robot in ["aloha", "ur5", "arx5", "franka_compat_8d"]:
        record_case(
            rows,
            f"robochallenge_observation_bridge_{robot}",
            lambda robot=robot: build_robochallenge_observation(
                obs, "put the banana in the bowl", robot_type=robot
            ).to_jsonable(),
        )

    record_expected_block(
        rows,
        "robochallenge_aloha_14d_requires_retarget",
        RetargetRequired,
        lambda: retarget_robochallenge_actions(np.zeros((3, 14), dtype=np.float32), source_robot="aloha"),
    )
    record_expected_block(
        rows,
        "robochallenge_ur5_7d_requires_retarget",
        RetargetRequired,
        lambda: retarget_robochallenge_actions(np.zeros((3, 7), dtype=np.float32), source_robot="ur5"),
    )
    record_case(
        rows,
        "robochallenge_ur5_placeholder_shape_only",
        lambda: retarget_robochallenge_actions(
            np.zeros((3, 7), dtype=np.float32), source_robot="ur5", allow_placeholder=True
        ).to_jsonable(),
    )

    record_case(rows, "rekep_requirement_inspection_minimal", lambda: inspect_rekep_observation_requirements(obs))
    record_expected_block(
        rows,
        "rekep_missing_depth_seg_camera_requires_planner_bridge",
        PlannerBridgeRequired,
        lambda: extract_keypoint_inputs(obs, "put the banana in the bowl"),
    )
    record_case(
        rows,
        "rekep_rich_perception_bundle_still_not_scoreable",
        lambda: extract_keypoint_inputs(obs_rich, "put the banana in the bowl").to_jsonable(),
    )
    record_case(rows, "rekep_stage_plan_schema", lambda: build_rekep_stage_plan_schema("put the banana in the bowl"))
    record_expected_block(
        rows,
        "rekep_eef_path_requires_ik",
        PlannerBridgeRequired,
        lambda: eef_path_to_franka_action_chunk(np.zeros((2, 7), dtype=np.float32)),
    )
    record_case(
        rows,
        "rekep_eef_placeholder_shape_only",
        lambda: eef_path_to_franka_action_chunk(np.zeros((2, 7), dtype=np.float32), allow_placeholder=True).to_jsonable(),
    )

    summary = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "root": str(ROOT),
        "purpose": "adapter contract validation without Isaac Sim rollout",
        "hard_action_contract": {
            "shape": "[N,8]",
            "columns": [
                "panda_joint1",
                "panda_joint2",
                "panda_joint3",
                "panda_joint4",
                "panda_joint5",
                "panda_joint6",
                "panda_joint7",
                "robotiq_gripper",
            ],
        },
        "counts": {
            "pass": sum(1 for r in rows if r["status"] == "pass"),
            "blocked_expected": sum(1 for r in rows if r["status"] == "blocked_expected"),
            "unexpected": sum(1 for r in rows if r["status"].startswith("unexpected") or r["status"] == "fail"),
        },
        "cases": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "counts": summary["counts"]}, ensure_ascii=False))
    if summary["counts"]["unexpected"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
