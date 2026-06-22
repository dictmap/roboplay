"""ReKep -> RoboLab planner adapter contract helpers.

ReKep 的合理定位是 planner baseline，而不是 Pi05/GR00T 这类每步输出动作的
VLA policy。它通常输出 keypoint、约束、子目标和末端轨迹；RoboLab 评分侧最终
仍然需要 Franka+Robotiq joint-position action chunk：``[N,8]``。

本文件把 ReKep 接 RoboLab 的缺口显式化：

1. perception bridge：RoboLab 必须提供 RGB、深度/点云、分割或对象 mask、相机内外参。
2. planner bridge：ReKep 生成 keypoint constraints、subgoal/path。
3. controller bridge：把末端位姿路径交给 IK/motion planner，转换为 `[N,8]`。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np


FRANKA_ROBOTIQ_ACTION_COLUMNS = (
    "panda_joint1",
    "panda_joint2",
    "panda_joint3",
    "panda_joint4",
    "panda_joint5",
    "panda_joint6",
    "panda_joint7",
    "robotiq_gripper",
)


class PlannerBridgeRequired(RuntimeError):
    """ReKep planner 尚缺 perception/IK/controller 桥。"""


class ReKepObservationError(RuntimeError):
    """RoboLab observation 不满足 ReKep planner 输入要求。"""


@dataclass
class ReKepAdapterConfig:
    """ReKep 侧 adapter 配置。"""

    rekep_root: str
    vlm_endpoint: str | None = None
    device: str = "cuda:0"
    controller: str = "franka_robotiq_low_level_controller"
    require_depth: bool = True
    require_segmentation: bool = True


@dataclass
class PlannerBridgeReport:
    """ReKep planner bridge 的机器可读报告。"""

    payload: dict[str, Any]
    scoreable: bool
    missing: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        """把数组替换为 shape/dtype，避免 JSON 里塞大图像。"""

        def summarize(value: Any) -> Any:
            if isinstance(value, np.ndarray):
                return {"shape": list(value.shape), "dtype": str(value.dtype)}
            if isinstance(value, dict):
                return {k: summarize(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [summarize(v) for v in value]
            return value

        return {
            "scoreable": self.scoreable,
            "missing": self.missing,
            "required_next_steps": self.required_next_steps,
            "payload": summarize(self.payload),
        }


def _group(obs: dict[str, Any], *names: str) -> dict[str, Any]:
    """从 observation 中按多个可能名字取 group。"""
    for name in names:
        value = obs.get(name)
        if isinstance(value, dict):
            return value
    return {}


def inspect_rekep_observation_requirements(robolab_obs: dict[str, Any]) -> dict[str, Any]:
    """检查 ReKep 所需的 perception 输入是否齐全。

    输入：RoboLab observation。
    输出：每类输入是否存在、shape 信息和缺失项。
    """
    if not isinstance(robolab_obs, dict):
        raise ReKepObservationError("RoboLab observation must be a dict")

    images = _group(robolab_obs, "image_obs", "images")
    depth = _group(robolab_obs, "depth_obs", "depth", "depth_images")
    seg = _group(robolab_obs, "segmentation_obs", "segmentation", "masks", "object_masks")
    camera = _group(robolab_obs, "camera_obs", "camera", "camera_info")

    def shape_map(group: dict[str, Any]) -> dict[str, Any]:
        out = {}
        for key, value in group.items():
            arr = np.asarray(value)
            out[key] = {"shape": list(arr.shape), "dtype": str(arr.dtype)}
        return out

    report = {
        "rgb": shape_map(images),
        "depth": shape_map(depth),
        "segmentation": shape_map(seg),
        "camera": shape_map(camera),
        "missing": [],
    }
    if not images:
        report["missing"].append("rgb_images")
    if not depth:
        report["missing"].append("depth_or_pointcloud")
    if not seg:
        report["missing"].append("segmentation_or_object_masks")
    if not camera:
        report["missing"].append("camera_intrinsics_extrinsics")
    return report


def extract_keypoint_inputs(
    robolab_obs: dict[str, Any],
    instruction: str,
    *,
    require_depth: bool = True,
    require_segmentation: bool = True,
) -> PlannerBridgeReport:
    """为 ReKep keypoint proposal 准备输入包。

    这一步不调用 VLM，只检查 RoboLab 是否能提供 ReKep 需要的 RGB-D/seg/camera 数据。
    """
    report = inspect_rekep_observation_requirements(robolab_obs)
    missing = list(report["missing"])
    if not require_depth:
        missing = [m for m in missing if m != "depth_or_pointcloud"]
    if not require_segmentation:
        missing = [m for m in missing if m != "segmentation_or_object_masks"]

    if missing:
        raise PlannerBridgeRequired("ReKep needs perception bridge before scoring; missing: " + ", ".join(missing))

    return PlannerBridgeReport(
        payload={"instruction": instruction, "perception_report": report},
        scoreable=False,
        required_next_steps=[
            "run keypoint proposal on RGB-D and masks",
            "bind 2D keypoints to 3D RoboLab/Isaac coordinates",
            "generate and solve ReKep constraints",
            "convert end-effector path to Franka+Robotiq [N,8] through IK/motion planner",
        ],
    )


def build_rekep_stage_plan_schema(instruction: str) -> dict[str, Any]:
    """给 ReKep planner baseline 定义统一的中间产物 schema。"""
    return {
        "instruction": instruction,
        "expected_intermediates": [
            "rgbd_observation_bundle",
            "object_masks_or_semantic_ids",
            "2d_keypoints",
            "3d_keypoints_in_world",
            "language_conditioned_constraints",
            "subgoal_sequence",
            "end_effector_pose_path",
            "franka_robotiq_action_chunk_Nx8",
        ],
        "success_metric": "same RoboLab episode_results.jsonl/subtask predicates as VLA policies",
        "method_type": "planner_baseline_not_step_policy",
    }


def eef_path_to_franka_action_chunk(
    eef_poses: Any,
    *,
    ik_solver: Callable[[np.ndarray], Any] | None = None,
    gripper: Any | None = None,
    allow_placeholder: bool = False,
) -> PlannerBridgeReport:
    """把 ReKep 末端位姿路径转换成 RoboLab `[N,8]` 动作 chunk。

    ``eef_poses`` 约定为 `[N, 7]`：XYZ + quaternion(xyzw)。没有 IK solver 时默认抛错。
    ``allow_placeholder=True`` 只用于 smoke，不可进入成功率统计。
    """
    poses = np.asarray(eef_poses, dtype=np.float32)
    if poses.ndim == 1:
        poses = poses.reshape(1, -1)
    if poses.ndim != 2 or poses.shape[1] != 7:
        raise PlannerBridgeRequired(f"eef_poses must be [N,7] XYZ+quat, got {poses.shape}")

    if ik_solver is None:
        if not allow_placeholder:
            raise PlannerBridgeRequired("ReKep eef path needs a Franka IK/motion-planner bridge before scoring.")
        actions = np.zeros((poses.shape[0], 8), dtype=np.float32)
        if gripper is not None:
            grip = np.asarray(gripper, dtype=np.float32).reshape(-1)
            if grip.size == 1:
                actions[:, 7] = grip[0]
            elif grip.size == poses.shape[0]:
                actions[:, 7] = grip
            else:
                raise PlannerBridgeRequired("gripper must be scalar or length N")
        return PlannerBridgeReport(
            payload={"action_chunk": actions, "contract": list(FRANKA_ROBOTIQ_ACTION_COLUMNS)},
            scoreable=False,
            missing=["franka_ik_motion_planner"],
            required_next_steps=["replace placeholder with IK/RMPFlow/cuRobo-generated joint positions"],
        )

    chunks = []
    for pose in poses:
        joints = np.asarray(ik_solver(pose), dtype=np.float32).reshape(-1)
        if joints.shape[0] != 7:
            raise PlannerBridgeRequired(f"IK solver must return 7 Franka joints, got {joints.shape}")
        chunks.append(joints)
    actions = np.zeros((poses.shape[0], 8), dtype=np.float32)
    actions[:, :7] = np.vstack(chunks)
    if gripper is not None:
        grip = np.asarray(gripper, dtype=np.float32).reshape(-1)
        actions[:, 7] = grip[0] if grip.size == 1 else grip
    return PlannerBridgeReport(
        payload={"action_chunk": actions, "contract": list(FRANKA_ROBOTIQ_ACTION_COLUMNS)},
        scoreable=True,
    )


class ReKepRoboLabAdapter:
    """把 ReKep planner 接入 RoboLab 的 fail-fast 封装。"""

    def __init__(self, config: ReKepAdapterConfig) -> None:
        self.config = config

    def extract_keypoints(self, robolab_obs: dict[str, Any], instruction: str) -> PlannerBridgeReport:
        """检查并准备 ReKep keypoint 输入。"""
        return extract_keypoint_inputs(
            robolab_obs,
            instruction,
            require_depth=self.config.require_depth,
            require_segmentation=self.config.require_segmentation,
        )

    def plan_subgoals(self, keypoints: list[dict[str, Any]], instruction: str) -> list[dict[str, Any]]:
        """调用 ReKep 约束生成和优化，得到子目标序列。"""
        raise PlannerBridgeRequired("ReKep constraint planning is not connected to RoboLab yet.")

    def execute_subgoals(self, subgoals: list[dict[str, Any]], robolab_env: Any) -> dict[str, Any]:
        """把 ReKep 子目标交给 RoboLab/Isaac 中的低层控制器执行。"""
        raise PlannerBridgeRequired("RoboLab low-level execution bridge is not implemented yet.")
