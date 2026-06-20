# 实验 22：Pi05 / asset-ready 15 任务能力轴子集真实结果

> [!NOTE]
> 这不是完整 RoboLab-120 的最终成绩，而是一次“先把可运行资产筛出来，再按能力轴覆盖”的 4090 子集实验。它比 smoke5 更接近论文评测口径：固定 Pi05，覆盖 visual / procedural / relational，每个任务都产出 episode 结果和 artifact check。

## 1. 这次为什么不直接盲跑 120 个任务

前一轮 `TASK_LIMIT=5` smoke 暴露了一个关键问题：有些任务不是 Pi05 策略失败，而是在环境初始化阶段就因为 USD 资产引用、contact sensor 或资源加载失败，没有产生可计分 episode。

所以本轮先新增了一个静态资产 preflight：

```bash
python scripts/preflight_robolab_task_assets.py \
  --matrix robolab_repro_artifacts/robolab120_task_matrix.json \
  --robolab-root /home/yjl/codex_robolab_4090_20260619/RoboLab \
  --out-json robolab_repro_artifacts/robolab120_asset_preflight_20260620_091852.json \
  --out-csv robolab_repro_artifacts/robolab120_asset_preflight_20260620_091852.csv
```

preflight 的核心作用不是证明任务一定成功，而是先过滤“场景文件本身引用不完整”的任务，避免把资产层失败误算成策略失败。

## 2. Asset preflight 结果

| 指标 | 数值 |
|---|---:|
| RoboLab-120 总任务数 | 120 |
| scene 文件缺失任务 | 0 |
| 资产引用完整任务 | 24 |
| 存在缺失引用任务 | 96 |

按能力轴看，当前本机 4090 环境中可直接跑的任务分布如下：

| 能力轴 | 总任务数 | asset-ready 任务数 |
|---|---:|---:|
| visual | 84 | 11 |
| procedural | 34 | 6 |
| relational | 42 | 13 |
| unknown_axis | 3 | 1 |

按难度看：

| 难度 | 总任务数 | asset-ready 任务数 |
|---|---:|---:|
| simple | 64 | 11 |
| moderate | 39 | 12 |
| complex | 17 | 1 |

> [!WARNING]
> `asset-ready=24/120` 不是论文 benchmark 本身的问题，而是当前这台 4090 checkout 的本地资产完整度问题。完整 RoboLab-120 仍然要补齐缺失 USD/Omni 资产后再跑，否则会混淆“环境失败”和“策略失败”。

## 3. 本轮选择的 15 个任务

选择策略：从 24 个 asset-ready 任务里抽取 15 个，确保每个能力轴至少覆盖 5 个任务。由于 RoboLab 任务是多标签的，一个任务可能同时属于 visual 和 relational。

| 序号 | 任务 | 能力轴 | 难度 |
|---:|---|---|---|
| 1 | BananaInBowlTask | visual | simple |
| 2 | PickDrillTask | visual | simple |
| 3 | TakeMeasuringSpoonOutTask | visual | simple |
| 4 | RedDishesInBinTask | visual | simple |
| 5 | BananasInBinOneMoreTask | relational, visual | moderate |
| 6 | RedItemsInBinTask | procedural, visual | moderate |
| 7 | ReorientRedMugTask | procedural, visual | moderate |
| 8 | ReorientWhiteMugsTask | procedural, visual | moderate |
| 9 | Stack3RubiksCubeTask | procedural | moderate |
| 10 | StackWhiteMugsTask | procedural, visual | moderate |
| 11 | RubiksCubeOrBananaTask | relational | simple |
| 12 | BananaThenRubiksCubeTask | relational | simple |
| 13 | BowlStackingLeftOnRightTask | relational | simple |
| 14 | BowlStackingRightOnLeftTask | relational | simple |
| 15 | RubiksCubeAndBananaTask | relational | simple |

任务矩阵文件：

```text
robolab_repro_artifacts/pi05_axis5_asset_ready_task_matrix_20260620.json
```

## 4. 4090 运行配置

| 项 | 值 |
|---|---|
| 远端机器 | `robolab4090` / RTX 4090 24GB |
| RoboLab 路径 | `/home/yjl/codex_robolab_4090_20260619/RoboLab` |
| roboplay 路径 | `/home/yjl/roboplay` |
| Policy | `pi05` |
| policy server | `localhost:8000` |
| num_envs | 1 |
| num_runs | 1 |
| video_mode | `all` |
| output prefix | `pi05_axis5_assetready_20260620_20260620_092157` |

启动方式本质上是复用 `scripts/run_pi05_robolab120_4090.sh`，但把 `MATRIX_PATH` 指到 asset-ready 15 任务矩阵，并设置 `GENERATE_MATRIX=0`：

```bash
cd /home/yjl/roboplay/robolab_2604_09860_repro_jupyter

GENERATE_MATRIX=0 \
MATRIX_PATH=/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/pi05_axis5_asset_ready_task_matrix_20260620.json \
RUN_PREFIX=pi05_axis5_assetready_20260620_20260620_092157 \
NUM_ENVS=1 \
NUM_RUNS=1 \
VIDEO_MODE=all \
bash scripts/run_pi05_robolab120_4090.sh
```

## 5. Artifact gate

本轮 15 个任务的 `run_returncode` 和 `verify_returncode` 全部为 0。

诊断文件：

```text
robolab_repro_artifacts/pi05_axis5_assetready_20260620_20260620_092157_failure_diagnosis.json
```

诊断结果：

```json
{
  "complete_scored_episode": 15
}
```

每个任务的 artifact check 都满足：

| 证据项 | 每任务状态 |
|---|---|
| `episode_results.jsonl` | 非空 |
| HDF5 | 1 个 |
| 视频 | 2 个 |
| event log | 1 个 |
| `env_cfg.json` | 1 个 |

> [!NOTE]
> GitHub 仓库里提交的是轻量化证据：summary JSON/CSV、artifact check、manifest 和 notebook。原始视频/HDF5 主要保留在 4090 远端 output 目录，避免把仓库变成大文件仓库。

远端原始输出根路径示例：

```text
/home/yjl/codex_robolab_4090_20260619/RoboLab/output/pi05_axis5_assetready_20260620_20260620_092157_BananaInBowlTask
/home/yjl/codex_robolab_4090_20260619/RoboLab/output/pi05_axis5_assetready_20260620_20260620_092157_RedItemsInBinTask
/home/yjl/codex_robolab_4090_20260619/RoboLab/output/pi05_axis5_assetready_20260620_20260620_092157_StackWhiteMugsTask
```

完整远端输出根列表见：

```text
robolab_repro_artifacts/pi05_axis5_assetready_20260620_20260620_092157_task_run_manifest.jsonl
```

## 6. 总体结果

15 个任务全部产生可计分 episode。按 success 口径：

| 指标 | 数值 |
|---|---:|
| episodes | 15 |
| complete scored episodes | 15 |
| successes | 9 |
| success rate | 0.600 |
| mean score | 0.733 |

这里要区分两个指标：

- `success`：整条任务是否最终成功，通常更严格。
- `score`：子任务或进度分，失败时也可能是 0.5 或 1.0，表示完成了一部分或满足过某些条件。

例如 `PickDrillTask` 的 `success=0`，但 `score=1.0`。这类 case 必须回看 event log 和视频，不能只看一个数字。

## 7. 按能力轴聚合

| 能力轴 | episodes | success rate | mean score | 平均步数 |
|---|---:|---:|---:|---:|
| procedural | 5 | 0.400 | 0.400 | 622.0 |
| relational | 6 | 1.000 | 1.000 | 300.7 |
| visual | 9 | 0.333 | 0.556 | 592.2 |

当前小样本里，关系轴表现最好，程序轴和视觉轴更容易出错。这个结果不能直接外推到论文全量结论，因为每个任务只有 1 个 episode，而且任务标签是多标签；但它已经能作为下一步扰动实验和 baseline 对照的任务选择依据。

## 8. 按难度聚合

| 难度 | episodes | success rate | mean score | 平均步数 |
|---|---:|---:|---:|---:|
| simple | 9 | 0.667 | 0.889 | 433.9 |
| moderate | 6 | 0.500 | 0.500 | 551.0 |

这个趋势符合直觉：moderate 任务平均更长、完成步数更高，成功率和 score 都下降。

## 9. 每任务结果

| 任务 | success | score | step | 主要事件 |
|---|---:|---:|---:|---|
| BananaInBowlTask | 1 | 1.0 | 197 | `GRIPPER_HIT_TABLE=2`, `TARGET_OBJECT_DROPPED=1` |
| PickDrillTask | 0 | 1.0 | 600 | `WRONG_OBJECT_GRABBED=1`, `GRIPPER_HIT_OBJECT=1` |
| TakeMeasuringSpoonOutTask | 0 | 0.5 | 600 | `MULTIPLE_OBJECTS_GRABBED=1`, `WRONG_OBJECT_GRABBED=2` |
| RedDishesInBinTask | 0 | 0.5 | 900 | `GRIPPER_FULLY_CLOSED=3`, `TARGET_OBJECT_DROPPED=2` |
| BananasInBinOneMoreTask | 1 | 1.0 | 196 | `TARGET_OBJECT_DROPPED=2` |
| RedItemsInBinTask | 0 | 0.0 | 900 | `GRIPPER_FULLY_CLOSED=5`, `WRONG_OBJECT_GRABBED=1` |
| ReorientRedMugTask | 0 | 0.0 | 900 | `WRONG_OBJECT_GRABBED=4` |
| ReorientWhiteMugsTask | 1 | 1.0 | 137 | `WRONG_OBJECT_GRABBED=2`, `OBJECT_BUMPED=2` |
| Stack3RubiksCubeTask | 1 | 1.0 | 273 | `WRONG_OBJECT_GRABBED=2`, `OBJECT_BUMPED=2` |
| StackWhiteMugsTask | 0 | 0.0 | 900 | `OBJECT_BUMPED=5`, `WRONG_OBJECT_GRABBED=3` |
| RubiksCubeOrBananaTask | 1 | 1.0 | 104 | `TARGET_OBJECT_DROPPED=1` |
| BananaThenRubiksCubeTask | 1 | 1.0 | 764 | `TARGET_OBJECT_DROPPED=5`, `WRONG_OBJECT_GRABBED=3` |
| BowlStackingLeftOnRightTask | 1 | 1.0 | 161 | `WRONG_OBJECT_GRABBED=3` |
| BowlStackingRightOnLeftTask | 1 | 1.0 | 161 | `OBJECT_BUMPED=1` |
| RubiksCubeAndBananaTask | 1 | 1.0 | 418 | `TARGET_OBJECT_DROPPED=5` |

## 10. 初步结论

这轮最有价值的结果不是“Pi05 有 60%”，而是把评测链路分清楚了：

1. 环境层：15 个任务都能真实启动、真实记录、真实计分。
2. 数据层：每个任务都有 episode/HDF5/video/event/env_cfg 的证据门。
3. 策略层：Pi05 在关系类任务上表现更稳定，在颜色/语义筛选、重定向和堆叠类任务上更容易出错。
4. 诊断层：`WRONG_OBJECT_GRABBED`、`TARGET_OBJECT_DROPPED`、`OBJECT_BUMPED` 比单个 success 更能解释失败原因。

## 11. 下一步实验怎么接

用户前面定的路线是正确的，但要按证据顺序推进：

1. 固定 Pi05，把每个能力轴至少 5 个任务跑完：本轮已完成。
2. 每个任务保存 episode_results、HDF5、视频和子任务日志：远端已完成，GitHub 提交轻量索引。
3. 用 `analysis/read_results.py` 按能力轴、难度、任务长度出表：本轮已生成 by-attributes / by-difficulty / by-task-length。
4. 选一个成功率中等任务做扰动：还需要补多次重复，因为当前每任务只有 1 次，成功率只能是 0 或 1。
5. 之后再换 RoboChallenge pi 或 ReKep 做对照：adapter 没完成前不能把它们记成失败分数。

当前可选的扰动候选任务：

| 候选 | 为什么选 |
|---|---|
| RedDishesInBinTask | `success=0` 但 `score=0.5`，适合看光照/背景是否影响红色餐具识别和放置 |
| TakeMeasuringSpoonOutTask | `success=0` 但 `score=0.5`，适合看语义识别和抓取稳定性 |
| ReorientWhiteMugsTask | `success=1`，但有抓错/碰撞事件，适合做姿态扰动 |
| Stack3RubiksCubeTask | 成功且是程序/堆叠能力代表，可做物体位置扰动压力测试 |

我的建议：下一轮先对 `RedDishesInBinTask` 和 `TakeMeasuringSpoonOutTask` 各补 3 次重复，若出现 1/3 或 2/3 成功率，就选它做光照/背景/物体位置扰动；如果仍然 0/3，则选 `ReorientWhiteMugsTask` 做扰动，因为它有成功但 event 较多，能观察鲁棒性下降。

## 12. 本轮产物索引

| 文件 | 作用 |
|---|---|
| `robolab_repro_artifacts/robolab120_asset_preflight_20260620_091852.json` | 120 任务资产完整性 preflight 结果 |
| `robolab_repro_artifacts/robolab120_asset_preflight_20260620_091852.csv` | preflight 表格版 |
| `robolab_repro_artifacts/pi05_axis5_asset_ready_task_matrix_20260620.json` | 15 任务能力轴矩阵 |
| `robolab_repro_artifacts/pi05_axis5_assetready_20260620_20260620_092157_task_run_manifest.jsonl` | 15 个任务的远端 output_root 和返回码 |
| `robolab_repro_artifacts/pi05_axis5_assetready_20260620_20260620_092157_episode_summary.json` | 每任务 episode 汇总 |
| `robolab_repro_artifacts/pi05_axis5_assetready_20260620_20260620_092157_policy_compare.json` | 按任务、能力轴、难度聚合 |
| `robolab_repro_artifacts/pi05_axis5_assetready_20260620_20260620_092157_policy_compare_by_axis.csv` | 能力轴 CSV |
| `robolab_repro_artifacts/pi05_axis5_assetready_20260620_20260620_092157_failure_diagnosis.json` | 运行日志与 artifact 诊断 |
| `remote_logs/pi05_axis5_assetready_20260620_20260620_092157.log` | 远端完整运行日志 |
| `remote_logs/pi05_axis5_assetready_20260620_20260620_092157_runner.sh` | 本轮远端 runner |

