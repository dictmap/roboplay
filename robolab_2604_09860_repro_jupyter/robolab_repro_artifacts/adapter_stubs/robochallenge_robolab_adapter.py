"""RoboChallenge pi -> RoboLab policy adapter contract helpers.

这个文件不是可直接得分的 RoboLab policy server。它的作用是把 RoboChallenge
与 RoboLab 之间最容易被混淆的接口差异写成可执行检查：

1. RoboLab 评分侧硬接口是 Franka+Robotiq joint-position action chunk：
   ``[N, 8] = 7 个 Franka 关节目标 + 1 个夹爪目标``。
2. RoboChallenge 公开推理工程按机器人分 schema：ALOHA/W1 常见是双臂
   ``14D``，UR5/ARX5 常见是单臂 ``7D = 6 joints + gripper``。
3. 这些 schema 可以做 observation key 映射，但不能只靠改名字就变成
   Franka+Robotiq 的可评分动作。真正评分前必须 retarget 或重训 action head。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

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

ROBOLAB_IMAGE_KEYS = (
    "over_shoulder_left_camera",
    "over_shoulder_right_camera",
    "wrist_cam",
)

ROBOCHALLENGE_ROBOT_SPECS: dict[str, dict[str, Any]] = {
    "aloha": {
        "images": ("cam_high", "cam_left_wrist", "cam_right_wrist"),
        "state_dim": 14,
        "action_dim": 14,
        "meaning": "dual-arm joint action",
        "direct_scoreable": False,
    },
    "dosw": {
        "images": ("cam_high", "cam_left_wrist", "cam_right_wrist"),
        "state_dim": 14,
        "action_dim": 14,
        "meaning": "dual-arm action with RoboChallenge-specific offsets",
        "direct_scoreable": False,
    },
    "ur5": {
        "images": ("cam_global", "cam_arm"),
        "state_dim": 7,
        "action_dim": 7,
        "meaning": "single-arm [6 joints + gripper]",
        "direct_scoreable": False,
    },
    "arx5": {
        "images": ("cam_global", "cam_arm", "cam_side"),
        "state_dim": 7,
        "action_dim": 7,
        "meaning": "single-arm [6 joints + gripper]",
        "direct_scoreable": False,
    },
    "franka_compat_8d": {
        "images": ("cam_global", "cam_arm", "cam_side"),
        "state_dim": 8,
        "action_dim": 8,
        "meaning": "already matches RoboLab Franka+Robotiq action contract",
        "direct_scoreable": True,
    },
}


class AdapterContractError(RuntimeError):
    """适配器契约错误的基类。"""


class ObservationSchemaError(AdapterContractError):
    """RoboLab observation 缺少必要字段。"""


class RetargetRequired(AdapterContractError):
    """源动作不是 Franka+Robotiq `[N,8]`，必须 retarget 或重训 action head。"""


@dataclass
class RoboChallengeAdapterConfig:
    """RoboChallenge 候选策略的适配配置。"""

    checkpoint_path: str = ""
    robot_type: Literal["aloha", "dosw", "ur5", "arx5", "franka_compat_8d"] = "aloha"
    device: str = "cuda:0"
    action_space: str = "franka_robotiq_joint_position_chunk"
    arm_for_dual: Literal["left", "right"] = "right"
    allow_placeholder_retarget: bool = False


@dataclass
class SchemaBridgeResult:
    """一次 observation/action bridge 的可审计结果。"""

    payload: dict[str, Any]
    source_robot: str
    scoreable: bool
    lossy_fields: list[str] = field(default_factory=list)
    required_next_steps: list[str] = field(default_factory=list)

    def to_jsonable(self) -> dict[str, Any]:
        """把 numpy 数组替换成 shape/dtype，便于写 JSON 报告。"""

        def summarize(value: Any) -> Any:
            if isinstance(value, np.ndarray):
                return {"shape": list(value.shape), "dtype": str(value.dtype)}
            if isinstance(value, dict):
                return {k: summarize(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [summarize(v) for v in value]
            return value

        return {
            "source_robot": self.source_robot,
            "scoreable": self.scoreable,
            "lossy_fields": self.lossy_fields,
            "required_next_steps": self.required_next_steps,
            "payload": summarize(self.payload),
        }


def _as_array(value: Any, name: str, *, min_ndim: int | None = None) -> np.ndarray:
    """统一把输入转成 numpy 数组，并给出更清楚的字段错误。"""
    if value is None:
        raise ObservationSchemaError(f"missing required field: {name}")
    arr = np.asarray(value)
    if min_ndim is not None and arr.ndim < min_ndim:
        raise ObservationSchemaError(f"{name} rank too small: expected >= {min_ndim}, got {arr.ndim}")
    return arr


def _obs_group(robolab_obs: dict[str, Any], primary: str, fallback: str) -> dict[str, Any]:
    """兼容 RoboLab runner 里常见的两套 group 命名。"""
    group = robolab_obs.get(primary)
    if group is None:
        group = robolab_obs.get(fallback)
    if not isinstance(group, dict):
        raise ObservationSchemaError(f"missing observation group: {primary} or {fallback}")
    return group


def validate_robolab_observation(robolab_obs: dict[str, Any]) -> dict[str, Any]:
    """检查 RoboLab observation 是否包含策略桥接所需的基础观测。

    输入：RoboLab 单步 observation 字典。
    输出：只含 shape/dtype 的报告，不返回大图像数组，便于日志记录。
    """
    if not isinstance(robolab_obs, dict):
        raise ObservationSchemaError("RoboLab observation must be a dict")

    image_obs = _obs_group(robolab_obs, "image_obs", "images")
    proprio = _obs_group(robolab_obs, "proprio_obs", "proprio")

    image_shapes: dict[str, dict[str, Any]] = {}
    for key in ROBOLAB_IMAGE_KEYS:
        arr = _as_array(image_obs.get(key), f"image_obs.{key}", min_ndim=3)
        image_shapes[key] = {"shape": list(arr.shape), "dtype": str(arr.dtype)}

    arm = _as_array(proprio.get("arm_joint_pos"), "proprio_obs.arm_joint_pos")
    grip = _as_array(proprio.get("gripper_pos"), "proprio_obs.gripper_pos")
    if arm.shape[-1] != 7:
        raise ObservationSchemaError(f"arm_joint_pos must end with 7 Franka joints, got {arm.shape}")
    if grip.shape[-1] != 1:
        raise ObservationSchemaError(f"gripper_pos must end with 1 value, got {grip.shape}")

    return {
        "image_shapes": image_shapes,
        "proprio_shapes": {"arm_joint_pos": list(arm.shape), "gripper_pos": list(grip.shape)},
    }


def validate_franka_robotiq_action_chunk(action_chunk: Any, *, source: str = "unknown") -> dict[str, Any]:
    """验证 RoboLab 硬动作接口：`[N,8]` Franka+Robotiq joint-position chunk。"""
    arr = np.asarray(action_chunk, dtype=np.float32)
    if arr.ndim != 2:
        raise AdapterContractError(f"{source}: action chunk must be rank-2 [N,8], got shape {arr.shape}")
    if arr.shape[1] != 8:
        raise AdapterContractError(f"{source}: action chunk width must be 8, got shape {arr.shape}")
    if arr.shape[0] <= 0:
        raise AdapterContractError(f"{source}: action chunk horizon N must be positive")
    if not np.isfinite(arr).all():
        raise AdapterContractError(f"{source}: action chunk contains NaN or Inf")
    return {
        "source": source,
        "shape": list(arr.shape),
        "columns": list(FRANKA_ROBOTIQ_ACTION_COLUMNS),
        "scoreable": True,
    }


def _single_arm7_from_franka_proprio(robolab_obs: dict[str, Any]) -> tuple[np.ndarray, list[str]]:
    """把 Franka 7 关节 + gripper 压成 RoboChallenge 单臂 7D 占位 state。

    这只是 schema/probe 需要的输入形状：UR5/ARX5 是 6 joints + gripper，
    Franka 是 7 joints + gripper。这里会丢掉 Franka 第 7 关节，因此返回 lossy 标记。
    """
    proprio = _obs_group(robolab_obs, "proprio_obs", "proprio")
    arm = np.asarray(proprio["arm_joint_pos"], dtype=np.float32).reshape(-1, 7)[-1]
    grip = np.asarray(proprio["gripper_pos"], dtype=np.float32).reshape(-1, 1)[-1]
    single = np.concatenate([arm[:6], grip[:1]], axis=0)
    return single, ["franka_joint7_dropped_for_6d_source_robot_state"]


def build_robochallenge_observation(
    robolab_obs: dict[str, Any],
    instruction: str,
    *,
    robot_type: str = "ur5",
) -> SchemaBridgeResult:
    """把 RoboLab observation 转成 RoboChallenge 侧输入 schema。

    这个函数只解决“RoboChallenge 代码如何被调用”的输入形状问题，不代表输出动作可评分。
    """
    validate_robolab_observation(robolab_obs)
    if robot_type not in ROBOCHALLENGE_ROBOT_SPECS:
        raise AdapterContractError(f"unknown RoboChallenge robot_type: {robot_type}")

    image_obs = _obs_group(robolab_obs, "image_obs", "images")
    single_state, lossy = _single_arm7_from_franka_proprio(robolab_obs)

    if robot_type in {"aloha", "dosw"}:
        state = np.zeros(14, dtype=np.float32)
        state[:7] = single_state
        state[7:] = single_state
        payload = {
            "prompt": instruction,
            "robot_type": robot_type,
            "images": {
                "cam_high": image_obs["over_shoulder_left_camera"],
                "cam_left_wrist": image_obs["wrist_cam"],
                "cam_right_wrist": image_obs["over_shoulder_right_camera"],
            },
            "state": state,
            "action_type": "joint",
        }
        lossy = lossy + ["dual_arm_state_synthesized_from_single_franka_arm"]
    elif robot_type == "franka_compat_8d":
        proprio = _obs_group(robolab_obs, "proprio_obs", "proprio")
        state = np.concatenate(
            [
                np.asarray(proprio["arm_joint_pos"], dtype=np.float32).reshape(-1, 7)[-1],
                np.asarray(proprio["gripper_pos"], dtype=np.float32).reshape(-1, 1)[-1],
            ],
            axis=0,
        )
        payload = {
            "prompt": instruction,
            "robot_type": robot_type,
            "images": {
                "cam_global": image_obs["over_shoulder_left_camera"],
                "cam_arm": image_obs["wrist_cam"],
                "cam_side": image_obs["over_shoulder_right_camera"],
            },
            "state": state,
            "action_type": "franka_jointpos",
        }
        lossy = []
    else:
        payload = {
            "prompt": instruction,
            "robot_type": robot_type,
            "images": {
                "cam_global": image_obs["over_shoulder_left_camera"],
                "cam_arm": image_obs["wrist_cam"],
                "cam_side": image_obs.get("over_shoulder_right_camera"),
            },
            "state": single_state,
            "action_type": "leftjoint",
        }

    return SchemaBridgeResult(
        payload=payload,
        source_robot=robot_type,
        scoreable=False,
        lossy_fields=lossy,
        required_next_steps=[
            "calibrate camera names, resolution, and normalization against the concrete RoboChallenge checkpoint",
            "retarget source robot action to Franka+Robotiq [N,8] or retrain a Franka action head",
            "run non-scoring smoke before any RoboLab success-rate table",
        ],
    )


def retarget_robochallenge_actions(
    actions: Any,
    *,
    source_robot: str,
    arm: Literal["left", "right"] = "right",
    allow_placeholder: bool = False,
) -> SchemaBridgeResult:
    """把 RoboChallenge 动作转成 RoboLab `[N,8]`。

    默认行为是严格的：不是天然 `[N,8]` 就抛 ``RetargetRequired``。如果
    ``allow_placeholder=True``，函数会输出形状正确但 ``scoreable=False`` 的占位动作，
    只允许用于 smoke/日志链路验证。
    """
    arr = np.asarray(actions, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.ndim != 2:
        raise AdapterContractError(f"source actions must be rank-2, got {arr.shape}")

    if source_robot == "franka_compat_8d" or arr.shape[1] == 8:
        validate_franka_robotiq_action_chunk(arr, source=source_robot)
        return SchemaBridgeResult(
            payload={"action_chunk": arr, "contract": list(FRANKA_ROBOTIQ_ACTION_COLUMNS)},
            source_robot=source_robot,
            scoreable=True,
        )

    if source_robot in {"aloha", "dosw"}:
        if arr.shape[1] != 14:
            raise AdapterContractError(f"{source_robot} actions expected width 14, got {arr.shape}")
        detail = (
            f"{source_robot} is dual-arm 14D; selecting the {arm} 7D arm still leaves a "
            "6-joint-source-to-7-joint-Franka retarget problem."
        )
        seven = arr[:, :7] if arm == "left" else arr[:, 7:14]
    elif source_robot in {"ur5", "arx5"}:
        if arr.shape[1] != 7:
            raise AdapterContractError(f"{source_robot} actions expected width 7, got {arr.shape}")
        detail = f"{source_robot} is 7D [6 joints + gripper], not Franka 7 joints + Robotiq gripper."
        seven = arr
    else:
        raise AdapterContractError(f"unknown source_robot: {source_robot}")

    if not allow_placeholder:
        raise RetargetRequired(
            detail
            + " Use a calibrated robot retargeter, IK/task-space bridge, or retrain a Franka+Robotiq action head."
        )

    # 占位逻辑：把源 6 个关节放到 Franka 前 6 个关节，第 7 关节置 0，夹爪放第 8 维。
    # 这只用于链路 smoke，不能进入成功率统计。
    out = np.zeros((seven.shape[0], 8), dtype=np.float32)
    out[:, :6] = seven[:, :6]
    out[:, 7] = seven[:, 6]
    validate_franka_robotiq_action_chunk(out, source=f"{source_robot}_placeholder")
    return SchemaBridgeResult(
        payload={"action_chunk": out, "contract": list(FRANKA_ROBOTIQ_ACTION_COLUMNS)},
        source_robot=source_robot,
        scoreable=False,
        lossy_fields=["placeholder_joint7_zero", "source_robot_kinematics_not_retargeted"],
        required_next_steps=["replace placeholder with calibrated retargeter or retrained action head before scoring"],
    )


class RoboChallengeRoboLabAdapter:
    """面向真实接入的薄封装。"""

    def __init__(self, config: RoboChallengeAdapterConfig) -> None:
        self.config = config
        self.model = self._load_model()

    def _load_model(self) -> Any:
        """加载 RoboChallenge checkpoint；当前保留 fail-fast，避免误报已接通。"""
        raise NotImplementedError("RoboChallenge model loading has not been implemented in this stub.")

    def build_robochallenge_observation(self, robolab_obs: dict[str, Any], instruction: str) -> SchemaBridgeResult:
        """生成 RoboChallenge 输入，同时保留 lossy/schema 报告。"""
        return build_robochallenge_observation(robolab_obs, instruction, robot_type=self.config.robot_type)

    def predict_action_chunk(self, robolab_obs: dict[str, Any], instruction: str) -> Any:
        """输出 RoboLab control loop 可执行的动作 chunk。"""
        rc_obs = self.build_robochallenge_observation(robolab_obs, instruction)
        raise NotImplementedError(
            "Action prediction is not wired yet; observation bridge prepared keys: "
            f"{list(rc_obs.payload.keys())}"
        )
