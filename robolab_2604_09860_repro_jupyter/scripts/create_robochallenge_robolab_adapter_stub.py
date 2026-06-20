"""Create a fail-fast RoboChallenge-to-RoboLab adapter skeleton."""

from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent


STUB = '''\
"""RoboChallenge pi -> RoboLab policy adapter skeleton.

这个文件是适配器模板，不是可直接得分的策略。
只有实现 `predict_action_chunk` 后，才能把 RoboChallenge pi 放进 RoboLab-120 真对照。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RoboChallengeAdapterConfig:
    """记录 RoboChallenge 候选模型的位置和 RoboLab 侧动作合约。"""

    checkpoint_path: str
    device: str = "cuda:0"
    action_space: str = "franka_robotiq_joint_position_chunk"


class RoboChallengeRoboLabAdapter:
    """把 RoboLab observation 转成 RoboChallenge 输入，再把输出动作转回 RoboLab。"""

    def __init__(self, config: RoboChallengeAdapterConfig) -> None:
        self.config = config
        self.model = self._load_model()

    def _load_model(self) -> Any:
        """加载 RoboChallenge checkpoint。

        这里必须由实际 RoboChallenge 代码完成：
        1. 读取 Table30v2/ALOHA 或 pi checkpoint。
        2. 构造推理模型。
        3. 确认模型输出的动作维度和 RoboLab Franka/Robotiq 控制维度一致。
        """
        raise NotImplementedError("RoboChallenge model loading has not been implemented.")

    def build_robochallenge_observation(self, robolab_obs: dict[str, Any], instruction: str) -> dict[str, Any]:
        """把 RoboLab 双相机、proprio 和语言指令映射到 RoboChallenge 输入 schema。"""
        raise NotImplementedError("Observation schema mapping has not been implemented.")

    def predict_action_chunk(self, robolab_obs: dict[str, Any], instruction: str) -> Any:
        """输出 RoboLab control loop 可执行的动作 chunk。"""
        rc_obs = self.build_robochallenge_observation(robolab_obs, instruction)
        raise NotImplementedError(f"Action prediction is not wired yet. Prepared obs keys: {list(rc_obs)}")
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("robolab_repro_artifacts/adapter_stubs/robochallenge_robolab_adapter.py"),
    )
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(dedent(STUB), encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
