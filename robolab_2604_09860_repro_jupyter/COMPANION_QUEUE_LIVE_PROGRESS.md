# RoboLab 4090 陪伴式实验实时记录

- 更新时间：2026-06-21T11:41:03
- 队列 ID：`roboplay_companion_20260621_074050`
- 实时日志：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/roboplay_companion_20260621_074050/live.log`
- 状态 JSONL：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_status.jsonl`
- 当前阶段：`04_camera_angle_20`
- 当前日志定位：`[96m[RoboLab] Running BlockStackingSpecifiedOrderTask_randomize_external_camera_0: 'Stack the blocks in the order from bottom to top: red, blue, green, yellow' (run 0, 1 envs)[0m`
- 当前进度：`47% 632/1350 elapsed=02:12 eta=02:26`

## 当前结论

- RoboLab-120 Pi05 完整复现已经通过校验：120/120 run ok，120/120 verify ok。
- Pi05 20 任务基线：已完成 `20/20`，全部 run/verify 通过。
- RoboChallenge pi 和 ReKep 当前记录为 adapter/probe：本地资源存在，但不是可直接接 RoboLab 的 action-policy server。
- 相机角度阶段：每个任务 3 个变体（external / wrist / wrist+external），当前 episode 行 `15/60`，目录 `16/60`，HDF5 `16`，MP4 `32`，子任务日志 `15`。

## 阶段状态

| 阶段 | 状态 | returncode | 说明 |
|---|---:|---:|---|
| `00_full120_checkpoint` | running | None | 确认 Pi05 RoboLab-120 已完整复现 |
| `00_full120_checkpoint` | completed | 0 | see /home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/roboplay_companion_20260621_074050/00_full120_checkpoint.log |
| `01_select20_pi05_baseline` | running | None | 选择 20 个任务并运行 Pi05 基线 |
| `01_select20_pi05_baseline` | completed | 0 | see /home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/roboplay_companion_20260621_074050/01_select20_pi05_baseline.log |
| `02_robochallenge_pi_probe` | running | None | RoboChallenge pi 20 任务 adapter 探测 |
| `02_robochallenge_pi_probe` | completed | 0 | see /home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/roboplay_companion_20260621_074050/02_robochallenge_pi_probe.log |
| `03_rekep_probe` | running | None | ReKep 20 任务 adapter 探测 |
| `03_rekep_probe` | completed | 0 | see /home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/roboplay_companion_20260621_074050/03_rekep_probe.log |
| `04_camera_angle_20` | running | None | 相机角度扰动 20 任务 |

## Pi05 20 个任务基线

| 序号 | 任务 | 状态 | run | verify | 输出目录 |
|---:|---|---|---:|---:|---|
| 1 | `FoodPackingByColorTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_FoodPackingByColorTask` |
| 2 | `NonHammerToolsInRightBinTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_NonHammerToolsInRightBinTask` |
| 3 | `CookingPickPastaToolTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_CookingPickPastaToolTask` |
| 4 | `ReorientJugTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_ReorientJugTask` |
| 5 | `YellowAndWhiteObjectsInBinTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_YellowAndWhiteObjectsInBinTask` |
| 6 | `BlockStackingSpecifiedOrderTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_BlockStackingSpecifiedOrderTask` |
| 7 | `ClampInRightBinTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_ClampInRightBinTask` |
| 8 | `PutMugsOnShelfTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_PutMugsOnShelfTask` |
| 9 | `PlasticBottlesInSquarePailTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_PlasticBottlesInSquarePailTask` |
| 10 | `ToolsPickingDrillTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_ToolsPickingDrillTask` |
| 11 | `CubesAndBlocksInBinTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_CubesAndBlocksInBinTask` |
| 12 | `CookingClearPlateTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_CookingClearPlateTask` |
| 13 | `ToolsPickingHammerTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_ToolsPickingHammerTask` |
| 14 | `AnimalsInBinTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_AnimalsInBinTask` |
| 15 | `BananasInBinOneMoreTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_BananasInBinOneMoreTask` |
| 16 | `BlackItemsInBinTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_BlackItemsInBinTask` |
| 17 | `BagelsOnPlateTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_BagelsOnPlateTask` |
| 18 | `BananasInBinThreeTotalTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_BananasInBinThreeTotalTask` |
| 19 | `CleanUpToysTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_CleanUpToysTask` |
| 20 | `BananaInBowlTask` | 完成 | 0 | 0 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robolab20_pi05_baseline_BananaInBowlTask` |

## 相机角度阶段已生成变体目录

| 序号 | 变体目录 |
|---:|---|
| 1 | `BlockStackingSpecifiedOrderTask_randomize_external_camera` |
| 2 | `CookingPickPastaToolTask_randomize_external_camera` |
| 3 | `CookingPickPastaToolTask_randomize_wrist_and_external_cam` |
| 4 | `CookingPickPastaToolTask_randomize_wrist_cam` |
| 5 | `FoodPackingByColorTask_randomize_external_camera` |
| 6 | `FoodPackingByColorTask_randomize_wrist_and_external_cam` |
| 7 | `FoodPackingByColorTask_randomize_wrist_cam` |
| 8 | `NonHammerToolsInRightBinTask_randomize_external_camera` |
| 9 | `NonHammerToolsInRightBinTask_randomize_wrist_and_external_cam` |
| 10 | `NonHammerToolsInRightBinTask_randomize_wrist_cam` |
| 11 | `ReorientJugTask_randomize_external_camera` |
| 12 | `ReorientJugTask_randomize_wrist_and_external_cam` |
| 13 | `ReorientJugTask_randomize_wrist_cam` |
| 14 | `YellowAndWhiteObjectsInBinTask_randomize_external_camera` |
| 15 | `YellowAndWhiteObjectsInBinTask_randomize_wrist_and_external_cam` |
| 16 | `YellowAndWhiteObjectsInBinTask_randomize_wrist_cam` |

## 记录原则

- `run_returncode=0` 表示仿真运行命令正常退出；`verify_returncode=0` 表示 HDF5、视频、episode_results、子任务日志等产物检查通过。
- 相机阶段的 `episode_results.jsonl` 位于阶段输出根目录；每个变体子目录保存自己的 HDF5、视频、子任务日志。
- 非直接 RoboLab action policy 的模型会先写 adapter/probe 结果，不伪装成真实成功率。


## 2026-06-21 12:55:58 - 相机角度扰动恢复进度

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running PutMugsOnShelfTask_randomize_wrist_cam_0: 'Put the two mugs on the shelf' (run 0, 1 envs)`
- episode 进度：`22/60`
- 产物计数：variant_dirs=`23`，HDF5=`23`，MP4=`46`，subtask_logs=`22`
- step 进度：`{'percent': 41, 'step': 1104, 'total_steps': 2700, 'elapsed': '04:29', 'eta': '05:45'}`
- GPU：`2026/06/21 12:55:58.411, 47, 105.64, 16645, 24564, 81`
- 恢复说明：4090 中途重启后，使用同一个输出目录恢复；脚本会读取已存在的 `episode_results.jsonl` 并跳过已完成变体。
- 日志：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/roboplay_companion_20260621_074050/04_camera_angle_20_resume_after_reboot.log`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 13:04:20 - 相机角度扰动进度更新

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running PutMugsOnShelfTask_randomize_wrist_and_external_cam_0: 'Put the two mugs on the shelf' (run 0, 1 envs)`
- episode 进度：`23/60`
- 产物计数：variant_dirs=`24`，HDF5=`24`，MP4=`48`，subtask_logs=`23`
- step 进度：`{'percent': 22, 'step': 601, 'total_steps': 2700, 'elapsed': '02:26', 'eta': '08:22'}`
- GPU：`2026/06/21 13:04:20.683, 53, 121.12, 17173, 24564, 46`

## 2026-06-21 13:08:13 - 4090 接力 supervisor 启动

- 状态：`running`
- 说明：等待当前相机阶段完成，随后自动执行腕部相机取消、机器人调整、其他模型 probe。
- 日志：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/roboplay_companion_20260621_074050/resume_supervisor.log`



## 2026-06-21 13:08:13 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running PutMugsOnShelfTask_randomize_wrist_and_external_cam_0: 'Put the two mugs on the shelf' (run 0, 1 envs)`
- episode 进度：`23/60`
- 产物计数：variant_dirs=`24`，HDF5=`24`，MP4=`48`，subtask_logs=`23`
- step 进度：`{'percent': 59, 'step': 1590, 'total_steps': 2700, 'elapsed': '06:19', 'eta': '03:57'}`
- GPU：`2026/06/21 13:08:13.763, 48, 122.38, 17173, 24564, 40`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 13:13:14 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running PlasticBottlesInSquarePailTask_randomize_external_camera_0: 'Put all the small plastic bottles in the square pail' (run 0, 1 envs)`
- episode 进度：`24/60`
- 产物计数：variant_dirs=`25`，HDF5=`25`，MP4=`50`，subtask_logs=`24`
- step 进度：`{'percent': 6, 'step': 165, 'total_steps': 2700, 'elapsed': '00:40', 'eta': '09:36'}`
- GPU：`2026/06/21 13:13:14.109, 47, 120.94, 17334, 24564, 59`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 13:18:14 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running PlasticBottlesInSquarePailTask_randomize_wrist_cam_0: 'Put all the small plastic bottles in the square pail' (run 0, 1 envs)`
- episode 进度：`25/60`
- 产物计数：variant_dirs=`26`，HDF5=`26`，MP4=`52`，subtask_logs=`25`
- step 进度：`{'percent': 2, 'step': 49, 'total_steps': 2700, 'elapsed': '00:11', 'eta': '10:02'}`
- GPU：`2026/06/21 13:18:14.430, 47, 120.84, 17412, 24564, 65`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 13:23:14 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running PlasticBottlesInSquarePailTask_randomize_wrist_and_external_cam_0: 'Put all the small plastic bottles in the square pail' (run 0, 1 envs)`
- episode 进度：`26/60`
- 产物计数：variant_dirs=`27`，HDF5=`27`，MP4=`54`，subtask_logs=`26`
- step 进度：`{'percent': 28, 'step': 759, 'total_steps': 2700, 'elapsed': '03:13', 'eta': '07:53'}`
- GPU：`2026/06/21 13:23:14.764, 47, 108.00, 17406, 24564, 32`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 13:28:15 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running PlasticBottlesInSquarePailTask_randomize_wrist_and_external_cam_0: 'Put all the small plastic bottles in the square pail' (run 0, 1 envs)`
- episode 进度：`26/60`
- 产物计数：variant_dirs=`27`，HDF5=`27`，MP4=`54`，subtask_logs=`26`
- step 进度：`{'percent': 70, 'step': 1903, 'total_steps': 2700, 'elapsed': '08:13', 'eta': '03:12'}`
- GPU：`2026/06/21 13:28:15.085, 49, 107.45, 17402, 24564, 74`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 13:33:15 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running ToolsPickingDrillTask_randomize_external_camera_0: 'Select the cordless drill and put it on the table' (run 0, 1 envs)`
- episode 进度：`27/60`
- 产物计数：variant_dirs=`28`，HDF5=`28`，MP4=`56`，subtask_logs=`27`
- step 进度：`{'percent': 32, 'step': 287, 'total_steps': 900, 'elapsed': '01:17', 'eta': '02:52'}`
- GPU：`2026/06/21 13:33:15.408, 47, 121.66, 17254, 24564, 40`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 13:38:15 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running ToolsPickingDrillTask_randomize_wrist_cam_0: 'Select the cordless drill and put it on the table' (run 0, 1 envs)`
- episode 进度：`28/60`
- 产物计数：variant_dirs=`29`，HDF5=`29`，MP4=`58`，subtask_logs=`28`
- step 进度：`{'percent': 53, 'step': 473, 'total_steps': 900, 'elapsed': '02:07', 'eta': '01:53'}`
- GPU：`2026/06/21 13:38:15.727, 47, 106.20, 17256, 24564, 33`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 13:43:16 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running ToolsPickingDrillTask_randomize_wrist_and_external_cam_0: 'Select the cordless drill and put it on the table' (run 0, 1 envs)`
- episode 进度：`29/60`
- 产物计数：variant_dirs=`30`，HDF5=`30`，MP4=`60`，subtask_logs=`29`
- step 进度：`{'percent': 76, 'step': 680, 'total_steps': 900, 'elapsed': '03:02', 'eta': '00:59'}`
- GPU：`2026/06/21 13:43:16.060, 47, 106.81, 17184, 24564, 42`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 13:48:16 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CubesAndBlocksInBinTask_randomize_external_camera_0: 'Put all the cubes and blocks in the bin' (run 0, 1 envs)`
- episode 进度：`30/60`
- 产物计数：variant_dirs=`31`，HDF5=`31`，MP4=`62`，subtask_logs=`30`
- step 进度：`{'percent': 23, 'step': 824, 'total_steps': 3600, 'elapsed': '03:53', 'eta': '13:17'}`
- GPU：`2026/06/21 13:48:16.376, 47, 106.69, 17456, 24564, 42`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 13:53:16 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CubesAndBlocksInBinTask_randomize_external_camera_0: 'Put all the cubes and blocks in the bin' (run 0, 1 envs)`
- episode 进度：`30/60`
- 产物计数：variant_dirs=`31`，HDF5=`31`，MP4=`62`，subtask_logs=`30`
- step 进度：`{'percent': 53, 'step': 1911, 'total_steps': 3600, 'elapsed': '08:54', 'eta': '08:08'}`
- GPU：`2026/06/21 13:53:16.698, 47, 106.74, 17456, 24564, 36`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 13:58:17 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CubesAndBlocksInBinTask_randomize_external_camera_0: 'Put all the cubes and blocks in the bin' (run 0, 1 envs)`
- episode 进度：`30/60`
- 产物计数：variant_dirs=`31`，HDF5=`31`，MP4=`62`，subtask_logs=`30`
- step 进度：`{'percent': 82, 'step': 2965, 'total_steps': 3600, 'elapsed': '13:54', 'eta': '03:16'}`
- GPU：`2026/06/21 13:58:17.026, 47, 107.81, 17456, 24564, 21`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 14:03:17 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CubesAndBlocksInBinTask_randomize_wrist_cam_0: 'Put all the cubes and blocks in the bin' (run 0, 1 envs)`
- episode 进度：`31/60`
- 产物计数：variant_dirs=`32`，HDF5=`32`，MP4=`64`，subtask_logs=`31`
- step 进度：`{'percent': 11, 'step': 389, 'total_steps': 3600, 'elapsed': '01:51', 'eta': '13:58'}`
- GPU：`2026/06/21 14:03:17.355, 47, 106.50, 17458, 24564, 63`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 14:08:17 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CubesAndBlocksInBinTask_randomize_wrist_cam_0: 'Put all the cubes and blocks in the bin' (run 0, 1 envs)`
- episode 进度：`31/60`
- 产物计数：variant_dirs=`32`，HDF5=`32`，MP4=`64`，subtask_logs=`31`
- step 进度：`{'percent': 40, 'step': 1451, 'total_steps': 3600, 'elapsed': '06:52', 'eta': '10:54'}`
- GPU：`2026/06/21 14:08:17.678, 47, 107.17, 17458, 24564, 42`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 14:13:18 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CubesAndBlocksInBinTask_randomize_wrist_and_external_cam_0: 'Put all the cubes and blocks in the bin' (run 0, 1 envs)`
- episode 进度：`32/60`
- 产物计数：variant_dirs=`33`，HDF5=`33`，MP4=`66`，subtask_logs=`32`
- step 进度：`{'percent': 20, 'step': 736, 'total_steps': 3600, 'elapsed': '03:26', 'eta': '13:43'}`
- GPU：`2026/06/21 14:13:17.994, 48, 119.87, 17456, 24564, 29`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 14:18:18 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CubesAndBlocksInBinTask_randomize_wrist_and_external_cam_0: 'Put all the cubes and blocks in the bin' (run 0, 1 envs)`
- episode 进度：`32/60`
- 产物计数：variant_dirs=`33`，HDF5=`33`，MP4=`66`，subtask_logs=`32`
- step 进度：`{'percent': 50, 'step': 1801, 'total_steps': 3600, 'elapsed': '08:26', 'eta': '08:58'}`
- GPU：`2026/06/21 14:18:18.319, 49, 122.73, 17456, 24564, 68`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 14:23:18 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CubesAndBlocksInBinTask_randomize_wrist_and_external_cam_0: 'Put all the cubes and blocks in the bin' (run 0, 1 envs)`
- episode 进度：`32/60`
- 产物计数：variant_dirs=`33`，HDF5=`33`，MP4=`66`，subtask_logs=`32`
- step 进度：`{'percent': 79, 'step': 2852, 'total_steps': 3600, 'elapsed': '13:26', 'eta': '03:36'}`
- GPU：`2026/06/21 14:23:18.638, 47, 122.63, 17458, 24564, 75`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 14:28:18 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CookingClearPlateTask_randomize_external_camera_0: 'Put the two measuring cups outside of the plate' (run 0, 1 envs)`
- episode 进度：`33/60`
- 产物计数：variant_dirs=`34`，HDF5=`34`，MP4=`68`，subtask_logs=`33`
- step 进度：`{'percent': 8, 'step': 206, 'total_steps': 2700, 'elapsed': '01:13', 'eta': '13:28'}`
- GPU：`2026/06/21 14:28:18.955, 47, 107.45, 17106, 24564, 52`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 14:33:19 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CookingClearPlateTask_randomize_wrist_cam_0: 'Put the two measuring cups outside of the plate' (run 0, 1 envs)`
- episode 进度：`34/60`
- 产物计数：variant_dirs=`35`，HDF5=`35`，MP4=`70`，subtask_logs=`34`
- step 进度：`{'percent': 13, 'step': 361, 'total_steps': 2700, 'elapsed': '02:06', 'eta': '14:44'}`
- GPU：`2026/06/21 14:33:19.281, 48, 122.23, 17106, 24564, 61`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 14:38:19 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running ToolsPickingHammerTask_randomize_external_camera_0: 'Select the blue hammer and put it on the table' (run 0, 1 envs)`
- episode 进度：`36/60`
- 产物计数：variant_dirs=`37`，HDF5=`37`，MP4=`74`，subtask_logs=`36`
- step 进度：`{'percent': 28, 'step': 255, 'total_steps': 900, 'elapsed': '01:08', 'eta': '02:50'}`
- GPU：`2026/06/21 14:38:19.609, 48, 121.05, 17250, 24564, 62`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 14:43:19 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running ToolsPickingHammerTask_randomize_wrist_cam_0: 'Select the blue hammer and put it on the table' (run 0, 1 envs)`
- episode 进度：`37/60`
- 产物计数：variant_dirs=`38`，HDF5=`38`，MP4=`76`，subtask_logs=`37`
- step 进度：`{'percent': 49, 'step': 444, 'total_steps': 900, 'elapsed': '02:03', 'eta': '02:07'}`
- GPU：`2026/06/21 14:43:19.935, 48, 107.14, 17250, 24564, 65`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 14:48:20 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running ToolsPickingHammerTask_randomize_wrist_and_external_cam_0: 'Select the blue hammer and put it on the table' (run 0, 1 envs)`
- episode 进度：`38/60`
- 产物计数：variant_dirs=`39`，HDF5=`39`，MP4=`78`，subtask_logs=`38`
- step 进度：`{'percent': 72, 'step': 649, 'total_steps': 900, 'elapsed': '02:54', 'eta': '01:08'}`
- GPU：`2026/06/21 14:48:20.255, 48, 108.58, 17250, 24564, 27`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 14:53:20 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running AnimalsInBinTask_randomize_external_camera_0: 'Put the lizards in the bin' (run 0, 1 envs)`
- episode 进度：`39/60`
- 产物计数：variant_dirs=`40`，HDF5=`40`，MP4=`80`，subtask_logs=`39`
- step 进度：`{'percent': 58, 'step': 789, 'total_steps': 1350, 'elapsed': '03:42', 'eta': '02:52'}`
- GPU：`2026/06/21 14:53:20.586, 48, 107.57, 17458, 24564, 58`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 14:58:20 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running AnimalsInBinTask_randomize_wrist_cam_0: 'Put the lizards in the bin' (run 0, 1 envs)`
- episode 进度：`40/60`
- 产物计数：variant_dirs=`41`，HDF5=`41`，MP4=`82`，subtask_logs=`40`
- step 进度：`{'percent': 36, 'step': 491, 'total_steps': 1350, 'elapsed': '02:19', 'eta': '04:16'}`
- GPU：`2026/06/21 14:58:20.907, 48, 107.42, 17458, 24564, 65`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 15:03:21 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running AnimalsInBinTask_randomize_wrist_and_external_cam_0: 'Put the lizards in the bin' (run 0, 1 envs)`
- episode 进度：`41/60`
- 产物计数：variant_dirs=`42`，HDF5=`42`，MP4=`84`，subtask_logs=`41`
- step 进度：`{'percent': 11, 'step': 150, 'total_steps': 1350, 'elapsed': '00:42', 'eta': '06:05'}`
- GPU：`2026/06/21 15:03:21.225, 48, 121.51, 17456, 24564, 73`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 15:08:21 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running AnimalsInBinTask_randomize_wrist_and_external_cam_0: 'Put the lizards in the bin' (run 0, 1 envs)`
- episode 进度：`41/60`
- 产物计数：variant_dirs=`42`，HDF5=`42`，MP4=`84`，subtask_logs=`41`
- step 进度：`{'percent': 91, 'step': 1228, 'total_steps': 1350, 'elapsed': '05:42', 'eta': '00:34'}`
- GPU：`2026/06/21 15:08:21.545, 47, 107.87, 17456, 24564, 42`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 15:13:21 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running BlackItemsInBinTask_randomize_external_camera_0: 'Put the black items in the grey bin' (run 0, 1 envs)`
- episode 进度：`45/60`
- 产物计数：variant_dirs=`46`，HDF5=`46`，MP4=`92`，subtask_logs=`45`
- step 进度：`{'percent': 17, 'step': 305, 'total_steps': 1800, 'elapsed': '01:41', 'eta': '08:47'}`
- GPU：`2026/06/21 15:13:21.878, 47, 108.48, 17122, 24564, 65`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 15:18:22 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running BlackItemsInBinTask_randomize_external_camera_0: 'Put the black items in the grey bin' (run 0, 1 envs)`
- episode 进度：`45/60`
- 产物计数：variant_dirs=`46`，HDF5=`46`，MP4=`92`，subtask_logs=`45`
- step 进度：`{'percent': 67, 'step': 1208, 'total_steps': 1800, 'elapsed': '06:41', 'eta': '03:18'}`
- GPU：`2026/06/21 15:18:22.215, 47, 107.83, 17122, 24564, 29`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 15:23:22 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running BlackItemsInBinTask_randomize_wrist_cam_0: 'Put the black items in the grey bin' (run 0, 1 envs)`
- episode 进度：`46/60`
- 产物计数：variant_dirs=`47`，HDF5=`47`，MP4=`94`，subtask_logs=`46`
- step 进度：`{'percent': 16, 'step': 297, 'total_steps': 1800, 'elapsed': '01:34', 'eta': '08:16'}`
- GPU：`2026/06/21 15:23:22.554, 48, 107.82, 17122, 24564, 65`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 15:28:22 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running BlackItemsInBinTask_randomize_wrist_cam_0: 'Put the black items in the grey bin' (run 0, 1 envs)`
- episode 进度：`46/60`
- 产物计数：variant_dirs=`47`，HDF5=`47`，MP4=`94`，subtask_logs=`46`
- step 进度：`{'percent': 66, 'step': 1196, 'total_steps': 1800, 'elapsed': '06:34', 'eta': '03:25'}`
- GPU：`2026/06/21 15:28:22.886, 48, 108.67, 17122, 24564, 24`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 15:33:23 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running BlackItemsInBinTask_randomize_wrist_and_external_cam_0: 'Put the black items in the grey bin' (run 0, 1 envs)`
- episode 进度：`47/60`
- 产物计数：variant_dirs=`48`，HDF5=`48`，MP4=`96`，subtask_logs=`47`
- step 进度：`{'percent': 16, 'step': 295, 'total_steps': 1800, 'elapsed': '01:34', 'eta': '08:48'}`
- GPU：`2026/06/21 15:33:23.198, 48, 107.58, 17132, 24564, 69`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 15:38:23 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running BlackItemsInBinTask_randomize_wrist_and_external_cam_0: 'Put the black items in the grey bin' (run 0, 1 envs)`
- episode 进度：`47/60`
- 产物计数：variant_dirs=`48`，HDF5=`48`，MP4=`96`，subtask_logs=`47`
- step 进度：`{'percent': 67, 'step': 1214, 'total_steps': 1800, 'elapsed': '06:34', 'eta': '03:19'}`
- GPU：`2026/06/21 15:38:23.527, 48, 107.29, 17132, 24564, 61`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 15:43:23 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running BagelsOnPlateTask_randomize_external_camera_0: 'Put the bagels on the plate' (run 0, 1 envs)`
- episode 进度：`48/60`
- 产物计数：variant_dirs=`49`，HDF5=`49`，MP4=`98`，subtask_logs=`48`
- step 进度：`{'percent': 49, 'step': 437, 'total_steps': 900, 'elapsed': '01:41', 'eta': '01:55'}`
- GPU：`2026/06/21 15:43:23.849, 48, 122.71, 17214, 24564, 84`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 15:48:24 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running BagelsOnPlateTask_randomize_wrist_cam_0: 'Put the bagels on the plate' (run 0, 1 envs)`
- episode 进度：`49/60`
- 产物计数：variant_dirs=`50`，HDF5=`50`，MP4=`100`，subtask_logs=`49`
- step 进度：`{'percent': 92, 'step': 832, 'total_steps': 900, 'elapsed': '03:12', 'eta': '00:13'}`
- GPU：`2026/06/21 15:48:24.174, 48, 108.59, 17204, 24564, 42`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 15:53:24 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running BananasInBinThreeTotalTask_randomize_wrist_cam_0: 'Make sure there are 3 (three) bananas in the grey bin.' (run 0, 1 envs)`
- episode 进度：`52/60`
- 产物计数：variant_dirs=`53`，HDF5=`53`，MP4=`106`，subtask_logs=`52`
- step 进度：`{'percent': 0, 'step': 3, 'total_steps': 900, 'elapsed': '00:01', 'eta': '04:42'}`
- GPU：`2026/06/21 15:53:24.500, 48, 101.95, 17028, 24564, 62`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 15:58:24 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CleanUpToysTask_randomize_external_camera_0: 'Clean up all the smaller toys and leave the birdhouse on the table' (run 0, 1 envs)`
- episode 进度：`54/60`
- 产物计数：variant_dirs=`55`，HDF5=`55`，MP4=`110`，subtask_logs=`54`
- step 进度：`{'percent': 16, 'step': 741, 'total_steps': 4500, 'elapsed': '03:27', 'eta': '18:24'}`
- GPU：`2026/06/21 15:58:24.830, 48, 107.81, 17462, 24564, 52`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 16:03:25 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CleanUpToysTask_randomize_external_camera_0: 'Clean up all the smaller toys and leave the birdhouse on the table' (run 0, 1 envs)`
- episode 进度：`54/60`
- 产物计数：variant_dirs=`55`，HDF5=`55`，MP4=`110`，subtask_logs=`54`
- step 进度：`{'percent': 41, 'step': 1832, 'total_steps': 4500, 'elapsed': '08:27', 'eta': '12:50'}`
- GPU：`2026/06/21 16:03:25.157, 48, 123.44, 17464, 24564, 17`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 16:08:25 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CleanUpToysTask_randomize_external_camera_0: 'Clean up all the smaller toys and leave the birdhouse on the table' (run 0, 1 envs)`
- episode 进度：`54/60`
- 产物计数：variant_dirs=`55`，HDF5=`55`，MP4=`110`，subtask_logs=`54`
- step 进度：`{'percent': 65, 'step': 2927, 'total_steps': 4500, 'elapsed': '13:28', 'eta': '07:19'}`
- GPU：`2026/06/21 16:08:25.508, 48, 122.88, 17464, 24564, 63`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 16:13:25 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CleanUpToysTask_randomize_external_camera_0: 'Clean up all the smaller toys and leave the birdhouse on the table' (run 0, 1 envs)`
- episode 进度：`54/60`
- 产物计数：variant_dirs=`55`，HDF5=`55`，MP4=`110`，subtask_logs=`54`
- step 进度：`{'percent': 89, 'step': 4015, 'total_steps': 4500, 'elapsed': '18:28', 'eta': '02:07'}`
- GPU：`2026/06/21 16:13:25.831, 47, 107.51, 17462, 24564, 60`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 16:18:26 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CleanUpToysTask_randomize_wrist_cam_0: 'Clean up all the smaller toys and leave the birdhouse on the table' (run 0, 1 envs)`
- episode 进度：`55/60`
- 产物计数：variant_dirs=`56`，HDF5=`56`，MP4=`112`，subtask_logs=`55`
- step 进度：`{'percent': 12, 'step': 548, 'total_steps': 4500, 'elapsed': '02:34', 'eta': '19:55'}`
- GPU：`2026/06/21 16:18:26.166, 47, 106.83, 17462, 24564, 47`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 16:23:26 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CleanUpToysTask_randomize_wrist_cam_0: 'Clean up all the smaller toys and leave the birdhouse on the table' (run 0, 1 envs)`
- episode 进度：`55/60`
- 产物计数：variant_dirs=`56`，HDF5=`56`，MP4=`112`，subtask_logs=`55`
- step 进度：`{'percent': 36, 'step': 1623, 'total_steps': 4500, 'elapsed': '07:35', 'eta': '13:06'}`
- GPU：`2026/06/21 16:23:26.492, 48, 122.32, 17462, 24564, 56`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 16:28:26 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CleanUpToysTask_randomize_wrist_cam_0: 'Clean up all the smaller toys and leave the birdhouse on the table' (run 0, 1 envs)`
- episode 进度：`55/60`
- 产物计数：variant_dirs=`56`，HDF5=`56`，MP4=`112`，subtask_logs=`55`
- step 进度：`{'percent': 60, 'step': 2700, 'total_steps': 4500, 'elapsed': '12:35', 'eta': '07:58'}`
- GPU：`2026/06/21 16:28:26.830, 47, 122.90, 17462, 24564, 30`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 16:33:27 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CleanUpToysTask_randomize_wrist_cam_0: 'Clean up all the smaller toys and leave the birdhouse on the table' (run 0, 1 envs)`
- episode 进度：`55/60`
- 产物计数：variant_dirs=`56`，HDF5=`56`，MP4=`112`，subtask_logs=`55`
- step 进度：`{'percent': 84, 'step': 3787, 'total_steps': 4500, 'elapsed': '17:35', 'eta': '03:41'}`
- GPU：`2026/06/21 16:33:27.151, 47, 107.32, 17462, 24564, 66`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 16:38:27 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CleanUpToysTask_randomize_wrist_and_external_cam_0: 'Clean up all the smaller toys and leave the birdhouse on the table' (run 0, 1 envs)`
- episode 进度：`56/60`
- 产物计数：variant_dirs=`57`，HDF5=`57`，MP4=`114`，subtask_logs=`56`
- step 进度：`{'percent': 8, 'step': 341, 'total_steps': 4500, 'elapsed': '01:33', 'eta': '18:40'}`
- GPU：`2026/06/21 16:38:27.480, 47, 106.98, 17464, 24564, 32`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 16:43:27 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CleanUpToysTask_randomize_wrist_and_external_cam_0: 'Clean up all the smaller toys and leave the birdhouse on the table' (run 0, 1 envs)`
- episode 进度：`56/60`
- 产物计数：variant_dirs=`57`，HDF5=`57`，MP4=`114`，subtask_logs=`56`
- step 进度：`{'percent': 31, 'step': 1401, 'total_steps': 4500, 'elapsed': '06:33', 'eta': '14:58'}`
- GPU：`2026/06/21 16:43:27.812, 48, 106.41, 17464, 24564, 66`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 16:48:28 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CleanUpToysTask_randomize_wrist_and_external_cam_0: 'Clean up all the smaller toys and leave the birdhouse on the table' (run 0, 1 envs)`
- episode 进度：`56/60`
- 产物计数：variant_dirs=`57`，HDF5=`57`，MP4=`114`，subtask_logs=`56`
- step 进度：`{'percent': 55, 'step': 2462, 'total_steps': 4500, 'elapsed': '11:34', 'eta': '09:29'}`
- GPU：`2026/06/21 16:48:28.143, 48, 120.88, 17464, 24564, 58`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 16:53:28 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running CleanUpToysTask_randomize_wrist_and_external_cam_0: 'Clean up all the smaller toys and leave the birdhouse on the table' (run 0, 1 envs)`
- episode 进度：`56/60`
- 产物计数：variant_dirs=`57`，HDF5=`57`，MP4=`114`，subtask_logs=`56`
- step 进度：`{'percent': 79, 'step': 3547, 'total_steps': 4500, 'elapsed': '16:34', 'eta': '04:15'}`
- GPU：`2026/06/21 16:53:28.476, 48, 108.01, 17462, 24564, 60`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 16:58:28 - 相机角度扰动运行中

- 阶段 ID：`04_camera_angle_20`
- 状态：`running_progress`
- 当前运行：`[RoboLab] Running BananaInBowlTask_randomize_external_camera_0: 'Pick up the banana and place it in the bowl' (run 0, 1 envs)`
- episode 进度：`57/60`
- 产物计数：variant_dirs=`58`，HDF5=`58`，MP4=`116`，subtask_logs=`57`
- step 进度：`{'percent': 21, 'step': 158, 'total_steps': 750, 'elapsed': '00:33', 'eta': '02:13'}`
- GPU：`2026/06/21 16:58:28.800, 47, 107.81, 17142, 24564, 27`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`

## 2026-06-21 17:03:29 - 相机角度扰动完成

- 阶段 ID：`04_camera_angle_20`
- 状态：`completed`
- episode：`60/60`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_camera_angle_camera_pose_variation`


## 2026-06-21 17:03:29 - 取消腕部相机/腕部黑屏 20 任务

- 阶段 ID：`05_wrist_blackout_20`
- 状态：`running`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_wrist_blackout_wrist_blackout`


## 2026-06-21 17:03:29 - 腕部相机取消结果

- 阶段 ID：`05_wrist_blackout_20`
- 状态：`failed_or_blocked`
- returncode：`127`
- episode：`0/20`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_wrist_blackout_wrist_blackout`


## 2026-06-21 17:03:29 - 机器人基座偏移 20 任务

- 阶段 ID：`06_robot_base_shift_20`
- 状态：`running`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robot_base_shift`
- 偏移：x=0.03m, y=0.00m


## 2026-06-21 17:03:30 - 机器人基座偏移结果

- 阶段 ID：`06_robot_base_shift_20`
- 状态：`failed_or_blocked`
- returncode：`1`
- episode：`0/20`
- 输出：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_robot_base_shift`


## 2026-06-21 17:03:30 - 其他模型对照记录

- 阶段 ID：`07_other_models_probe`
- 状态：`completed`
- 说明：Pi05 使用真实 20 任务结果；RoboChallenge pi、ReKep、PaliGemma、GR00T、Cosmos、阿里/Qwen 系列按当前本地可运行性写入 adapter/probe，不伪装成真实 RoboLab 成功率。
- 输出：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_other_models_probe_summary.json`


## 2026-06-21 17:03:30 - 接力队列到达终态

- 状态：`completed`
- 状态 JSONL：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_status.jsonl`
- 日志：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/roboplay_companion_20260621_074050/resume_supervisor.log`

<!-- ROBOPLAY_COMPANION_FINAL_SUMMARY_START -->

## 2026-06-21 22:05 - 最终核验与重试补录

> 重要说明：上方日志里 `05_wrist_blackout_20` 和 `06_robot_base_shift_20` 的 `failed_or_blocked`
> 是第一次尝试的失败记录。后续已完成 retry：`05_wrist_blackout_20_retry` 与
> `06_robot_base_shift_20_retry2`，下面表格是以最终 retry 产物为准的核验结果。

### 总结果

| 实验 | episode rows | successes | success rate | HDF5 | MP4 | subtask logs | summary |
|---|---:|---:|---:|---:|---:|---:|---|
| Pi05 RoboLab-120 | 120 | 34 | 28.3% | - | - | - | `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_read_results_summary.json` |
| Pi05 20-task baseline | 20 | 5 | 25.0% | - | - | - | `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_pi05_baseline_read_results_summary.json` |
| Camera angle variants | 60 | 15 | 25.0% | 60 | 120 | 60 | `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_camera_angle_read_results_summary.json` |
| Wrist camera blackout | 20 | 1 | 5.0% | 20 | 40 | 20 | `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_wrist_blackout_read_results_summary.json` |
| Robot base shift | 20 | 6 | 30.0% | 20 | 40 | 20 | `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_robot_base_shift_read_results_summary.json` |
| Companion combined | 120 | 27 | 22.5% | - | - | - | `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_combined120_read_results_summary.json` |

### 分组统计表

- 120 任务：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_read_results_by_axis.csv`，`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_read_results_by_difficulty.csv`，`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/robolab120_pi05_full_assetsfixed_20260620_170411_read_results_by_task_length.csv`
- Pi05 20 基线：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_pi05_baseline_read_results_by_axis.csv`，`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_pi05_baseline_read_results_by_difficulty.csv`，`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_pi05_baseline_read_results_by_task_length.csv`
- 相机角度：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_camera_angle_read_results_by_axis.csv`，`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_camera_angle_read_results_by_difficulty.csv`，`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_camera_angle_read_results_by_task_length.csv`
- 取消腕部相机：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_wrist_blackout_read_results_by_axis.csv`，`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_wrist_blackout_read_results_by_difficulty.csv`，`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_wrist_blackout_read_results_by_task_length.csv`
- 机器人基座偏移：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_robot_base_shift_read_results_by_axis.csv`，`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_robot_base_shift_read_results_by_difficulty.csv`，`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_robot_base_shift_read_results_by_task_length.csv`

### 机器人基座偏移 20 任务逐条记录

| task | result | steps | reason |
|---|---|---:|---|
| FoodPackingByColorTask | fail | 1800 | Condition not satisfied: object_grabbed(object=mustard) (step 1/2) |
| NonHammerToolsInRightBinTask | fail | 2700 | Conditions not satisfied: object_grabbed(object=cordless_drill) (step 1/2); object_grabbed(object=spring_clamp) (step 1/ |
| CookingPickPastaToolTask | fail | 900 | Condition not satisfied: object_grabbed(object=pink_spaghetti_spoon) (step 1/2) |
| ReorientJugTask | fail | 900 | Condition not satisfied: object_grabbed(object=utilityjug_a02) (step 1/2) |
| YellowAndWhiteObjectsInBinTask | fail | 900 | Conditions not satisfied: object_grabbed(object=mug) (step 1/2); object_grabbed(object=banana) (step 1/2) |
| BlockStackingSpecifiedOrderTask | fail | 1350 | Condition not satisfied: stacked(objects=['red_block', 'blue_block'], order=bottom_to_top) (step 1/1) |
| ClampInRightBinTask | fail | 900 | Condition not satisfied: object_grabbed(object=spring_clamp) (step 1/2) |
| PutMugsOnShelfTask | fail | 2700 | Condition not satisfied: object_grabbed(object=mug) (step 1/2) |
| PlasticBottlesInSquarePailTask | success | 1548 | Completed subtask 'pick_and_place' 1/1 |
| ToolsPickingDrillTask | fail | 900 | Condition not satisfied: object_grabbed(object=cordless_drill) (step 1/2) |
| CubesAndBlocksInBinTask | success | 2912 | Completed subtask 'pick_and_place' 2/2 |
| CookingClearPlateTask | success | 497 | success: object_grabbed(object=spoon_1). advanced 1 step(s) to step 1 for spoon_1. |
| ToolsPickingHammerTask | fail | 900 | Condition not satisfied: object_grabbed(object=blue_hammer) (step 1/2) |
| AnimalsInBinTask | fail | 1350 | Condition not satisfied: object_in_container(object=lizard_figurine_01, container=grey_bin, require_contact_with=False,  |
| BananasInBinOneMoreTask | success | 211 | Completed subtask 'pick_and_place' 1/1 |
| BlackItemsInBinTask | fail | 1800 | Conditions not satisfied: object_grabbed(object=remote_control) (step 1/2); object_grabbed(object=computer_mouse) (step  |
| BagelsOnPlateTask | fail | 900 | Conditions not satisfied: object_grabbed(object=bagel_00) (step 1/2); object_grabbed(object=bagel_06) (step 1/2) |
| BananasInBinThreeTotalTask | success | 115 | Completed subtask 'pick_and_place' 1/1 |
| CleanUpToysTask | fail | 4500 | Conditions not satisfied: object_grabbed(object=rubiks_cube) (step 1/2); object_grabbed(object=rubiks_cube_1) (step 1/2) |
| BananaInBowlTask | success | 421 | Completed subtask 'pick_and_place' 1/1 |

### 当前边界

- RoboChallenge pi、ReKep、GR00T、PaliGemma、Cosmos、阿里/Qwen 目前已有 probe/adapter-required 记录，但还不是 RoboLab action-policy 真实 20 任务 rollout。
- 真实对照需要补齐 `observation -> action` 适配器：接收 RoboLab 多相机观测和语言指令，输出 Franka/Robotiq 控制动作，并接入同一套 `episode_results.jsonl + HDF5 + video + subtask log` 记录链路。
- 以上边界已写入 `robolab_repro_artifacts/roboplay_companion_20260621_074050_other_models_probe_summary.json`，后续不能把 probe 结果当成功率对比。

<!-- ROBOPLAY_COMPANION_FINAL_SUMMARY_END -->

## 2026-06-22 01:56:15 CST - Pi05 base/DROID 20 任务完整闭环结果与模型下载进展

### 结论

- 队列：`roboplay_companion_20260621_074050_pi05_base_droid20`。
- 状态：20/20 任务完整运行，队列 `EXIT_CODE=0`。
- 成功率：`0/20 = 0.00%`。
- 解释边界：这是 `pi05_base` checkpoint 通过 DROID/RoboLab adapter 的弱对照，不是 RoboLab 官方调优后的 Pi05 策略；结果证明闭环可执行和证据链完整，但策略能力与 RoboLab 任务不匹配。
- 产物核验：episode_results `20`、HDF5 `20`、视频 `40`、子任务日志 `20`、artifact check `20/20`。

### 关键文件

- Manifest：`robolab_repro_artifacts/roboplay_companion_20260621_074050_pi05_base_droid20_task_run_manifest.jsonl`
- Summary：`robolab_repro_artifacts/roboplay_companion_20260621_074050_pi05_base_droid20_read_results/roboplay_companion_20260621_074050_pi05_base_droid20_summary.json`
- 按能力轴：`robolab_repro_artifacts/roboplay_companion_20260621_074050_pi05_base_droid20_read_results/roboplay_companion_20260621_074050_pi05_base_droid20_by_axis.csv`
- 按难度：`robolab_repro_artifacts/roboplay_companion_20260621_074050_pi05_base_droid20_read_results/roboplay_companion_20260621_074050_pi05_base_droid20_by_difficulty.csv`
- 按任务：`robolab_repro_artifacts/roboplay_companion_20260621_074050_pi05_base_droid20_read_results/roboplay_companion_20260621_074050_pi05_base_droid20_by_task.csv`
- 产物清单：`robolab_repro_artifacts/roboplay_companion_20260621_074050_pi05_base_droid20_artifact_inventory.json`
- 子任务日志索引：`robolab_repro_artifacts/roboplay_companion_20260621_074050_pi05_base_droid20_subtask_log_index.jsonl`

### 按能力轴汇总

|axis|episodes|successes|success_rate|score_mean|policy_inference_avg_ms_mean|
|---|---|---|---|---|---|
|procedural|10|0|0.0|0.020000000298023225|11.68|
|relational|11|0|0.0|0.09090909090909091|11.681818181818182|
|visual|18|0|0.0|0.06666666683223513|11.71111111111111|

### 按难度汇总

|difficulty|episodes|successes|success_rate|score_mean|episode_step_mean|
|---|---|---|---|---|---|
|complex|5|0|0.0|0.04000000059604645|2790.0|
|moderate|7|0|0.0|0.0|1800.0|
|simple|8|0|0.0|0.125|937.5|

### 逐任务失败原因摘要

|task_name|success_rate|score_mean|episode_step_mean|reason|
|---|---|---|---|---|
|AnimalsInBinTask|0.0|0.0|1350.0|Conditions not satisfied: object_grabbed(object=lizard_figurine) (step 1/2); object_grabbed(object=lizard_figurine_01) (step 1/2)|
|BagelsOnPlateTask|0.0|0.0|900.0|Conditions not satisfied: object_grabbed(object=bagel_00) (step 1/2); object_grabbed(object=bagel_06) (step 1/2)|
|BananaInBowlTask|0.0|0.0|750.0|Condition not satisfied: object_grabbed(object=banana) (step 1/2)|
|BananasInBinOneMoreTask|0.0|0.0|900.0|Only 0/1 objects completed. Failed: object_grabbed(object=banana) (step 1/2)|
|BananasInBinThreeTotalTask|0.0|0.0|900.0|Only 0/1 objects completed. Failed: object_grabbed(object=banana) (step 1/2)|
|BlackItemsInBinTask|0.0|0.20000000298023224|1800.0|Conditions not satisfied: object_grabbed(object=remote_control) (step 1/2); object_grabbed(object=computer_mouse) (step 1/2); object_grab...|
|BlockStackingSpecifiedOrderTask|0.0|0.0|1350.0|Condition not satisfied: stacked(objects=['red_block', 'blue_block'], order=bottom_to_top) (step 1/1)|
|ClampInRightBinTask|0.0|0.0|900.0|Condition not satisfied: object_grabbed(object=spring_clamp) (step 1/2)|
|CleanUpToysTask|0.0|0.0|4500.0|Conditions not satisfied: object_grabbed(object=rubiks_cube) (step 1/2); object_grabbed(object=rubiks_cube_1) (step 1/2); object_grabbed(...|
|CookingClearPlateTask|0.0|0.0|2700.0|Conditions not satisfied: object_grabbed(object=spoon_1) (step 1/2); object_grabbed(object=measuring_cups_1) (step 1/2)|
|CookingPickPastaToolTask|0.0|0.0|900.0|Condition not satisfied: object_grabbed(object=pink_spaghetti_spoon) (step 1/2)|
|CubesAndBlocksInBinTask|0.0|0.0|3600.0|Conditions not satisfied: object_grabbed(object=rubiks_cube) (step 1/2); object_grabbed(object=rubiks_cube_1) (step 1/2); object_grabbed(...|
|FoodPackingByColorTask|0.0|0.0|1800.0|Condition not satisfied: object_grabbed(object=mustard) (step 1/2)|
|NonHammerToolsInRightBinTask|0.0|0.0|2700.0|Conditions not satisfied: object_grabbed(object=cordless_drill) (step 1/2); object_grabbed(object=spring_clamp) (step 1/2)|
|PlasticBottlesInSquarePailTask|0.0|0.0|2700.0|Conditions not satisfied: object_grabbed(object=whitepackerbottle_a01) (step 1/2); object_grabbed(object=whitepackerbottle_a02) (step 1/2...|
|PutMugsOnShelfTask|0.0|0.0|2700.0|Conditions not satisfied: object_grabbed(object=ceramic_mug) (step 1/2); object_grabbed(object=mug) (step 1/2)|
|ReorientJugTask|0.0|0.0|900.0|Condition not satisfied: object_upright(object=utilityjug_a02, require_gripper_detached=True) (step 2/2)|
|ToolsPickingDrillTask|0.0|0.0|900.0|Condition not satisfied: object_grabbed(object=cordless_drill) (step 1/2)|
|ToolsPickingHammerTask|0.0|1.0|900.0|Condition not satisfied: object_grabbed(object=blue_hammer) (step 1/2)|
|YellowAndWhiteObjectsInBinTask|0.0|0.0|900.0|Conditions not satisfied: object_grabbed(object=mug) (step 1/2); object_grabbed(object=banana) (step 1/2)|

### GR00T / Cosmos3 准备进展

- 4090 上已启动 `mihomo`，代理监听：`127.0.0.1:7897`。
- Hugging Face 通过代理可访问；`nvidia/GR00T-N1.6-DROID` 与 `nvidia/Cosmos3-Nano-Policy-DROID` 均为 public、非 gated。
- Cosmos 本地环境已补齐：`cosmos_framework`、`openpi_client`、`openpi_server`、`transformers_cosmos3` 都可导入。
- 下载已后台启动：`tmux` session `hf_dl_gr00t_droid`、`hf_dl_cosmos3_droid`。当前阶段只下载 checkpoint，不启动模型 server，避免抢 Pi05 实验 GPU。

## 2026-06-22 02:45:11 CST - GR00T DROID smoke 证据补齐

> 结论标识：这是 **GR00T eager/no-flash fallback smoke**，用于确认 server、policy wrapper、RoboLab 环境、视频/HDF5/episode 记录链路能跑通；由于本机 CUDA 11.5 与 `flash-attn` 构建要求不匹配，本轮不是官方 GR00T 性能复现。

| 项目 | 结果 |
|---|---:|
| 任务 | `BananaInBowlTask` |
| policy | `gr00t` / `OXE_DROID` server |
| success | `False` |
| score | `0.0` |
| episode_step | `750` |
| policy inference avg | `18.8 ms` |
| 失败原因 | `Condition not satisfied: object_grabbed(object=banana) (step 1/2)` |
| 视频 | `2 个` |
| HDF5 | `1 个` |
| 子任务日志 | `1 个` |
| artifact check | `1/1` |

关键文件：

- inventory: `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_gr00t_smoke_BananaInBowlTask_artifact_inventory.json`
- output root: `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_gr00t_smoke_BananaInBowlTask`
- episode_results: `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_gr00t_smoke_BananaInBowlTask/episode_results.jsonl`
- subtask_log: `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_gr00t_smoke_BananaInBowlTask_subtask_log.json`

下一步执行顺序保持为：Cosmos3 checkpoint 下载完成后再启动 Cosmos server；GR00T 若扩到 20 任务，必须在表格中单独标为 `eager/no-flash fallback`，不能和论文官方 baseline 混排。

## 2026-06-22 04:10:05 CST - GR00T 20 半程状态与 Cosmos3 checkpoint 完成

| 项目 | 当前状态 |
|---|---:|
| GR00T 20 已完成任务 | 10/20 |
| GR00T 20 成功任务 | 0 |
| 已完成任务 artifact 校验 | 10/10 |
| 当前标签 | `gr00t_eager_noflash_fallback` |
| Cosmos3 checkpoint | 42/42 文件完成，缺失 0，snapshot 约 30.68GB，cache 约 39GB |

说明：GR00T 这组仍然标记为 **eager/no-flash fallback**。它解决的是本机 `flash-attn`/CUDA 版本不匹配时的可运行对照问题，不能作为论文官方 GR00T 分数直接引用。当前前 10 条全部完成闭环运行、视频/HDF5/episode/校验文件落盘，但成功率为 0/10，主要失败集中在第一阶段抓取条件未满足。

关键路径：

- GR00T 20 manifest: `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_gr00t20_eager_task_run_manifest.jsonl`
- GR00T 20 log: `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/roboplay_companion_20260621_074050_gr00t20_eager_retry_20260622_025039.log`
- Cosmos3 snapshot: `/home/yjl/.cache/huggingface/hub/models--nvidia--Cosmos3-Nano-Policy-DROID/snapshots/93d045d11280f2f6ceff57d851f00dbfa236c851`

已完成任务概览：

| # | task | success | score | 失败摘要 |
|---:|---|---:|---:|---|
| 1 | `FoodPackingByColorTask` | False | 0.0 | Condition not satisfied: object_grabbed(object=mustard) (step 1/2) |
| 2 | `NonHammerToolsInRightBinTask` | False | 0.0 | Conditions not satisfied: object_grabbed(object=cordless_drill) (step 1/2); object_grabbed(object=spring_clamp) (step 1/ |
| 3 | `CookingPickPastaToolTask` | False | 0.0 | Condition not satisfied: object_grabbed(object=pink_spaghetti_spoon) (step 1/2) |
| 4 | `ReorientJugTask` | False | 0.0 | Condition not satisfied: object_grabbed(object=utilityjug_a02) (step 1/2) |
| 5 | `YellowAndWhiteObjectsInBinTask` | False | 0.0 | Conditions not satisfied: object_grabbed(object=mug) (step 1/2); object_grabbed(object=banana) (step 1/2) |
| 6 | `BlockStackingSpecifiedOrderTask` | False | 0.0 | Condition not satisfied: stacked(objects=['red_block', 'blue_block'], order=bottom_to_top) (step 1/1) |
| 7 | `ClampInRightBinTask` | False | 0.0 | Condition not satisfied: object_grabbed(object=spring_clamp) (step 1/2) |
| 8 | `PutMugsOnShelfTask` | False | 0.0 | Conditions not satisfied: object_grabbed(object=ceramic_mug) (step 1/2); object_grabbed(object=mug) (step 1/2) |
| 9 | `PlasticBottlesInSquarePailTask` | False | 0.0 | Conditions not satisfied: object_grabbed(object=whitepackerbottle_a01) (step 1/2); object_grabbed(object=whitepackerbott |
| 10 | `ToolsPickingDrillTask` | False | 0.0 | Condition not satisfied: object_grabbed(object=cordless_drill) (step 1/2) |

## 2026-06-22 05:49:55 CST - GR00T 20 完整运行结果

> 结果标签：`gr00t_eager_noflash_fallback`。这是为绕过本机 CUDA 11.5 与 `flash-attn` 构建不匹配而做的 eager/no-flash 可运行对照；**不能等同论文官方 GR00T baseline 分数**。

| 项目 | 结果 |
|---|---:|
| 任务数 | 20 |
| episode rows | 20 |
| success | 0/20 |
| success rate | 0.00% |
| mean score | 0.0600 |
| HDF5 | 20 |
| 视频 MP4 | 40 |
| 子任务日志 | 20 |
| artifact check | 20/20 |

关键输出：

- inventory: `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_gr00t20_eager_artifact_inventory.json`
- manifest: `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_gr00t20_eager_task_run_manifest.jsonl`
- merged output: `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/roboplay_companion_20260621_074050_gr00t20_eager_merged`
- subtask index: `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_gr00t20_eager_subtask_log_index.jsonl`
- read_results tables: `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_gr00t20_eager_read_results`
- Cosmos3 checkpoint: `/home/yjl/.cache/huggingface/hub/models--nvidia--Cosmos3-Nano-Policy-DROID/snapshots/93d045d11280f2f6ceff57d851f00dbfa236c851`，42/42 文件，缺失 0

### 按能力轴 / 属性

| attribute | episodes | success_rate | score_mean |
|---|---:|---:|---:|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

### 按难度

| difficulty | episodes | success_rate | score_mean |
|---|---:|---:|---:|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

### 任务级结果

| # | task | success | score |
|---:|---|---:|---:|
| 1 | `FoodPackingByColorTask` | False | 0.0 |
| 2 | `NonHammerToolsInRightBinTask` | False | 0.0 |
| 3 | `CookingPickPastaToolTask` | False | 0.0 |
| 4 | `ReorientJugTask` | False | 0.0 |
| 5 | `YellowAndWhiteObjectsInBinTask` | False | 0.0 |
| 6 | `BlockStackingSpecifiedOrderTask` | False | 0.0 |
| 7 | `ClampInRightBinTask` | False | 0.0 |
| 8 | `PutMugsOnShelfTask` | False | 0.0 |
| 9 | `PlasticBottlesInSquarePailTask` | False | 0.0 |
| 10 | `ToolsPickingDrillTask` | False | 0.0 |
| 11 | `CubesAndBlocksInBinTask` | False | 0.0 |
| 12 | `CookingClearPlateTask` | False | 0.0 |
| 13 | `ToolsPickingHammerTask` | False | 1.0 |
| 14 | `AnimalsInBinTask` | False | 0.0 |
| 15 | `BananasInBinOneMoreTask` | False | 0.0 |
| 16 | `BlackItemsInBinTask` | False | 0.20000000298023224 |
| 17 | `BagelsOnPlateTask` | False | 0.0 |
| 18 | `BananasInBinThreeTotalTask` | False | 0.0 |
| 19 | `CleanUpToysTask` | False | 0.0 |
| 20 | `BananaInBowlTask` | False | 0.0 |

备注：`ToolsPickingHammerTask` 出现 `success=false` 但 `score=1.0`，说明 episode score/子条件进度与最终 success gate 并非完全同一指标；汇总时必须同时看 success、score 和 reason。

## 2026-06-22 06:07:14 CST - Cosmos3 RoboLab server 启动验证结果

> 结果标签：`cosmos3_nano_policy_droid_4090_oom_blocked`。这不是任务失败率；Cosmos3 在当前 RTX 4090 24GB 单卡环境中没有进入 RoboLab episode rollout，失败发生在 policy server 模型初始化阶段。

| 检查项 | 结果 |
|---|---|
| Clash 代理 | `127.0.0.1:7897` 已验证可访问 Hugging Face |
| Cosmos3 checkpoint | `/home/yjl/.cache/huggingface/hub/models--nvidia--Cosmos3-Nano-Policy-DROID/snapshots/93d045d11280f2f6ceff57d851f00dbfa236c851` |
| checkpoint 完整性 | 42/42 文件已下载，缺失 0 |
| openpi 依赖 | `openpi-client` / `openpi-server` 已安装 |
| RoboLab client | `policies/cosmos3/run.py` 存在，协议为 OpenPI WebSocket |
| server 初始 blocker | `nvidia/Cosmos-Guardrail1` gated；已用本地补丁关闭 guardrails |
| 省显存尝试 | 关闭 `use_torch_compile/compile_dynamic`，加 `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`、`CUDA_MODULE_LOADING=LAZY`、`PYTORCH_NO_CUDA_MEMORY_CACHING=1`、`TORCH_CUDNN_V8_API_LRU_CACHE_LIMIT=0` |
| 最终状态 | 仍在模型 `net.to_empty(device=CUDA)` 阶段 OOM；未生成 Cosmos episode/HDF5/video/subtask log |

关键日志：

- guardrail 权限失败：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/cosmos3_robolab_server_8000_20260622_055440.log`
- 关闭 guardrails 后 OOM：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/cosmos3_robolab_server_8000_noguardpatch_20260622_055807.log`
- 4090 省显存启动 OOM：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/cosmos3_robolab_server_8000_4090mem_20260622_060343.log`
- 关闭 CUDA cache 后 OOM：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/remote_logs/cosmos3_robolab_server_8000_nocache_20260622_060450.log`
- blocker JSON：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_cosmos3_4090_startup_blocker.json`

结论：Cosmos3-Nano-Policy-DROID 的本地 policy server 在当前 4090 24GB + 保留 VNC/桌面可视化的条件下不能完整加载。后续如果要把 Cosmos3 纳入 20 任务对照，需要切到 48GB+ 显存机器，或使用官方/社区提供的更小或量化 checkpoint；否则不能把 Cosmos3 记成“20 任务已跑”。

## 2026-06-22 06:17:15 CST - Pi/接口适配与结果深度分析补充

已新增深度分析文档：`EXPERIMENT_23_policy_interface_and_result_analysis.md`。

本补充专门回答：Pi05 tuned、Pi05 base-DROID、RoboChallenge pi、ReKep、GR00T、Cosmos、Qwen/阿里模型之间的接口差异；`step 571/900` 与 `395/2700` 的含义；adapter-required 模型如何优化成可跑 RoboLab 的 `[N,8]` Franka+Robotiq action chunk；以及当前结果为何如此、训练数据应该怎么改。

<!-- ROBOPLAY_ADAPTER_CONTRACT_UPDATE_START -->

## 2026-06-22 08:35 - Adapter 契约验证补录

- 新增文档：`EXPERIMENT_24_adapter_contract_validation.md`
- 新增硬接口契约：`robolab_repro_artifacts/adapter_contracts/franka_robotiq_jointpos_contract.json`
- 新增验证脚本：`scripts/validate_adapter_contracts.py`
- 新增验证输出：`robolab_repro_artifacts/adapter_contracts/roboplay_companion_20260621_074050_adapter_contract_validation.json`

结论：RoboChallenge/ReKep 已从“口头 adapter required”推进为可运行门禁。任何模型只有输出真实 Franka+Robotiq `[N,8]`，且不是 placeholder retarget，才允许进入 RoboLab 成功率表。

<!-- ROBOPLAY_ADAPTER_CONTRACT_UPDATE_END -->
