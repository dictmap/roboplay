# 精讲 7：Baseline 方法，论文里的对照场景生成怎么实现

> [!NOTE]
> **颜色标识**：绿色表示核心结论，蓝色表示源码/输入输出路径，橙色表示边界、风险和容易误解的点。

## 先说结论

论文 Appendix C-C 的 **Baseline Method** 指的是“场景生成 baseline”，不是 Pi05、GR00T、PaliGemma 这些策略 baseline。它是拿来和 RoboLab 自己的层级式 scene generation 方法对比的。

> [!TIP]
> **核心结论**：baseline 是一种标准 domain randomization 风格的单次布局方法：LLM 先选一批对象，再给出一个桌面网格；算法把桌面切成 `rows x columns` 个 cell，把对象按顺序塞进 cell，并在 cell 内随机 jitter。它能保证基本间隔，但不会生成“放进容器”“堆叠在支撑物上”“围绕 anchor 聚类”这些有语义结构的真实场景。

一句话记住：

```text
baseline = 选物体 + 网格分格 + cell 内随机抖动 + 固定安全高度 + 一次物理 settle
RoboLab ours = 语义谓词 + 几何约束求解 + 物理约束求解 + 失败反馈修复
```

## 1. Baseline 在论文里解决什么问题

论文做 scene generation 时，需要证明自己的层级式方法不是“看起来复杂但没必要”。所以它设计了一个强但简单的对照组：

| 方法 | 作用 |
|---|---|
| Baseline | 代表常见 domain randomization / grid random placement：对象能分散摆在桌面上 |
| Ours | 代表 RoboLab 的层级式语义场景生成：对象有容器、支撑、聚类、相对位置和物理检查 |

这个 baseline 不是为了跑 policy 评测，而是为了回答：

```text
如果只用网格随机摆放，生成场景质量能不能接近 RoboLab 的层级式场景？
```

论文结论是不能。baseline 可以摆开物体，但在视觉真实感、功能性、布局正确性、完整性和 GPT preference 上都明显弱于层级式方法。

> [!WARNING]
> **不要把 baseline 误读成策略 baseline**：这里的 baseline 是 scene generation baseline。策略对比表里那些模型是 policy baseline/被评测策略；Appendix C-C 的 baseline 是场景生成方法对照。

## 2. Baseline 的输入输出

Baseline 输入：

| 输入 | 含义 |
|---|---|
| `theme` | 场景主题，例如 kitchen counter、bathroom counter、classroom supplies |
| `object catalog` | 可选对象和尺寸 |
| `target object count` | 希望场景里放多少物体 |
| `rows, columns` | LLM 建议的桌面网格尺寸 |
| `table bounds` | 桌面范围，例如 X/Y 边界 |
| `jitter range` | cell 内随机偏移范围 |

Baseline 输出：

| 输出 | 含义 |
|---|---|
| object list | LLM 选出来的对象 |
| `(x, y, z, yaw)` | 每个物体在桌面上的位置、高度和朝向 |
| settled scene | 物理仿真 settle 后的场景 |
| rendered images | 用于 VQA/GPT preference/quality 评分 |

代码层面可以抽象成：

```python
objects = llm_select_objects(theme, catalog, target_count)
rows, cols = llm_suggest_grid(objects, table_size)
cells = split_table_into_grid(table_bounds, rows, cols)

for object, cell in zip(objects, cells):
    x = cell.center_x + uniform(-jitter_x, jitter_x)
    y = cell.center_y + uniform(-jitter_y, jitter_y)
    z = safe_height(object)
    yaw = random_yaw()
    place_on_table(object, x, y, z, yaw)

simulate_under_gravity()
```

> [!NOTE]
> **源码对照**：当前 checkout 里没有看到单独的 `baseline.py` 主入口；可对照阅读的是主方法实现：`robolab/scene_gen/llm_scene_gen/predicates.py`、`spatial_solver.py`、`physical_solver.py`、`feedback_system.py`。Baseline 更像论文实验里的对照算法，而不是 RoboLab 用户日常运行的主路径。

## 3. Baseline 为什么合理

它不是一个“故意很差”的 strawman。它合理的地方在于：

1. **简单稳定**：网格保证对象基本分开，不容易初始就全撞在一起。
2. **实现成本低**：不需要复杂谓词库，也不需要多轮 LLM 修复。
3. **符合常见随机化习惯**：很多仿真 benchmark 会随机选物体、随机位置、随机 yaw。
4. **可批量生成**：一次 pass 就能产出很多场景。

所以它可以代表一类常见做法：

```text
只要让物体在桌面上随机且不重叠，就可以做大规模评测。
```

RoboLab 论文要反驳的正是这个假设：真实任务评测需要的不只是“物体不重叠”，还需要语义和功能结构。

## 4. Baseline 的核心局限

论文里 baseline 的关键限制是：对象只是被放到安全高度上，不做复杂堆叠或容器关系。

| 局限 | 具体表现 | 对机器人评测的影响 |
|---|---|---|
| 没有 containment | 水果不会自然在碗里，工具不会在托盘里 | 很多真实目标状态和初始状态不自然 |
| 没有 stacking/support | 物体不会在盘子、托盘、架子、其他物体上 | 过程化任务和堆叠任务缺少结构 |
| 没有 anchor/cluster | 物体均匀铺开，不像真实桌面上的“物品堆” | 视觉和空间关系不自然 |
| 没有语义修复 | 如果 LLM 选了不合适的大物体组合，只能物理 settle，不能回去改计划 | 高密度场景更容易失败或不完整 |
| 没有任务导向结构 | 场景可能能看，但不一定适合生成任务 | 后续 TaskGen 质量受限 |

> [!WARNING]
> **物理 settle 不是万能修复**：baseline 最后也会跑物理仿真，让小穿插或轻微不稳定通过重力 settle。但它没有能力修复“为什么一个碗里没有东西”“为什么所有物体网格排列得像展板”这种语义和结构问题。

## 5. RoboLab 主方法比 baseline 多了什么

论文 Appendix C 描述的主方法可以看成四层：

```text
Stage I: LLM 生成结构化 scene plan
  -> 选择对象
  -> 写出 place-in / place-on / cluster-around / place-on-base 等谓词

Stage II: 几何约束求解
  -> 把谓词变成 2D/3D 坐标
  -> 检查碰撞、边界、相对位置

Stage III: 物理仿真检查
  -> 在 Isaac/物理环境下 settle
  -> 检查掉落、位移、穿插

Stage IV: feedback repair
  -> 如果失败，把错误反馈给 LLM
  -> 让 LLM 改对象、改关系、改密度、改布局
```

这和 baseline 的差别不是“随机数用得更高级”，而是表达空间不同：

| 维度 | Baseline | RoboLab 主方法 |
|---|---|---|
| 布局单位 | 网格 cell | 语义谓词 |
| 空间关系 | 基本无，只靠 cell 顺序 | left/right/front/back/align/cluster 等 |
| 物理关系 | 全部 on table | place-on、place-in、place-anywhere |
| 失败处理 | 一次 pass | solver/physics feedback 后可修复 |
| 场景真实感 | 容易网格化 | 更像真实桌面结构 |
| 任务可用性 | 初始状态较浅 | 更适合生成多步骤/关系/过程化任务 |

## 6. 源码对应：主方法怎么落地

虽然 baseline 自身没有在当前 checkout 里作为主脚本暴露，但主方法的核心模块很清楚。

### `predicates.py`

这里定义 scene generation 的谓词类型：

```text
Spatial predicates:
  left-of / right-of / front-of / back-of
  place-on-base
  align-left / align-right / align-center
  facing-left / random-rot

Physical predicates:
  place-on
  place-in
  place-anywhere
```

说人话：这相当于给 LLM 一个“场景语法”。LLM 不直接输出乱七八糟的坐标，而是输出“苹果放进碗里”“勺子放在盘子上”“杯子在碗左边”这种可求解结构。

### `spatial_solver.py`

`SpatialSolver.solve()` 做 2D 空间求解：

```text
1. 根据场景复杂度调整 collision margin 和 iteration
2. 先处理 place-on-base
3. 再处理 relative position predicates
4. 再处理 orientation predicates
5. 检查 unsolved objects
6. 做 collision optimization
7. 如果失败，可尝试 relaxation
```

这比 baseline 的 grid 多了两个关键能力：

- 可以表达相对关系，而不是固定格子。
- 可以在碰撞失败时迭代优化，而不是一次摆完。

### `physical_solver.py`

`PhysicalSolver.solve()` 处理 3D/物理关系：

```text
place-on:
  把物体放在 support 上，检查 footprint 是否能放下

place-in:
  把多个物体按层塞到 container mouth 上方
  再让物理 settle 把它们落入容器

place-anywhere:
  在可行区域找一个不冲突的位置
```

这正是 baseline 缺少的能力：baseline 所有物体都只是桌面上的独立 item，主方法可以生成“容器里有东西”“支撑物上有东西”“密集物品堆”的场景。

### `feedback_system.py`

失败后会生成反馈，例如：

```text
SOLVER FAILURE:
  collisions detected
  objects out of bounds
  increase distance or reposition

PHYSICS VALIDATION FAILURE:
  object moved too much after simulation
  increase support_ratio
  place unstable objects inside containers
```

论文图 17 里的修复提示，就是把 solver/physics 的错误消息打包回 LLM，让它下一轮改场景计划。

> [!TIP]
> **怎么记**：baseline 是“摆坐标”；RoboLab 主方法是“先写语义关系，再让 solver 把关系翻译成坐标，失败了还能反馈修复”。

## 7. 论文实验怎么看

论文 Appendix C-D 用生成场景指标比较 baseline 和 ours。核心指标包括：

| 指标 | 含义 |
|---|---|
| VQA score | 用视觉问答检查生成图像是否符合语义问题 |
| GPT preference | 给 GPT 看两张图，让它偏好哪种方法 |
| Real. | 视觉真实感 |
| Func. | 功能性，比如容器/支撑关系是否合理 |
| Lay. | 布局正确性 |
| Qual. | 总体质量 |
| Compl. | 场景完整性 |

论文报告的总体趋势是：RoboLab 主方法在所有这些维度上都超过 baseline，尤其是视觉真实感、语义功能性和场景完整性。表 VI 里 baseline 的 GPT preference 是 `18%`，ours 是 `82%`；这说明评估器更常偏好层级式方法生成的场景。

> [!WARNING]
> **指标不是机器人成功率**：这些是 scene generation 质量指标，不是 Pi05 在任务里的 success rate。它们评价“生成场景像不像、合不合理、完不完整”，不是评价策略动作做得好不好。

## 8. 为什么 baseline 对 RoboLab-120 不够

RoboLab-120 的任务不是只看“桌上有哪些物体”，还看：

- 视觉属性：颜色、语义、大小。
- 关系推理：left/right、counting、and/or。
- 过程推理：affordance、reorientation、stacking。
- 多步骤：先 A 再 B。

如果场景只是网格化随机摆放，很多任务很难自然成立：

| 任务需求 | baseline 问题 |
|---|---|
| “把碗里的苹果拿出来” | baseline 初始状态没有 place-in |
| “把杯子放到托盘上” | baseline 不知道 support surface |
| “把左边的红物体放进箱子” | cell 位置可能有 left/right，但不是语义规划出来的场景关系 |
| “把三个 cube 叠起来” | baseline 不生成稳定堆叠结构 |
| “整理一堆杂乱柜台物品” | grid 排列不像真实杂乱场景 |

所以 baseline 可以作为对照，但不能作为高质量任务生成的主路径。

## 9. 本次 notebook 的轻量测试要验证什么

我们不需要在本机重跑 Isaac 渲染，也能验证 baseline 的结构局限。轻量测试做三件事：

1. 用 `grid_baseline_layout()` 复刻论文 baseline：对象按 grid cell 顺序摆放，cell 内 jitter。
2. 用一个 `hierarchical_layout_example()` 表示主方法能表达的结构：`place-in`、`place-on`、`cluster-around`。
3. 检查 baseline 能做到基本分离，但不能表达容器/支撑/聚类关系。

预期结论：

```text
baseline_min_distance_ok = True
baseline_semantic_relations_supported = False
hierarchical_relations_supported = True
baseline_top_level_slots > hierarchical_top_level_slots
```

这对应论文里的差异：baseline 不是不能摆东西，而是只能摆“平面散点”；RoboLab 主方法能生成“有功能结构的场景”。

## 10. 一句话总结

> [!TIP]
> **核心结论**：Appendix C-C 的 baseline 是“网格随机摆放 + 一次物理 settle”的场景生成对照。它能保证物体基本分开，却不能生成容器、支撑、堆叠、聚类和可修复的语义结构；RoboLab 主方法真正多出来的是谓词表达、几何/物理求解和失败反馈闭环。

