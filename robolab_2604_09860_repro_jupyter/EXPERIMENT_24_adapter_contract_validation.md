# 实验 24：RoboLab policy/action adapter 契约验证

更新时间：2026-06-22 08:35 CST

## 0. 这一步推进了什么

这次没有把 RoboChallenge 或 ReKep 伪装成“已经跑出成功率”。我把它们接入 RoboLab 的关键差异落成了可运行的 adapter contract gate：

- RoboLab 评分硬接口：`[N,8] = 7 个 Franka 关节目标 + 1 个 Robotiq 夹爪目标`。
- RoboChallenge 当前本地代码：按机器人输出 `ALOHA/W1 14D` 或 `UR5/ARX5 7D`，不是 Franka+Robotiq 8D。
- ReKep 当前本地代码：planner/perception 方法，输出 keypoint、constraints、subgoal/path，需要 IK/motion planner 才能变成 `[N,8]`。
- GR00T 类 DROID action policy：已有 client 能拼 `[joint_position_7 + gripper_1]`，但当前 no-flash fallback 不是官方高性能环境。
- Cosmos：理论 action 接口能接，但 4090 24GB 已经遇到 OOM。
- Qwen/阿里 VLM：不能直接作为 action policy，必须加 action head 或 planner bridge。

新增验证脚本：`scripts/validate_adapter_contracts.py`。

验证结果写入：`robolab_repro_artifacts/adapter_contracts/roboplay_companion_20260621_074050_adapter_contract_validation.json`。

## 1. 核心输入/输出契约

### 1.1 RoboLab 侧输入

RoboLab policy runner 给策略的核心观测可以抽象成：

| 字段 | 形状/含义 | 用途 |
|---|---|---|
| `image_obs.over_shoulder_left_camera` | RGB 图像 | 全局目标和场景布局 |
| `image_obs.over_shoulder_right_camera` | RGB 图像 | 另一个外部视角，用于遮挡补偿 |
| `image_obs.wrist_cam` | RGB 图像 | 夹爪近场、抓取和放置精修 |
| `proprio_obs.arm_joint_pos` | `[..., 7]` | Franka 当前 7 个关节 |
| `proprio_obs.gripper_pos` | `[..., 1]` | 当前夹爪开合 |
| 可选 `ee_pos/ee_quat` | `[...,3] / [...,4]` | planner/IK 更容易用 |

### 1.2 RoboLab 侧输出

所有可评分模型最终必须输出：

```text
[N, 8] = [panda_joint1, panda_joint2, panda_joint3, panda_joint4,
          panda_joint5, panda_joint6, panda_joint7, robotiq_gripper]
```

这里 `N` 是 action horizon，不是任务数，也不是 episode step。RoboLab control loop 每次取 chunk 里的动作执行，episode 成功率来自同一套 `episode_results.jsonl` 和子任务谓词。

## 2. RoboChallenge 为什么不能直接算成功率

本地 RoboChallenge 推理代码的核心事实：

| robot_type | camera keys | state/action | 和 RoboLab 的差异 |
|---|---|---|---|
| `aloha` / `dosw` | `cam_high`, `cam_left_wrist`, `cam_right_wrist` | 14D 双臂 | RoboLab 是单 Franka 7 关节 + Robotiq；双臂切片后仍不是 Franka 运动学 |
| `ur5` | `cam_global`, `cam_arm` | 7D = 6 joints + gripper | UR5 是 6 关节，RoboLab Franka 是 7 关节 |
| `arx5` | `cam_global`, `cam_arm`, `cam_side` | 7D = 6 joints + gripper | 机器人几何、关节顺序、夹爪语义均不同 |
| `franka_compat_8d` | adapter 假想目标 | 8D | 只有这种才可直接进 RoboLab 成功率 |

所以只做 key rename 会造成一个危险假象：代码能运行，但动作不是目标机器人能执行的动作。现在脚本默认会拦截：

- `ALOHA 14D -> RoboLab [N,8]`：抛 `RetargetRequired`。
- `UR5/ARX5 7D -> RoboLab [N,8]`：抛 `RetargetRequired`。
- 如果开启 `allow_placeholder=True`，只生成 shape 正确的占位动作，并标记 `scoreable=False`，只能用于日志/HDF5/video 链路 smoke。

### 2.1 未来优化路线

| 路线 | 能否公平对比 | 成本 | 说明 |
|---|---:|---:|---|
| key/schema bridge | 低 | 低 | 只能验证 server 能收输入，不适合报成功率 |
| task-space retarget | 中 | 中 | 把源动作转末端轨迹，再 Franka IK；能跑，但效果依赖标定和 IK 质量 |
| 重训 Franka+Robotiq action head | 高 | 高 | 最适合正式对比：同 observation、同 action、同 success metric |

## 3. ReKep 为什么应该作为 planner baseline

ReKep 的输入/输出链路不是“每个 control step 输出动作”，而是：

```text
RGB-D + mask + camera params + language
  -> keypoints
  -> language-conditioned constraints
  -> subgoals / end-effector pose path
  -> IK / motion planner
  -> Franka+Robotiq [N,8]
  -> RoboLab success metric
```

当前缺口主要是三块：

| 缺口 | 为什么关键 | 不补会怎样 |
|---|---|---|
| RGB-D/seg/camera perception bundle | ReKep 需要把语言目标绑定到 3D 关键点 | 只有 RGB 时很难稳定反投影到世界坐标 |
| ReKep constraints 到 RoboLab object/world frame | 约束必须作用在 Isaac/RoboLab 的真实对象和坐标系上 | 约束能生成文本，但无法安全执行 |
| Franka IK/motion planner | ReKep 给的是末端位姿/路径，不是 Franka 关节 chunk | 无法进入 `[N,8]` 评分接口 |

因此文档和脚本里把 ReKep 标为 `planner_adapter_required`，不是失败成功率。

## 4. 已落地的代码

### 4.1 RoboChallenge adapter helper

文件：`robolab_repro_artifacts/adapter_stubs/robochallenge_robolab_adapter.py`

| 函数 | 输入 | 输出 | 作用 |
|---|---|---|---|
| `validate_robolab_observation(obs)` | RoboLab observation dict | shape/dtype report | 检查图像和 proprio 是否够 bridge |
| `build_robochallenge_observation(obs, instruction, robot_type=...)` | RoboLab obs + 语言 + 源机器人类型 | RoboChallenge payload + lossy report | 只做输入 schema bridge，不代表可评分 |
| `validate_franka_robotiq_action_chunk(chunk)` | 任意动作数组 | `[N,8]` contract report | 最终评分前硬门禁 |
| `retarget_robochallenge_actions(actions, source_robot=...)` | RoboChallenge 输出动作 | 默认抛 `RetargetRequired` | 防止 14D/7D 被误算成功率 |

### 4.2 ReKep adapter helper

文件：`robolab_repro_artifacts/adapter_stubs/rekep_robolab_adapter.py`

| 函数 | 输入 | 输出 | 作用 |
|---|---|---|---|
| `inspect_rekep_observation_requirements(obs)` | RoboLab observation | 缺失项 report | 检查 RGB-D、seg、camera params |
| `extract_keypoint_inputs(obs, instruction)` | observation + 语言 | perception bundle report | 缺少 perception 时抛 `PlannerBridgeRequired` |
| `build_rekep_stage_plan_schema(instruction)` | 语言任务 | 中间产物 schema | 规定 planner baseline 该保存什么 |
| `eef_path_to_franka_action_chunk(eef_poses, ik_solver=...)` | `[N,7]` 末端位姿路径 | `[N,8]` 或 bridge blocker | 没有 IK 默认拦截 |

## 5. 验证用例设计

`validate_adapter_contracts.py` 覆盖以下用例：

| 用例 | 期望 |
|---|---|
| 最小 RoboLab observation | pass |
| 直接 `[N,8]` action chunk | pass |
| RoboChallenge ALOHA/UR5/ARX5 observation bridge | pass，但 `scoreable=False` |
| ALOHA 14D action 直接进 RoboLab | `blocked_expected` |
| UR5 7D action 直接进 RoboLab | `blocked_expected` |
| UR5 placeholder retarget | pass，但 `scoreable=False` |
| ReKep 缺少 depth/seg/camera | `blocked_expected` |
| ReKep RGB-D/seg/camera bundle | pass，但仍然不是 action policy |
| ReKep eef path 没有 IK | `blocked_expected` |
| ReKep eef placeholder | pass，但 `scoreable=False` |

## 6. 下一步实验阶梯

1. 保持 Pi05 tuned 作为 RoboLab-120 主基线。
2. 对 GR00T 先修 no-flash fallback，确认官方 server 环境后重跑 20 任务。
3. 对 Cosmos 换 48GB+ GPU 或量化/小模型 checkpoint，再做 server startup smoke。
4. 对 RoboChallenge 先做 UR5/ARX5 单臂路线的 task-space retarget prototype；ALOHA 双臂优先级低于单臂。
5. 对 ReKep 先做 1 个任务 planner dry-run：`RGB-D/seg -> keypoints -> eef pose -> Franka IK placeholder`，验证记录链路；再替换真 IK。
6. 只有当输出通过 `[N,8]` 且不是 placeholder，才进入 20 任务成功率表。

## 7. 当前结论

这一步把“为什么不能直接比较”推进成了可运行门禁。以后任何新模型要进 RoboLab 表格，必须先过三问：

1. 输入是不是能消费 RoboLab 多相机 + proprio + language？
2. 输出是不是原生或真实 retarget 成 `[N,8]`？
3. 产物是不是完整保存 `episode_results.jsonl + HDF5 + video + subtask logs`？

三问里任何一问没过，就只能写 probe / adapter-required / planner-required，不能写成功率。
