# Current RoboLab-120 Reproduction Status (Pi05 / RTX 4090)

> [!TIP]
> Final checkpoint: Pi05 full RoboLab-120 has completed on the RTX 4090. `run_returncode=0` and `verify_returncode=0` mean every task produced and verified its artifacts; policy success rate is a separate metric reported below.

## Progress

| Item | Value |
|---|---|
| Updated at | `2026-06-21T06:27:40+08:00` |
| Host | `y12` |
| Policy | `Pi05 / OpenPI pi05_droid_jointpos` |
| Run prefix | `robolab120_pi05_full_assetsfixed_20260620_170411` |
| State | `completed` |
| Manifest progress | `120/120` |
| Rows with run+verify returncode 0 | `120/120` |
| Failed/error rows | `0` |
| GPU used/total/util at refresh | `10912, 24564, 0` |

## Final Success Tables

### Overall / Ability Axis

| Category/Attribute | Success | Success % | Total | Score(total) | Score(fail) | Time(s) | Time σ | EE SPARC | SPARC σ | PathLen(m) | Path σ | Speed(cm/s) | Speed σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TOTAL | 34 | 28.3 | 120 | 0.438 | 0.216 | 32.50 | 32.54 | -8.08 | 3.18 | 4.12 | 3.51 | 5.2 | 1.5 |
| PROCEDURAL | 6 | 17.6 | 34 | 0.396 | 0.267 | 58.11 | 59.92 | -9.41 | 2.97 | 5.47 | 3.93 | 4.8 | 1.3 |
|   affordance | 1 | 8.3 | 12 | 0.111 | 0.030 | 12.27 | - | -10.72 | 3.28 | 4.13 | 3.36 | 3.7 | 1.1 |
|   reorientation | 1 | 16.7 | 6 | 0.556 | 0.467 | 39.07 | - | -10.69 | 2.65 | 4.07 | 2.21 | 4.4 | 1.2 |
|   sorting | 3 | 25.0 | 12 | 0.525 | 0.367 | 90.40 | 75.28 | -8.56 | 3.00 | 8.02 | 4.63 | 5.4 | 1.1 |
|   stacking | 1 | 16.7 | 6 | 0.472 | 0.366 | 26.13 | - | -8.36 | 2.05 | 4.01 | 1.54 | 5.5 | 0.8 |
| RELATIONAL | 15 | 35.7 | 42 | 0.462 | 0.164 | 26.19 | 23.52 | -7.77 | 3.49 | 3.45 | 3.02 | 5.3 | 1.5 |
|   conjunction | 5 | 62.5 | 8 | 0.781 | 0.417 | 29.81 | 15.57 | -6.15 | 2.24 | 3.84 | 4.19 | 6.2 | 1.9 |
|   counting | 4 | 57.1 | 7 | 0.714 | 0.333 | 36.33 | 39.29 | -10.09 | 4.61 | 3.65 | 2.84 | 5.3 | 2.1 |
|   spatial | 6 | 20.7 | 29 | 0.282 | 0.094 | 16.41 | 14.79 | -8.04 | 3.56 | 3.57 | 2.93 | 4.9 | 1.2 |
| VISUAL | 20 | 23.8 | 84 | 0.396 | 0.207 | 41.29 | 38.58 | -8.52 | 3.08 | 4.63 | 3.65 | 5.2 | 1.5 |
|   color | 6 | 23.1 | 26 | 0.441 | 0.273 | 31.20 | 16.95 | -7.89 | 2.79 | 3.55 | 2.16 | 4.9 | 1.6 |

### Difficulty

| Attribute | Success | Success % | LCB % | UCB % | Total | Score(total) | Score(fail) | Time(s) | Time σ | EE SPARC | SPARC σ | PathLen(m) | Path σ | Speed(cm/s) | Speed σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| simple | 21 | 32.8 | 22.6 | 45.1 | 64 | 0.414 | 0.128 | 26.02 | 17.62 | -6.93 | 2.64 | 2.74 | 1.89 | 5.4 | 1.6 |
| moderate | 10 | 25.6 | 14.6 | 41.2 | 39 | 0.466 | 0.282 | 22.53 | 13.51 | -8.76 | 3.32 | 4.53 | 3.67 | 5.1 | 1.4 |
| complex | 3 | 17.6 | 6.4 | 41.4 | 17 | 0.464 | 0.349 | 111.11 | 57.74 | -10.80 | 2.68 | 8.31 | 4.30 | 4.8 | 1.2 |

### Task Length

| # Subtasks | Success | Success % | LCB % | UCB % | Total | Score(total) | Score(fail) | Time(s) | Time σ | EE SPARC | SPARC σ | PathLen(m) | Path σ | Speed(cm/s) | Speed σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 20 | 37.7 | 25.9 | 51.3 | 53 | 0.434 | 0.091 | 21.93 | 12.33 | -6.97 | 2.83 | 1.88 | 0.90 | 5.2 | 1.7 |
| 2 | 9 | 22.0 | 12.1 | 36.8 | 41 | 0.390 | 0.219 | 34.95 | 20.81 | -8.34 | 2.92 | 4.80 | 2.53 | 5.3 | 1.4 |
| 3 | 5 | 29.4 | 13.3 | 53.5 | 17 | 0.608 | 0.444 | 70.37 | 69.14 | -9.29 | 3.59 | 6.00 | 4.47 | 5.4 | 1.3 |
| 4 | 0 | 0.0 | 0.5 | 52.2 | 4 | 0.312 | 0.312 | - | - | -11.30 | 3.41 | 7.74 | 2.17 | 4.2 | 1.2 |
| 5 | 0 | 0.0 | 1.3 | 84.2 | 1 | 0.800 | 0.800 | - | - | -6.77 | - | 6.44 | - | 5.3 | - |
| 7 | 0 | 0.0 | 0.8 | 70.8 | 2 | 0.589 | 0.589 | - | - | -11.37 | 1.64 | 12.12 | 0.71 | 4.4 | 1.0 |
| 9 | 0 | 0.0 | 1.3 | 84.2 | 1 | 0.000 | 0.000 | - | - | -11.86 | - | 18.34 | - | 5.8 | - |
| 11 | 0 | 0.0 | 1.3 | 84.2 | 1 | 0.000 | 0.000 | - | - | -13.31 | - | 13.90 | - | 5.5 | - |

## Artifact Completeness

| Artifact | Count |
|---|---:|
| Task output folders | `120` |
| HDF5 files | `120` |
| MP4 videos total | `240` |
| Viewport MP4 videos | `120` |
| Main MP4 videos | `120` |
| Task-level `episode_results.jsonl` | `120` |
| Subtask/event logs `log_0_env0.json` | `120` |

## Integrity Check

- The repository `analysis/check_results.py` had a local bug: it referenced an undefined `hdf5_path` after collecting `hdf5_files`.
- I patched the local 4090 copy to iterate over `hdf5_files`, then reran the checker across all 120 task folders.
- Result: `analysis/check_results.py` returned `rc=0`; each checked folder reported `All episodes have valid HDF5 data!`.
- Log: `robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_check_results.log`.

## Model Download / Prefetch Status

| Model | Path | Size | Status |
|---|---|---:|---|
| Cosmos Reason1 7B | /data/light/roboplay_models/cosmos/cosmos_reason1_7b_full | 16G | complete/full |
| Cosmos Policy LIBERO Predict2 2B | /data/light/roboplay_models/cosmos/cosmos_policy_libero_predict2_2b_full | 3.7G | complete/full |
| Cosmos Policy ALOHA Predict2 2B | /data/light/roboplay_models/cosmos/cosmos_policy_aloha_predict2_2b_full | 3.7G | complete/full |
| Cosmos Policy ALOHA Planning Predict2 2B | /data/light/roboplay_models/cosmos/cosmos_policy_aloha_planning_predict2_2b_full | 3.7G | complete/full |
| Cosmos Policy RoboCasa Predict2 2B | /data/light/roboplay_models/cosmos/cosmos_policy_robocasa_predict2_2b_full | 4.1G | complete/full |
| Cosmos Predict2.5 2B | /data/light/roboplay_models/cosmos/cosmos_predict2_5_2b_metadata | 56K | complete/metadata |
| Cosmos Reason2 32B | /data/light/roboplay_models/cosmos/cosmos_reason2_32b_metadata | 12M | complete/metadata |
| Cosmos Reason2 2B | /data/light/roboplay_models/cosmos/cosmos_reason2_2b_full | 64K | blocked: HF gated access required |
| Cosmos Reason2 8B | /data/light/roboplay_models/cosmos/cosmos_reason2_8b_full | 64K | blocked: HF gated access required |
| GR00T N1.5 3B | /data/light/roboplay_models/open_model_baselines/groot_n1_5_3b_full | 5.1G | complete/full |
| Qwen2.5-VL 3B Instruct | /data/light/roboplay_models/open_model_baselines/qwen2_5_vl_3b_instruct_full | 7.1G | complete/full |
| Qwen2.5-VL 7B Instruct | /data/light/roboplay_models/open_model_baselines/qwen2_5_vl_7b_instruct_metadata | 12M | metadata only |
| PaliGemma2 3B PT 224 | /data/light/roboplay_models/open_model_baselines/paligemma2_3b_pt_224_full | 56K | incomplete: README only |

Cosmos policy checkpoints were prefetched through `HF_ENDPOINT=https://hf-mirror.com`. Reason2-2B and Reason2-8B remain blocked by Hugging Face gated-access authorization for the current account/token.

## Evidence Files

- Manifest: `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_task_run_manifest.jsonl`
- Status JSON: `robolab_repro_artifacts/current_robolab120_status.json`
- Final CSV tables:
  - `robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_read_results_by_attributes.csv`
  - `robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_read_results_by_difficulty.csv`
  - `robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_read_results_by_task_length.csv`
- Output prefix: `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/robolab120_pi05_full_assetsfixed_20260620_170411_<TaskName>`
- GitHub sample videos: `sample_videos/` plus `SAMPLE_VIDEOS.md`.

## Interpretation Boundary

- Completed reproduction means all 120 task rollouts produced verified artifacts.
- Pi05 achieved `34/120 = 28.3%` task success in this run.
- RoboChallenge pi, ReKep, GR00T, Cosmos, PaliGemma/Qwen/Alibaba-family policies are not yet scored in RoboLab until their observation/action adapter is implemented and run on the same task matrix.

## Next Steps

1. Choose a medium-success task from this final table for camera/light/background/object-position perturbation.
2. Keep Cosmos and other baseline model downloads running in the background.
3. Implement adapters for RoboChallenge pi and ReKep before putting them into the same success-rate table.
4. Add GR00T/Cosmos/Qwen/PaliGemma/Alibaba models only after the adapter can emit RoboLab-compatible continuous robot actions.
