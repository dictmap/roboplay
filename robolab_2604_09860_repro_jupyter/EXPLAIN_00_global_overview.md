# 精讲 0：RoboLab 全局总览，先把整件事讲透

> [!NOTE]
> **颜色标识**：绿色表示核心结论，蓝色表示源码/输入输出路径，橙色表示边界、风险和容易误解的点。

## 先说结论

RoboLab 不是“一个能跑 pick-and-place 的仿真 demo”，而是一套用高保真仿真评估真实世界通用机器人策略的 benchmark 框架。它真正要解决的问题不是“机器人能不能在一个固定场景里拿香蕉”，而是：

```text
真实世界数据训练出来的通用策略
  在高保真、可控、可扩展的仿真任务里
  到底能不能泛化到新物体、新语言、新空间关系、新操作流程和新视觉扰动？
```

> [!TIP]
> **核心结论**：RoboLab 的主线是“把真实策略放进可控仿真考场”。场景、任务、机器人、策略、相机、光照、背景和指标是分层解耦的。这样同一个任务可以换策略，同一个策略可以跑不同任务，同一个任务还可以系统化改变相机/光照/材质来分析鲁棒性。

一句话记住：

```text
RoboLab = 高保真场景 + 语言任务 + 任务谓词 + Isaac Lab 环境 + VLA policy 接口 + 多维指标 + 敏感性分析
```

## 1. 论文为什么要做 RoboLab

论文的背景是：机器人 foundation policy 已经越来越强，但评测很容易出现两个问题。

| 问题 | 说人话解释 | RoboLab 的应对 |
|---|---|---|
| 训练域和评测域太像 | 模型可能只是熟悉 benchmark，而不是具备真正泛化能力 | 用真实数据训练的策略，在高保真仿真里做新任务评测 |
| 只看 success 太粗 | 成功/失败不能解释错在哪里、动作顺不顺、对相机/光照是否脆弱 | 输出 success、score、subtask/event、SPARC、speed、path length、MNPE 敏感性 |
| 任务太静态 | 固定任务集容易被刷熟，不能长期保持挑战 | 支持人工和 LLM 辅助生成场景/任务 |
| 真实世界评测太贵 | 真实机器人跑 120 个任务、多个策略、多个扰动成本很高 | 用 Isaac Sim / Isaac Lab 构造可重复、可批量运行的仿真评测 |

> [!WARNING]
> **不要把它理解成 sim2real 训练框架**：RoboLab 论文重点是评估真实世界策略，不是主要拿仿真数据去训练策略。它关心的是“真实策略在仿真考场里的表现是否能揭示泛化问题”。

## 2. 全局数据流

从最上层看，一次 RoboLab 评测大概是下面这条链：

```text
论文/任务设计
  -> 资产库：USD/SimReady objects, fixtures, robots, backgrounds
  -> 场景：某个 USD scene，里面摆好对象和支撑关系
  -> 任务：Task Python 类，写语言指令、成功条件、subtasks
  -> 注册：auto_env_registrations 把 task 变成 gym env id
  -> 环境：create_env / RobolabEnv / Isaac Lab managers
  -> 策略：Pi0/Pi05/GR00T/PaliGemma/ReKep 等接口适配
  -> episode：仿真 step、policy action、event tracking、recorder
  -> 输出：video, HDF5, event log, episode_results.jsonl
  -> 分析：success/score/axis/difficulty/SPARC/MNPE
```

对复现来说，最重要的是每一层都要有证据：

| 层 | 输入 | 输出 | 证据文件 |
|---|---|---|---|
| 安装层 | RoboLab repo、`uv sync`、Isaac Sim/Lab 依赖 | Python 环境可导入 | `uv_freeze.txt`、安装日志 |
| 资产层 | LFS 场景/物体/机器人/背景 | 可加载的 USD assets | 资产目录大小、缺失资产报错 |
| 任务层 | `Task` 类、scene、instruction、subtasks | task metadata / env id | `task_metadata.json`、task py 文件 |
| 环境层 | task name、robot、camera、variation | Isaac Lab env | `env_cfg.json`、Isaac 日志 |
| 策略层 | observations、language prompt | action chunk | OpenPI server log、policy timing |
| episode 层 | actions + simulation steps | success/score/events/video/HDF5 | `episode_results.jsonl`、`log_0_env0.json`、`run_0.hdf5`、mp4 |
| 分析层 | 多任务 episode records | 表格、图、posterior | summary csv/json、notebook 图表 |

> [!NOTE]
> **源码/输入输出路径**：复现时不要只看终端有没有报错。真正的闭环证据是 `output/<run_id>/.../episode_results.jsonl`、任务 event log、HDF5、视频，以及 notebook 里同步出来的 `remote_outputs/` 和 `robolab_repro_artifacts/`。

## 3. 代码目录按职责看

RoboLab 仓库可以先按职责分成十块，不要一上来平铺读所有文件：

| 目录/文件 | 负责什么 | 该怎么读 |
|---|---|---|
| `robolab/constants.py` | 包根目录、资产目录、输出目录、能力权重、难度阈值 | 先看路径和全局常量 |
| `assets/` | scene/object/fixture/robot/background 等 USD 资产 | 跑任务报缺资产时回到这里 |
| `robolab/tasks/benchmark/*.py` | 每个 benchmark 任务的定义 | 读 language、scene、termination、subtasks |
| `robolab/tasks/_metadata/` | 任务索引和 metadata | 按任务名看能力轴、难度、subtask 数 |
| `robolab/core/task/` | 条件谓词、subtask、task 基类 | 读 success/score 是怎么计算的 |
| `robolab/core/environments/` | 从任务名创建 Isaac Lab env，并管理 episode 生命周期 | 读 `create_env`、`RobolabEnv.step`、reset/freeze |
| `robolab/registrations/` | 把任务注册成 gym env | 读 auto registration 如何绑定 robot/camera/background |
| `robolab/variations/` | 相机、灯光、背景等扰动配置 | 读 sensitivity / robustness 实验 |
| `policies/pi0_family/` | Pi0/Pi05 policy runner 和 client | 读 observation/action 如何接 OpenPI |
| `analysis/sensitivity_analysis/` | MNPE/NPE 后验分析 | 读 CSV -> `theta/x` -> posterior |

> [!TIP]
> **阅读顺序**：先读 `BananaInBowlTask`，再读 `conditionals.py` / `subtask.py`，再读 `runtime.py:create_env`，最后读 `policies/pi0_family/run.py`。这样能从一个具体任务把整条链串起来。

## 4. 一个任务到底“标注”了什么

RoboLab 的“标注”不是传统视觉数据集那种 bounding box 或 segmentation mask。一个 RoboLab task 的标注更像“可执行任务规范”。

以 `BananaInBowlTask` 为例，一个任务至少包含：

| 字段 | 说人话 | 作用 |
|---|---|---|
| `scene` | 用哪个 USD 场景 | 决定桌面、碗、香蕉等对象在哪里 |
| `contact_object_list` | 哪些对象需要 contact sensor | 抓取、碰撞、掉落等事件依赖它 |
| `instruction` | 给策略看的语言任务 | policy 输入的一部分 |
| `terminations` | 成功/失败/超时条件 | 决定 episode 什么时候结束 |
| `attributes` | 颜色、语义、空间、堆叠、重定向等标签 | 后续按能力轴统计 |
| `subtasks` | 把任务拆成可评分步骤 | 用来算 partial score 和错误分析 |

所以：

```text
Task = 场景 + 语言 + 对象 + 成功条件 + 子任务评分 + 能力标签
```

> [!NOTE]
> **关键区别**：RoboLab 不是先录一段视频再人工标注“哪一帧成功”。它是先把任务目标写成代码里的谓词和 subtask，episode 运行时自动判断事件、成功条件和分数。

## 5. 场景、任务、环境三者不要混

这三个词非常容易混，必须拆开：

| 概念 | 是什么 | 例子 |
|---|---|---|
| Scene | 世界里有什么对象，摆在哪里 | `banana_bowl.usda` |
| Task | 要完成什么目标，怎么判成功 | “put the banana in the bowl” + `object_in_container` |
| Environment | 把 scene/task/robot/camera/policy/variation 装配成能 step 的仿真 | `gym.make(task_env, cfg=env_cfg)` |

论文说的三步是：

```text
1. 定位和定向物体，创建场景
2. 把目标状态写成语言任务
3. 选择机器人、策略、摄像头、光照、背景等变化，实例化环境
```

源码里对应为：

```text
scene/import_scene
  -> Task class
  -> registration / parse_env_cfg / create_env
  -> RobolabEnv
```

> [!WARNING]
> **不要用“能打开场景”替代“任务复现成功”**：USD 能加载，只说明资产和 stage 基本可用；任务成功还需要 contact sensor、termination、subtask、policy action、recorder 都正常。

## 6. 策略接入层：Pi05 是怎么进来的

RoboLab 自己不把 OpenPI 权重硬编码进任务里。它让任务和策略解耦：

```text
RoboLab env observation
  -> Pi0/Pi05 client 打包成 OpenPI 请求
  -> OpenPI server 根据图像/关节/夹爪/语言输出 action chunk
  -> client 拆 action
  -> env.step(action)
```

对 Pi05 来说，我们这次关心的几类输入是：

| 输入 | 来源 | 作用 |
|---|---|---|
| 外部相机图 | RoboLab camera render | 看桌面和目标物 |
| 腕部相机图 | wrist camera render | 看末端附近细节 |
| 关节位置 | robot state | 让 policy 知道机械臂状态 |
| 夹爪状态 | robot state | 控制抓取/释放 |
| 语言指令 | Task instruction | 告诉 policy 当前目标 |

输出是 action chunk，也就是一段连续动作。client 会按 `open_loop_horizon` 执行一小段，再重新请求下一段动作。

> [!TIP]
> **怎么判断策略真的接上了**：只看 Isaac 启动不够。要看到 OpenPI server restored checkpoint、8000 端口监听、policy inference timing、episode_results 里有真实 policy 字段和动作导致的 success/score。

## 7. 4090 上我们已经复现到哪一步

这部分必须说实话，不能把 smoke 当完整 benchmark。

已经完成：

| 项目 | 状态 | 含义 |
|---|---|---|
| RoboLab 环境安装 | 已完成 `uv sync` | Isaac Sim 5.0 / Isaac Lab 2.2 / RoboLab 可导入 |
| 资产补齐 | 已按任务补齐核心 scenes/robots/fixtures | 足够跑 Banana 和一批 subset，但不是完整 LFS 全量 |
| no-policy smoke | 累计 21 个任务初始化和日志导出 | 证明环境链路可启动，不代表策略成功率 |
| Pi05 checkpoint | 已下载并校验 | OpenPI 权重文件可加载 |
| Pi05 server | 已监听 8000 | 策略服务端可用 |
| 单任务闭环 | BananaInBowlTask 成功 | 证明 Pi05 -> RoboLab -> Isaac -> 视频/HDF5/JSON 通了 |
| 复杂任务抽样 | 3 个任务，1 成功 2 失败 | 初步看到长时序/集合/重定向更难 |

还没完成：

| 项目 | 为什么还不能说完成 |
|---|---|
| 完整 RoboLab-120 | 需要更多资产、更多 GPU 时间和严格结果汇总 |
| 正式 MNPE | 需要同一任务/策略在多组扰动参数下的大量 rollout CSV |
| RoboChallenge pi / ReKep 对比 | 需要统一任务、接口、相机、动作空间、成功条件后才能公平比较 |
| 论文级表格复现 | 小样本 smoke 不能和论文完整 benchmark 直接比较 |

> [!WARNING]
> **结果口径**：环境成功、策略接上、任务成功、论文复现是四个层级。当前已经有真实 Pi05 单任务成功闭环和复杂任务抽样，但还不是完整 RoboLab-120 论文表格复现。

## 8. 为什么不能一上来跑 120 个任务

RoboLab-120 全量评测不是一条命令就能可信完成，至少有四个约束：

1. **资产完整性**：很多任务依赖不同 object/material/background LFS 文件，缺一个就会在 Isaac 初始化时报错。
2. **4090 显存**：24GB 可以跑单任务和小子集，但复杂任务、高清相机、视频/HDF5、policy server 同时占资源时很容易接近上限。
3. **时间成本**：完整 benchmark 是几十 GPU 小时量级，失败重跑也要成本。
4. **统计口径**：中途失败要区分环境失败、资产失败、策略失败、timeout，不能只把所有非 0 return code 混成失败率。

正确路线是：

```text
单任务闭环
  -> 能力轴小子集
  -> 补齐资产失败项
  -> 每类任务多 episode
  -> 输出统一 CSV/JSON
  -> 再扩展 RoboLab-120
```

> [!TIP]
> **4090 策略**：先 `num_envs=1` 保守跑通，确认显存、视频、HDF5、episode_results 稳定后再加并行度。不要为了看起来快，直接把并行度拉爆导致半路 OOM。

## 9. 论文里的七个核心机制如何互相连接

前面的精讲 1-6 分别拆单点。全局上，它们是一个闭环：

| 精讲 | 解决的问题 | 在全局里的位置 |
|---|---|---|
| 精讲 1 real-to-sim eval | 为什么不用逐场景 3DGS/NeRF 重建，而用高质量资产和程序化场景快速评测 | 评测场景来源 |
| 精讲 2 scene/task/env | 场景、任务、环境如何装配 | 可执行仿真的骨架 |
| 精讲 3 TaskGen | LLM 如何生成/验证/修复任务代码 | 扩展任务规模 |
| 精讲 4 能力轴/难度 | visual/procedural/relational 和 difficulty 如何标记 | 评测维度 |
| 精讲 5 SPARC | 动作平滑度怎么量化 | 连续轨迹指标 |
| 精讲 6 MNPE | 成功/失败和扰动参数如何关联 | 鲁棒性诊断 |

如果只看其中一个，会容易误解：

| 只看某一块 | 容易误解成 | 实际应该放回全局理解 |
|---|---|---|
| 只看场景 | RoboLab 是资产库 | 场景只是任务评测的物理载体 |
| 只看任务类 | RoboLab 是 hard-coded task list | Task 是目标状态规范，可人工/LLM 扩展 |
| 只看 success | 模型强弱只有二值成功率 | 还要看 subtask score、错误类型、轨迹质量、敏感性 |
| 只看 Pi05 成功 demo | 已复现论文 | 单任务成功只是闭环证据，不是 RoboLab-120 |
| 只看 MNPE | 可以不用跑任务直接分析 | MNPE 必须依赖大量扰动 rollout 数据 |

## 10. 一次完整复现应该长什么样

我建议把“完整复现”分成五级，而不是只说“跑没跑成”。

| 等级 | 名称 | 通过标准 |
|---|---|---|
| L0 | 安装级 | RoboLab / Isaac Sim / Isaac Lab / OpenPI 可导入 |
| L1 | 环境级 | no-policy smoke 能创建 env 并导出 episode log |
| L2 | 策略级 | Pi05 server 接上，policy runner 能执行真实动作 |
| L3 | 单任务闭环 | 单任务成功，有 video/HDF5/event/episode_results |
| L4 | 小子集评测 | 多任务覆盖 visual/procedural/relational，有成功/失败分析 |
| L5 | 论文级复现 | RoboLab-120 或明确子集，多策略/多扰动/统计汇总/可复查证据 |

当前学习包已经到 L3，并有 L4 的初步抽样证据；还没到 L5。

> [!NOTE]
> **这也是 notebook 的结构**：前面记录安装和证据，中间讲源码与论文机制，后面放运行结果、指标、可视化、学习日志和最终 gate。这样每一步都有可复查文件，而不是只靠终端输出。

## 11. RoboChallenge pi、OpenPI pi05、ReKep 怎么放在同一张图里

这几个东西不要混成“都是一个模型”。

| 名称 | 更像什么 | 什么时候用 |
|---|---|---|
| RoboLab | 评测框架和 benchmark | 需要统一任务、场景、指标、视频/HDF5 输出时 |
| OpenPI pi05 | VLA policy checkpoint / server | 需要在 RoboLab 里跑真实 learned policy 时 |
| RoboChallenge 的 pi | 另一个项目语境里的策略/接口资产 | 做对比前要先适配 observation/action 和成功条件 |
| ReKep | 偏基于关键点/约束/规划的机器人方法 | 做“学习策略 vs 结构化方法”对比时 |

公平对比的前提：

```text
同一任务
同一场景或可说明差异的场景
同一机器人/动作空间或明确适配层
同一相机/观测输入
同一成功条件和 subtask score
同一 episode 数和随机种子策略
同一输出格式
```

否则结果只能叫“跑通案例”，不能叫 benchmark 对比。

## 12. 最后用一张总图记住

```text
为什么评测
  -> 真实策略泛化难，只看 success 不够

评测什么
  -> RoboLab-120：visual / procedural / relational
  -> simple / moderate / complex

在哪里评测
  -> Isaac Sim + Isaac Lab + USD/SimReady assets

怎么定义任务
  -> Task = scene + instruction + termination + subtask + attributes

怎么跑策略
  -> RoboLab env observation -> policy client/server -> action chunk -> env.step

怎么留证据
  -> episode_results.jsonl + event log + HDF5 + video + notebook artifacts

怎么分析
  -> success / score / subtask / error reason / SPARC / MNPE

当前状态
  -> Pi05 单任务成功闭环已完成，复杂任务抽样已完成，完整 RoboLab-120 尚未执行
```

> [!TIP]
> **一句话总括**：RoboLab 的价值不是“做了一个更漂亮的仿真场景”，而是把任务定义、策略接口、可控扰动、细粒度指标和可回放证据组织成一套评估通用机器人策略泛化能力的实验系统。

