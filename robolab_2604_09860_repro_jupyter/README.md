# RoboLab 4090 复现与学习记录

本目录是 RoboLab 复现学习用的 Jupyter 交付物。

## 文件

- `RoboLab_4090_repro_learning_record.ipynb`：主 notebook，按阶段记录环境检查、安装、验证、smoke run、4090 小子集评测、论文机制、核心源码讲解、结果解析和学习日志。
- `source_manifest.json`：准备 notebook 时核对过的官方来源。
- `build_robolab_notebook.py`：生成 notebook 和来源清单的脚本。
- `REMOTE_EVIDENCE_MANIFEST.md`：解释 GitHub 已提交资料与本地原始远端证据之间的边界，列出 `remote_outputs/`、`remote_logs/`、HTML 渲染版未直接提交的原因和本地证据概览。
- `EXPLAIN_SOURCE_QUESTION_INDEX.md`：所有精讲的问题来源与核心内容索引，把每个精讲对应的原问题、论文/代码来源、来源核心内容和复现/代码落点并排展示，已内嵌进 notebook，并配有来源覆盖轻量测试用例。
- `EXPLAIN_00_global_overview.md`：论文与复现全局总览精讲，已优化为全精讲入口，补齐来源索引阅读顺序、四条主线、全精讲路线图、复现证据层级、任务标注、策略接入、4090 边界和后续路线，已内嵌进 notebook，并配有全局结构轻量测试用例。
- `EXPLAIN_01_real_to_sim_eval.md`：论文“真实场景到模拟场景评估”的代码实现精讲，已内嵌进 notebook。
- `EXPLAIN_02_scene_task_env_generation.md`：论文“场景、任务和环境生成”的代码实现精讲，已内嵌进 notebook。
- `EXPLAIN_03_task_generation_validation.md`：论文“扩展任务生成、验证和自动修复”的代码实现精讲，已内嵌进 notebook，并配有轻量测试用例。
- `EXPLAIN_04_competency_axes_difficulty.md`：论文“能力轴、任务属性、子任务和难度分数”的代码实现精讲，已内嵌进 notebook，并配有难度公式轻量测试用例。
- `EXPLAIN_05_sparc_trajectory_metric.md`：论文“SPARC 轨迹平滑度指标”的代码实现精讲，已内嵌进 notebook，并配有 SPARC 方向性轻量测试用例。
- `EXPLAIN_06_mnpe_sensitivity_analysis.md`：论文“MNPE 敏感性分析”的代码实现精讲，已内嵌进 notebook，并配有 posterior 直觉轻量测试用例。
- `EXPLAIN_07_baseline_method.md`：论文 Appendix C-C “Baseline Method”的代码实现精讲，已内嵌进 notebook，并配有 grid+jitter baseline 轻量测试用例。
- `EXPLAIN_08_paper_experiments.md`：论文实验体系与 Algorithm 1 Spatial Constraint Solver 精讲，已加深为“实验地图 + 证据链”，覆盖 success/score/event/trajectory 指标分工、主表能力画像读法、场景生成质量表、task generation judge 六维和 4090 小论文矩阵，已内嵌进 notebook，并配有增强版实验地图/2D 空间约束轻量测试用例。
- `EXPLAIN_09_dtge.md`：论文 Appendix D “Details on Task Generation Evaluation / DTGE”的精讲，已内嵌进 notebook，并配有 AST 静态抽取与简化 judge 轻量测试用例。
- `EXPLAIN_10_prompt_design.md`：论文 Appendix C Stage I scene generation prompt 精讲，已内嵌进 notebook，并配有 prompt 输出格式/依赖/对象目录/尺寸限制轻量测试用例。
- `EXPLAIN_11_spatial_physical_solver_feedback.md`：论文 Appendix C 空间求解器、物理放置求解器和失败反馈块精讲，已加深 Spatial/Physical 的 typed predicate 中间表示、dense scene margin retry、相对坐标、碰撞推开、support 局部坐标、container packing、stability threshold 和反馈诊断压缩，已内嵌进 notebook，并配有增强版支撑/容器/反馈轻量测试用例。
- `EXPLAIN_12_gaussian_sim_methods.md`：论文中 Gaussian Splat + Mesh、collision mesh、VoMP、MNPE Gaussian KDE 与 NVIDIA 2026 NuRec/3DGUT/Lyra 等前沿路线精讲，已补前沿来源链接速查表，已内嵌进 notebook，并配有分层职责和链接覆盖轻量测试用例。
- `EXPLAIN_13_remaining_core_topics.md`：对照论文后补充的剩余核心内容精讲，覆盖实验协议、success/score gap、语言变体、复杂度 sweep、事件追踪、真实世界相关性、统计置信和限制边界，已内嵌进 notebook，并配有覆盖差分轻量测试用例。
- `EXPLAIN_13_deep_evaluation_evidence_chain.md`：精讲13补充深挖版，把单条 rollout 到论文结论的证据链讲透，覆盖 episode 样本单位、score/success 数学直觉、event tracking、置信区间、dashboard、RoboArena 相关性、limitations 和 4090 小矩阵实验设计，已内嵌进 notebook，并配有深挖轻量测试用例。
- `EXPLAIN_14_core_code_runtime_chain.md`：RoboLab policy rollout 到证据链的核心代码精讲，覆盖 `runner.py`、`episode.py`、`InferenceClient`、Pi05 client、`WorldState`、`EventTracker`、HDF5 recorder、`summarize_run`、results 和 dashboard loader，已内嵌进 notebook，并配有源码链路轻量测试用例。
- `EXPLAIN_14_deep_runtime_code_chain.md`：精讲14补充深挖版，把源码主干继续拆成输入、处理、输出、状态边界、故障路由和证据归档，重点讲透 `runner -> episode -> client -> Pi05 server -> env/world -> event -> HDF5 -> summarize -> dashboard`，已内嵌进 notebook，并配有运行链路覆盖轻量测试用例。
- `EXPLAIN_15_reviewer_synthesis.md`：全文总梳理与审稿人视角精讲，覆盖贡献、优点、主要问题、优化点和未来创新方向，已内嵌进 notebook，并配有 reviewer rubric 轻量测试用例。
- `EXPLAIN_16_recommended_reading.md`：基于 RoboLab 的推荐阅读与开源学习路线，已改成 2026-first：优先补 RoboLab、RoboCasa365、RDT2、GR00T N1.7、Isaac Lab-Arena、Lightwheel LW-BenchHub、Lyra 和 NVIDIA 2026 Physical AI stack；BEHAVIOR/DROID/OpenVLA/Octo/ReKep 等降级为基础背景，已内嵌进 notebook，并配有 reading map 轻量测试用例。
- `COMPLETE_REPRO_pi05_banana_20260620.md`：Pi05 / BananaInBowlTask 成功闭环记录，已内嵌进 notebook。
- `COMPLEX_TASKS_pi05_20260620.md`：Pi05 三个复杂任务抽样复现记录，已内嵌进 notebook。
- `REMOTE_EVIDENCE_MANIFEST.md`：远端原始证据清单。`remote_logs/`、`remote_outputs/` 和 HTML 渲染版目前保留在本地，未进入普通 Git 提交；如需完整原始视频/HDF5，可后续走 Git LFS 或 GitHub Release artifact。

## 当前状态

- 已在远端 RTX 4090 / Ubuntu 22.04.4 上完成 `uv sync`，并确认 `robolab==0.1.0`、`isaacsim==5.0.0.0`、`isaaclab==2.2.0`、`torch==2.7.0+cu128` 可导入。
- 已补齐 `assets/scenes/`、`assets/robots/` 和核心 `assets/fixtures/`，足够运行 `BananaInBowlTask` 的 no-policy smoke。
- `BananaInBowlTask` headless smoke 已完成 2 step 并导出 episode log；`success: False` 是空动作运行的预期结果，不是 VLA 策略评测。
- 已追加三任务 no-policy subset smoke：`RubiksCubeAndBananaTask`、`RubiksCubeLeftOfBowlTask`、`ReorientWhiteMugsTask`，三者均完成环境初始化、2 step 和 episode log 导出。
- 已扩展到累计 21 个 no-policy 初始化 smoke，覆盖语义、颜色、空间关系、顺序组合、重定向、堆叠等任务属性；额外候选任务失败原因已记录，证据包为 `remote_logs/robolab_remote_policy_subset21_evidence_20260619_223200.tar.gz`。
- 已新增论文与核心源码讲解章节，并生成 `robolab_repro_artifacts/core_code_reading_map.json`，用于追踪论文概念到源码文件的映射。
- 已新增“精讲问题来源与核心内容索引”，集中展示每个精讲回答的问题、问题来自论文哪一节/appendix/图/源码、来源核心内容和复现代码落点，避免只看解释而看不到出处。
- 已优化“精讲0：RoboLab 全局总览”，把它从早期背景概览升级为全精讲入口：先连接来源索引，再用生成线、任务线、运行线、证据线、评价线串起 1-16 全部精讲，并保留 4090 复现边界、RoboChallenge/OpenPI/ReKep 对比前提和完整复现分级。
- 已新增“场景、任务和环境生成”精讲，覆盖 `scene_gen` 谓词求解、`Task` 语言/成功条件、registration/runtime 环境装配，并包含场景 JSON、任务类、背景随机化等示例。
- 已新增“扩展任务生成、验证和自动修复”精讲，覆盖 taskgen skill、谓词库、`load_task_from_file`、场景对象验证、容器尺寸检查和失败修复提示，并在 notebook 里加入 6 个轻量测试用例。
- 已轻量化三篇精讲之间的重复内容：精讲1聚焦 real-to-sim 评估闭环，精讲2深讲 scene/task/env 装配，精讲3深讲 TaskGen 验证与修复。
- 已新增“能力轴、任务属性、子任务和难度分数”精讲，覆盖 visual/procedural/relational、多标签属性、`Subtask` 并行事件、`compute_difficulty_score` 和 metadata 生成，并在 notebook 里加入难度公式轻量测试。
- 已新增“SPARC 轨迹平滑度指标”精讲，覆盖论文 III-C Trajectory Metrics、`compute_sparc`、HDF5 到 `episode_metrics.json` 的离线指标链路，并在 notebook 里加入平滑/抖动/静止速度曲线测试。
- 已新增“MNPE 敏感性分析”精讲，覆盖论文 III-D 与 Appendix B、`posterior_inference.py` 的 CSV -> `theta/x` -> MNPE/NPE -> posterior 采样链路，并在 notebook 里加入 success posterior 直觉测试。
- 已新增“Baseline 场景生成方法”精讲，覆盖论文 Appendix C-C 的 grid+jitter 单次布局 baseline、与谓词/solver/feedback 主方法的差异，并在 notebook 里加入 baseline vs hierarchical semantic relation 轻量测试。
- 已增强“论文实验总览与 Algorithm 1”精讲，把原先的实验清单扩展成论文级证据链：从场景/任务生成质量，到 rollout artifact、success/score/event/trajectory、能力画像、扰动敏感性、真实相关性和 4090 小论文矩阵；notebook 里也加入实验地图与分组汇总轻量测试。
- 已新增“DTGE 任务生成质量评估”精讲，覆盖 Appendix D 的 LLM-as-judge、instruction-code alignment、relation/target/object/quantifier/clarity/feasibility 六维评分、object/predicate coverage，并在 notebook 里加入 AST 静态抽取轻量测试。
- 已新增“Scene Generation Prompt 设计”精讲，覆盖 Appendix C 三段 prompt 的系统约束、JSON-only 合约、对象目录注入、medium scene strategy、失败反馈思路，并在 notebook 里加入 6 类 prompt 输出校验用例。
- 已增强“空间求解器、物理放置求解器与失败反馈”精讲，覆盖 Algorithm 1、Figure 17 和 Algorithm 2，并进一步补充 Spatial 的 dense scene/margin retry/relative coordinate/collision repair，以及 Physical 的 support-frame packing/container packing/stability threshold/feedback diagnostics；notebook 里也加入相对关系、碰撞推开、support yaw 旋转和容器拥挤测试。
- 已增强“Gaussian 方法与 NVIDIA 2026 前沿路线”精讲，区分 RoboLab 本文里的 Gaussian Splat + Mesh、collision mesh、mesh foreground、VoMP、MNPE Gaussian KDE，并补充 NuRec、3DGUT/3DGRT、Isaac Sim 6、Lyra 2.0、Physically Embodied Gaussians、Marble+Isaac Sim 工作流的来源链接和重点阅读项。
- 已新增“剩余核心内容与评测证据链”精讲，补齐实验协议、`success` 与 `score` 的差异、语言变体、复杂度 sweep、事件追踪、RoboArena 真实世界相关性、统计置信区间和论文限制边界。
- 已新增“精讲13补充：评测证据链深挖”，把原先偏目录式的剩余内容扩展成论文级评测逻辑：episode identity、视频/HDF5/event/result/dashboard 证据分工、score/success gap、event failure taxonomy、CI 解释、真实世界 rank correlation 边界和 4090 小规模实验矩阵。
- 已新增“policy rollout 到证据链”代码精讲，补齐真实策略评测时 `runner -> episode -> client -> env/world -> event -> recorder -> summarize -> dashboard` 的源码主干和故障定位路径。
- 已新增“精讲14补充：核心运行时代码深挖”，把精讲14从文件作用说明扩展到源码输入/输出、action chunk、active/frozen env、多 env 隔离、WorldState 谓词、EventTracker 稀疏事件、HDF5 score、JSONL summary、dashboard 读取和 4090 故障路由。
- 已新增“全文总梳理与审稿人视角”精讲，补齐论文贡献评价、审稿式 strengths/weaknesses/questions、复现侧优化点和未来创新方向。
- 已增强“推荐阅读与开源学习路线”精讲，补上每个推荐来源背后的核心问题、原始内容要点、和 RoboLab 的关系；本次又新增 2026-first 阅读层，把 RoboLab、RoboCasa365、RDT2、GR00T N1.7、Isaac Lab-Arena、Lightwheel LW-BenchHub、Lyra 和 NVIDIA 2026 Physical AI stack 放到最前，并把 2025 及更早材料明确标成基础背景。
- `uv run pytest tests/` 在当前 HEAD 返回 4，因为仓库没有 `tests/` 路径；这已记录为 README 与当前仓库文件面的不一致。
- Pi0/Pi05 评测入口是 `policies/pi0_family/run.py`；OpenPI Pi05 `pi05_droid_jointpos` checkpoint 已下载并通过 26 个对象大小校验，policy server 已监听 8000。
- 已完成真实 Pi05 policy 单任务 smoke：`BananaInBowlTask` 1 episode，`success=True`，`score=1.0`，`episode_step=178`，平均 policy inference `84.2 ms`。这是真实 VLA/OpenPI policy score，但仍只是单任务 smoke，不是完整 RoboLab-120。
- 已完成一条更完整的 Pi05 / `BananaInBowlTask` 闭环复现：`success=True`，`episode_step=198`，生成主视频、viewport 视频、HDF5、event log 和 `episode_results.jsonl`。
- 已完成三个复杂任务抽样：`ReorientAllMugsTask` 失败、`Stack3RubiksCubeTask` 成功、`RedItemsInBinTask` 失败；3 个任务中成功 1 个，失败 2 个，视频和 JSON 结果已同步到 `remote_outputs/`。
- 已把交流中的核心判断记录进 notebook：4090 显存边界、下载慢的原因、OpenPI pi05 与 RoboChallenge pi 的区别、视频位置、环境失败和策略失败的区别、为什么不先盲跑 RoboLab-120。
- 完整 RoboLab-120 仍未执行；仓库还有大量 object/material LFS 资产未下载，需要按任务继续补齐或全量拉取。

## 使用方式

在 Ubuntu 22.04+ / RTX 4090 机器上：

```bash
cd <this-folder>
jupyter lab RoboLab_4090_repro_learning_record.ipynb
```

先执行配置与 preflight cell。确认机器正确后，再逐步打开：

1. `EXECUTE_INSTALL = True`
2. `EXECUTE_TESTS = True`
3. `EXECUTE_NO_POLICY_SMOKE = True`
4. `EXECUTE_POLICY_SMOKE = True`
5. `EXECUTE_SUBSET_EVAL = True`

4090 首轮保持 `NUM_ENVS_4090_SMOKE = 1`。确认没有 OOM、输出完整后，再尝试更高并行度。

## 生成时间

2026-06-19T00:00:00+08:00
