# 实验 23：Pi05 中等成功率任务选择与扰动实验结果

> [!NOTE]
> 这次实验承接 `EXPERIMENT_22`。目标不是重新跑完整 RoboLab-120，而是在已经跑通的 asset-ready 任务基础上，先找一个“成功率不是 0 也不是 1”的任务，再做背景、物体位置、光照扰动的链路验证。

## 结论先说

本轮在 4090 上完成了三件事：

1. **中等成功率任务选择**：对 `TakeMeasuringSpoonOutTask` 和 `RedDishesInBinTask` 各重复 3 次。
2. **有效扰动 episode**：完成了 1 条背景扰动 episode 和 1 条真正命中 `measuring_cup` 的物体位置扰动 episode，均保存了 `episode_results.jsonl`、HDF5 和视频。
3. **lighting 子项未形成有效 episode**：官方 lighting runner 在当前 checkout 中有 hard-code 背景文件和任务选择兼容问题；修掉缺失 `home_office.exr` 后能退出并生成 summary，但 `groups=0`，没有 episode rows，所以不能算作有效 lighting 评测。

> [!WARNING]
> 本节的扰动结果是 **链路验证 / smoke 级别**：每个扰动只有 1 条 episode，不足以得出稳健统计结论。论文级敏感性分析需要多 seed、多重复、多扰动强度，并用 MNPE 或至少置信区间汇总。

## 1. 中等任务 probe

输入矩阵：

- 本地：`robolab_repro_artifacts/pi05_medium_probe_tasks_20260620.json`
- 远端：`/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/pi05_medium_probe_tasks_20260620.json`

运行前缀：

- `pi05_medium_probe_20260620_101607`

结果：

| 任务 | 能力轴 | 重复数 | 成功数 | 成功率 | 平均 score | 平均步数 | 主要失败/事件 |
|---|---:|---:|---:|---:|---:|---:|---|
| `TakeMeasuringSpoonOutTask` | visual / semantics | 3 | 1 | 0.333 | 0.333 | 462.0 | `WRONG_OBJECT_GRABBED=5`, `GRIPPER_FULLY_CLOSED=6` |
| `RedDishesInBinTask` | visual / color+semantics | 3 | 0 | 0.000 | 0.333 | 900.0 | `TARGET_OBJECT_DROPPED=11`, `GRIPPER_FULLY_CLOSED=17` |

因此选 `TakeMeasuringSpoonOutTask` 做后续扰动。原因是它在 3 次重复里 1 次成功、2 次失败，比单次成功/失败更适合做扰动敏感性 probe。

## 2. 发现并修复的实验脚本问题

本轮不是“一次就跑完”的，过程中暴露了几个真实复现问题：

| 问题 | 现象 | 处理 |
|---|---|---|
| 远端没有 `python` 命令 | `run_selected_perturbations_4090.sh: line 69: python: command not found` | 脚本加入 `PYTHON_BIN="${PYTHON_BIN:-python3}"`，所有本地 helper 调用改用 `${PYTHON_BIN}` |
| object-position runner import 顺序过早 | `ModuleNotFoundError: No module named 'isaaclab.managers'` | `create_object_position_variation_runner.py` 改为先启动 `AppLauncher`，再导入 `EventTermCfg` |
| 任务矩阵提错扰动对象名 | `skip missing rigid object: taking_measuring_cup_out` | `generate_axis5_task_matrix.py` 改为只接受真实 `contact_objects` 里的对象名，否则回退到 contact list |
| lighting runner hard-code 缺失背景 | `Background file 'home_office.exr' not found` | 远端实验 checkout 临时把 lighting 注册中的 `home_office.exr` 改成已有的 `empty_warehouse.hdr` |

> [!TIP]
> 这里要区分“策略失败”和“复现实验管线失败”。`python`、`isaaclab.managers`、`home_office.exr` 都是管线/资产问题，不能算 Pi05 策略分数。

## 3. 扰动实验结果

### 3.1 背景扰动

运行前缀：

- `pi05_perturb_medium_20260620_104243_background_seed0`

结果：

| 字段 | 值 |
|---|---:|
| episodes | 1 |
| successes | 0 |
| success_rate | 0.0 |
| score_mean | 0.0 |
| episode_step_mean | 600 |
| duration_mean | 40.0s |

事件：

- `GRIPPER_FULLY_CLOSED=4`
- `WRONG_OBJECT_GRABBED=1`
- `GRIPPER_HIT_OBJECT=2`
- `OBJECT_BUMPED=1`
- `MULTIPLE_OBJECTS_GRABBED=1`

说人话：换背景后这条没有成功，跑满 600 step。由于只有 1 条样本，不能说“背景一定导致失败”，只能说这条背景扰动样本比 probe 中那次成功更差，需要增加 seed 和重复数。

### 3.2 物体位置扰动

第一次 object-position 用错对象名 `taking_measuring_cup_out`，runner 打印：

```text
[object-position-variation] skip missing rigid object: taking_measuring_cup_out
```

这条虽然产出了成功 episode，但不应该计为“有效物体位置扰动”，因为实际没有移动目标 rigid object。

修正后补跑：

- 运行前缀：`pi05_perturb_medium_fixed_20260620_105014_object_position`
- 扰动对象：`measuring_cup`
- 扰动幅度：`xy_range=0.03m`, `yaw_range=0.20rad`

| 字段 | 值 |
|---|---:|
| episodes | 1 |
| successes | 1 |
| success_rate | 1.0 |
| score_mean | 1.0 |
| episode_step_mean | 537 |
| duration_mean | 35.8s |

事件：

- `WRONG_OBJECT_GRABBED=7`
- `GRIPPER_FULLY_CLOSED=4`
- `GRIPPER_HIT_OBJECT=2`
- `MULTIPLE_OBJECTS_GRABBED=1`
- `OBJECT_BUMPED=2`

说人话：轻微移动 `measuring_cup` 后，Pi05 仍然完成了任务，但过程里错误抓取次数不少，说明成功不等于执行路径干净。后续应该把 `score/success` 和 event counts 一起看。

### 3.3 光照扰动

运行前缀：

- `pi05_perturb_medium_lighting_20260620_105533_lighting`

结果：

| 字段 | 值 |
|---|---:|
| runner exit code | 0 |
| summary groups | 0 |
| episode rows | 0 |
| 是否可计入策略评测 | 否 |

失败边界：

1. 官方 lighting 注册文件多处 hard-code `home_office.exr`，但当前背景资产目录没有该文件。
2. 改成 `empty_warehouse.hdr` 后，runner 可以结束并生成 summary，但没有产生 episode rows。
3. 因此本轮 lighting 只能记为“runner smoke 通过、有效 episode 未生成”，不能和 background/object-position 放在同一张成功率表里。

后续修法：

- 给 lighting 单独写一个 selected-task runner，不再依赖当前官方 `run_lighting.py` 的批量任务名拼接。
- 或者修官方 lighting registration 的 `task` 过滤和 `get_envs(task=...)` 命名匹配，再补跑至少 `num_runs=3`。

## 4. 证据文件

本地 summary：

- `robolab_repro_artifacts/pi05_medium_probe_20260620_101607_episode_summary.json`
- `robolab_repro_artifacts/pi05_medium_probe_20260620_101607_policy_compare.json`
- `robolab_repro_artifacts/pi05_medium_probe_20260620_101607_selected_medium_task.json`
- `robolab_repro_artifacts/pi05_perturb_medium_20260620_104243_summary.json`
- `robolab_repro_artifacts/pi05_perturb_medium_fixed_20260620_105014_summary.json`
- `robolab_repro_artifacts/pi05_perturb_medium_lighting_20260620_105533_summary.json`

远端视频 / HDF5 / episode 结果：

| 子项 | 远端路径 |
|---|---|
| background `episode_results.jsonl` | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/pi05_perturb_medium_20260620_104243_background_seed0/episode_results.jsonl` |
| background HDF5 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/pi05_perturb_medium_20260620_104243_background_seed0/TakeMeasuringSpoonOutTask/run_0.hdf5` |
| background video | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/pi05_perturb_medium_20260620_104243_background_seed0/TakeMeasuringSpoonOutTask/Take_the_white_colored_measuring_spoon_out_of_the_red_bowl_and_put_it_on_the_table_0.mp4` |
| object-position fixed `episode_results.jsonl` | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/pi05_perturb_medium_fixed_20260620_105014_object_position/episode_results.jsonl` |
| object-position fixed HDF5 | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/pi05_perturb_medium_fixed_20260620_105014_object_position/TakeMeasuringSpoonOutTask_ObjectPosition/run_0.hdf5` |
| object-position fixed video | `/home/yjl/codex_robolab_4090_20260619/RoboLab/output/pi05_perturb_medium_fixed_20260620_105014_object_position/TakeMeasuringSpoonOutTask_ObjectPosition/Take_the_white_colored_measuring_spoon_out_of_the_red_bowl_and_put_it_on_the_table_0.mp4` |

## 5. 当前能说明什么，不能说明什么

能说明：

- Pi05 server、RoboLab runner、episode logging、HDF5、视频保存、summary 聚合都能在 4090 上闭环。
- `TakeMeasuringSpoonOutTask` 是一个合适的中等成功率 probe：3 次里成功 1 次。
- 背景扰动和物体位置扰动至少能跑出可分析的完整 episode。

不能说明：

- 不能说明 background 一定降低成功率，因为只有 1 条扰动样本。
- 不能说明 object-position 一定鲁棒，因为只有 `measuring_cup` 的小幅扰动 1 次。
- 不能说明 lighting 结果，因为当前没有有效 episode rows。
- 不能把这些扰动样本和论文的完整 sensitivity analysis 直接比较。

## 6. 下一步

建议顺序：

1. 修 lighting 的 selected-task runner，让它至少产生 3 条有效 episode。
2. 对 background seeds `0/1/2` 各跑 3 次。
3. 对 object-position 扰动跑 3 个强度：`xy=0.01/0.03/0.05m`，每个强度 3 次。
4. 用 `analysis/read_results.py` 或 `scripts/summarize_ablation_outputs.py` 出同一张表：baseline probe vs background vs object-position vs lighting。
5. 再进入 RoboChallenge pi / ReKep adapter 对照，避免在 Pi05 主线未稳定前混入太多变量。
