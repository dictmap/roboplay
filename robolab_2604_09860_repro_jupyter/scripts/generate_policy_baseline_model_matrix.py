"""Generate a policy/model baseline matrix for RoboLab follow-up experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


POLICY_BASELINES = [
    {
        "id": "pi05",
        "display_name": "OpenPI pi0.5 / Pi05",
        "tier": "direct_robolab_openpi",
        "robolab_policy_arg": "pi05",
        "can_run_now": True,
        "role": "main baseline already used in the current reproduction",
        "adapter_work": [],
        "source": "RoboLab policies/pi0_family supports --policy pi05",
    },
    {
        "id": "paligemma",
        "display_name": "OpenPI PaliGemma baseline",
        "tier": "direct_robolab_openpi",
        "robolab_policy_arg": "paligemma",
        "can_run_now": True,
        "role": "paper-style direct baseline if checkpoint/server is available",
        "adapter_work": [],
        "source": "RoboLab policies/pi0_family supports --policy paligemma",
    },
    {
        "id": "paligemma_fast",
        "display_name": "OpenPI PaliGemma-FAST baseline",
        "tier": "direct_robolab_openpi",
        "robolab_policy_arg": "paligemma_fast",
        "can_run_now": True,
        "role": "fast PaliGemma direct baseline if checkpoint/server is available",
        "adapter_work": [],
        "source": "RoboLab policies/pi0_family supports --policy paligemma_fast",
    },
    {
        "id": "pi0",
        "display_name": "OpenPI pi0",
        "tier": "direct_robolab_openpi",
        "robolab_policy_arg": "pi0",
        "can_run_now": True,
        "role": "older Pi0-family direct baseline",
        "adapter_work": [],
        "source": "RoboLab policies/pi0_family supports --policy pi0",
    },
    {
        "id": "pi0_fast",
        "display_name": "OpenPI pi0-FAST",
        "tier": "direct_robolab_openpi",
        "robolab_policy_arg": "pi0_fast",
        "can_run_now": True,
        "role": "fast Pi0-family direct baseline",
        "adapter_work": [],
        "source": "RoboLab policies/pi0_family supports --policy pi0_fast",
    },
    {
        "id": "groot_n1_7",
        "display_name": "NVIDIA Isaac GR00T N1.7",
        "tier": "adapter_required_vla",
        "robolab_policy_arg": None,
        "can_run_now": False,
        "role": "VLA candidate, not a RoboLab Pi0-family drop-in runner",
        "adapter_work": [
            "map RoboLab over_shoulder/wrist/proprio/prompt observations into GR00T input schema",
            "map GR00T action output into Franka+Robotiq joint-position action space",
            "confirm checkpoint license, embodiment support, and inference server command",
            "run a single BananaInBowlTask adapter smoke before axis5 matrix",
        ],
        "source": "NVIDIA Isaac-GR00T repository describes GR00T as an open VLA model",
    },
    {
        "id": "cosmos_world",
        "display_name": "NVIDIA Cosmos world foundation models",
        "tier": "not_drop_in_action_policy",
        "robolab_policy_arg": None,
        "can_run_now": False,
        "role": "world-model / simulation / data-generation component, not directly comparable to Pi05 success rate unless wrapped as a policy or planner",
        "adapter_work": [
            "decide whether to test Cosmos as world-model augmentation, video prediction, or policy component",
            "do not report it beside Pi05 as a direct action-policy baseline unless an action-producing Cosmos Policy checkpoint/adapter is available",
        ],
        "source": "NVIDIA Cosmos repository describes an open platform of world models, datasets, and tools",
    },
    {
        "id": "qwen_vla",
        "display_name": "Alibaba Qwen-VLA",
        "tier": "adapter_required_vla",
        "robolab_policy_arg": None,
        "can_run_now": False,
        "role": "Alibaba/Qwen VLA candidate; needs action and embodiment adapter before RoboLab evaluation",
        "adapter_work": [
            "confirm open weights/API and action representation",
            "map RoboLab image/proprio/prompt observations into Qwen-VLA input schema",
            "map output actions into Franka+Robotiq control or a low-level controller",
            "start with BananaInBowlTask then the same axis5 matrix",
        ],
        "source": "Qwen-VLA blog describes a general-purpose Vision-Language-Action model",
    },
    {
        "id": "qwen_robot_manip",
        "display_name": "Alibaba Qwen-RobotManip",
        "tier": "adapter_required_vla",
        "robolab_policy_arg": None,
        "can_run_now": False,
        "role": "manipulation-oriented Qwen RobotSuite candidate; availability and action interface must be confirmed",
        "adapter_work": [
            "confirm release status, weights/API, and robot action contract",
            "build RoboLab policy client only after action interface is known",
        ],
        "source": "Qwen RobotSuite announcement lists Qwen-RobotManip among robotics foundation models",
    },
    {
        "id": "robochallenge_pi",
        "display_name": "RoboChallenge pi",
        "tier": "adapter_required_existing_local",
        "robolab_policy_arg": None,
        "can_run_now": False,
        "role": "local comparison candidate after Pi05 axis5 matrix is stable",
        "adapter_work": [
            "locate existing RoboChallenge pi checkpoint and inference command",
            "normalize observation/action schema to RoboLab's episode result format",
            "run the exact same axis5 task list",
        ],
        "source": "local previous RoboChallenge work; not a RoboLab built-in policy arg",
    },
    {
        "id": "rekep",
        "display_name": "ReKep",
        "tier": "planner_adapter_required",
        "robolab_policy_arg": None,
        "can_run_now": False,
        "role": "planner-style baseline, useful but not a pure learned VLA comparison",
        "adapter_work": [
            "define perception/keypoint extraction from RoboLab camera observations",
            "define motion execution through Franka+Robotiq low-level controller",
            "report separately from learned VLA policies",
        ],
        "source": "ReKep project is a planning/perception baseline, not a RoboLab Pi0-family runner",
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("robolab_repro_artifacts/policy_baseline_model_matrix.json"))
    args = parser.parse_args()

    payload = {
        "purpose": "Separate direct RoboLab policy baselines from adapter-required VLA/world/planner candidates.",
        "recommended_order": [
            "direct_robolab_openpi",
            "adapter_required_existing_local",
            "adapter_required_vla",
            "planner_adapter_required",
            "not_drop_in_action_policy",
        ],
        "baselines": POLICY_BASELINES,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "baselines": len(POLICY_BASELINES)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
