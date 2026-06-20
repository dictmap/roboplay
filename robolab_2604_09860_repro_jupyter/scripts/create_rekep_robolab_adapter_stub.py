"""Create a fail-fast ReKep-to-RoboLab planner adapter skeleton."""

from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent


STUB = '''\
"""ReKep -> RoboLab planner adapter skeleton.

这个文件是 ReKep 接入 RoboLab 的模板，不是已经跑通的 planner baseline。
ReKep 的合理比较对象是“规划方法”，不是 Pi05 那种每步输出动作的 VLA policy。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ReKepAdapterConfig:
    """记录 ReKep 代码路径、VLM 服务和 RoboLab 控制器设置。"""

    rekep_root: str
    vlm_endpoint: str | None = None
    device: str = "cuda:0"
    controller: str = "franka_robotiq_low_level_controller"


class ReKepRoboLabAdapter:
    """把 RoboLab 观测变成 keypoint constraints，再执行成 Franka/Robotiq 动作。"""

    def __init__(self, config: ReKepAdapterConfig) -> None:
        self.config = config

    def extract_keypoints(self, robolab_obs: dict[str, Any], instruction: str) -> list[dict[str, Any]]:
        """从 RoboLab 相机画面和语言指令中抽取 ReKep 所需关键点。"""
        raise NotImplementedError("Keypoint extraction from RoboLab observations is not implemented.")

    def plan_subgoals(self, keypoints: list[dict[str, Any]], instruction: str) -> list[dict[str, Any]]:
        """调用 ReKep 约束生成和优化，得到子目标序列。"""
        raise NotImplementedError("ReKep constraint planning is not implemented.")

    def execute_subgoals(self, subgoals: list[dict[str, Any]], robolab_env: Any) -> dict[str, Any]:
        """把 ReKep 子目标交给 RoboLab/Isaac 中的低层控制器执行。"""
        raise NotImplementedError("RoboLab low-level execution bridge is not implemented.")
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("robolab_repro_artifacts/adapter_stubs/rekep_robolab_adapter.py"),
    )
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(dedent(STUB), encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
