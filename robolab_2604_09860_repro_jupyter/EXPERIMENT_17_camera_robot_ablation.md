# 实验拓展 17：相机角度、腕部相机和机器人替换消融

<!-- FINAL-20260621-UPDATE:BEGIN -->

> [!TIP]
> **2026-06-21 更新**：Pi05 full-120 已完成，因此相机/腕部相机/机器人消融不再只建议从 `BananaInBowlTask` 起步。下一阶段应从最终表里选一个成功率中等、视频和 HDF5 都完整的任务，先做 camera/light/background/object-position sweep；机器人替换仍需 adapter，不应只换 USD。

<!-- FINAL-20260621-UPDATE:END -->


## 先说结论

这三个实验不是同一个难度层级：

| 问题 | 能否直接跑 | 核心原因 |
|---|---|---|
| 调整外部相机角度 | 可以先小范围跑 | 不破坏 Pi05 输入 schema，只改变视觉分布。 |
| 取消腕部相机 | 不能直接硬删 | Pi05/RoboLab 当前观测合约需要 `wrist_cam`，硬删会变成缺 key 或 adapter 错误。 |
| 调整/替换机器人 | 不能只换 USD | 动作关节、夹爪、EEF frame、腕部相机挂载、contact sensor 和 policy action space 都绑定了当前 Franka+Robotiq 合约。 |

所以正确测试顺序应该是：

1. 先跑 `camera angle sweep`，因为它最接近论文里的 camera pose variation。
2. 再做 `wrist camera blackout`，不是硬删除，而是保留 key、把腕部图像置黑，才能测“少一只眼睛”的策略退化。
3. 最后做机器人替换，但必须同时替换 robot cfg、action adapter、frame transformer、contact sensor 和 policy adapter；否则测到的是配置崩溃，不是策略泛化。

## Baseline 真实配置

本实验基于已经同步下来的 Pi05 / `BananaInBowlTask` 完整闭环：

```text
remote_outputs/pi05_banana_full_20260620_015206/env_cfg.json
```

关键信息：

| 项 | 当前值 |
|---|---|
| 任务 | `BananaInBowlTask` |
| 策略 | `pi05` |
| 成绩 | `success=True`, `score=1.0`, `episode_step=178` |
| 外部策略相机 | `over_shoulder_left_camera` |
| 腕部策略相机 | `wrist_cam` |
| viewport 相机 | `egocentric_mirrored_camera`，主要用于视频/人工查看，不等同于 policy 输入 |
| 机器人 | `franka_robotiq_2f_85_flattened.usd` |
| 机械臂动作关节 | `panda_joint.*` |
| 夹爪动作关节 | `finger_joint` |

Pi05 的关键输入可以简化理解为：

```text
over_shoulder_left_camera + wrist_cam + arm_joint_pos + gripper_pos + prompt
```

这就是为什么“删腕部相机”和“换机器人”不是简单配置项：它们会碰到 policy 输入输出合约。

## 1. 调整相机角度会如何？

### 原理

外部相机改变的是模型看到的图像分布：

- 物体在图像中的位置会变。
- 遮挡关系会变。
- 深度和距离线索会变。
- 抓取目标可能从“训练中常见视角”变成“没见过的视角”。

如果只小范围移动 `over_shoulder_left_camera.offset.pos/rot`，RoboLab 环境和 Pi05 请求仍然能成立；这类实验可以直接进入真实评测。

### 预期现象

| 改法 | 预期 |
|---|---|
| 小幅升高/降低 | 通常还能跑，成功率可能下降，步数可能变多。 |
| 左右平移 | 如果目标仍清晰，影响较小；如果遮挡变强，抓取失败会增多。 |
| 大角度旋转 | 更容易失败，因为 Pi05 可能依赖 DROID/OpenPI 训练分布里的常见相机视角。 |

### 建议真实测试矩阵

先用 `BananaInBowlTask` 做 sanity test：

| variant | 说明 |
|---|---|
| `default` | 原始视角 |
| `higher` | 外部相机 z + 0.10m |
| `lower` | 外部相机 z - 0.10m |
| `left_shift` | 外部相机 y + 0.10m |
| `right_shift` | 外部相机 y - 0.10m |

每个 variant 先跑 `num_runs=3`，记录：

- success rate
- score
- episode_step
- `GRIPPER_HIT_TABLE`
- `TARGET_OBJECT_DROPPED`
- 视频/viewport 视频

## 2. 取消腕部相机会如何？

### 硬删除不等于公平测试

如果直接从 env config 删除：

```text
scene.wrist_cam
observations.image_obs.wrist_cam
```

程序大概率不是“成功率下降”，而是：

- policy request 缺少 `wrist_cam`
- Pi05 client 打包失败
- OpenPI server 端 schema 不匹配

这只能证明配置不兼容，不能证明腕部相机是否重要。

### 正确做法：soft ablation

更合理的是保留 `wrist_cam` 这个 key，但在 policy adapter 里做：

```text
wrist_cam = zeros_like(wrist_cam)
```

或者固定成第一帧/模糊帧。这样：

- observation schema 不变；
- action space 不变；
- 环境仍可运行；
- 唯一变化是策略少了腕部近距离视觉信息。

### 预期现象

腕部相机通常对下面几类环节更关键：

- 接近物体前的精确定位；
- 夹爪与目标物体的相对位姿；
- 遮挡后的局部确认；
- 放入容器、堆叠、翻正这类末端精度任务。

所以我预期：

| 任务 | 去腕部相机影响 |
|---|---|
| `BananaInBowlTask` | 可能仍有机会成功，但步数增加、drop/table-hit 事件可能增加。 |
| `Stack3RubiksCubeTask` | 影响更大，堆叠末端对局部视觉更敏感。 |
| `ReorientAllMugsTask` | 影响很大，因为姿态修正和接触细节依赖近距离观察。 |

## 3. 调整机器人会如何？

### 不能只换 USD

当前 baseline 不是“任意机器人 + 任意策略”，而是：

```text
Franka + Robotiq 2F-85
动作: panda_joint.* + finger_joint
EEF frame: robot/Gripper/Robotiq_2F_85/base_link
腕部相机: robot/Gripper/Robotiq_2F_85/base_link/wrist_cam
policy: pi05 的 DROID/OpenPI 风格观测动作合约
```

只把 `scene.robot.spawn.usd_path` 改成另一个机器人，通常会失败，因为：

- 新机器人没有 `panda_joint.*`；
- 新夹爪没有 `finger_joint`；
- EEF frame 路径不同；
- 腕部相机挂载点不同；
- contact sensor 路径不同；
- Pi05 输出的动作维度/语义仍按旧机器人解释。

### 机器人实验分两档

| 档位 | 说明 | 价值 |
|---|---|---|
| 同机器人微调 | 改 base pose、初始关节、相机挂载小偏移 | 测策略对 embodiment pose 的鲁棒性。 |
| 真正换机器人 | 换 robot cfg + action adapter + frame/contact/camera + policy adapter | 测跨机器人泛化，但工程量大。 |

## 4. 已做的配置级测试

我新增了脚本：

```text
tools/camera_robot_ablation_config_test.py
```

它读取真实 `env_cfg.json`，验证：

- baseline 是否真的有两路 policy camera；
- `wrist_cam` 是否挂在 robot 路径下；
- baseline 是否是 Franka action contract；
- 小范围外部相机 sweep 是否保留 Pi05 输入合约；
- 硬删除腕部相机是否会破坏 Pi05 合约；
- 只换机器人 USD 是否仍残留旧 Franka action/frame 合约；
- baseline 成功记录是否可读。

输出：

```text
robolab_repro_artifacts/camera_robot_ablation_config_tests.json
```

这不是 Isaac/Pi05 真实重跑，而是“运行前门禁测试”。它的价值是先筛掉会把实验变成配置错误的方案。

## 5. 真正上 4090 的下一步命令

远端 SSH 当前返回 `Permission denied`，所以本轮没有发起 4090 真实重跑。等 SSH 可用后，建议先跑最小矩阵：

```bash
cd /home/yjl/codex_robolab_4090_20260619/RoboLab

# 1) baseline 再跑 3 次，确认当天环境稳定
/home/yjl/.local/bin/uv run python policies/pi0_family/run.py \
  --policy pi05 \
  --remote-host localhost \
  --remote-port 8000 \
  --task BananaInBowlTask \
  --num-envs 1 \
  --num-runs 3 \
  --video-mode all \
  --output-folder-name pi05_camera_ablation_baseline_YYYYMMDD \
  --headless \
  --device cuda:0
```

然后再跑相机扰动脚本或补一个小 wrapper，把 `over_shoulder_left_camera.offset` 按 variant 改掉后逐个运行。腕部相机实验不要先硬删，应该先做 zero-image adapter。

## 6. 已准备好的 4090 执行包

为了后续 4090 SSH 恢复后不用临时拼命令，我补了三个脚本：

| 脚本 | 作用 |
|---|---|
| `scripts/run_camera_ablation_4090.sh` | 在 4090 RoboLab checkout 中运行 baseline、官方 camera pose variation、可选 wrist blackout。 |
| `scripts/create_pi05_wrist_blackout_runner.py` | 在 RoboLab repo 内生成 `policies/pi0_family/client_wrist_blackout.py` 和 `run_wrist_blackout.py`，实现“保留 wrist_cam key 但把图像置黑”的 soft ablation。 |
| `scripts/summarize_ablation_outputs.py` | 离线解析一个或多个 RoboLab output 目录里的 `episode_results.jsonl`，按 task/policy/variant 聚合 success rate、步数、耗时和事件。 |

官方 RoboLab 当前已经提供 `policies/pi0_family/run_camera_pose_variation.py`，其内部会在 reset 时对：

- `over_shoulder_left_camera`
- `wrist_cam`
- `over_shoulder_left_camera + wrist_cam`

做随机位姿扰动。因此第一版相机角度实验先用官方脚本，而不是自己手写相机 pose patch。

### 4090 上的推荐执行方式

先把本目录的脚本同步到 4090，然后运行：

```bash
export ROBO_ROOT=/home/yjl/codex_robolab_4090_20260619/RoboLab
export TASKS="BananaInBowlTask Stack3RubiksCubeTask RedItemsInBinTask"
export NUM_ENVS=1
export NUM_RUNS=3
export RUN_BASELINE=1
export RUN_CAMERA_VARIATION=1
export RUN_WRIST_BLACKOUT=0

bash scripts/run_camera_ablation_4090.sh
```

如果要做腕部相机 soft ablation：

```bash
python scripts/create_pi05_wrist_blackout_runner.py --robolab-root "$ROBO_ROOT" --force

export RUN_BASELINE=0
export RUN_CAMERA_VARIATION=0
export RUN_WRIST_BLACKOUT=1
export WRIST_BLACKOUT_INSTALLER="$PWD/scripts/create_pi05_wrist_blackout_runner.py"

bash scripts/run_camera_ablation_4090.sh
```

注意：`RUN_WRIST_BLACKOUT=1` 会新建一个 Pi05 client 子类，只把进入 OpenPI/Pi05 server 的 wrist image 置零；环境仍会渲染腕部相机，因此视频和 env_cfg 仍可用于人工检查。

### 本地汇总方式

把远端 output 同步回来后：

```bash
python scripts/summarize_ablation_outputs.py \
  --roots remote_outputs/pi05_camera_robot_ablation_YYYYMMDD_* \
  --out-json robolab_repro_artifacts/camera_robot_ablation_summary.json \
  --out-csv robolab_repro_artifacts/camera_robot_ablation_summary.csv
```

我已经用现有 baseline 和复杂任务输出做了冒烟测试：

```text
robolab_repro_artifacts/camera_robot_ablation_parser_smoke_summary.json
robolab_repro_artifacts/camera_robot_ablation_parser_smoke_summary.csv
```

这两个文件只证明解析器可用，不代表已经完成新的相机/腕部相机消融重跑。
