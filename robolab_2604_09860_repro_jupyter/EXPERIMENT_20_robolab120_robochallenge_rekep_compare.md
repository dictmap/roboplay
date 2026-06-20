# 实验拓展 20：RoboLab-120 全量复现与 RoboChallenge/ReKep 对照

## 先说结论

可以做完整 RoboLab-120，但它不是“点一下就出表”的短任务。正确顺序是：

1. 固定 `Pi05`，先跑完整 120 任务，`NUM_ENVS=1`，`NUM_RUNS=1` 做第一遍打通。
2. 每个任务都保存 `episode_results.jsonl`、HDF5、视频、事件/子任务日志和 `env_cfg.json`。
3. 用同一份 `robolab120_task_matrix.json` 做按能力轴、难度、任务长度的聚合。
4. 再把同一份任务矩阵交给其他 direct policy，例如 `paligemma`、`paligemma_fast`、`pi0`、`pi0_fast`。
5. RoboChallenge pi 和 ReKep 先标记为 `adapter_required`，只有完成 RoboLab observation/action adapter 后才进入 success-rate 对照表。

> [!WARNING]
> 当前我这边不能直接替你启动 4090 全量跑，因为本轮 SSH 测试返回 `Permission denied (publickey,password)`。所以下面交付的是可在 4090 上直接执行的全量脚本、任务矩阵、对照聚合和 adapter 边界；真实 120 个任务的分数需要在 4090 端跑完后生成。

## 为什么不能把 RoboChallenge pi 和 ReKep 直接塞进同一张表

RoboLab 的 policy runner 期待的是：

```text
RoboLab observation
  = 外部相机 + 腕部相机 + 机器人 proprio + 语言指令 + 环境状态
Policy output
  = Franka/Robotiq 可执行的 action 或 action chunk
Evidence output
  = episode_results.jsonl + HDF5 + mp4 + log_*_env*.json
```

OpenPI/Pi05 系列已经有 RoboLab `policies/pi0_family/run.py` 入口，所以能直接跑。

RoboChallenge pi 的本地候选更像比赛/数据集侧的 policy 或 ALOHA/Table30v2 checkpoint。它需要先做：

- RoboLab 双相机/状态/指令到 RoboChallenge 输入 schema 的转换。
- RoboChallenge 动作输出到 RoboLab Franka/Robotiq 控制维度的转换。
- 推理频率、action horizon、夹爪控制和关节空间的合约确认。
- 单任务 `BananaInBowlTask` 真正执行并写出视频/HDF5/JSONL 后，才算 adapter smoke 通过。

ReKep 是 planner 路线，不是每步直接输出动作的 VLA。它需要：

- 从 RoboLab 相机画面抽 keypoints。
- 根据语言生成或选择 constraints。
- 做子目标优化。
- 通过低层控制器把子目标变成 Franka/Robotiq 动作。
- 把规划失败、约束失败、执行失败分别写进日志。

所以，RoboChallenge/ReKep 的第一步不是“算 0 分”，而是显式标记：

```text
adapter_required / planner_adapter_required
```

这能避免把“没接上接口”误解释成“模型能力为 0”。

## 新增文件

核心入口：

```text
scripts/generate_robolab120_task_matrix.py
scripts/run_pi05_robolab120_4090.sh
scripts/run_policy_robolab120_compare_4090.sh
scripts/generate_adapter_baseline_plan.py
scripts/write_adapter_pending_results.py
scripts/create_robochallenge_robolab_adapter_stub.py
scripts/create_rekep_robolab_adapter_stub.py
```

生成的关键证据：

```text
robolab_repro_artifacts/robolab120_task_matrix.json
robolab_repro_artifacts/adapter_baseline_plan.json
robolab_repro_artifacts/adapter_stubs/robochallenge_robolab_adapter.py
robolab_repro_artifacts/adapter_stubs/rekep_robolab_adapter.py
```

## 1. 生成 RoboLab-120 任务矩阵

在学习包目录执行：

```bash
cd /path/to/robolab_2604_09860_repro_jupyter
python scripts/generate_robolab120_task_matrix.py \
  --out robolab_repro_artifacts/robolab120_task_matrix.json
```

这个矩阵来自官方：

```text
https://raw.githubusercontent.com/NVlabs/RoboLab/main/robolab/tasks/_metadata/task_metadata.json
```

每个任务保留：

- `task_name`
- `instruction`
- `axes`
- `attributes`
- `difficulty_label`
- `difficulty_score`
- `num_subtasks`
- `num_atomic_conditions`
- `episode_s`
- `scene`
- `filename`
- `contact_objects`
- `primary_objects_for_object_pose_variation`

这些字段后面用于：

- 按 visual / procedural / relational 汇总。
- 按 easy / medium / hard 汇总。
- 按任务长度和子任务数汇总。
- 找成功率中等的任务做光照、背景、物体位置扰动。

## 2. 固定 Pi05 跑完整 120 任务

4090 端执行：

```bash
export ROBO_ROOT=/home/yjl/codex_robolab_4090_20260619/RoboLab
export UV_BIN=/home/yjl/.local/bin/uv
export NUM_ENVS=1
export NUM_RUNS=1
export VIDEO_MODE=all
export STOP_ON_FAILURE=0

bash scripts/run_pi05_robolab120_4090.sh
```

脚本默认逐任务运行，而不是一次把 120 个任务塞进一个 `run.py`。原因是完整评测最怕某个任务或资产异常导致全局停止；逐任务可以做到：

- 第 37 个任务失败，第 38 个任务仍继续。
- 每个任务有独立输出目录。
- 最后自动合并 `episode_results.jsonl`，再出总表。

如果只是先测脚本，不想跑完整 120：

```bash
export TASK_LIMIT=5
bash scripts/run_pi05_robolab120_4090.sh
```

## 3. 每个任务必须保存哪些东西

每个任务输出目录至少应有：

```text
episode_results.jsonl
run_*.hdf5
*.mp4
log_*_env*.json
env_cfg.json
```

脚本会调用：

```bash
python scripts/verify_robolab_artifacts.py \
  --output-root <task-output-root> \
  --matrix robolab_repro_artifacts/robolab120_task_matrix.json \
  --tasks <task-name> \
  --out robolab_repro_artifacts/<task>_artifact_check.json
```

注意：视频/HDF5 存在只能证明仿真链路有输出；是否成功还要看 `episode_results.jsonl` 里的 `success`、`score`、`episode_step` 和事件日志。

## 4. 按能力轴、难度、任务长度出表

脚本跑完后会生成：

```text
robolab_repro_artifacts/robolab120_pi05_<stamp>_episode_summary.json
robolab_repro_artifacts/robolab120_pi05_<stamp>_episode_summary.csv
robolab_repro_artifacts/robolab120_pi05_<stamp>_policy_compare.json
robolab_repro_artifacts/robolab120_pi05_<stamp>_policy_compare_by_axis.csv
robolab_repro_artifacts/robolab120_pi05_<stamp>_selected_medium_task.json
```

同时会在 RoboLab 仓库的 merged output 上尝试调用官方：

```bash
uv run python analysis/read_results.py <merged-folder> --by-attributes --output-csv <...>
uv run python analysis/read_results.py <merged-folder> --by-difficulty --output-csv <...>
uv run python analysis/read_results.py <merged-folder> --by-task-length --output-csv <...>
```

如果官方 `read_results.py` 因版本差异失败，本地 `summarize_ablation_outputs.py` 和 `compare_policy_matrix_results.py` 仍会保留轻量聚合结果。

## 5. 加入其他 direct OpenPI policy

第一批可直接进 RoboLab `run.py` 的对照是：

```text
pi05
paligemma
paligemma_fast
pi0
pi0_fast
```

示例：

```bash
export DIRECT_POLICIES="pi05 paligemma paligemma_fast"
export NUM_ENVS=1
export NUM_RUNS=1
export STOP_ON_FAILURE=0

bash scripts/run_policy_robolab120_compare_4090.sh
```

脚本会按同一份 `robolab120_task_matrix.json` 逐 policy 跑 full-120，并汇总到：

```text
robolab_repro_artifacts/robolab120_policy_compare_<stamp>.json
robolab_repro_artifacts/robolab120_policy_compare_by_axis_<stamp>.csv
```

## 6. RoboChallenge pi 和 ReKep 的当前处理

默认对比脚本会生成 adapter-pending 行：

```text
robolab_repro_artifacts/robolab120_robochallenge_pi_adapter_pending_<stamp>/episode_results.jsonl
robolab_repro_artifacts/robolab120_rekep_adapter_pending_<stamp>/episode_results.jsonl
```

这些行的含义是：

```json
{
  "policy": "robochallenge_pi",
  "status": "adapter_required",
  "success": null,
  "adapter_required": true
}
```

聚合脚本会把它们计入 `pending_episodes`，但不会参与 `success_rate` 计算。

这样表里可以同时看到：

| policy | scored_episodes | pending_episodes | success_rate |
|---|---:|---:|---:|
| pi05 | 120 | 0 | 实测值 |
| robochallenge_pi | 0 | 120 | 空 |
| rekep | 0 | 120 | 空 |

这比把未接入 baseline 算成 0% 更严谨。

## 7. 适配器模板

生成模板：

```bash
python scripts/create_robochallenge_robolab_adapter_stub.py
python scripts/create_rekep_robolab_adapter_stub.py
```

输出：

```text
robolab_repro_artifacts/adapter_stubs/robochallenge_robolab_adapter.py
robolab_repro_artifacts/adapter_stubs/rekep_robolab_adapter.py
```

这两个文件都是 fail-fast skeleton。它们的作用不是假装能跑，而是固定实现边界：

- 输入是什么。
- 输出是什么。
- 哪些函数必须实现。
- 没实现时明确 `NotImplementedError`。

## 8. 预计耗时

保守估计：

| 实验 | 4090 建议配置 | 预计耗时 |
|---|---|---:|
| `TASK_LIMIT=5` smoke | `NUM_ENVS=1, NUM_RUNS=1` | 约 0.5-2 小时，取决于资产缓存 |
| Pi05 full-120 第一遍 | `NUM_ENVS=1, NUM_RUNS=1` | 约数小时到十几小时 |
| Pi05 full-120 稳定统计 | `NUM_ENVS=1, NUM_RUNS=3` | 可能接近论文级 GPU 小时 |
| Pi05 + PaliGemma + Pi0 full compare | 每个 policy 单独跑 | 约为单 policy 的 3-5 倍 |
| RoboChallenge/ReKep adapter smoke | 先 1 个任务 | 取决于 adapter 实现 |

4090 的关键不是 CUDA 算力不够，而是 24GB 显存、Isaac 资源加载、视频/HDF5 写盘和单任务长 horizon 的总时间。

## 9. 这一步完成后看什么

第一层看执行完整性：

- 120 个任务是否都有输出目录。
- 每个任务是否有视频、HDF5、JSONL、事件日志。
- 哪些任务是仿真/资产失败，哪些是真正 policy 失败。

第二层看能力画像：

- visual 是否主要在颜色/语义/尺寸混淆上失败。
- relational 是否主要在左右/上方/计数/连接词上失败。
- procedural 是否主要在堆叠、重定向、排序、可供性上失败。

第三层才看 policy 对照：

- Pi05 vs PaliGemma/Pi0 是 direct policy 对照。
- RoboChallenge pi 是 adapter 后的本地模型对照。
- ReKep 是 planner baseline，对比时要单独标注路线差异。

## 10. 当前真实状态

已准备：

- full-120 任务矩阵生成器。
- full-120 Pi05 逐任务执行脚本。
- full-120 direct policy 对照脚本。
- RoboChallenge/ReKep adapter plan。
- RoboChallenge/ReKep fail-fast adapter skeleton。
- adapter-pending 对比行，避免未接入 baseline 被误算成 0%。

未完成：

- 由于当前 SSH 权限失败，尚未在 4090 上真实跑完 120 个任务。
- RoboChallenge pi 还没有 RoboLab observation/action adapter。
- ReKep 还没有 RoboLab keypoint/planner/controller adapter。

下一步只要 4090 SSH 可用，就可以先跑：

```bash
export TASK_LIMIT=5
bash scripts/run_pi05_robolab120_4090.sh
```

确认 5 个任务输出完整后，再取消 `TASK_LIMIT` 跑完整 120。
