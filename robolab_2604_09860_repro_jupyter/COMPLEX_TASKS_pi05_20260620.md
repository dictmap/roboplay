# RoboLab 复杂任务复现实测记录 - OpenPI pi05 / RTX 4090

<!-- FINAL-20260621-UPDATE:BEGIN -->

> [!TIP]
> **2026-06-21 更新**：这份文档是 full-120 之前的复杂任务抽样。最终 120 任务聚合结果已经生成：Pi05 `34/120 = 28.3%`；复杂难度任务为 `3/17 = 17.6%`，以 `CURRENT_ROBOLAB120_STATUS.md` 为准。

<!-- FINAL-20260621-UPDATE:END -->


时间：2026-06-20  
远端机器：`y12` / RTX 4090 24GB  
RoboLab 路径：`/home/yjl/codex_robolab_4090_20260619/RoboLab`  
输出目录：`/home/yjl/codex_robolab_4090_20260619/RoboLab/output/pi05_complex_assets_ok_20260620_020721`

## 这次测了什么

前一个香蕉放碗任务太简单，所以这次改测多物体、多目标或更长时序的任务：

1. `ReorientAllMugsTask`：把多个杯子全部翻正，杯口朝上。
2. `Stack3RubiksCubeTask`：把 3 个魔方堆成塔。
3. `RedItemsInBinTask`：识别所有红色物体，并全部放入灰色收纳盒。

第一次尝试还包含 `BlockStackingSpecifiedOrderTask`，但该任务在本 checkout 中触发 contact sensor / asset 初始化失败：

```text
Sensor at path '/World/envs/env_.*/scene/red_block' could not find any bodies with contact reporter API.
```

这属于环境/资产配置失败，不是策略执行失败，所以没有计入下面的策略成功率。

## 总体结果

| 任务 | 能力轴 | 指令输入 | 成功 | 步数 | 仿真时长 | 墙钟耗时 | 平均策略推理 |
|---|---|---|---:|---:|---:|---:|---:|
| `ReorientAllMugsTask` | reorientation / complex | Reorient all the mugs upright so that the opening is facing upwards. | 否 | 1350 | 90.0s | 367.913s | 13.3ms |
| `Stack3RubiksCubeTask` | stacking / moderate | Stack the rubiks cubes in a tower | 是 | 353 | 23.53s | 84.072s | 13.4ms |
| `RedItemsInBinTask` | color / sorting / moderate | Put all the red things in the grey bin | 否 | 900 | 60.0s | 220.808s | 13.3ms |

结论：这 3 个较复杂任务中，pi05 成功 1 个，失败 2 个。失败不是程序崩溃，而是策略没有在最大步数内完成任务。

## 视频核验

每个任务都保存了主视频和 viewport 视频。`ffprobe` 已确认 mp4 可读：

| 任务 | 主视频 | 主视频规格 | viewport 规格 |
|---|---|---|---|
| `ReorientAllMugsTask` | `Reorient_all_the_mugs_upright_so_that_the_opening_is_facing_upwards_0.mp4` | 1280x360, 15 FPS, 89.93s, 1349 frames | 864x480, 15 FPS, 89.93s |
| `Stack3RubiksCubeTask` | `Stack_the_rubiks_cubes_in_a_tower_0.mp4` | 1280x360, 15 FPS, 23.47s, 352 frames | 864x480, 15 FPS, 23.47s |
| `RedItemsInBinTask` | `Put_all_the_red_things_in_the_grey_bin_0.mp4` | 1280x360, 15 FPS, 59.93s, 899 frames | 864x480, 15 FPS, 59.93s |

本地同步目录：

```text
C:\Users\robot\Documents\成长学习库\robolab_2604_09860_repro_jupyter\remote_outputs\pi05_complex_assets_ok_20260620_020721
```

远端原始目录：

```text
/home/yjl/codex_robolab_4090_20260619/RoboLab/output/pi05_complex_assets_ok_20260620_020721
```

## 关键观察

`Stack3RubiksCubeTask` 成功，说明 pi05 对短时序堆叠任务有一定泛化能力；它在 353 步内完成，没有跑满上限。

`ReorientAllMugsTask` 更难，因为它要求多个杯子的姿态都满足条件，不是只抓起一个物体。它跑满 1350 步仍未成功，是这次最能暴露策略长时序/多目标控制短板的任务。

`RedItemsInBinTask` 失败点在“所有红色物体”这个集合式目标上：需要视觉颜色识别、选择多个目标、逐个搬运和确认完成。它跑满 900 步没有达成成功条件，说明这个策略在多物体排序任务上还不稳定。

## 4090 运行情况

运行过程中显存接近 4090 上限，观测到约 `22551 MiB / 24564 MiB`。这解释了为什么不能盲目把并行环境数拉高；当前复现使用 `--num-envs 1` 是合理的。

这次完整命令：

```bash
cd /home/yjl/codex_robolab_4090_20260619/RoboLab
/home/yjl/.local/bin/uv run python policies/pi0_family/run.py \
  --policy pi05 \
  --remote-host localhost \
  --remote-port 8000 \
  --task ReorientAllMugsTask Stack3RubiksCubeTask RedItemsInBinTask \
  --num-envs 1 \
  --num-runs 1 \
  --video-mode all \
  --output-folder-name pi05_complex_assets_ok_20260620_020721 \
  --headless \
  --device cuda:0
```

## 结果文件

核心结果 JSONL：

```text
C:\Users\robot\Documents\成长学习库\robolab_2604_09860_repro_jupyter\remote_outputs\pi05_complex_assets_ok_20260620_020721\episode_results.jsonl
```

远端运行日志：

```text
C:\Users\robot\Documents\成长学习库\robolab_2604_09860_repro_jupyter\remote_outputs\pi05_complex_assets_ok_20260620_020721.log
```

主视频：

```text
C:\Users\robot\Documents\成长学习库\robolab_2604_09860_repro_jupyter\remote_outputs\pi05_complex_assets_ok_20260620_020721\ReorientAllMugsTask\Reorient_all_the_mugs_upright_so_that_the_opening_is_facing_upwards_0.mp4
C:\Users\robot\Documents\成长学习库\robolab_2604_09860_repro_jupyter\remote_outputs\pi05_complex_assets_ok_20260620_020721\Stack3RubiksCubeTask\Stack_the_rubiks_cubes_in_a_tower_0.mp4
C:\Users\robot\Documents\成长学习库\robolab_2604_09860_repro_jupyter\remote_outputs\pi05_complex_assets_ok_20260620_020721\RedItemsInBinTask\Put_all_the_red_things_in_the_grey_bin_0.mp4
```

## 下一步建议

如果继续做论文级对比，下一步不要直接跑完整 120 个任务。建议先按能力轴各抽 5-10 个任务，建立 `pi05`、RoboChallenge 的 pi、ReKep 三套方法的同一任务子集对比表。等确认每类任务资产都完整、不会卡在初始化错误后，再扩大到 RoboLab-120。
