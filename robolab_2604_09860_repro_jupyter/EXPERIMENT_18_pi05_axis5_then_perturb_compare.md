# 实验拓展 18：固定 Pi05 的能力轴 5×任务评测，再做扰动与后续对照

## 目标

这一步把实验路线从“单任务/少量复杂任务 smoke”推进到更接近论文评测的最小矩阵：

1. 固定策略为 OpenPI/Pi05。
2. 每个能力轴至少 5 个任务。
3. 每个任务保存 `episode_results.jsonl`、HDF5、视频和子任务/事件日志。
4. 用 RoboLab 官方 `analysis/read_results.py` 按能力轴、难度、任务长度出表。
5. 从 Pi05 结果中选一个成功率中等的任务，再跑光照、背景、物体位置扰动。
6. 最后才把同一套任务换成 RoboChallenge pi 或 ReKep 做对照。

## 任务矩阵

矩阵由脚本生成：

```bash
python scripts/generate_axis5_task_matrix.py \
  --out robolab_repro_artifacts/pi05_axis5_task_matrix.json
```

当前矩阵共 16 个任务，覆盖数为：

| 能力轴 | 覆盖任务数 |
|---|---:|
| visual | 7 |
| procedural | 6 |
| relational | 6 |

任务列表：

| 任务 | 能力轴 | 属性 | 难度 | 子任务数 |
|---|---|---|---|---:|
| `BananaInBowlTask` | visual | semantics | simple | 1 |
| `BBQSauceInBinTask` | visual | color, semantics | simple | 2 |
| `BigPumpkinInBinTask` | visual | size | simple | 1 |
| `CannedFoodInBinTask` | visual | semantics | simple | 1 |
| `RedItemsInBinTask` | visual, procedural | color, sorting | moderate | 2 |
| `Stack3RubiksCubeTask` | procedural | stacking | moderate | 2 |
| `ReorientAllMugsTask` | procedural | reorientation | complex | 3 |
| `AppleAndYogurtInBowlTask` | procedural | affordance | moderate | 2 |
| `BlocksInBinTask` | procedural | sorting | complex | 4 |
| `BlackItemsInBinTask` | visual, procedural | color, sorting | complex | 5 |
| `RubiksCubeLeftOfBowlTask` | relational | spatial | moderate | 3 |
| `BowlStackingLeftOnRightTask` | relational | spatial | simple | 1 |
| `BananaThenRubiksCubeTask` | relational | conjunction | simple | 2 |
| `BananasInCrateTask` | relational | counting | moderate | 1 |
| `ClampInRightBinTask` | visual, relational | semantics, spatial | simple | 1 |
| `ButterAboveRaisinTask` | relational | spatial | simple | 1 |

`BlockStackingSpecifiedOrderTask` 暂不放进第一批主矩阵，因为之前在当前 checkout 中触发过 contact reporter / asset 初始化失败。等资产问题处理完，可以作为 procedural backup 加回。

## 4090 主评测脚本

脚本：

```text
scripts/run_pi05_axis5_4090.sh
```

推荐运行：

```bash
export ROBO_ROOT=/home/yjl/codex_robolab_4090_20260619/RoboLab
export NUM_ENVS=1
export NUM_RUNS=3
export VIDEO_MODE=all
export POLICY=pi05

bash scripts/run_pi05_axis5_4090.sh
```

它会做这些事：

1. 生成/刷新 `pi05_axis5_task_matrix.json`。
2. 调用 `policies/pi0_family/run.py`。
3. 固定 `--policy pi05`。
4. 传入 16 个任务。
5. 设置 `--enable-subtask` 和 `--video-mode all`。
6. 用 `verify_robolab_artifacts.py` 检查每个任务是否有 HDF5、视频、子任务/事件日志。
7. 调用官方 `analysis/read_results.py` 输出三张表：
   - `--by-attributes`
   - `--by-difficulty`
   - `--by-task-length`
8. 用 `select_medium_success_task.py` 选出后续扰动任务。

## 每个任务的证据要求

每个任务至少需要：

| 证据 | 用途 |
|---|---|
| `episode_results.jsonl` | 主结果，包含 success、score、步数、耗时、事件计数。 |
| `run_*.hdf5` | 轨迹和状态证据，用于后续 SPARC/ISJ/路径长度等轨迹指标。 |
| `*.mp4` | 主视频或 policy camera 视频，用于人工复核失败原因。 |
| `*_viewport.mp4` | viewport 视频，用于检查仿真画面、遮挡、对象状态。 |
| `log_*_env*.json` | 子任务/事件日志，用于解释抓取、掉落、碰桌、错误对象等失败。 |

校验脚本：

```bash
python scripts/verify_robolab_artifacts.py \
  --output-root "$ROBO_ROOT/output/<output_folder>" \
  --matrix robolab_repro_artifacts/pi05_axis5_task_matrix.json \
  --out robolab_repro_artifacts/<output_folder>_artifact_check.json
```

## 出表方式

主脚本会自动跑：

```bash
uv run python analysis/read_results.py <output_folder> \
  --by-attributes \
  --output-csv <output_folder>_by_attributes.csv

uv run python analysis/read_results.py <output_folder> \
  --by-difficulty \
  --output-csv <output_folder>_by_difficulty.csv

uv run python analysis/read_results.py <output_folder> \
  --by-task-length \
  --output-csv <output_folder>_by_task_length.csv
```

这里的 “能力轴” 在 RoboLab 官方工具中主要通过 `attributes` 聚合；我们再用矩阵文件把属性映射回 visual/procedural/relational。

## 选择成功率中等任务

脚本：

```text
scripts/select_medium_success_task.py
```

它按 task 统计 success rate，优先选择 `0 < success_rate < 1` 且最接近 0.5 的任务。如果样本太少导致全是 0 或 1，会选择最接近 0.5 的 fallback，并在 JSON 中说明。

输出示例：

```text
robolab_repro_artifacts/<output_folder>_selected_medium_task.json
```

## 扰动阶段

脚本：

```text
scripts/run_selected_perturbations_4090.sh
```

运行方式：

```bash
export ROBO_ROOT=/home/yjl/codex_robolab_4090_20260619/RoboLab
export BASE_OUTPUT_FOLDER=<pi05_axis5_output_folder>
export NUM_RUNS=3
export RUN_LIGHTING=1
export RUN_BACKGROUND=1
export RUN_OBJECT_POSITION=1

bash scripts/run_selected_perturbations_4090.sh
```

扰动分三类：

| 扰动 | 实现 |
|---|---|
| 光照 | 官方 `policies/pi0_family/run_lighting.py` |
| 背景 | `run.py --randomize-background --background-seed <seed>`，避免官方 background 全任务 sweep 太大 |
| 物体位置 | 本包生成 `run_object_position_variation.py`，对选中任务的 primary objects 做小范围 `x/y/yaw` reset-time perturbation |

物体位置扰动 runner 由这个脚本安装到远端 RoboLab repo：

```bash
python scripts/create_object_position_variation_runner.py \
  --robolab-root "$ROBO_ROOT" \
  --force
```

默认扰动幅度：

| 参数 | 默认 |
|---|---:|
| `OBJECT_XY_RANGE` | 0.03m |
| `OBJECT_YAW_RANGE` | 0.20 rad |

这个幅度是保守值，目标是先测策略敏感性，不是故意把场景变成不可达。

## 为什么最后才换 RoboChallenge pi 或 ReKep

先固定 Pi05 有两个好处：

1. 先把任务、资产、日志、视频、HDF5 和分析链跑通，避免把环境问题误判成方法问题。
2. Pi05 的结果会告诉我们哪些任务太简单、太难或刚好中等；对照方法应该优先放在中等区间任务上，才更有区分度。

后续对照顺序：

1. 固定同一任务矩阵。
2. 固定同一输出 schema。
3. 替换 policy adapter：RoboChallenge pi。
4. 再替换 policy adapter / planner：ReKep。
5. 用同一套 `read_results.py` 和本包汇总器出表。

## 当前状态

已完成：

- 任务矩阵生成。
- 16 任务覆盖校验。
- artifact 校验脚本。
- `analysis/read_results.py` 出表脚本入口。
- 中等成功率任务选择器。
- 光照/背景/物体位置扰动执行脚本。
- 物体位置扰动 runner 生成器。
- 用已有复杂任务输出做 artifact check 冒烟测试。

尚未完成：

- 4090 上真正跑 16 任务 Pi05 主矩阵。
- 4090 上真正跑扰动阶段。
- RoboChallenge pi / ReKep 对照。

阻塞原因：当前本地到 `robolab4090` 的 SSH 仍需要恢复；恢复后可以直接运行上述脚本。
