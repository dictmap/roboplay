# RoboLab-120 / Pi05 最终复现收口记录（2026-06-21）

> [!TIP]
> 这份文档是给前面所有学习记录、精讲和实验计划做的统一更新。早期文档里的单任务、复杂任务抽样、axis5 计划和 full-120 执行包仍保留历史价值；当前最终事实以这里和 `CURRENT_ROBOLAB120_STATUS.md` 为准。

## 一句话结论

在 RTX 4090 / Ubuntu 22.04.4 上，固定 OpenPI `pi05_droid_jointpos`，RoboLab-120 已完整跑完：120 个任务全部生成并通过 artifact verify；Pi05 的任务成功率是 `34/120 = 28.3%`。

## 运行身份

| 项 | 值 |
|---|---|
| Host | `y12` |
| Policy | `Pi05 / OpenPI pi05_droid_jointpos` |
| Run prefix | `robolab120_pi05_full_assetsfixed_20260620_170411` |
| Manifest | `robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_task_run_manifest.jsonl` |
| GitHub main | `6f88462` |
| 远端 RoboLab | `/home/yjl/codex_robolab_4090_20260619/RoboLab` |
| 输出前缀 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/robolab120_pi05_full_assetsfixed_20260620_170411_<TaskName>` |

## 最终结果表

### 总体与能力轴

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

### 难度

| Attribute | Success | Success % | LCB % | UCB % | Total | Score(total) | Score(fail) | Time(s) | Time σ | EE SPARC | SPARC σ | PathLen(m) | Path σ | Speed(cm/s) | Speed σ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| simple | 21 | 32.8 | 22.6 | 45.1 | 64 | 0.414 | 0.128 | 26.02 | 17.62 | -6.93 | 2.64 | 2.74 | 1.89 | 5.4 | 1.6 |
| moderate | 10 | 25.6 | 14.6 | 41.2 | 39 | 0.466 | 0.282 | 22.53 | 13.51 | -8.76 | 3.32 | 4.53 | 3.67 | 5.1 | 1.4 |
| complex | 3 | 17.6 | 6.4 | 41.4 | 17 | 0.464 | 0.349 | 111.11 | 57.74 | -10.80 | 2.68 | 8.31 | 4.30 | 4.8 | 1.2 |

### 任务长度

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

## 证据完整性

| 证据类型 | 数量 | 说明 |
|---|---:|---|
| Task output folder | 120 | 每个任务一个输出目录 |
| HDF5 | 120 | 每个任务 `run_0.hdf5` |
| MP4 | 240 | 每个任务主视频 + viewport 视频 |
| `episode_results.jsonl` | 120 | task-level 结果 |
| `log_0_env0.json` | 120 | 子任务/事件日志 |
| 官方完整性检查 | 通过 | `analysis/check_results.py` 修复本地 bug 后 120/120 确认有效 HDF5 demo |

关键文件：

- `CURRENT_ROBOLAB120_STATUS.md`
- `MODEL_DOWNLOADS_STATUS.md`
- `SAMPLE_VIDEOS.md`
- `robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_read_results_by_attributes.csv`
- `robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_read_results_by_difficulty.csv`
- `robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_read_results_by_task_length.csv`
- `robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_check_results.log`

## 旧文档如何理解

| 旧文档 | 当前解释 |
|---|---|
| `COMPLETE_REPRO_pi05_banana_20260620.md` | 仍是最小成功闭环样例；不再代表最终进度，因为 full-120 已完成。 |
| `COMPLEX_TASKS_pi05_20260620.md` | 仍是复杂任务早期抽样；最终统计以 120 任务聚合表为准。 |
| `EXPERIMENT_17_camera_robot_ablation.md` | 相机/腕部相机/机器人替换仍是下一阶段消融；现在应从 full-120 中选中等成功率任务，而不是只用 Banana。 |
| `EXPERIMENT_18_pi05_axis5_then_perturb_compare.md` | axis5 是保守小矩阵设计；已被 full-120 正式结果覆盖，但仍可用作调参和快速回归。 |
| `EXPERIMENT_19_policy_baseline_models.md` | 多模型对照的接口边界仍成立；模型权重下载状态已更新到 `MODEL_DOWNLOADS_STATUS.md`。 |
| `EXPERIMENT_20_robolab120_robochallenge_rekep_compare.md` | full-120 的 Pi05 部分已完成；RoboChallenge pi / ReKep 仍需 adapter，不能直接算 0 分。 |
| `EXPLAIN_08/13/14/15` | 这些精讲现在可以用本次 120 任务结果作为证据样例，而不是只停留在论文解释。 |

## 模型下载状态

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

## 仍未完成的部分

- RoboChallenge pi 和 ReKep 还没有进入同一张 success-rate 表；它们需要 observation/action/planner adapter。
- GR00T、Cosmos、Qwen/阿里、PaliGemma 等模型不能只因为权重存在就算 RoboLab policy；必须能输出 RoboLab 当前 Franka/Robotiq 可执行动作。
- Cosmos Reason2-2B / Reason2-8B 当前是 Hugging Face gated access 阻塞，需要账号授权后再拉完整权重。
- 相机角度、取消腕部相机、机器人替换这三个消融尚未基于 full-120 正式重跑；下一步建议先选一个中等成功率任务做 light/background/object-position/camera sweep。
