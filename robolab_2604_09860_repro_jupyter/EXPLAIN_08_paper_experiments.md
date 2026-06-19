# 精讲 8：论文实验总览与 Algorithm 1 空间约束求解器

> **【绿色标识｜核心结论】** 论文里的“实验”不是单一跑分，而是一组互相支撑的验证：策略评测、细粒度分析、扰动敏感性、真实世界相关性、场景生成质量、任务生成质量。  
> **【蓝色标识｜源码路径】** 这些实验分别落在 `policies/pi0_family/`、`robolab/eval/`、`robolab/core/logging/`、`analysis/`、`robolab/scene_gen/`、`skills/robolab-taskgen/` 等模块。  
> **【橙色标识｜容易误解】** Algorithm 1 不是策略评测算法，也不是完整 3D 物理放置算法；它主要解决“桌面基础对象的 2D 布局约束”，后续的 `place-in`、`place-on` 等 3D 接触关系还要交给物理求解/settle。

## 先说结论

论文实验可以按 6 条主线理解：

| 实验主线 | 它回答的问题 | 主要输入 | 主要输出 | 代码/文件入口 |
|---|---|---|---|---|
| RoboLab-120 策略评测 | VLA/机器人策略在 120 个任务上到底能不能完成 | 任务集、策略服务、机器人环境 | success、score、subtask、episode log、视频、HDF5 | `policies/pi0_family/run.py`、`robolab/eval/runner.py` |
| 细粒度能力分析 | 失败到底来自视觉、空间关系、长时序还是程序操作 | episode 结果 + task metadata | 按属性/难度/对象数/子任务数分组的成功率 | `analysis/read_results.py`、`robolab/core/logging/results.py` |
| 扰动敏感性实验 | 光照、背景、桌面纹理、相机、物体初始位置变化会不会让策略崩 | variation rollout CSV / episode 结果 | 各扰动下成功率、MNPE 后验敏感性 | `policies/pi0_family/run_*_variation.py`、`analysis/sensitivity_analysis/` |
| 真实世界相关性验证 | RoboLab 仿真评测排名是否和真实机器人 arena 排名一致 | RoboLab score + RoboArena/Elo 类真实评测结果 | Spearman/Pearson 相关性 | 论文实验分析脚本口径，结果不等于单任务真实部署 |
| 场景生成质量实验 | 主方法生成的场景是否比 baseline 更真实、更完整、更可评测 | LLM 生成的场景、渲染图、VQA/GPT judge | VQA score、GPT preference、Real/Func/Lay/Compl/Qual | `robolab/scene_gen/llm_scene_gen/` |
| 任务生成质量实验 | 自动生成的任务代码和自然语言目标是否对齐、清晰、可行 | 任务代码、对象目录、谓词库、LLM judge prompt | alignment、clarity、feasibility、match、coverage | `skills/robolab-taskgen/`、任务验证脚本 |

一句话概括：

> RoboLab 不是只问“某个模型成功率多少”，而是把“场景是否可信、任务是否合理、策略是否泛化、扰动是否敏感、仿真排名是否有现实意义”拆开分别验证。

## 实验 1：RoboLab-120 策略评测

最核心的主实验是 RoboLab-120 benchmark。它评测一组通用机器人策略在 120 个任务上的表现。

输入可以理解成四类：

| 输入 | 说人话解释 |
|---|---|
| 任务定义 | 每个任务是一个 Python task class，里面有语言指令、场景、对象、子任务、成功条件 |
| 策略服务 | 例如 OpenPI/pi0/pi05 一类 VLA policy server，RoboLab 通过 client 请求动作 |
| 仿真环境 | Isaac Sim / Isaac Lab 负责物理、渲染、机器人状态和相机观测 |
| 运行参数 | `--task`、`--num-envs`、`--num-runs`、`--instruction-type`、`--video-mode` 等 |

输出不是一个单独数字，而是一整套 episode 证据：

| 输出 | 用途 |
|---|---|
| `episode_results.jsonl` | 每条 episode 的 success、score、耗时、步数、任务名、策略名等 |
| HDF5 | 离线计算轨迹指标、回放状态和观测 |
| 视频 | 人眼检查策略到底做了什么 |
| event/subtask log | 定位失败发生在抓取、悬停、放置、完成判定中的哪一步 |

**【蓝色标识｜源码路径】**

- `policies/pi0_family/run.py`：Pi0/Pi05 family 的命令行评测入口。
- `robolab/eval/runner.py`：共享评测循环，负责按任务创建 env、运行 episode、写出结果。
- `robolab/core/environments/runtime.py`：根据任务和 policy 组装 Isaac/RoboLab 环境。
- `robolab/core/logging/results.py`：把 episode 结果汇总成分组统计。

**【橙色标识｜我们当前复现边界】**

我们已经完成的是 Pi05 在简单任务和复杂任务抽样上的 smoke/小样本复现。它证明链路通了，但还不是完整 RoboLab-120。完整实验需要对 120 个任务、固定 policy 集合、足够 episode 数、统一输出目录和统一分析脚本全部跑完。

## 实验 2：按能力轴、难度和任务结构做细粒度分析

论文不只报平均成功率，因为平均数会掩盖失败原因。RoboLab 会把任务按多个维度拆开：

| 分析维度 | 它想看什么 |
|---|---|
| 能力轴 | visual、procedural、relational 三类能力是否表现不同 |
| 属性标签 | color、semantics、spatial relation、counting、stacking、reorientation 等 |
| 难度 | easy / medium / hard，来自子任务数量和最高需求级别 |
| 场景规模 | 物体数量变多后，策略是否更容易拿错对象或漏执行 |
| 子任务数 | 多步骤任务越长，错误是否累积 |
| 指令类型 | default / vague / specific 指令是否影响成功率 |

这个分析的关键是：每个任务本身携带 metadata。评测后，分析脚本不是重新理解视频，而是读取 task metadata 和 episode result 做分组。

**【蓝色标识｜源码路径】**

- `robolab/core/task/task.py`：任务对象上有 `attributes`、`subtasks`、instruction 等字段。
- `robolab/core/task/subtask_utils.py`：计算子任务数和难度分数。
- `robolab/constants.py`：保存技能权重、难度阈值、benchmark 类别等配置。
- `analysis/read_results.py`：按 attributes、difficulty、scene、wrong objects、instruction type 等维度读结果。

**【绿色标识｜怎么读结果】**

如果一个模型在 easy 任务上成功，但在 hard 任务上大幅下降，通常说明不是“看不见物体”，而是长 horizon、对象保持、阶段切换或恢复能力不足。  
如果 visual 属性下降明显，重点看颜色/语义识别；如果 relational 下降明显，重点看左右、前后、容器、并列/或/计数等语言结构。

## 实验 3：扰动敏感性和 MNPE

扰动实验问的是：模型是不是只会在“刚好这张桌子、刚好这个相机、刚好这个光照”下成功。

论文里关心的扰动包括：

| 扰动类型 | 示例 |
|---|---|
| 光照 | 颜色、阴影、昏暗、过曝 |
| 视觉背景 | HDR/背景、桌面纹理 |
| 物体初始位置 | 10 cm / 20 cm / 30 cm 级别随机扰动 |
| 相机位姿 | 外部相机、腕部相机的位姿变化 |

普通做法是逐个扰动看成功率。MNPE 更进一步：把扰动参数当成变量，观察“成功 episode 的参数后验分布”和“原始采样分布”差多少。

说人话：

> 如果某个相机角度在原始采样里很多，但成功样本里几乎没有，它就是高风险区域；如果成功样本都集中在某个窄范围，说明策略对这个因素很敏感。

**【蓝色标识｜源码路径】**

- `policies/pi0_family/run_lighting.py`
- `policies/pi0_family/run_background_variation.py`
- `policies/pi0_family/run_table_variation.py`
- `policies/pi0_family/run_camera_pose_variation.py`
- `analysis/sensitivity_analysis/posterior_inference.py`

**【橙色标识｜复现注意】**

扰动实验很耗 GPU，因为它不是多跑几个 episode，而是系统性扫参数。4090 上建议先固定一个任务、一个策略、一个扰动维度做小样本，再扩到多任务和多扰动。

## 实验 4：真实世界相关性验证

论文还做了 real-world verification：把 RoboLab 中的策略表现和真实世界 benchmark/arena 中的策略排名比较。

这个实验的核心不是证明“仿真等于真实”，而是看：

| 问题 | 解释 |
|---|---|
| 排名是否一致 | RoboLab 里更强的 policy，在真实 arena 中是否也更强 |
| 相关性是否为正 | RoboLab 分数和真实世界 Elo/score 是否同向 |
| 仿真是否有评估价值 | 即使绝对成功率不同，排名和趋势是否仍可用 |

**【橙色标识｜容易误解】**

这个实验是 policy-level 的相关性，不是说某个 RoboLab 单任务成功就能直接迁移到真实机器人。它更像“这个仿真 benchmark 是否能给真实评测前的模型筛选提供参考”。

## 实验 5：场景生成质量实验

论文 Appendix C-D 对比了主方法和 baseline 的场景生成质量。baseline 是精讲7讲过的“LLM 选物体 + 网格布局 + jitter”。主方法则使用对象目录、谓词、空间约束、物理检查和反馈修复。

评估指标包括：

| 指标 | 含义 |
|---|---|
| VQA score | 用视觉问答检查场景是否满足描述 |
| GPT preference | 让 GPT 在两种生成结果之间做偏好判断 |
| Real. | 场景是否真实 |
| Func. | 是否能支持任务操作 |
| Lay. | 布局是否合理 |
| Compl. | 场景是否完整 |
| Qual. | 综合质量 |
| #Obj | 场景包含对象数量 |

论文总体结果里，主方法相对 baseline 明显更高：例如 overall VQA 从约 0.398 提到约 0.554，GPT preference 从 18% 提到 82%。这说明主方法不只是“摆得更密”，而是更能生成可评测、有关系结构、视觉和功能上更合理的场景。

**【蓝色标识｜源码路径】**

- `robolab/scene_gen/llm_scene_gen/predicates.py`：谓词库，描述 `place-in`、`place-on`、`cluster-around`、相对位置等。
- `robolab/scene_gen/llm_scene_gen/spatial_solver.py`：Algorithm 1 对应的 2D 空间约束求解器。
- `robolab/scene_gen/llm_scene_gen/physical_solver.py`：处理容器、支撑、碰撞、稳定性等更接近 3D 物理的问题。
- `robolab/scene_gen/llm_scene_gen/feedback_system.py`：失败后收集错误并反馈给 LLM 修复。

## Algorithm 1：Spatial Constraint Solver 是干什么的

你图里这段 Algorithm 1 是场景生成实验的核心之一。它的作用是：

> 给定一堆对象和空间谓词，先在桌面 2D 平面上找一个大体合理、无碰撞、满足相对关系的基础布局。

### 输入

| 符号 | 代码里对应什么 | 解释 |
|---|---|---|
| `B` Objects | object states / object dims | 场景对象以及每个对象的尺寸、半径、当前状态 |
| `P` Predicates | predicate list | LLM 生成的空间关系，例如放在桌面、围绕某物、在某物左边 |
| `Lmax` Table Bounds | table bounds | 桌面可用区域，限制 `(x, y)` 不能飞出桌子 |

### 输出

| 输出 | 解释 |
|---|---|
| `(x, y, theta)` | 每个基础对象在桌面平面上的位置和朝向 |

这里强调“基础对象”很重要。比如“香蕉在碗里”，碗是基础对象，香蕉的精确 3D 放置可能由后续物理求解处理。Algorithm 1 主要解决“碗、盘子、杯子、工具等基础对象先怎么摆开”。

## Algorithm 1 三阶段拆解

### Phase 1：初始化

论文伪代码：

```text
Randomize (x, y) for all loose objects inside Lmax
if predicate is place-on-base:
    put object at specified x, y, theta
elif predicate is cluster-around:
    polar place targets around anchor
```

说人话：

1. 先把没有硬约束的对象随机撒到桌面范围内。
2. 如果某个对象被指定放在基础位置，就直接设置它的 `(x, y, yaw)`。
3. 如果某些对象要围绕一个 anchor，就用极坐标把它们摆在 anchor 周围。

为什么要这么做？因为 LLM 给的是语义关系，不一定给每个对象的精确坐标。求解器先把“明显关系”落实成一个初始几何布局。

### Phase 2：相对关系约束

论文伪代码：

```text
while constraints not satisfied:
    ApplyRelativeConstraints(P)
ApplyOrientations(P)
```

说人话：

如果任务说“红杯在碗左边”“勺子朝前”“三个物体围着盘子”，这一阶段会反复调整位置和朝向，直到这些相对关系大体满足。

注意：这不是高精度优化器，更像一个规则驱动的约束传播器。它把语言里的空间词转换为可执行的几何关系。

### Phase 3：碰撞消解

论文伪代码：

```text
for k = 1 to Kmax:
    C <- FindCollisions(B, margin)
    if C is empty:
        return Success
    if collision count not decreasing:
        PerturbPositions(B)
    for each collision pair:
        ResolveOverlap(...)
        ClampToBounds(...)
return Failure
```

说人话：

1. 检查对象之间有没有重叠或距离太近。
2. 没有碰撞就成功。
3. 如果碰撞数量长时间不下降，就轻微扰动对象，避免卡死在坏局部解。
4. 对每一对碰撞对象，把它们沿相反方向推开。
5. 推开后再把坐标夹回桌面范围，防止对象被推到桌外。

### Margin `M = [mu, 1.25mu, 1.5mu, 2.0mu]`

margin 是对象之间的安全间距。伪代码会尝试一组 margin 候选。直观理解：

| margin | 效果 |
|---|---|
| 小 margin | 更容易塞进密集场景，但对象距离更近 |
| 大 margin | 更保守，要求对象之间留更多空间 |

当前源码实现里也会根据对象数量和大对象数量调整基础 collision margin。密集场景会有更长的优化迭代预算。

## Algorithm 1 和源码怎么对上

**【蓝色标识｜源码路径】** `robolab/scene_gen/llm_scene_gen/spatial_solver.py`

| 论文伪代码 | 源码职责 |
|---|---|
| `SpatialConstraintSolver` | `SpatialSolver` 类 |
| `Input: Objects B, Predicates P, Table Bounds Lmax` | `solve(object_states, object_dims, max_iterations, fixed_objects, allow_relaxation)` |
| `Randomize loose objects` | `solve()` 中对非固定对象初始化/重采样 |
| `place-on-base` | `_apply_place_on_base(...)` 一类函数 |
| `cluster-around` | 极坐标围绕 anchor 放置 target 的逻辑 |
| `ApplyRelativeConstraints(P)` | `_apply_relative_position(...)` 一类函数 |
| `ApplyOrientations(P)` | orientation/yaw 约束处理 |
| `FindCollisions` | 碰撞检测函数簇 |
| `ResolveOverlap` | overlap 消解函数簇 |
| `ClampToBounds` | 坐标边界 clamp |

**【橙色标识｜代码边界】**

`spatial_solver.py` 解决的是 2D 桌面平面布局。真正的 `place-in`、`place-on`、容器尺寸、支撑稳定性、物理 settle，需要和 `physical_solver.py`、Isaac Sim 物理模拟一起看。

## 实验 6：任务生成质量实验

任务生成实验验证的是：自动生成出来的 task 代码是不是“语言目标、成功条件、物理可行性”都靠谱。

论文里的流程可以拆成：

| 步骤 | 说人话解释 |
|---|---|
| 生成任务代码 | LLM 根据对象目录、模板、谓词库、难度约束写 task class |
| 语法验证 | 代码能不能 import，类和字段是否完整 |
| 资源验证 | 用到的对象是否存在，是否在禁用集合，容器尺寸是否放得下 |
| 语义验证 | 语言指令和程序化 success condition 是否一致 |
| 失败修复 | 把错误反馈给 LLM，要求它改代码再验证 |

论文报告的 task generation 评估包括 alignment、clarity、feasibility、match、object coverage、predicate coverage 等指标。总体上，自动生成任务已经能达到较高对齐度，但 predicate coverage 不高，说明任务生成仍需要人工审查和迭代，不应被当成完全自动、无需验收的 benchmark 生产线。

**【蓝色标识｜源码路径】**

- `skills/robolab-taskgen/SKILL.md`
- `skills/robolab-taskgen/references/examples.md`
- `skills/robolab-taskgen/references/conditionals.md`
- `robolab/core/task/task_utils.py`
- `robolab/core/scenes/utils.py`

## 这部分和我们后续复现怎么衔接

要按论文口径继续推进，建议把实验分成 4 个层级，不要一上来盲跑 120 个任务：

| 层级 | 目标 | 4090 上的建议 |
|---|---|---|
| L1 链路验证 | 单任务能不能通，视频/HDF5/JSON 是否完整 | 已完成 Pi05 BananaInBowlTask |
| L2 复杂任务抽样 | 多对象、空间关系、重定向、堆叠是否能跑起来 | 已跑复杂任务抽样，可继续补 5-10 个 |
| L3 小型 benchmark | 每个能力轴抽一批任务，按 difficulty 分组 | 建议先 15-30 个任务，`num_envs=1` |
| L4 论文级复现 | RoboLab-120 + 多策略 + 扰动 + 分析脚本 | 需要全量资产、长时间 GPU、统一结果目录 |

**【绿色标识｜复现优先级】**

下一步最有价值的不是立刻全量 120，而是：

1. 固定 Pi05，扩到每个能力轴至少 5 个任务。
2. 每个任务保存 `episode_results.jsonl`、HDF5、视频和子任务日志。
3. 用 `analysis/read_results.py` 按能力轴、难度、任务长度出表。
4. 再选一个成功率中等的任务做光照/背景/物体位置扰动。
5. 最后才把同一套任务换成 RoboChallenge pi 或 ReKep 做对照。

这样得到的结论会比“下载没齐就盲跑 RoboLab-120”更可信。

## 最容易混淆的三件事

| 容易混淆 | 正确认知 |
|---|---|
| 场景生成实验 vs 策略评测实验 | 场景生成实验评估生成环境质量；策略评测实验评估模型执行任务能力 |
| Algorithm 1 vs 物理仿真 | Algorithm 1 做 2D 空间约束；Isaac/physical solver 做 3D 接触、稳定性和渲染 |
| 单任务成功 vs 论文级复现 | 单任务成功证明链路通；论文级复现需要固定任务集、策略集、采样次数和分析脚本 |

## 小结

论文实验的主线可以记成：

```text
生成可信场景 -> 生成可验证任务 -> 跑策略 -> 记录 episode -> 分组分析 -> 扰动敏感性 -> 和真实世界排名对照
```

Algorithm 1 位于第一步“生成可信场景”里。它不是最终评测指标，但它决定了场景能否在几何上成立。如果这一步失败，后面的任务、物理 settle、策略评测都会被污染。
