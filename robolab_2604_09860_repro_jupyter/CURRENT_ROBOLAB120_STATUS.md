# Current RoboLab-120 Reproduction Status (Pi05 / RTX 4090)

> [!NOTE]
> This is an in-progress checkpoint from 2026-06-20, not the final 120/120 result table. Final success-rate tables must be regenerated after the manifest reaches 120 rows.

## Progress

| Item | Value |
|---|---|
| Updated at | `2026-06-21T05:22:16+08:00` |
| Host | `y12` |
| Policy | `Pi05 / OpenPI pi05_droid_jointpos` |
| Run prefix | `robolab120_pi05_full_assetsfixed_20260620_170411` |
| State | `running` |
| Manifest progress | `110/120` |
| Rows with run+verify returncode 0 | `110/110` |
| Failed/error rows so far | `0` |
| Latest log line | ` 22%|██▏       | 199/900 [00:56<03:18,  3.53it/s]` |
| GPU used/total/util | `18894, 24564, 56` |

## Completed Preflight

- Required 120-task LFS assets and backgrounds were checked out before this clean run; `missing_count=0` was verified before launch.
- Preflight test10 run: `robolab120_pi05_assetsfixed_test10_20260620_162403`, `10/10` rows had `run_returncode=0` and `verify_returncode=0`.
- The formal run uses `NUM_ENVS=1`, `NUM_RUNS=1`, `VIDEO_MODE=all`, `STOP_ON_FAILURE=0`, which is the conservative RTX 4090 24GB setting.

## Recent Manifest Rows

| Task | run_returncode | verify_returncode | output_root |
|---|---:|---:|---|
| `TakeMeasuringSpoonOutTask` | `0` | `0` | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/robolab120_pi05_full_assetsfixed_20260620_170411_TakeMeasuringSpoonOutTask` |
| `TakeMugsOffOfShelfTask` | `0` | `0` | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/robolab120_pi05_full_assetsfixed_20260620_170411_TakeMugsOffOfShelfTask` |
| `TakeSpatulaOffShelfTask` | `0` | `0` | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/robolab120_pi05_full_assetsfixed_20260620_170411_TakeSpatulaOffShelfTask` |
| `ThrowAwayAppleTask` | `0` | `0` | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/robolab120_pi05_full_assetsfixed_20260620_170411_ThrowAwayAppleTask` |
| `ThrowAwaySnacksTask` | `0` | `0` | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/robolab120_pi05_full_assetsfixed_20260620_170411_ThrowAwaySnacksTask` |
| `ToolOrganizationBothTask` | `0` | `0` | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/robolab120_pi05_full_assetsfixed_20260620_170411_ToolOrganizationBothTask` |
| `ToolOrganizationTask` | `0` | `0` | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/robolab120_pi05_full_assetsfixed_20260620_170411_ToolOrganizationTask` |
| `ToolsPickingAllHammersTask` | `0` | `0` | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/robolab120_pi05_full_assetsfixed_20260620_170411_ToolsPickingAllHammersTask` |

## Current Errors

None so far.

## Evidence Files

- Manifest: `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_task_run_manifest.jsonl`
- Status JSON: `robolab_repro_artifacts/current_robolab120_status.json`
- Output prefix: `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/robolab120_pi05_full_assetsfixed_20260620_170411_<TaskName>`
- Per-task output should include `episode_results.jsonl`, HDF5, video, event/subtask logs, and artifact-check JSON.

## Next Steps

1. Wait for Pi05 full-120 to reach `120/120`.
2. Regenerate final tables with `analysis/read_results.py`, `scripts/summarize_ablation_outputs.py`, and `scripts/compare_policy_matrix_results.py`.
3. Pick a medium-success task for lighting/background/object-position perturbations.
4. Only then run the same task matrix through RoboChallenge pi or ReKep adapters; adapter-pending rows are not real zero scores.
