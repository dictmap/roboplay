# 实验拓展 19：Pi05、PaliGemma、GR00T、Cosmos、阿里模型等多模型对照

<!-- FINAL-20260621-UPDATE:BEGIN -->

> [!TIP]
> **2026-06-21 更新**：Pi05 full-120 已完成；GR00T/Qwen/Cosmos/PaliGemma 等的权重或 metadata 状态已更新在 `MODEL_DOWNLOADS_STATUS.md`。注意：权重下载完成不等于能进入 RoboLab success-rate 表，仍需要 RoboLab observation/action adapter。

<!-- FINAL-20260621-UPDATE:END -->


## 先分清模型类型

不能把所有名字都放进同一列直接比 success rate。RoboLab 评测需要 policy 在每一步输出机器人动作；不同模型的成熟度和接口不一样：

| 类别 | 模型 | 能否直接跑 RoboLab `run.py` | 说明 |
|---|---|---:|---|
| RoboLab/OpenPI 直接 baseline | `pi05`、`paligemma`、`paligemma_fast`、`pi0`、`pi0_fast` | 是 | RoboLab `policies/pi0_family/run.py --policy ...` 已支持。 |
| VLA，但需 adapter | NVIDIA GR00T N1.7 | 否 | 是开放 VLA 候选，但不是 RoboLab Pi0-family runner，需要 observation/action adapter。 |
| 世界模型/数据生成/物理 AI 平台 | NVIDIA Cosmos | 否 | Cosmos 主要是 world foundation model / 数据 / 仿真增强，不等于能直接输出 Franka 动作的 policy。 |
| 阿里/Qwen 机器人模型 | Qwen-VLA、Qwen-RobotManip | 否 | 方向对，但需要确认权重/API、动作表示和 robot embodiment adapter。 |
| 本地对照 | RoboChallenge pi、ReKep | 否 | 需要本地 adapter；ReKep 更像 planner，不是纯 learned VLA。 |

结论：第一批可直接做公平对照的是：

```text
pi05 vs paligemma vs paligemma_fast vs pi0 vs pi0_fast
```

GR00T、Cosmos、Qwen/阿里模型不要先塞进同一脚本硬跑；先做 adapter readiness。

## 基线矩阵

文件：

```text
robolab_repro_artifacts/policy_baseline_model_matrix.json
```

生成脚本：

```bash
python scripts/generate_policy_baseline_model_matrix.py \
  --out robolab_repro_artifacts/policy_baseline_model_matrix.json
```

它把模型分成：

- `direct_robolab_openpi`
- `adapter_required_vla`
- `adapter_required_existing_local`
- `planner_adapter_required`
- `not_drop_in_action_policy`

## 直接可跑：OpenPI / PaliGemma 系列

脚本：

```text
scripts/run_direct_openpi_policy_matrix_4090.sh
```

示例：

```bash
export ROBO_ROOT=/home/yjl/codex_robolab_4090_20260619/RoboLab
export NUM_ENVS=1
export NUM_RUNS=3
export DIRECT_POLICIES="pi05 paligemma paligemma_fast"

bash scripts/run_direct_openpi_policy_matrix_4090.sh
```

这个脚本会：

1. 读取同一份 `pi05_axis5_task_matrix.json`。
2. 对每个 policy 跑同一批 16 个任务。
3. 保存 `episode_results.jsonl`、HDF5、视频和事件/子任务日志。
4. 调用 `analysis/read_results.py` 输出 attributes/difficulty/task-length 表。
5. 调用 `compare_policy_matrix_results.py` 生成跨 policy 的 axis/task/difficulty 聚合。

重要边界：脚本不负责下载或启动每个 OpenPI policy server/checkpoint。每个 policy 的服务端必须先准备好，否则会在连接或 checkpoint 阶段失败。

## GR00T 怎么接

GR00T 是值得测的 VLA，但不是一行 `--policy groot` 就能跑。需要先解决：

1. 输入：把 RoboLab 的 `over_shoulder_left_camera`、`wrist_cam`、关节状态、夹爪状态、prompt 转成 GR00T 接口需要的 schema。
2. 输出：把 GR00T 动作转成 RoboLab 当前 Franka+Robotiq 的 `panda_joint.* + finger_joint` 动作。
3. embodiment：确认 GR00T 当前 checkpoint 是否支持 tabletop Franka/Robotiq，还是主要面向 humanoid/双臂/手。
4. 服务：确定推理服务命令、显存占用、action horizon 和控制频率。

建议顺序：

```text
GR00T adapter smoke on BananaInBowlTask
-> 3 task subset
-> axis5 matrix
-> perturbation
```

## Cosmos 怎么接

Cosmos 不能直接当 Pi05 那样测。更合理的实验位是：

| 用法 | 如何评测 |
|---|---|
| 世界模型/视频预测 | 给定 RoboLab 当前帧和动作候选，预测未来帧或风险。 |
| 数据增强 | 用 Cosmos 生成/增强背景、场景或扰动，再测 Pi05/其他 policy。 |
| Cosmos Policy 如果有可用动作接口 | 才能作为 direct policy baseline 接入 RoboLab。 |

所以当前矩阵把 Cosmos 标成 `not_drop_in_action_policy`。后续如果有开放的 Cosmos Policy checkpoint 和动作接口，再把它升级到 `adapter_required_vla` 或 direct baseline。

## 阿里/Qwen 模型怎么接

目前可以关注两条线：

- Qwen-VLA：通用 Vision-Language-Action 方向。
- Qwen-Robot Suite：例如 Qwen-RobotManip、Qwen-RobotNav、Qwen-RobotWorld。

对 RoboLab manipulation 评测来说，优先级是：

```text
Qwen-RobotManip / Qwen-VLA > Qwen-RobotWorld > Qwen-RobotNav
```

接入前需要确认：

1. 是否开放权重或 API。
2. 是否输出连续动作、离散动作、关键点、轨迹还是高级指令。
3. 是否支持 Franka/Robotiq 或能否通过低层 controller 执行。
4. 是否能稳定接受双相机 + proprio + prompt。

没有这些信息时，不能把它放进 `run.py` 直接跑。

## 结果汇总

脚本：

```text
scripts/compare_policy_matrix_results.py
```

示例：

```bash
python scripts/compare_policy_matrix_results.py \
  --matrix robolab_repro_artifacts/pi05_axis5_task_matrix.json \
  --roots /path/to/RoboLab/output/axis5_pi05_xxx /path/to/RoboLab/output/axis5_paligemma_xxx \
  --out-json robolab_repro_artifacts/axis5_policy_compare.json \
  --out-csv robolab_repro_artifacts/axis5_policy_compare_by_axis.csv
```

输出会按：

- policy × axis
- policy × task
- policy × difficulty

聚合 success rate、score、平均步数。

## 当前推进顺序

1. 固定 Pi05 跑完整 axis5 矩阵。
2. 跑 `paligemma` 和 `paligemma_fast`，因为 RoboLab 现有 runner 已支持。
3. 根据 checkpoint/显存情况再跑 `pi0` 和 `pi0_fast`。
4. 找本地 RoboChallenge pi adapter。
5. ReKep 单独作为 planner baseline。
6. GR00T/Qwen 等等先做 adapter smoke，不直接进主表。
7. Cosmos 暂放在 world-model / data-generation 分支，不放进 direct policy 表。
