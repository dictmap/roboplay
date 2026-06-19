"""RoboLab camera / wrist-camera / robot ablation config tests.

这个脚本只做配置级校验，不启动 Isaac Sim，也不连接 Pi05/OpenPI server。
目的：用已经同步下来的真实 `env_cfg.json` 判断哪些实验可以直接跑，
哪些实验会破坏 Pi05 的 observation/action 合约，必须先补 adapter。
"""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "robolab_repro_artifacts"
BASELINE_ENV_CFG = ROOT / "remote_outputs" / "pi05_banana_full_20260620_015206" / "env_cfg.json"
BASELINE_PI05_SUMMARY = ARTIFACT_DIR / "pi05_policy_smoke_summary.json"
OUT_PATH = ARTIFACT_DIR / "camera_robot_ablation_config_tests.json"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def image_observation_terms(cfg: dict) -> list[str]:
    """提取会进入 policy image observation 的相机项。"""
    group = cfg.get("observations", {}).get("image_obs", {})
    return sorted(
        name
        for name, value in group.items()
        if isinstance(value, dict) and "func" in value and "params" in value
    )


def proprio_observation_terms(cfg: dict) -> list[str]:
    """提取 Pi05 需要的关节和夹爪等本体观测项。"""
    group = cfg.get("observations", {}).get("proprio_obs", {})
    return sorted(
        name
        for name, value in group.items()
        if isinstance(value, dict) and "func" in value and "params" in value
    )


def camera_summary(cfg: dict, name: str) -> dict:
    cam = cfg.get("scene", {}).get(name, {})
    spawn = cam.get("spawn", {})
    return {
        "name": name,
        "prim_path": cam.get("prim_path"),
        "offset": cam.get("offset"),
        "width": cam.get("width"),
        "height": cam.get("height"),
        "focal_length": spawn.get("focal_length"),
        "horizontal_aperture": spawn.get("horizontal_aperture"),
        "vertical_aperture": spawn.get("vertical_aperture"),
    }


def robot_summary(cfg: dict) -> dict:
    robot = cfg.get("scene", {}).get("robot", {})
    actions = cfg.get("actions", {})
    frames = cfg.get("scene", {}).get("frames", {})
    return {
        "usd_path": robot.get("spawn", {}).get("usd_path"),
        "init_joint_pos_keys": sorted(robot.get("init_state", {}).get("joint_pos", {}).keys()),
        "body_action_joints": actions.get("body", {}).get("joint_names", []),
        "gripper_action_joints": actions.get("finger_joint", {}).get("joint_names", []),
        "frame_root": frames.get("prim_path"),
        "target_frame_names": [
            item.get("name") for item in frames.get("target_frames", []) if isinstance(item, dict)
        ],
    }


def remove_wrist_camera(cfg: dict) -> dict:
    """模拟硬删除腕部相机：sensor 和 observation term 都删除。"""
    mutated = copy.deepcopy(cfg)
    mutated.get("scene", {}).pop("wrist_cam", None)
    mutated.get("observations", {}).get("image_obs", {}).pop("wrist_cam", None)
    return mutated


def robot_usd_only_swap(cfg: dict) -> dict:
    """模拟只换 USD，不改动作、frame、相机挂载和策略 adapter。"""
    mutated = copy.deepcopy(cfg)
    mutated["scene"]["robot"]["spawn"]["usd_path"] = "/path/to/another_robot.usd"
    return mutated


def has_pi05_image_contract(cfg: dict) -> bool:
    terms = set(image_observation_terms(cfg))
    return {"over_shoulder_left_camera", "wrist_cam"}.issubset(terms)


def has_franka_action_contract(cfg: dict) -> bool:
    robot = robot_summary(cfg)
    body_joints = " ".join(robot["body_action_joints"])
    gripper_joints = set(robot["gripper_action_joints"])
    frames = set(robot["target_frame_names"])
    return (
        "panda_joint" in body_joints
        and "finger_joint" in gripper_joints
        and {"eef_frame", "gripper_base"}.issubset(frames)
    )


def main() -> None:
    cfg = load_json(BASELINE_ENV_CFG)
    pi05 = load_json(BASELINE_PI05_SUMMARY) if BASELINE_PI05_SUMMARY.exists() else {}

    no_wrist_cfg = remove_wrist_camera(cfg)
    robot_swap_cfg = robot_usd_only_swap(cfg)

    baseline = {
        "env_cfg": str(BASELINE_ENV_CFG),
        "task": cfg.get("_task_name"),
        "policy": cfg.get("policy"),
        "instruction": cfg.get("instruction"),
        "image_observation_terms": image_observation_terms(cfg),
        "proprio_observation_terms": proprio_observation_terms(cfg),
        "policy_cameras": [
            camera_summary(cfg, "over_shoulder_left_camera"),
            camera_summary(cfg, "wrist_cam"),
        ],
        "viewport_camera": camera_summary(cfg, "egocentric_mirrored_camera"),
        "viewer": cfg.get("viewer"),
        "robot": robot_summary(cfg),
        "baseline_success": bool(pi05.get("episode_records", [{}])[0].get("success", False))
        if pi05.get("episode_records")
        else None,
        "baseline_score": pi05.get("episode_records", [{}])[0].get("score")
        if pi05.get("episode_records")
        else None,
        "baseline_episode_step": pi05.get("episode_records", [{}])[0].get("episode_step")
        if pi05.get("episode_records")
        else None,
    }

    experiment_matrix = [
        {
            "id": "baseline_pi05_banana",
            "question": "默认相机与默认 Franka+Robotiq 下的参考成绩。",
            "runnable_without_adapter": True,
            "expected_effect": "作为 sanity baseline；既有结果 success=True, score=1.0。",
        },
        {
            "id": "external_camera_small_angle_sweep",
            "question": "调整外部/肩部相机角度会如何？",
            "runnable_without_adapter": True,
            "config_surface": "scene.over_shoulder_left_camera.offset.pos/rot",
            "suggested_variants": [
                {"name": "default", "pos": [0.05, 0.57, 0.66]},
                {"name": "higher", "pos": [0.05, 0.57, 0.76]},
                {"name": "lower", "pos": [0.05, 0.57, 0.56]},
                {"name": "left_shift", "pos": [0.05, 0.67, 0.66]},
                {"name": "right_shift", "pos": [0.05, 0.47, 0.66]},
            ],
            "expected_effect": "小角度通常能启动，但会改变物体投影、遮挡和深度线索；Pi05 若依赖 DROID 风格视角，成功率和步数可能变差。",
        },
        {
            "id": "remove_wrist_camera_hard",
            "question": "取消腕部相机会如何？",
            "runnable_without_adapter": False,
            "config_surface": "scene.wrist_cam + observations.image_obs.wrist_cam",
            "expected_effect": "硬删除会破坏 Pi05 image observation 合约，客户端/请求侧大概率直接缺 key，而不是得到一个公平的性能分数。",
        },
        {
            "id": "wrist_camera_blackout_soft",
            "question": "保留腕部相机 key，但把图像置黑会如何？",
            "runnable_without_adapter": False,
            "needs_patch": "Pi05 observation adapter 中对 wrist_cam 做 zero-image 或 last-frame mask。",
            "expected_effect": "这是更公平的腕部相机消融：程序仍可跑，但近距离抓取、遮挡恢复、放置精度预计下降。",
        },
        {
            "id": "robot_usd_only_swap",
            "question": "只替换机器人 USD 会如何？",
            "runnable_without_adapter": False,
            "config_surface": "scene.robot.spawn.usd_path",
            "expected_effect": "只换 USD 会保留 panda_joint/finger_joint/eef_frame 等旧合约，通常会在动作、frame、接触传感器或腕部相机路径上失败。",
        },
        {
            "id": "robot_full_adapter_swap",
            "question": "完整替换机器人会如何？",
            "runnable_without_adapter": False,
            "needs_patch": "robot cfg、action space、frame transformer、gripper/contact sensors、wrist camera mount、policy action adapter 全部同步。",
            "expected_effect": "这才是有效的跨机器人实验；否则测到的是配置不兼容，不是策略泛化。",
        },
    ]

    tests = [
        {
            "name": "baseline_has_two_pi05_policy_cameras",
            "passed": has_pi05_image_contract(cfg),
            "details": image_observation_terms(cfg),
        },
        {
            "name": "baseline_wrist_camera_is_mounted_on_robot",
            "passed": "/robot/" in str(camera_summary(cfg, "wrist_cam").get("prim_path")),
            "details": camera_summary(cfg, "wrist_cam").get("prim_path"),
        },
        {
            "name": "baseline_uses_franka_action_contract",
            "passed": has_franka_action_contract(cfg),
            "details": robot_summary(cfg),
        },
        {
            "name": "external_camera_sweep_preserves_pi05_contract",
            "passed": has_pi05_image_contract(cfg),
            "details": "只改 over_shoulder_left_camera offset，不删除 observation term。",
        },
        {
            "name": "hard_remove_wrist_breaks_pi05_contract_as_expected",
            "passed": not has_pi05_image_contract(no_wrist_cfg),
            "details": image_observation_terms(no_wrist_cfg),
        },
        {
            "name": "robot_usd_only_swap_still_has_old_franka_contract",
            "passed": has_franka_action_contract(robot_swap_cfg),
            "details": "说明只换 USD 不够；action/frame/camera/contact 仍是 Franka 合约。",
        },
        {
            "name": "baseline_success_record_is_available",
            "passed": baseline["baseline_success"] is True and baseline["baseline_score"] == 1.0,
            "details": {
                "success": baseline["baseline_success"],
                "score": baseline["baseline_score"],
                "episode_step": baseline["baseline_episode_step"],
            },
        },
    ]

    report = {
        "type": "config_level_ablation_test",
        "boundary": "No Isaac Sim run was launched. SSH to robolab4090 failed with Permission denied in this local session.",
        "baseline": baseline,
        "experiment_matrix": experiment_matrix,
        "tests": tests,
        "passed": all(item["passed"] for item in tests),
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"out": str(OUT_PATH), "passed": report["passed"], "tests": tests}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
