"""Write the RoboChallenge/ReKep adapter plan used by RoboLab comparison runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_ROBOCHALLENGE_ROOT = "/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask"
DEFAULT_ROBOCHALLENGE_CHECKPOINT = "/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha"
DEFAULT_REKEP_ROOT = "/home/yjl/yjl/ReKep"


def build_plan(args: argparse.Namespace) -> dict:
    """Return a truthful adapter-readiness matrix for non-drop-in baselines."""
    return {
        "purpose": "Document why RoboChallenge pi and ReKep cannot be fairly scored on RoboLab-120 until adapters exist.",
        "comparison_rule": (
            "Only policies that emit RoboLab-compatible Franka/Robotiq actions from RoboLab observations "
            "can enter success-rate tables as real results. Others are marked adapter_required."
        ),
        "baselines": [
            {
                "id": "robochallenge_pi",
                "display_name": "RoboChallenge pi / Table30v2 ALOHA baseline",
                "status": "adapter_required",
                "local_candidate_root": args.robochallenge_root,
                "local_candidate_checkpoint": args.robochallenge_checkpoint,
                "main_mismatch": [
                    "RoboChallenge baseline is built around its own task/data interface.",
                    "Existing checkpoint path is a Table30v2/ALOHA style candidate, not a RoboLab Pi0-family policy arg.",
                    "RoboLab expects per-step observations with over-shoulder camera, wrist camera, proprio, prompt, and Franka/Robotiq action chunks.",
                ],
                "adapter_contract": {
                    "input": [
                        "RoboLab observation dict",
                        "language instruction",
                        "robot joint positions and gripper state",
                        "camera calibration/image tensors",
                    ],
                    "output": [
                        "RoboLab action vector or action chunk compatible with policies/pi0_family/run.py control loop",
                        "timing statistics",
                        "policy metadata for episode_results.jsonl",
                    ],
                    "first_smoke": "BananaInBowlTask with NUM_RUNS=1, NUM_ENVS=1",
                    "promotion_gate": "Only after one full episode writes video, HDF5, event log, and episode_results.jsonl.",
                },
            },
            {
                "id": "rekep",
                "display_name": "ReKep keypoint-constraint planner",
                "status": "planner_adapter_required",
                "local_candidate_root": args.rekep_root,
                "main_mismatch": [
                    "ReKep is a perception/planning/control route, not a direct learned VLA action policy.",
                    "It needs keypoint extraction, constraint generation, subgoal optimization, and a RoboLab low-level controller.",
                    "Its result should be reported as planner baseline, not mixed silently with Pi05/PaliGemma policy baselines.",
                ],
                "adapter_contract": {
                    "input": [
                        "RoboLab RGB-D or RGB observation",
                        "language instruction",
                        "scene object/keypoint candidates",
                        "current robot state",
                    ],
                    "output": [
                        "subgoal sequence",
                        "constraint satisfaction diagnostics",
                        "low-level Franka/Robotiq actions",
                        "same episode_results.jsonl/HDF5/video evidence contract as VLA policies",
                    ],
                    "first_smoke": "A single pick-place task with visible target object and container.",
                    "promotion_gate": "Only after planner actions are executed in Isaac, not merely generated offline.",
                },
            },
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("robolab_repro_artifacts/adapter_baseline_plan.json"))
    parser.add_argument("--robochallenge-root", default=DEFAULT_ROBOCHALLENGE_ROOT)
    parser.add_argument("--robochallenge-checkpoint", default=DEFAULT_ROBOCHALLENGE_CHECKPOINT)
    parser.add_argument("--rekep-root", default=DEFAULT_REKEP_ROOT)
    args = parser.parse_args()

    payload = build_plan(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "baselines": [row["id"] for row in payload["baselines"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
