# 精讲 8：论文实验总览与 Algorithm 1 空间约束求解器

<!-- FINAL-20260621-UPDATE:BEGIN -->

> [!TIP]
> **2026-06-21 复现实证更新**：现在本地已有一套完整 Pi05/RoboLab-120 实验结果，可作为论文实验体系的小规模复现锚点：成功率 `34/120 = 28.3%`，并已按能力轴、难度、任务长度输出 CSV。

<!-- FINAL-20260621-UPDATE:END -->


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

## 深挖 0：论文实验真正想证明的不是一个分数，而是一条证据链

这篇论文的实验体系可以按“从可用场景到可信结论”的证据链理解：

```text
场景生成质量
  -> 任务生成质量
  -> 策略 rollout 证据
  -> success / score / trajectory / event 统计
  -> 按能力轴和难度分组
  -> 扰动敏感性
  -> 真实世界相关性
```

每一层回答一个不同的问题：

| 层 | 核心问题 | 如果这一层不过关，会污染什么 |
|---|---|---|
| 场景生成 | 场景是否真实、合理、物理可用 | 后续策略失败可能只是场景垃圾 |
| 任务生成 | 指令和成功条件是否一致、可执行 | success/score 失去语义可信度 |
| rollout 记录 | 观测、动作、事件、视频是否可追溯 | 无法复查模型到底怎么失败 |
| 指标统计 | 成功率、score、轨迹质量是否区分清楚 | 平均成功率会掩盖部分完成和坏动作 |
| 分组分析 | 能力轴、难度、任务长度是否拆开看 | 无法定位视觉/关系/程序哪类能力弱 |
| 扰动敏感性 | 光照、背景、相机、位姿变化是否影响策略 | 无法判断模型是否只是碰巧适配某个设置 |
| 真实相关性 | 仿真排名是否和真实机器人评测同向 | 无法说明仿真 benchmark 对真实评估有用 |

**【绿色标识｜核心结论】**

RoboLab 的实验设计不是“跑 120 个任务得到一个排行榜”。更准确地说，它是在证明：这个 benchmark 产生的失败、趋势、敏感因素和真实世界排序有足够的信息量，能帮助分析 task-generalist policy 的泛化能力。

## 深挖 1：实验矩阵怎么读，别把所有结果混成一个平均数

论文里至少有四个维度会互相交叉：

| 维度 | 例子 | 读结果时要问 |
|---|---|---|
| policy | Pi0 / Pi0.5 / GR00T 等 | 哪个模型整体更强，是否只是某类任务强 |
| task attribute | color、semantics、spatial、stacking、reorientation | 强弱来自视觉、空间语言还是操作能力 |
| difficulty / horizon | simple、moderate、complex；子任务数量 | 长任务是否出现错误累积 |
| variation | lighting、background、camera、object pose | 模型是否对某个场景因素极敏感 |

所以一条实验记录至少应该包含：

```text
policy_id
task_name
task_attributes
difficulty
instruction_type
scene_variation_id
episode_id
success
score
event_log
trajectory_metrics
video / hdf5 path
```

这也是为什么本地复现不能只保存视频。视频能说明“看起来发生了什么”，但论文级分析需要 metadata 和结构化结果才能分组。

## 深挖 2：Success、Score、Event、Trajectory 四类指标各自回答什么

论文主表里有 success 和 score，后面还有 SPARC、speed、path length、event tracking 等指标。它们不是重复指标。

| 指标 | 说人话 | 典型解释 |
|---|---|---|
| `success` | 最终任务是否完全达成 | 适合排行榜，但太粗 |
| `score` | 子任务/事件完成程度 | 能区分完全失败和部分完成 |
| event log | 失败具体发生在哪里 | wrong object、drop、hit、tipped、out-of-scene |
| SPARC | 末端运动是否平滑 | 同样成功时，动作质量不同 |
| speed / path length | 动作是否高效、路径是否绕 | 反映控制质量和策略犹豫程度 |

举例：

| 现象 | success | score | event | 解释 |
|---|---|---|---|---|
| 抓对苹果但没放进碗 | False | 中等 | drop / incomplete | 感知可能对，放置或接触失败 |
| 抓了橙子放进碗 | False | 可能偏低 | wrong object | 目标绑定失败 |
| 完成任务但路径绕、抖动 | True | 1.0 | 可能无严重事件 | 任务成功但轨迹质量差 |
| 多步骤前两步成功，第三步失败 | False | 不为 0 | subtask incomplete | 长 horizon 错误累积 |

**【橙色标识｜容易误解】**

论文里的 score 不是 success 的同义词。`success=True` 通常意味着 score 达到最终完成口径；但 `success=False` 时，score 仍然能告诉你模型是不是完成了部分子任务。

## 深挖 3：主实验表应该按“能力画像”读

论文主表把 overall、difficulty、procedural、relational、visual 等维度放在一起。读法不是只看最高 overall，而是看画像：

| 画像 | 可能含义 |
|---|---|
| visual 高、relational 低 | 能识别物体属性，但空间语言/多对象关系弱 |
| simple 高、complex 低 | 单步或短 horizon 可以，长任务错误累积 |
| score 明显高于 success | 经常部分完成，但最后一个关键事件失败 |
| SPARC 更接近 0 但 success 不高 | 运动可能平滑，但任务语义/目标绑定失败 |
| speed/path length 很大 | 策略犹豫、绕路或反复修正 |

这类画像比“模型 A 比模型 B 高 3%”更有价值。RoboLab 的定位是分析 benchmark，不只是 leaderboard。

## 深挖 4：论文实验的六组验证如何互相支撑

| 实验 | 单独能说明什么 | 和其他实验如何互相支撑 |
|---|---|---|
| RoboLab-120 | 策略在任务集上的表现 | 给细粒度分析、真实相关性提供基础数据 |
| 细粒度分析 | 哪类能力弱 | 解释 RoboLab-120 平均分背后的失败结构 |
| 扰动敏感性 | 哪些场景因素影响策略 | 解释同一任务为什么在不同环境下表现不同 |
| 真实世界相关性 | 仿真趋势是否有现实意义 | 证明 RoboLab 不是只在仿真内部自洽 |
| 场景生成质量 | 自动场景是否可信 | 支撑 benchmark 可规模化生成 |
| 任务生成质量 | 自动任务是否语义可评测 | 支撑未来 benchmark 扩展不是纯人工瓶颈 |

这也是为什么精讲8要和精讲1、2、3、4、5、6、11、13、14 串起来看：

- 精讲1讲 real-to-sim 评估思想。
- 精讲2讲 scene/task/env 生成。
- 精讲3讲 task generation validation。
- 精讲4讲能力轴和难度公式。
- 精讲5/6讲 SPARC 和 MNPE。
- 精讲11讲 spatial/physical solver。
- 精讲13/14讲证据链和运行时代码。

精讲8在中间起“实验地图”的作用：告诉你每个机制最后服务于哪张表、哪类图、哪种结论。

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

### 场景生成质量表怎么读

Appendix C-D 的表不是在评估 policy，而是在评估“场景生成器”。它回答的是：主方法生成的桌面场景是否比 baseline 更适合作为 benchmark 场景。

| 读表维度 | 应该看什么 | 说明 |
|---|---|---|
| VQA | 渲染图是否满足文本问题 | 偏视觉一致性和可识别性 |
| Real. | 是否像真实桌面/工作台 | 对抗“网格摆拍感” |
| Func. | 是否能支持机器人操作 | 对抗“好看但不可操作” |
| Lay. | 布局是否自然、有组合关系 | 对抗均匀撒点 |
| Compl. | 场景是否完整 | 是否有足够对象和结构 |
| Qual. | 综合质量 | 人类/LLM judge 的整体观感 |
| #Obj | 对象数量 | 数量高不代表质量高，要和 Real/Func/Lay 一起看 |
| Pref. | GPT preference | 成对比较主方法和 baseline 的偏好 |

**【绿色标识｜核心结论】**

场景生成实验真正说明的是：谓词、solver 和反馈闭环让场景更像“可操作的真实桌面”，而不是只让 LLM 输出更多对象。

### 为什么 baseline 会输

baseline 的典型流程是：

```text
LLM 选对象 -> 网格位置 -> jitter -> 单次生成
```

它的问题是：

- 缺少 `place-in` / `place-on` 这样的语义关系，容器和支撑物不能形成真实组合。
- 网格布局天然有“摆拍感”，物体不容易形成真实的局部聚簇。
- 没有 feedback repair，失败样本很难在下一轮变好。
- 缺少物理/几何检查时，场景可能视觉上有对象，但作为机器人任务不可用。

主方法的优势来自：

```text
对象目录 + typed predicates + spatial solver + physical solver + validation + feedback
```

这就是为什么同样用 LLM，主方法和 baseline 的差异会很大：LLM 不是独立完成场景生成，而是被放进一个可验证的工程闭环。

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

### 任务生成质量实验怎么读

任务生成的难点不是“让 LLM 写 Python”，而是让自然语言目标、场景对象、成功谓词和物理可行性同时成立。

| 维度 | 它检查什么 | 失败例子 |
|---|---|---|
| relation match | 空间/逻辑关系是否一致 | 指令说左边，代码检查右边 |
| target match | 目标状态是否一致 | 指令说放进碗，代码检查放到盘子 |
| object match | 对象引用是否正确 | 指令说红杯，代码用蓝杯 |
| quantifier match | all/any/count 是否一致 | 指令说两个，代码只检查一个 |
| clarity | 语言是否清楚 | 指令含糊，不知道目标对象 |
| feasibility | 机器人和场景是否可完成 | 容器太小、堆叠不稳、对象不可达 |

**【橙色标识｜边界】**

LLM-as-judge 可以提高扩展速度，但不能完全替代人工验收。尤其是 predicate coverage 和物理可行性，最终还需要静态检查、场景资源检查和实际仿真 smoke 共同兜底。

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

## 深挖 5：4090 上怎么设计一个“像论文但可承受”的实验矩阵

完整 RoboLab-120 + 多策略 + 多扰动很重。4090 上更现实的做法是先做一个“小论文矩阵”：

| 轴 | 最小设置 | 为什么 |
|---|---|---|
| task | 每个能力轴 5 个，共 15 个 | 覆盖 visual/procedural/relational |
| difficulty | easy/medium/hard 各至少 3 个 | 看难度斜率 |
| policy | Pi05 先跑，再加 RoboChallenge Pi / ReKep 对照 | 先稳定主链路，再做方法对比 |
| episode | 每任务 1-3 条 | 先出趋势，不冒充统计显著 |
| variation | 选 1 个任务做 lighting 或 object pose sweep | 先验证敏感性 pipeline |
| artifacts | JSONL + HDF5 + video + event log | 保证能复查 |

输出应该至少包含四张表：

1. `task_result_table.csv`：每条 episode 的 success、score、step、reason。
2. `axis_summary.csv`：按 visual/procedural/relational 分组。
3. `difficulty_summary.csv`：按 easy/medium/hard 分组。
4. `failure_reason_summary.csv`：wrong object、drop、collision、timeout、predicate incomplete 等。

**【绿色标识｜核心结论】**

这个小矩阵不是论文级全量复现，但它的结构是论文级的：任务选择、指标、证据、分组和边界都对齐论文，只是样本量更小。

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
