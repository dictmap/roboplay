# 精讲 13：对照论文后还没讲透的核心内容

> **【绿色标识｜核心结论】** 前 12 讲已经覆盖了 RoboLab 的生成链路、任务结构、能力轴、SPARC、MNPE、baseline、DTGE、prompt、solver、Gaussian 路线。剩下最值得补的一块不是“再讲一个算法”，而是论文如何把一次机器人 rollout 变成可信评测证据：实验协议、严格成功率与部分分数、语言变体、错误事件、真实世界相关性、统计置信和限制边界。
>
> **【蓝色标识｜源码/输入输出路径】** 这部分主要对应论文 III-C Metrics、IV Experiments、IV-D Real-World Verification、V Limitations，以及 RoboLab docs 里的 `analysis/read_results.py`、`docs/data.md`、`docs/event_tracking.md`、`docs/dashboard.md`、`docs/subtask.md`。
>
> **【橙色标识｜容易误解】** 视频好看不等于复现成功；单任务成功不等于 RoboLab-120；`success=True` 不等于模型完全懂任务；`score>0` 才能告诉我们模型在哪些中间步骤已经会了、在哪里失败。

## 先做覆盖差分

| 论文核心点 | 前面是否已讲 | 还缺什么 |
|---|---:|---|
| scene/task/env generation | 已讲，精讲 1-3、10-11 | 不重复 |
| competency axes/difficulty | 已讲，精讲 4 | 不重复 |
| SPARC trajectory metrics | 已讲，精讲 5 | 不重复 |
| MNPE sensitivity | 已讲，精讲 6 | 不重复 |
| scene generation baseline / DTGE / prompt | 已讲，精讲 7、9、10 | 不重复 |
| Gaussian Splat + Mesh / NuRec | 已讲，精讲 12 | 不重复 |
| evaluation protocol | 弱讲 | 需要明确输入、输出、episode 数、policy/robot/action/camera 绑定 |
| success vs score | 弱讲 | 需要解释为什么论文强调 score/success gap |
| language variations | 弱讲 | 需要解释 vague/default/specific 为什么是泛化测试 |
| event tracking / failure taxonomy | 弱讲 | 需要解释 wrong object、drop、hit table 等事件怎么帮助诊断 |
| real-world verification | 弱讲 | 需要解释 RoboArena 相关性是什么、不是什么 |
| statistical confidence / dashboard | 弱讲 | 需要解释 95% CI、Beta interval、Student-t、结果聚合 |
| limitations | 弱讲 | 需要讲清楚哪些任务 RoboLab 暂时不擅长评估 |

## 1. 实验协议：RoboLab 真正测的是什么

论文的实验设置不是“打开一个仿真，看看机器人能不能动”。它更像一个标准化测评表：

```text
task + scene + instruction variant
  + robot embodiment
  + policy client/server
  + camera/action/observation config
  + controlled variations
  + repeated episodes
  -> episode_results + videos + HDF5 + event logs + metrics
```

论文 IV-A 的关键信息：

- 策略是现实数据训练出来的 task-generalist policy，而不是在 RoboLab 任务里专门训练的 policy。
- action space 是 Franka 7-DOF joint positions + 1-DOF binary gripper command。
- 环境用 office-like background 和 natural lighting，腕部相机与外部相机尽量贴近 DROID 真实机器人设置。
- 每个任务重复运行多个 episode，论文里每个任务是 10 episodes。

说人话：

> RoboLab 的重点是把真实机器人策略拿到一个高保真、可控、可重复的仿真考试场里，看它是否真的泛化，而不是让模型提前适应这个仿真器。

### 输入输出

| 层 | 输入 | 输出 | 为什么重要 |
|---|---|---|---|
| task | scene、instruction、termination、subtasks、attributes | env config | 决定要考什么 |
| policy | observation images、proprio、instruction | robot action | 决定模型如何行动 |
| robot/env | action、physics、camera、contact | next observation、events | 决定 rollout 过程 |
| logging | per-step state、events、subtask status | HDF5、JSONL、videos | 决定可解释证据 |
| analysis | episode_results、HDF5、event logs | success、score、CI、wrong object、SPARC | 决定论文表格 |

## 2. Success 和 Score 的区别：论文最容易被低估的一点

论文 IV-B 明确强调：成功率是最终是否完成任务，score 表示过程中是否完成了部分里程碑。这个差异非常关键。

例如一个任务：

```text
Put the cube and the banana in the bowl
```

可以拆成：

```text
cube: grab -> hover/above bowl -> drop -> in bowl
banana: grab -> hover/above bowl -> drop -> in bowl
```

如果模型只把 banana 放进 bowl，但 cube 没完成：

```text
success = False
score   > 0
```

这不是“失败就没价值”。它说明模型可能已经掌握了：

- 语言里的一部分目标。
- 某个对象的识别。
- 抓取/搬运/放置中的部分动作。

但它还没掌握：

- 多对象组合。
- 顺序规划。
- 全部目标的终止条件。

**【绿色标识｜核心直觉】**

`success` 回答“最后有没有做完”；`score` 回答“做到了哪一步”。RoboLab 的分析价值主要来自第二个问题。

## 3. Language Variations：为什么 vague/default/specific 很重要

论文 III-C 和 IV-B 都强调 instruction variation。RoboLab 同一个底层任务可以有不同语言版本：

| 类型 | 例子 | 考什么 |
|---|---|---|
| default | Put the cube and the banana in the bowl | 标准任务理解 |
| vague | Put everything in the bowl | 抽象语言到目标集合 |
| specific | Pick up the rubiks cube and the yellow banana and place both inside the bowl | 细粒度对象绑定 |

论文观察到：指令越抽象，很多模型成功率会明显下降。  
这说明模型可能不是在理解“目标状态”，而是在依赖训练中常见的语言模板。

说人话：

> 真懂任务的机器人，不应该因为“把香蕉放进碗里”和“把黄色水果放进碗里”的说法不同，就完全换一种行为。

我们后续复现如果要靠近论文，不能只跑 default instruction，至少要跑：

```bash
python analysis/read_results.py <run> --by-instruction-type
```

否则看不到语言泛化这一层。

## 4. 三条复杂度 sweep：不是能力轴，而是诊断轴

前面精讲 4 已经讲了 visual/procedural/relational 能力轴。论文 IV-B 还有另一组实验轴：

| 诊断轴 | 怎么变 | 观察什么 |
|---|---|---|
| instruction specificity | vague/default/specific | 语言抽象程度影响 |
| scene complexity | 增加桌面可见物体数量 | 视觉 clutter 和目标识别稳定性 |
| task horizon | 增加 subtasks/多步长度 | 多步骤规划和长期执行稳定性 |

这三条轴不是重新定义任务类别，而是把同一类任务放进不同压力测试里。

例如：

```text
同一个 pick-place 能力
  -> 指令变 vague
  -> 桌面多几个干扰物
  -> 从一个物体变成多个物体
```

如果只看总成功率，很难知道模型是“看错了对象”“没听懂语言”还是“长时序执行崩了”。  
这三条 sweep 就是把失败原因拆开。

## 5. Event Tracking：为什么 Figure 3 比成功率更有用

论文 Figure 3 展示了几类失败：

- 抓了错误对象。
- 太早放手，目标没进容器。
- 先重定向了无关对象。
- 多次尝试错误对象。

RoboLab docs 的 event tracking 也对应这些诊断事件，例如：

- `WRONG_OBJECT_GRABBED`
- `TARGET_OBJECT_DROPPED`
- `GRIPPER_HIT_TABLE`
- `OBJECT_MOVED`
- `OBJECT_OUT_OF_SCENE`
- `OBJECT_TIPPED_OVER`
- `MULTIPLE_OBJECTS_GRABBED`

说人话：

> 成功率告诉你“考了多少分”；事件日志告诉你“错题错在哪里”。

### 输入输出

```text
input:
  per-step world state
  gripper contact state
  target object list
  object poses and movement thresholds

output:
  event log JSON
  wrong-object counts
  dropped-object counts
  object-moved/tipped/out-of-scene counts
```

这也解释了为什么我们复现时要保存：

- `log_0_env0.json`
- `episode_results.jsonl`
- `run_0.hdf5`
- 视频

视频是给人看，event/HDF5/JSON 是给统计和论文表格用。

## 6. Real-World Verification：RoboLab 能不能代表真实世界

论文 IV-D 做了一件重要但容易被误读的事：它把 RoboLab-120 上的策略成功率和 RoboArena 真实机器人 benchmark 的 Elo 排名做相关性比较。

这里重点是：

- RoboLab 输出 success rate。
- RoboArena 输出 Elo score。
- 两者单位不一样。
- 因此 Spearman rank correlation 更合适，因为它看的是策略排名是否一致。

说人话：

> RoboLab 不是声称“仿真分数等于真实分数”，而是说“在这些策略上，仿真排序和真实排序有一致性，所以它可以作为真实评测的有用 proxy”。

边界也要讲清楚：

- 这不是任务级别逐项一致性证明。
- 这不是 motion-level 行为一致性证明。
- 这不是说所有真实世界 failure 都能在仿真里复现。
- 样本策略数量有限，论文也把更深的相关性分析留给 future work。

## 7. 统计置信和 Dashboard：为什么不能只看一条视频

论文和项目 docs 都强调结果分析：

- 每个任务有多 episode。
- `episode_results.jsonl` 是聚合主数据。
- HDF5 存轨迹、动作、状态、subtask 等细节。
- dashboard 和 analysis 脚本按任务、属性、难度、场景、wrong objects、instruction type 聚合。
- dashboard 中 success rate 使用 Beta credible interval，score 使用 Student-t 区间。

我们复现时如果只给一条视频，只能说明：

```text
这条 episode 发生过
```

还不能说明：

```text
这个策略在这个任务族上稳定有效
```

**【橙色标识｜复现边界】**

我们当前已经有 Pi05 单任务成功闭环和 3 个复杂任务抽样，但这仍然不是完整 RoboLab-120，也不是论文级统计结果。

## 8. Appendix A 里还有两个细节值得记

### 8.1 Statistical significance

论文 Appendix A-A 讨论统计显著性。这里的要点不是某个单独公式，而是评测必须有 episode 数和置信区间。  
对我们来说，最实用的原则是：

```text
不要用 1 episode 的 success=True 推导整体能力。
至少按任务重复，再按属性/难度/语言变体聚合。
```

### 8.2 Anomalous long-horizon success

Appendix A-D 还解释了一个看似反常的现象：某些长 horizon 任务反而表现更好。  
论文的解读是，这可能不是模型突然会了长任务，而是特定任务的结构、对象分布或目标状态让它更容易触发部分成功。

说人话：

> 不要看到“长任务成功率更高”就立刻下结论说模型更擅长长时序。要回头看具体任务、对象和 subtask 结构。

## 9. Limitations：论文自己承认哪些事还没解决

论文 V Limitations 说得很直接，RoboLab 目前主要是：

- rigid-body tabletop scenes。
- 桌面操作。
- 可用谓词描述的目标状态。

还不充分覆盖：

- cloth、cables、bags 等 deformable objects。
- 需要精细力控的 contact-rich skills。
- 复杂摩擦、顺应性接触、低层控制任务。
- open-ended ambiguous long-horizon tasks，比如 “clean up all the laundry”。
- 残余视觉分布偏移。

这对我们复现很重要。因为当一个任务失败时，先判断它属于哪类：

| 失败类型 | 该不该怪 RoboLab |
|---|---|
| 资产缺失、环境启动失败 | 复现环境问题 |
| 模型抓错对象 | policy/generalization 问题 |
| 模型做了一半但未完成 | score/subtask 诊断问题 |
| cloth/cable/force-control 失败 | RoboLab 当前能力边界 |
| 单任务视频成功但统计不足 | 证据规模问题 |

## 10. 和我们当前复现记录怎么接起来

我们现在已经完成：

- `BananaInBowlTask` Pi05 成功闭环。
- 三个复杂任务抽样。
- no-policy 初始化 smoke。
- 视频、HDF5、JSON、event log 同步。
- notebook 里对生成、solver、prompt、metrics、MNPE、Gaussian 的解释。

如果要更接近论文级复现，下一步应该按这个顺序：

1. 同一个任务跑 `default/vague/specific`，看语言变体。
2. 同一个任务跑 object pose / camera pose / lighting / background sweep，接 MNPE。
3. 复杂任务至少按属性分组，不只挑几个视频。
4. 用 `analysis/read_results.py --by-attributes --by-difficulty --by-instruction-type --by-wrong-objects` 输出表。
5. 如果接 RoboChallenge/ReKep/OpenPI 多策略，再做 per-policy rank 对比。

## 小结

前面 12 讲回答了：

```text
RoboLab 怎么生成任务、怎么建场景、怎么判成功、怎么分析轨迹/敏感性。
```

精讲 13 补的是：

```text
RoboLab 怎么把 rollout 变成可信实验结论。
```

最重要的记法：

```text
success: 最终是否做完
score: 做到了哪一步
language variation: 是否真懂任务语义
event tracking: 错在什么行为
complexity sweep: 哪种压力导致失败
CI/dashboard: 结果是否有统计可信度
real-world verification: 仿真排序是否接近真实排序
limitations: 哪些问题不是这个 benchmark 当前擅长回答的
```

