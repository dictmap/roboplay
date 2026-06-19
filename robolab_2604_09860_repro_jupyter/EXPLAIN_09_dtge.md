# 精讲 9：DTGE - Details on Task Generation Evaluation

> **【绿色标识｜核心结论】** DTGE 不是一个新模型，也不是策略执行评测；它是论文 Appendix D 的 “Details on Task Generation Evaluation”，核心问题是：自动生成出来的 RoboLab task，语言指令和程序化成功条件是否真的一致。  
> **【蓝色标识｜源码路径】** 它对应的代码表面主要在 `skills/robolab-taskgen/`、`robolab/core/task/task.py`、`robolab/core/task/conditionals.py`、`robolab/tasks/_utils/generate_task_metadata.py`。  
> **【橙色标识｜容易误解】** DTGE 评的是任务生成质量，不是机器人策略成功率。一个 task 被 DTGE 判为高质量，只说明“任务定义可信”，不说明 Pi05、RoboChallenge pi 或 ReKep 一定能完成它。

## 先说结论

DTGE 可以用一句话概括：

> 给 LLM 自动生成的任务代码做“审题”：自然语言说的目标，和 Python success condition 真正检查的目标，是否是同一件事。

它关注的是 task 本身有没有问题，而不是 policy 表现：

| 问题 | DTGE 看不看 | 解释 |
|---|---:|---|
| 指令是否清楚 | 看 | 例如“把苹果放进碗里”是否明确 |
| 成功条件是否匹配指令 | 看 | 例如代码是否真的检查 `object_in_container(apple, bowl)` |
| 物理上是否可实现 | 看 | 例如太大的物体不能塞进太小容器 |
| 任务覆盖了哪些对象 | 看 | 用 object coverage 统计 |
| 任务用了多少谓词种类 | 看 | 用 predicate coverage 统计 |
| 策略是否执行成功 | 不看 | 那是 RoboLab-120 policy benchmark |
| 轨迹是否平滑 | 不看 | 那是 SPARC/trajectory metrics |

## DTGE 在论文里的完整流程

论文 Appendix D 的流程可以拆成 5 步：

| 步骤 | 说人话解释 | 输入 | 输出 |
|---|---|---|---|
| 1. 生成任务 | 用 LLM 根据场景描述和类别模板生成 Python task | scene description、category templates | task Python code |
| 2. 静态抽取 | 不运行机器人，只读代码 | task class | instruction + termination success predicate |
| 3. LLM-as-judge | 让 LLM 评估语言和代码是否一致 | instruction、success condition | 6 个维度评分 |
| 4. 聚合评分 | 把多个维度合成 alignment / match / verdict | judge scores | aligned / partial / misaligned |
| 5. 覆盖率统计 | 看任务是否充分利用场景对象和谓词库 | generated task set | object coverage / predicate coverage |

这一步很关键：**DTGE 的静态抽取对象是 task 代码，不是视频、不是 HDF5、也不是 policy rollout。**

## 论文里的数据口径

论文使用 7 个类别，每个类别 116 个任务，总计 812 个自动生成任务。评估结果大致如下：

| Category | Count | Alignment | Clarity | Feasibility | Match | Aligned% | Partial% | Object Coverage | Predicate Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| color | 116 | 0.81 | 0.94 | 0.80 | 0.90 | 57 | 40 | 0.88 | 0.29 |
| conjunction | 116 | 0.97 | 0.98 | 1.00 | 0.98 | 91 | 9 | 0.88 | 0.29 |
| counting | 116 | 0.87 | 0.97 | 0.90 | 0.92 | 60 | 38 | 0.88 | 0.29 |
| recognition | 116 | 0.96 | 0.97 | 0.96 | 0.97 | 85 | 15 | 0.88 | 0.29 |
| semantics | 116 | 0.89 | 0.95 | 0.94 | 0.94 | 72 | 27 | 0.88 | 0.29 |
| sorting | 116 | 0.94 | 0.95 | 0.97 | 0.96 | 86 | 14 | 0.88 | 0.29 |
| spatial | 116 | 0.92 | 0.98 | 0.89 | 0.95 | 80 | 17 | 0.88 | 0.29 |
| Overall | 812 | 0.91 | 0.96 | 0.92 | 0.95 | 76 | 23 | 0.88 | 0.29 |

**【绿色标识｜读表结论】**

- Overall alignment 0.91：语言目标和代码成功条件整体比较一致。
- Clarity 0.96：生成的自然语言大多清楚。
- Match 0.95：relation / target / object / quantifier 这类语义匹配总体较好。
- Object coverage 0.88：多数可操作对象能被任务覆盖到。
- Predicate coverage 0.29：谓词覆盖很低，说明生成器偏向使用少数可靠谓词，而不是探索所有谓词。

**【橙色标识｜风险点】**

color 类 alignment 较低，说明“颜色词 -> 具体对象实例”的 grounding 容易出错。spatial 类 feasibility 较低，说明精确空间摆放可能超出机器人实际容忍度。

## 六个 judge 维度怎么理解

DTGE 的 judge 不是只给一个“好/坏”，而是拆成更具体的维度：

| 维度 | 问的问题 | 例子 |
|---|---|---|
| relation match | 空间/逻辑关系是否一致 | 指令说“放进碗”，代码却检查“放到盘子上”就是错 |
| target match | 目标状态是否一致 | 指令要最终在 bowl，代码却把 bowl 写成 plate |
| object match | 被操作对象是否一致 | 指令是 apple，代码检查 banana |
| quantifier match | 数量词是否一致 | 指令说 all，代码只要求 any |
| instruction clarity | 指令是否清晰 | “put it there” 缺少对象和目标 |
| physical feasibility | 物理上是否可完成 | 大盒子塞进小碗不可行 |

可以把它记成：

```text
关系对不对 -> 目标对不对 -> 对象对不对 -> 数量对不对 -> 人话清不清楚 -> 物理能不能做
```

## 代码里它评的到底是什么

RoboLab 的 task class 结构大致是：

```python
@configclass
class BananaInBowlTerminations:
    success = DoneTerm(
        func=object_in_container,
        params={"object": "banana", "container": "bowl"},
    )

@dataclass
class BananaInBowlTask(Task):
    instruction = {
        "default": "Pick up the banana and place it in the bowl",
        "vague": "Put the fruit in the bowl",
        "specific": "Grasp the yellow banana and place it inside the bowl",
    }
    terminations = BananaInBowlTerminations
    attributes = ["semantics"]
    subtasks = [
        pick_and_place(object=["banana"], container="bowl", logical="all", score=1.0)
    ]
```

DTGE 关心的核心是：

| 代码字段 | DTGE 怎么用 |
|---|---|
| `instruction` | 抽出自然语言目标 |
| `terminations.success.func` | 抽出成功谓词，例如 `object_in_container` |
| `terminations.success.params` | 抽出对象、容器、reference、surface、logical 等参数 |
| `attributes` | 对应 color、sorting、spatial 等类别分析 |
| `subtasks` | 辅助理解任务结构，但 DTGE 的主判断是 instruction 和 success condition 是否一致 |

## 和精讲3的区别

精讲3讲的是“怎么生成任务”：给 LLM 对象目录、谓词库、模板、约束，让它写 task，然后做语法/资源/尺寸检查和失败修复。

精讲9讲的是“怎么评价生成出来的任务质量”：

| 精讲3：TaskGen | 精讲9：DTGE |
|---|---|
| 关注生成流程 | 关注评估流程 |
| 目标是产出 task code | 目标是判断 task code 是否可信 |
| 检查语法、资源、容器尺寸 | 检查语言和 success condition 是否对齐 |
| 失败后给 LLM 修复 prompt | 输出 alignment、clarity、feasibility、coverage |

两者关系是：

```text
TaskGen 负责“造题”
DTGE 负责“审题”
Policy benchmark 负责“做题”
```

## 为什么要有 DTGE

自动生成任务最大的风险是“看起来像任务，但其实评测目标错了”。

例如：

```text
指令：把苹果放进碗里
代码：object_in_container(object="banana", container="bowl")
```

这个 task 如果拿去评测 policy，就会出现严重污染：

- 模型按指令拿苹果，代码判失败。
- 模型误拿香蕉，代码可能判成功。
- 最后你以为是模型失败，其实是 benchmark 自己标错了。

DTGE 的作用就是在 policy rollout 前尽量发现这种问题。

## Object Coverage 和 Predicate Coverage

### Object Coverage

object coverage 问的是：

> 一个场景里的可操作对象，有多少至少出现在一个生成任务里？

如果一个厨房场景有 20 个可操作对象，但生成任务只反复使用苹果和碗，那么 object coverage 就低。  
论文里 object coverage 约 0.88，说明任务生成能覆盖大多数对象。

### Predicate Coverage

predicate coverage 问的是：

> 可用成功谓词里，有多少被生成任务真正使用过？

论文里 predicate coverage 约 0.29。这个数低不一定是坏事，它说明生成器比较保守，更偏向可靠谓词，例如 `object_in_container`、`object_on_top`、`object_left_of`、`stacked`，而不是把所有边缘谓词都用一遍。

**【橙色标识｜取舍】**

高 predicate coverage 代表任务多样，但可能降低可靠性；低 predicate coverage 代表更稳，但 benchmark 的行为覆盖面可能不够广。

## 复现 DTGE 需要准备什么

如果我们要按论文复现 DTGE，需要准备：

| 资产 | 用途 |
|---|---|
| 场景集合 | 论文里是多个场景，每个场景生成多类任务 |
| Category templates | color、conjunction、counting、recognition、semantics、sorting、spatial |
| taskgen prompt | 生成 Python task code |
| 静态分析脚本 | 从 task code 中抽 instruction 和 termination condition |
| judge prompt | 让 LLM 评分 relation/target/object/quantifier/clarity/feasibility |
| 汇总脚本 | 统计 alignment、match、coverage、verdict |

**【橙色标识｜复现边界】**

论文里使用 o1 做生成和 judge，并使用 temperature 0 以增强复现性。但 LLM-as-judge 仍然可能随模型版本、系统提示、解析规则变化而漂移。因此我们复现时应该保存 prompt、输入 task code、judge 原始 JSON、聚合脚本版本，而不是只保存最终表格。

## 和我们当前 4090 复现的关系

当前我们已经跑通 Pi05 单任务和复杂任务抽样。DTGE 是下一层质量控制：

1. 如果我们使用官方 RoboLab-120 任务，DTGE 主要作为理解论文任务质量的背景。
2. 如果我们自己用 LLM 扩展任务，DTGE 必须变成生成流程的一部分。
3. 如果要对比 RoboChallenge pi、OpenPI pi05、ReKep，必须先确认 task 本身没有 instruction-code mismatch，否则模型对比会被污染。

最实用的执行顺序是：

```text
任务代码静态校验 -> DTGE 审题 -> no-policy 环境初始化 -> policy rollout -> result analysis
```

这样能把失败分层：

| 失败阶段 | 说明 |
|---|---|
| 静态校验失败 | task 文件格式、对象名或 predicate 参数有问题 |
| DTGE 失败 | 指令和 success condition 不一致 |
| no-policy 初始化失败 | 资产、场景、物理或注册有问题 |
| policy rollout 失败 | 策略本身没有完成任务 |

## 小结

DTGE 的价值不在于给 policy 打分，而在于保护 benchmark 的可信度：

```text
没有 DTGE：模型失败和任务标错混在一起
有 DTGE：先确认题目靠谱，再评价模型会不会做
```

对我们的复现来说，DTGE 是后续扩展任务、做模型对比、跑 RoboLab-120 子集时必须保留的一道质量门。
