# 实验 23：Pi 区分、接口适配与结果深度分析

更新时间：2026-06-22 06:17:15 CST

## 0. 先把几个 Pi 和模型名字说清楚

| 名称 | 这次记录里的含义 | 能否直接作为 RoboLab 成功率 | 注意事项 |
|---|---|---:|---|
| `Pi05 tuned / RoboLab-compatible` | 已经能通过 `policies/pi0_family/run.py --policy pi05` 接 RoboLab 的 OpenPI websocket server，输入是 RoboLab 多相机/关节状态，输出是 Franka+Robotiq joint-position action chunk。 | 是 | 这是 120 任务和 20 任务基线的主结果。 |
| `Pi05 base-DROID / RoboChallenge弱适配` | 使用 DROID schema 尝试接入的 base Pi05/RoboChallenge 相关模型路径，能跑完 20 个 episode，但不是 RoboLab tuned checkpoint。 | 只能作为弱适配失败对照 | 成功率 0/20，主要失败在抓取/目标选择，不能和 tuned Pi05 混称为同一个 Pi05。 |
| `Pi0-family variants` | `pi0`、`pi0_fast`、`paligemma`、`paligemma_fast` 的 RoboLab runner 已有参数入口。 | 只有匹配 checkpoint/server 存在时才算 | runner 支持不等于 checkpoint 已可跑；要先通过 policy server smoke。 |
| `RoboChallenge pi` | 本地有 checkpoint/probe 记录，但当前是 ALOHA/Table30v2 schema，不是 Franka+Robotiq joint-position websocket policy。 | 否，当前是 adapter required | 需要 observation/action retarget 或再训练 action head。 |
| `ReKep` | keypoint/constraint planner，不是每步 action policy server。 | 不能当 VLA 成功率直接比 | 可以做 planner baseline，但要先接 perception、keypoint、IK/motion planner、执行控制器。 |
| `GR00T N1.6 DROID` | 这次跑通的是 eager/no-flash fallback，因为本机 CUDA/flash-attn 不匹配。 | 可作为 fallback rollout 证据，不是官方分数 | 已生成 20 任务 artifact，但 0/20，不能写成论文官方 GR00T baseline。 |
| `Cosmos3-Nano-Policy-DROID` | checkpoint 和 openpi server 依赖已解决，但 4090 24GB 模型初始化 OOM。 | 否，未进入 episode | blocker 记录见 `/home/yjl/roboplay/robolab_2604_09860_repro_jupyter/robolab_repro_artifacts/roboplay_companion_20260621_074050_cosmos3_4090_startup_blocker.json`。 |
| `Qwen/阿里 VLM` | 视觉语言模型本身不输出机器人 action。 | 否 | 需要 action head 或 planner 桥接后才能测 RoboLab 成功率。 |

## 1. step 571/900、395/2700、2700 step 到底是什么

RoboLab 运行里有两种容易混淆的 step：

| 表达 | 含义 | 解释 |
|---|---|---|
| `571/900` | 当前单个 episode 的仿真控制步进度 | `900` 不是任务总数，而是这个 episode 的最大控制步数。RoboLab 的常见控制频率约 15Hz，900 step 约等于 60 秒。 |
| `395/2700` | 当前 episode 已跑 395 step，上限 2700 step | 2700 step 约等于 180 秒，常见于更长或更多子任务的任务。如果界面显示成 `395/270`，大概率是截图/日志截断，正式记录里是 2700。 |
| `episode_step=900/2700/4500` | episode 结束时实际用掉的步数 | 如果刚好等于上限，经常表示一直没成功直到 timeout。 |
| `step 1/2` | 子任务谓词链里的第 1 个条件/共 2 个条件 | 例如 PickPlace 通常先 `object_grabbed`，再 `object_in_container` 或 `object_dropped`。这不是仿真步。 |

因此，看进度时要分三层：队列进度是第几个任务/总任务数；episode 进度是 `当前 step / max_episode_length`；子任务进度是谓词链 `step 1/2`、`step 2/2`。

## 2. 结果总览

| 实验 | episodes | success | success rate | mean score | mean episode step | max episode step |
|---|---:|---:|---:|---:|---:|---:|
| Pi05 tuned / RoboLab-120 正式 | 120 | 34 | 28.3% | 0.417 | 1223.133 | 4500.000 |
| Pi05 tuned / 20任务基线 | 20 | 5 | 25.0% | 0.283 | 1455.300 | 4500.000 |
| Pi05 tuned / 相机角度扰动 | 60 | 15 | 25.0% | n/a | 1412.317 | 4500.000 |
| Pi05 tuned / 取消腕部相机 | 20 | 1 | 5.0% | n/a | 1687.450 | 4500.000 |
| Pi05 tuned / 机器人基座偏移 | 20 | 6 | 30.0% | 0.335 | 1410.200 | 4500.000 |
| Pi05 base-DROID / RoboChallenge弱适配 | 20 | 0 | 0.0% | 0.060 | 1702.500 | 4500.000 |
| GR00T N1.6 DROID / eager-no-flash fallback | 20 | 0 | 0.0% | 0.060 | 1702.500 | 4500.000 |

## 3. Pi05 120 任务结果怎么读

Pi05 tuned 的 RoboLab-120 完整结果是 34/120，成功率 28.3%。从属性看：

```csv
Category/Attribute,Success,Success %,Total,Score(total),Score(fail),Time(s),Time σ,EE SPARC,SPARC σ,PathLen(m),Path σ,Speed(cm/s),Speed σ
TOTAL,34,28.3,120,0.438,0.216,32.50,32.54,-8.08,3.18,4.12,3.51,5.2,1.5
PROCEDURAL,6,17.6,34,0.396,0.267,58.11,59.92,-9.41,2.97,5.47,3.93,4.8,1.3
  affordance,1,8.3,12,0.111,0.030,12.27,-,-10.72,3.28,4.13,3.36,3.7,1.1
  reorientation,1,16.7,6,0.556,0.467,39.07,-,-10.69,2.65,4.07,2.21,4.4,1.2
  sorting,3,25.0,12,0.525,0.367,90.40,75.28,-8.56,3.00,8.02,4.63,5.4,1.1
  stacking,1,16.7,6,0.472,0.366,26.13,-,-8.36,2.05,4.01,1.54,5.5,0.8
RELATIONAL,15,35.7,42,0.462,0.164,26.19,23.52,-7.77,3.49,3.45,3.02,5.3,1.5
  conjunction,5,62.5,8,0.781,0.417,29.81,15.57,-6.15,2.24,3.84,4.19,6.2,1.9
  counting,4,57.1,7,0.714,0.333,36.33,39.29,-10.09,4.61,3.65,2.84,5.3,2.1
  spatial,6,20.7,29,0.282,0.094,16.41,14.79,-8.04,3.56,3.57,2.93,4.9,1.2
VISUAL,20,23.8,84,0.396,0.207,41.29,38.58,-8.52,3.08,4.63,3.65,5.2,1.5
  color,6,23.1,26,0.441,0.273,31.20,16.95,-7.89,2.79,3.55,2.16,4.9,1.6
  semantics,14,23.3,60,0.371,0.180,45.57,44.71,-9.02,3.17,5.29,3.97,5.3,1.5
```

从难度看：

```csv
difficulty,episodes,successes,success_rate,episode_step_mean,score_mean,policy_inference_avg_ms_mean
complex,17,3,0.17647058823529413,2570.5882352941176,0.46422969593721275,11.941176470588236
moderate,39,10,0.2564102564102564,1359.7179487179487,0.4529914550292186,11.992307692307692
simple,64,21,0.328125,781.984375,0.3828125,12.0078125
```

核心解释：

1. 简单任务成功率最高，复杂任务最低，符合“错误会随子任务长度累积”的规律。`1_subtasks` 约 37.7%，`2_subtasks` 约 22.0%，更长任务普遍更差。
2. relational 总体高于 procedural，是因为 conjunction/counting 里有一些“选对并放入”的简单多对象任务；真正的 spatial 只有 20.7%。
3. procedural 最难，尤其 affordance、reorientation、stacking。它们不只要求看懂物体，还要动作轨迹、接触、姿态和稳定性都正确。
4. 失败主因不是渲染或资产缺失，而是 policy 在第一阶段 `object_grabbed` 上失败很多：120 任务里失败 family 为抓取/目标选择 67 次，放置/容器 8 次，堆叠 4 次，重定向 1 次，其他谓词 6 次。

## 4. 20 任务扩展和扰动实验怎么读

20 任务是从能力轴里抽出来的固定对照集合。它不是替代 120 任务，而是给模型/扰动做低成本横向比较。

Pi05 20 任务按轴：

```csv
axis,episodes,successes,success_rate,episode_step_mean,score_mean,policy_inference_avg_ms_mean
procedural,10,2,0.2,2172.9,0.26500000059604645,12.0
relational,11,2,0.18181818181818182,1433.3636363636363,0.29545454545454547,11.99090909090909
visual,18,5,0.2777777777777778,1267.0,0.24444444477558136,12.016666666666667
```

腕部相机 blackout：

```csv
axis,episodes,successes,success_rate,episode_step_mean,score_mean,policy_inference_avg_ms_mean
procedural,10,0,0.0,2475.0,,11.69
relational,11,1,0.09090909090909091,1527.1818181818182,,11.7
visual,18,1,0.05555555555555555,1524.9444444444443,,11.694444444444445
```

机器人基座偏移：

```csv
axis,episodes,successes,success_rate,episode_step_mean,score_mean,policy_inference_avg_ms_mean
procedural,10,3,0.3,2070.7,0.3200000002980232,11.709999999999999
relational,11,3,0.2727272727272727,1358.0,0.3181818181818182,11.745454545454544
visual,18,5,0.2777777777777778,1255.111111111111,0.28888888905445737,11.744444444444444
```

相机角度三组变体：

| variant | episodes | successes | success rate |
|---|---:|---:|---:|
| `randomize_external_camera` | 20 | 5 | 25.0% |
| `randomize_wrist_cam` | 20 | 5 | 25.0% |
| `randomize_wrist_and_external_cam` | 20 | 5 | 25.0% |

解释：

1. `Pi05 tuned / 20任务基线` 是 5/20，和 120 任务 28.3% 接近，说明 20 任务集合大体没有明显过易。
2. `取消腕部相机` 掉到 1/20，是目前最强的因果信号：策略对近距离抓取和放置的 wrist view 高度依赖。外部相机能看语义和全局布局，但很难提供夹爪-物体的精细相对位姿。
3. `相机角度扰动` 三个 variant 都是 5/20，表面看没有比基线差。但这不代表相机不重要，因为该实验每个 variant 只有 20 episode，且扰动可能仍在模型泛化范围内；更可靠的结论需要同任务多 seed 和连续角度 sweep。
4. `机器人基座偏移` 是 6/20，略高于 5/20，不能解读为偏移提升模型。更合理解释是：20 个任务样本小，某些任务因为初始几何/可达性变化刚好更容易，另一些更难，整体波动超过了一个任务的差距。

## 5. RoboChallenge 和 ReKep 怎么优化，未来怎么做公平对比

当前 probe 记录：

| policy | status | reason |
|---|---|---|
| `pi05` | `completed_in_phase_01` | Pi05 direct RoboLab policy server; 20-task rollout completed in phase 01. |
| `robochallenge_pi` | `adapter_required` | Local RoboChallenge pi05/Table30v2 ALOHA checkpoint exists, but it is not a RoboLab Franka+Robotiq joint-position websocket policy. |
| `rekep` | `planner_adapter_required` | ReKep is a keypoint/planner method and needs perception plus low-level controller adapters before RoboLab scoring. |
| `paligemma` | `checkpoint_or_runner_missing` | RoboLab runner supports PaliGemma only if the matching openpi-assets-simeval checkpoint and config are present. |
| `groot_n1_5_3b` | `adapter_required` | GR00T checkpoints are not currently exposed as a RoboLab Pi0-family websocket action policy. |
| `cosmos_policy` | `adapter_required` | Cosmos assets/checkpoints need task and action-schema adapter before Franka+Robotiq RoboLab rollout. |
| `qwen_vl_alibaba` | `not_action_policy` | Qwen/Qwen-VL models are VLMs unless paired with a robot action head; not directly scoreable as RoboLab policy. |

### RoboChallenge pi 的可行路线

RoboChallenge 本地 checkpoint 的主要问题是 schema 和 action contract 不一致。RoboLab 要的是 Franka+Robotiq 的 joint-position action chunk：`[N, 8] = 7个Franka关节目标 + 1个夹爪开合`。如果 RoboChallenge 是 ALOHA/Table30v2，则通常会遇到：相机命名不同、机器人关节维度不同、动作归一化不同、夹爪语义不同、甚至双臂/单臂结构不同。

可行路线分三档：

1. 轻量 schema bridge：只做 key 映射、图像 resize、action unnormalize、gripper convention 对齐。只有当底层机器人和动作语义接近时才可能有效。
2. Retarget adapter：把 ALOHA/其他机器人动作先转为末端位姿或任务空间轨迹，再用 Franka IK 转成 joint position。这个能跑，但效果取决于标定、速度限制、碰撞和 gripper 时序。
3. 重新微调 action head：把 RoboLab/DROID/RoboChallenge 数据统一成 Franka+Robotiq joint-position chunk，再用相同 observation schema 训练。这是最靠谱的路线，也是唯一适合做严肃成功率对比的路线。

### ReKep 的可行路线

ReKep 更像 planner baseline：语言和图像生成 keypoint/constraint，再用优化和控制器执行。它不是 VLA policy，所以不能直接塞进 `InferenceClient` 当每步 action server。

要做公平对比，应该把它实现为 planner-runner：

1. 从 RoboLab 多相机 RGB/深度或分割中提取目标物体、容器、关键点。
2. 把 2D keypoint 反投影到 3D，绑定到 USD/物理对象坐标。
3. 让 ReKep 生成约束和子目标，例如“夹爪到 banana 上方”“banana 到 bowl 内部”。
4. 用 Franka IK/RMPFlow/motion planner 执行子目标，记录同样的 episode_results、HDF5、视频、子任务日志。
5. 报告时标成 `planner baseline`，和 VLA 放同一成功率表可以，但必须单独列方法类型。

## 6. GR00T、Cosmos、Qwen/阿里模型能不能处理成 RoboLab 格式

| 模型类 | 能否处理成 `[N,8]` action chunk | 当前状态 | 需要做什么 |
|---|---:|---|---|
| GR00T DROID | 可以，已有 `policies/gr00t/client.py` 把 `action.joint_position + action.gripper_position` 拼成 `[N,8]` | 已跑 20 任务 fallback，0/20 | 修复 CUDA/flash-attn 环境，用官方 server 重跑；校准 action horizon、归一化和相机 schema。 |
| Cosmos3-Nano-Policy-DROID | 理论可以，RoboLab 已有 `policies/cosmos3/client.py`，server 返回 `action` | 4090 24GB OOM，未进 episode | 换 48GB+ GPU，或等待更小/量化 checkpoint。 |
| PaliGemma / pi0-family | 可以，但必须是 OpenPI action checkpoint，不是普通 VLM | runner 有入口，checkpoint/server 未完整落地 | 下载匹配 checkpoint，启动 server，先 smoke 再 20 任务。 |
| Qwen/阿里 VLM | 不能直接输出 action chunk | 当前只是视觉语言模型 | 加 action head 或作为 ReKep-style planner 的 perception/semantic 模块。 |
| ALOHA/Table30v2 checkpoint | 不能直接映射 | robot/action schema 不同 | retarget 或重新训练 Franka+Robotiq action head。 |

## 7. 为什么这些结果会这样

| 现象 | 更可能的原因 | 证据 |
|---|---|---|
| tuned Pi05 只有 28.3% | RoboLab 比普通 pick-place 更强调长程、多对象、空间关系和物理接触；训练数据覆盖不足会直接暴露。 | complex 17.6%，procedural 17.6%，抓取/目标选择失败 67 次。 |
| 大量失败停在 `object_grabbed` | 第一阶段目标 grounding 和抓取姿态没稳定。策略可能看懂语言，但没把目标物体定位成可执行 grasp。 | 120 任务失败 family 最大项是抓取/目标选择。 |
| wrist blackout 大幅下降 | 腕部相机提供近距离物体-夹爪相对位姿，去掉后闭环修正能力下降。 | 20 任务从 25% 到 5%。 |
| 相机角度扰动没有明显下降 | 扰动范围可能仍在训练分布附近；也可能 20 任务样本太小，统计波动掩盖影响。 | 三个 variant 都是 5/20，需要多 seed。 |
| base-DROID Pi05 和 GR00T fallback 都 0/20 | 不是模型“完全不会机器人”，而是 observation/action schema、训练任务分布、动作归一化、horizon、相机布局和本地 fallback 环境都不匹配。 | 两者 score_mean 只有 0.06，失败多卡在抓取。 |
| Cosmos 没有分数 | 不是策略失败，而是 server 在 4090 24GB 加载阶段 OOM。 | blocker JSON 和四次启动日志。 |

## 8. 如果要优化模型效果，训练数据应该怎么调

1. 统一 action contract：训练数据必须直接覆盖 Franka+Robotiq `[joint_pos_7 + gripper_1]` action chunk，包含相同 horizon、相同归一化、相同 gripper 0/1 语义。
2. 强化 wrist-view 数据：保留腕部相机，并加入 wrist camera pose jitter、遮挡、曝光变化；不要只训练外部相机。
3. 增加 hard negative：同色、同类、相似形状、多个容器、多个 distractor 同时出现，专门训练“选对目标而不是随便抓一个”。
4. 增加程序技能轨迹：堆叠、重定向、放入狭窄容器、从容器取出、多个物体顺序执行。这些是当前 procedural 短板。
5. 增加失败恢复数据：抓空、抓错、碰撞、物体滑落后如何重新定位和二次抓取。当前模型一旦第一抓失败，episode 往往拖到 timeout。
6. 做任务分解监督：不仅训练最终 action，还给模型或辅助 head 监督当前子任务状态，例如 target selected、grasp pose、place target、done predicate。
7. 多 seed、多场景扰动训练：相机角度、光照、背景、桌面材质、物体位置、容器尺寸都要覆盖，但要保留物理可行性边界。
8. 从成功轨迹中做 curriculum：先单物体、再双物体、再空间关系、再顺序任务、再动态/重定向，避免模型在长任务上一开始就学到噪声。

## 9. 后续测试建议

1. 所有模型先过 `probe -> server smoke -> 1 task artifact -> 20 task matched rollout -> 120 task full` 五级门禁。
2. 只有输出 `[N,8]` Franka+Robotiq action chunk 的模型，才能进入 VLA 成功率主表。
3. ReKep/Qwen 这类 planner 或 VLM 进入 planner/perception 表，使用同样 success metric，但方法类型单列。
4. 每个 20 任务对照至少跑 3 seeds，否则 5/20 和 6/20 这种差距不能下结论。
5. 每个结果必须同时提交：`episode_results.jsonl`、HDF5、视频、子任务日志、artifact inventory、read_results 表。
