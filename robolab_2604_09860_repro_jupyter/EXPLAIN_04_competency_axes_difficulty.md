# 精讲 4：能力轴、任务属性、子任务和难度分数，代码怎么实现

> [!NOTE]
> **颜色标识**：绿色表示核心结论，蓝色表示源码/输入输出路径，橙色表示边界、风险和容易误解的点。

## 先说结论

论文这一段讲的是 RoboLab-120 的“任务组织方式”：它不只是列 120 个任务，然后看总体成功率，而是给每个任务贴上一个或多个属性标签，再把这些标签归到三条能力轴：

| 能力轴 | 关注什么 | 典型属性 |
|---|---|---|
| Visual | 模型能不能识别颜色、语义、大小，并把感知属性用于推理 | `color`, `semantics`, `size` |
| Procedural | 模型能不能执行带动作导向推理的任务，例如可供性、重定向、堆叠、分类 | `affordance`, `reorientation`, `stacking`, `sorting` |
| Relational | 模型能不能理解多对象语言、计数和空间关系 | `conjunction`, `counting`, `spatial` |

> [!TIP]
> **核心结论**：RoboLab 的任务不是单标签分类。一个任务可以同时是 visual + procedural，例如 `RedItemsInBinTask` 同时考颜色识别和多对象分类；难度也不是手写主观等级，而是由 `num_subtasks + max(skill_weight)` 计算出来。

这部分对应代码主线是：

```text
Task.attributes
  -> BENCHMARK_TASK_CATEGORIES / SKILL_WEIGHTS
  -> Task.subtasks
  -> count_subtasks()
  -> compute_difficulty_score()
  -> task_metadata.json / task_table.csv / README.md
  -> 结果分析按 visual/procedural/relational/simple/moderate/complex 分组
```

## 1. 能力轴：不是互斥分类，而是多标签诊断

论文说任何单个任务都很难“只评估一个属性”。代码里对应的是 `Task.attributes`：

```python
@dataclass
class BananaInBowlTask(Task):
    attributes = ["semantics"]

@dataclass
class RedItemsInBinTask(Task):
    attributes = ["color", "sorting"]

@dataclass
class RubiksCubeLeftOfBowlTask(Task):
    attributes = ["spatial"]

@dataclass
class Stack3RubiksCubeTask(Task):
    attributes = ["stacking"]
```

这些属性再由 `robolab/constants.py` 映射到能力轴：

```python
BENCHMARK_TASK_CATEGORIES = {
    "size": "visual",
    "color": "visual",
    "semantics": "visual",
    "spatial": "relational",
    "conjunction": "relational",
    "counting": "relational",
    "stacking": "procedural",
    "sorting": "procedural",
    "reorientation": "procedural",
    "affordance": "procedural",
}
```

> [!NOTE]
> **源码入口**：属性写在 `robolab/tasks/benchmark/*.py` 的 `Task.attributes`；能力轴映射在 `robolab/constants.py::BENCHMARK_TASK_CATEGORIES`；metadata 汇总在 `robolab/tasks/_utils/load_task_info.py`。

说人话：`attributes` 是任务的“诊断标签”。它告诉我们一次失败更可能暴露哪类能力短板：识别错颜色、空间关系理解错、还是动作序列/堆叠能力不足。

## 2. Visual 能力：从“看见对象”到“用属性推理”

Visual 不是只看图像识别，而是看策略能不能把视觉属性接到目标推理上。

| 属性 | 任务在问什么 | 失败时通常说明什么 |
|---|---|---|
| `semantics` | 这是香蕉、碗、杯子还是魔方 | 语义识别或语言 grounding 出错 |
| `color` | 哪些东西是红色/蓝色/指定颜色 | 颜色识别、颜色和对象绑定出错 |
| `size` | 大小是否满足目标 | 尺寸判断、遮挡下几何理解不足 |

例子：

```python
RedItemsInBinTask.attributes = ["color", "sorting"]
instruction = "Put all the red things in the grey bin"
success = object_in_container(object=["mug", "bowl"], container="grey_bin", logical="all")
```

这个任务不是单纯“看到红色”就完了。策略还要：

1. 在图像里找出所有红色目标。
2. 把红色属性绑定到具体对象实例，例如 `mug` 和 `bowl`。
3. 忽略非红色干扰物，例如 banana、rubiks cube。
4. 把目标对象逐个放进同一个容器。

所以它同时考 visual 和 procedural。

## 3. Procedural 能力：不只是知道目标，还要会执行动作链

Procedural 评估“动作导向推理”。它关注模型是否知道怎样利用物体可供性、怎样重定向、怎样堆叠或分类。

| 属性 | 典型目标 | 动作难点 |
|---|---|---|
| `affordance` | 使用对象的可供性，例如可放入、可支撑、可抓取部位 | 不只是识别对象，还要理解对象能怎么被操作 |
| `reorientation` | 把杯子、容器、物体转正或转到特定方向 | 抓取姿态和释放姿态都更难 |
| `stacking` | 把多个物体堆起来 | 接触、稳定性和中间状态要求高 |
| `sorting` | 按颜色/类别/目标容器分配多个对象 | 多轮 pick-place，目标集合容易漏或错 |

以 `Stack3RubiksCubeTask` 为例：

```python
attributes = ["stacking"]
subtasks = [
    Subtask(name="stack_any_2_cubes", logical="any", score=0.5),
    Subtask(name="stack_all_3_cubes", score=0.5),
]
```

第一阶段用 `logical="any"`：任意两个 cube 先堆起来都算阶段进展。第二阶段再要求三个 cube 都堆成塔。这样做的好处是：即使最终失败，也能知道策略是否已经完成了部分过程。

> [!TIP]
> **核心机制**：success predicate 只判断终点，`subtasks` 记录过程。RoboLab 用 subtask 让失败有层次：是没抓到、抓错对象、放错位置，还是完成了前半段但长时序崩了。

## 4. Relational 能力：语言连接词、多对象和空间结构

Relational 评估策略是否理解场景结构和多对象语言。

| 属性 | 典型指令 | 关键难点 |
|---|---|---|
| `conjunction` | “把 X 和 Y 放到 Z” | 需要同时满足多个对象目标 |
| `counting` | “放两个/三个对象” | 需要计数和停止条件 |
| `spatial` | “把 X 放到 Y 左边/右边/前面” | 需要把语言空间关系映射到机器人/场景坐标 |

以 `RubiksCubeLeftOfBowlTask` 为例：

```python
attributes = ["spatial"]
success = object_left_of(
    object="rubiks_cube",
    reference_object="bowl",
    frame_of_reference="robot",
)
```

这里策略不仅要抓起魔方，还要判断“left of bowl”在机器人参考系下是什么方向。空间关系任务经常失败在两个地方：

- 语言理解对了，但放置方向反了。
- 方向对了，但距离/接触/释放状态没有满足成功谓词。

## 5. Subtask：顺序阶段里可以包含并行事件

论文里的例子是：

```text
Put the apple and orange on the plate, then put the banana in the bowl
```

它可以拆成：

```text
Stage 1: PickPlace(apple) 和 PickPlace(orange) 并行属于同一阶段
Stage 2: PickPlace(banana)
```

RoboLab 代码里用 `Subtask` 表达这个结构：

```python
Subtask(
    conditions={
        "apple": [grasp, hover, drop, done],
        "orange": [grasp, hover, drop, done],
    },
    logical="all",
)
```

`Subtask` 里有两个层次：

| 层次 | 代码结构 | 含义 |
|---|---|---|
| 顺序阶段 | `subtasks = [stage1, stage2, ...]` | 前后阶段组成 task horizon |
| 并行组 | `conditions={"apple": ..., "orange": ...}` | 同一阶段内多个对象都要/任选/选 K 个完成 |

`logical` 决定并行组怎么计数：

| `logical` | 计数逻辑 | 例子 |
|---|---|---|
| `all` | 所有对象组都要完成 | apple 和 orange 都要放到 plate |
| `any` | 任意一个对象组完成即可 | 三个 cube 里任意两个先形成一组堆叠 |
| `choose` | 完成 K 个对象组即可 | 从 5 个物体里选 2 个满足目标 |

## 6. 难度分数：任务长度 + 最难能力权重

论文公式可以写成：

```text
difficulty_score = num_subtasks + max(w)
```

其中 `w` 表示任务属性里最难的能力要求。当前代码里的权重在 `robolab/constants.py`：

```python
SKILL_WEIGHTS = {
    "color": 0,
    "semantics": 0,
    "size": 0,
    "conjunction": 0,
    "vague": 0,
    "spatial": 1,
    "counting": 2,
    "sorting": 2,
    "stacking": 2,
    "affordance": 2,
    "reorientation": 3,
}
DIFFICULTY_THRESHOLDS = (2, 4)
```

难度标签：

| 分数 | 标签 |
|---|---|
| `<= 2` | simple |
| `3-4` | moderate |
| `>= 5` | complex |

计算位置在 `robolab/core/task/subtask_utils.py`：

```python
def compute_difficulty_score(num_subtasks, attributes):
    non_diff = [a for a in attributes if a not in ("simple", "moderate", "complex")]
    skill_weight = max((SKILL_WEIGHTS.get(a, 0) for a in non_diff), default=0)
    score = num_subtasks + skill_weight
    ...
```

> [!WARNING]
> **注意边界**：难度分数是任务设计层面的粗粒度估计，不等于某个 policy 的真实失败概率。我们已经实测过 `Stack3RubiksCubeTask` 成功、`RedItemsInBinTask` 失败，说明策略表现还会受到物体姿态、抓取质量、模型偏好和 rollout 长度影响。

## 7. 从 Task 文件到 metadata 表

`load_task_info.py::extract_task_metadata()` 会从 Task 类抽取：

```text
task_name
instruction / instruction_variants
episode_s
scene
contact_objects
attributes
subtasks
num_sequential_stages
num_atomic_conditions
num_subtasks
difficulty_score
difficulty_label
```

其中难度相关字段来自：

```text
count_stages_and_conditions(subtasks)
count_subtasks(subtasks)
compute_difficulty_score(num_subtasks, attributes)
```

`generate_task_metadata.py` 再把这些结果写成：

```text
robolab/tasks/_metadata/task_metadata.json
robolab/tasks/_metadata/task_table.csv
robolab/tasks/README.md
```

这些文件就是后续按能力轴、属性和难度等级做结果分析的基础。

## 8. 用几个任务算一遍

| 任务 | attributes | subtask 计数直觉 | max(w) | score | label |
|---|---|---|---:|---:|---|
| `BananaInBowlTask` | `["semantics"]` | 1 个 pick-place | 0 | 1 | simple |
| `RubiksCubeLeftOfBowlTask` | `["spatial"]` | 1 个空间放置 | 1 | 2 | simple |
| `RedItemsInBinTask` | `["color", "sorting"]` | 2 个对象都要入箱 | 2 | 4 | moderate |
| `Stack3RubiksCubeTask` | `["stacking"]` | 任意两块先堆 + 三块全堆 | 2 | 4 | moderate |
| 复杂重定向长任务 | `["reorientation", ...]` | 多阶段动作链 | 3 | 通常 >=5 | complex |

说人话：`num_subtasks` 衡量“任务有多长”，`max(w)` 衡量“最难推理/灵巧要求是什么”。两者相加，就是 RoboLab 给用户快速扫结果用的 difficulty label。

## 9. 分析结果时该怎么看

不要只看总体 success rate。更有价值的切法是：

1. **按能力轴看**：visual / procedural / relational 哪条轴掉分最大。
2. **按细粒度属性看**：是 `color` 差，还是 `spatial` 差，还是 `stacking` 差。
3. **按难度看**：simple 是否接近饱和，moderate 是否开始掉，complex 是否几乎失败。
4. **按 subtask 看**：失败发生在 grasp、hover、drop、done 哪个阶段。
5. **按场景构成看**：物体数量、干扰物、容器大小、背景/光照是否改变成功率。

> [!TIP]
> **一句话记忆**：能力轴回答“模型弱在哪类能力”，subtask 回答“失败卡在哪一步”，difficulty 回答“这个任务设计上有多难”，三者合起来才比单个 success rate 更有解释力。
