# 精讲问题来源与核心内容索引

> **【绿色标识｜核心结论】** 这张索引不是新的论文精讲，而是所有精讲的“出处地图”。它回答：每个精讲为什么要讲、问题来自论文哪一节/哪张图/哪个 appendix/哪段代码、原始内容的核心是什么、我们在复现里应该怎么用。  
> **【蓝色标识｜主要来源】** 论文 [RoboLab arXiv HTML](https://arxiv.org/html/2604.09860v3)、项目页 [NVIDIA RoboLab](https://research.nvidia.com/labs/srl/projects/robolab/)、官方代码 [NVlabs/RoboLab](https://github.com/NVlabs/RoboLab)、本地远端 4090 复现证据 `remote_logs/` / `remote_outputs/`。  
> **【橙色标识｜边界】** 下面的“来源核心内容”是可溯源摘要，不是论文或源码逐字摘录。要核查完整上下文，应点开对应论文节、appendix 或 GitHub 文件。

## 先看这张总表

| 精讲 | 要回答的问题 | 核心来源 | 来源里的核心内容 | 复现/代码落点 |
|---|---|---|---|---|
| 00 全局总览 | RoboLab 到底是 benchmark、生成框架还是复现工程？ | Paper Abstract / Introduction / III RoboLab / IV Experiments；GitHub README | RoboLab 用高保真仿真评测真实数据训练的通用策略，强调任务泛化、细粒度分析和可扩展场景/任务生成 | `README.md`、`robolab/eval/`、`robolab/scene_gen/`、本 notebook 全局路线 |
| 01 real-to-sim 评估 | 论文说的真实场景到模拟评估，RoboLab 实际怎么做？ | Paper II-B Real-to-sim Evaluation；III-A Scene/Task Generation | 不是逐场景视频重建，而是用高质量资产、程序化布局、物理检查和扰动矩阵快速构造可评测仿真场景 | `assets/`、`scene_gen/`、Isaac Sim/Isaac Lab、variation runners |
| 02 场景/任务/环境生成 | 从场景到任务再到 env 的三步如何落到代码？ | Paper III-A；Figure workflow；GitHub `robolab/scene_gen`、`robolab/core/environments` | 先定位和定向对象形成 scene，再用语言目标定义 task，最后绑定 robot、policy、camera、lighting、background 生成 environment | `runtime.py`、task registry、scene configs、policy runner |
| 03 扩展任务生成 | LLM 生成任务代码怎样验证和修复？ | Paper III-A 2；Appendix D；`skills/robolab-taskgen` | LLM 生成 task code 后做语法、资产、容器尺寸和物理可行性验证，失败后把错误打回 prompt 修复 | taskgen skill、`conditionals`、`load_task_from_file`、asset validation |
| 04 能力轴/难度 | visual、procedural、relational 和难度分数怎么定义？ | Paper III-B Benchmark Design；Figure 4；Appendix A | 任务可多标签，不是单一能力；难度由子任务长度和最高需求级别共同决定 | task metadata、`subtask_utils.py`、`constants.py` |
| 05 SPARC | 轨迹平滑度为什么要看频谱弧长？ | Paper III-C Trajectory Metrics；SPARC reference；analysis metrics | 成功率不说明动作质量，SPARC 用速度频谱复杂度衡量末端运动平滑性 | HDF5 trajectory、`analysis/read_results.py`、trajectory metrics |
| 06 MNPE | 扰动敏感性为什么要做 posterior，而不是只看平均成功率？ | Paper III-D；Appendix B；`analysis/sensitivity_analysis/posterior_inference.py` | 把 lighting/camera/object pose 等扰动作为参数，学习成功/失败条件下参数后验分布，定位高风险区域 | variation CSV、posterior inference、sensitivity plots |
| 07 Baseline 方法 | Appendix C-C 的 baseline 是什么，为什么不是策略 baseline？ | Paper Appendix C-C Baseline Method | baseline 是 scene generation 对照：LLM 选物体 + 网格布局 + jitter + settle；缺少谓词、solver 和反馈修复 | grid+jitter toy baseline、scene generation comparison |
| 08 实验总览 | 论文实验不是单一跑分，它的证据链是什么？ | Paper IV Experiments；III-C Metrics；Appendix C-D / D | 组合验证 RoboLab-120、细粒度分析、扰动敏感性、真实相关性、场景生成质量和任务生成质量 | `runner.py`、`results.py`、dashboard、analysis scripts |
| 09 DTGE | Task generation evaluation 具体评什么？ | Paper Appendix D Details on Task Generation Evaluation | 用 LLM-as-judge 和静态分析评估 instruction 与 code success condition 的关系、对象、量词、清晰度和可行性 | AST 抽取、judge prompt、task generation metrics |
| 10 Prompt 设计 | 为什么 scene prompt 要写这么多规则？ | Paper Appendix C Stage I；Figure prompt examples | prompt 把真实场景原则、坐标系、placement types、JSON-only、对象目录和尺寸限制注入给 LLM | prompt schema、catalog injection、JSON validation |
| 11 Spatial/Physical/Feedback | 2D 空间求解、3D 物理放置和失败反馈如何串起来？ | Paper Appendix C-B；Algorithm 1；Figure 17；Algorithm 2；`spatial_solver.py` / `physical_solver.py` | Spatial 先解 base 2D 位姿，Physical 再解 `place-on` / `place-in`，失败反馈回到 LLM 修复 | `spatial_solver.py`、`physical_solver.py`、`feedback_system.py` |
| 12 Gaussian/前沿 | 本文用了哪些 Gaussian 思路，和 2026 NVIDIA 前沿有什么关系？ | Paper real-to-sim discussion / MNPE KDE；NVIDIA NuRec、3DGUT、Lyra、Isaac Sim sources | RoboLab 本文不是主打 3DGS 重建；Gaussian 更多出现在相邻 real-to-sim 路线和 MNPE KDE，前沿路线可作为后续扩展 | NuRec/3DGUT/Lyra links、Isaac Sim、future reading |
| 13 剩余核心内容 | 还有哪些评测侧问题没有在前面讲透？ | Paper III-C / IV-B / IV-D / Appendix A / Limitations | success 与 score、语言变体、复杂度 sweep、event tracking、真实相关性和统计置信共同构成论文级证据 | `episode_results.jsonl`、event log、dashboard、analysis |
| 13b 证据链深挖 | 单条 rollout 怎么变成论文级结论？ | Paper metrics + event tracking + dashboard/result schema | 视频、人眼判断、HDF5、JSONL、event log、dashboard 角色不同，不能混用 | HDF5、event JSON、`results.py`、dashboard loader |
| 14 runtime 主链 | 真实策略评测代码从哪里开始，证据怎么落盘？ | GitHub `robolab/eval/runner.py`、`episode.py`、`base_client.py`、Pi05 client、`summarize.py` | runner 选任务和输出目录，episode 逐步执行 policy，client 请求动作，summary 写结果 | `runner.py`、`episode.py`、policy client、summary |
| 14b runtime 深挖 | 多 env、action chunk、WorldState、EventTracker 这些状态边界怎么理解？ | GitHub runtime/eval/world/logging source files | 多 env 要按 env_id 隔离 chunk 和 episode；WorldState 支撑谓词；EventTracker 记录稀疏失败事件；HDF5/JSONL 是证据源 | `WorldState`、`EventTracker`、RecorderManager、dashboard |
| 15 审稿人视角 | 如果作为审稿人，这篇论文强在哪里、弱在哪里？ | Paper full text；Limitations；GitHub install/runtime evidence | 贡献是 benchmark+生成+诊断工具链；风险在仿真真实性、资产依赖、统计样本和生成任务验收 | reviewer rubric、未来路线、复现边界 |
| 16 推荐阅读 | 读完 RoboLab 后该补哪些 2026-first 相关工作？ | RoboLab related work；官方项目页；OpenPI、Isaac、Lightwheel、RDT、RoboCasa365 等来源 | 把后续阅读按 policy、benchmark、asset、sim-to-real、world model、real data 等路线组织 | source-linked reading map |
| 17 深水机制手册 | 怎样把所有精讲从章节覆盖推进到源码状态机级深读？ | Paper III/IV/Appendix B-C-D；NVIDIA 项目页；GitHub runtime/scene/eval/dashboard tree；本地 4090 artifacts | 把 RoboLab 视为评测编译器：task contract、typed predicates、env binding、policy rollout、WorldState/EventTracker、证据产物、扰动探针、baseline adapter 边界和 4090 分层复现 | `TaskContract`、typed predicates、policy client、WorldState/EventTracker、`episode_results.jsonl`、HDF5、video、artifact gates |

## 按论文结构反查精讲

| 论文位置 | 原问题 | 对应精讲 |
|---|---|---|
| Abstract / Introduction | 为什么需要新的仿真 benchmark？现有 benchmark 为什么会饱和或域重叠？ | 00、01、08、15 |
| II-B Real-to-sim Evaluation | 为什么不逐场景重建真实视频？RoboLab 的 scale 优势在哪里？ | 01、12 |
| III-A Scene and Task Generation | 场景、任务、环境如何生成和验证？ | 02、03、10、11 |
| III-B Benchmark Design | 三条能力轴、任务属性、子任务和难度如何定义？ | 04 |
| III-C Metrics | 为什么不能只看成功率？score、语言变体、trajectory metrics 如何补充？ | 05、08、13、13b |
| III-D Sensitivity | 如何找出哪些扰动最影响策略？ | 06、08 |
| IV Experiments | 论文实验具体证明了什么？ | 08、13、15 |
| IV-D Real-World Verification | 仿真评测如何与真实世界排名关联？ | 08、13、15 |
| Appendix A | 统计显著性、复杂度、score gap 和异常 horizon 怎么解释？ | 13、13b |
| Appendix B | MNPE 变量、prior、posterior 和 importance correction 怎么理解？ | 06 |
| Appendix C | scene generation prompt、solver、baseline 和 scene quality experiment 怎么实现？ | 07、10、11、08 |
| Appendix D | task generation judge 怎么评估自动任务？ | 03、09 |
| GitHub eval/runtime | 策略评测代码怎么运行，结果怎么保存？ | 14、14b |
| Cross-cutting mechanism | 论文概念、源码状态、复现证据如何连成一条调试路径？ | 17 |

## 按复现问题反查来源

| 你在复现中问的问题 | 应该先看 | 为什么 |
|---|---|---|
| “为什么视频看起来成功但 `success=False`？” | 13、13b、14b | 视频只是人眼证据，最终判定来自 predicate/subtask score/event log |
| “为什么不先全跑 RoboLab-120？” | 08、13、15 | 全量需要固定任务、策略、episode、资产和分析口径；4090 先做小矩阵更稳 |
| “OpenPI Pi05 和 RoboChallenge Pi 怎么对比？” | 14、16 | 先统一 policy client、任务、输出和 action/observation schema |
| “为什么下载慢或资产不齐会影响结果？” | 00、02、11、14 | scene asset、USD、physics 和 recorder 都是评测证据链的一部分 |
| “怎么判断策略弱在视觉、空间还是程序操作？” | 04、08、13 | 要按 task attributes、difficulty、subtask 和 event reason 分组 |
| “为什么 prompt 要写得这么复杂？” | 10、11 | prompt 是生成 typed predicates 的约束入口，solver/feedback 依赖它 |
| “为什么要讲 Gaussian/NuRec 等前沿？” | 01、12、16 | 它们不是本文主流程，但决定未来 real-to-sim 和高保真资产路线 |
| “为什么感觉精讲还是不够深？” | 17 | 需要从章节式知识点切换成输入、状态、输出、失败边界和证据落点的机制式读法 |

## 本索引如何维护

新增或修改精讲时，应同步补三件事：

1. 在本文件加入“问题 -> 来源 -> 核心内容 -> 代码/复现落点”。
2. 在 `source_manifest.json` 的 `used_for` 里记录对应来源用途。
3. 在 notebook 里保留一个轻量验证 cell，检查精讲是否至少有问题、来源和落点三类信息。

这样后续不会只剩“讲解内容”，而是能追溯到论文、代码和复现证据。
