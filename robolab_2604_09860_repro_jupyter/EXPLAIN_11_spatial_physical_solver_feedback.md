# 精讲 11：空间求解器、物理放置求解器与失败反馈

> **【绿色标识｜核心结论】** 这两张图讲的是 RoboLab 场景生成的“自动修复闭环”：LLM 先产出语义谓词，空间求解器解 2D 基础布局，物理放置求解器解 3D 支撑/容器关系；如果任一步失败，就把诊断反馈追加回下一轮 prompt。  
> **【蓝色标识｜源码路径】** 主要对应 `robolab/scene_gen/llm_scene_gen/spatial_solver.py`、`physical_solver.py`、`feedback_system.py`、`predicates.py`。  
> **【橙色标识｜容易误解】** Algorithm 1 和 Algorithm 2 不是互相替代。Algorithm 1 解决“桌面上基础对象怎么摆”，Algorithm 2 解决“对象怎么放到支撑物上或容器里”。

## 先说结论

RoboLab 场景生成可以理解成三段流水线：

```text
Stage I: LLM semantic planning
  输入：主题、对象目录、桌面尺寸、目标对象数
  输出：objects + predicates JSON

Stage II-A: Spatial Constraint Solver
  输入：基础对象 + 空间谓词 + 桌面边界
  输出：base objects 的 2D 位姿 (x, y, yaw)

Stage II-B: Physical Placement Solver
  输入：对象 + physical predicates + 已解出的 base poses
  输出：所有对象的 3D 位姿 (x, y, z)

Feedback Loop
  输入：语法错误、碰撞、出界、物理不稳定、容器/支撑失败
  输出：下一轮 prompt 的 PREVIOUS ATTEMPT FAILED block
```

一句话：

> LLM 负责“怎么组织场景”，solver 负责“几何和物理上能不能摆”，feedback 负责“失败后怎么让 LLM 改”。

## 图 1：Previous Attempt Failed 反馈块

你第一张图是 Figure 17：当 spatial solving、physical placement、grammar checks 或 intersection validation 失败时，系统把一段反馈追加到 user prompt。

图里的结构是：

```text
PREVIOUS ATTEMPT FAILED:
feedback string produced by spatial/physical solver or grammar checks

Please fix the issues. Common fixes:
- Use MORE containment (place-in) to reduce table crowding
- Use MORE stacking (place-on) to utilize vertical space
- Use clustering (cluster-around) instead of individual placements
- Select SMALLER objects if collisions persist
```

### 为什么这个反馈块很重要

没有这个块，LLM 每次失败后可能还是生成同一种坏布局。  
有了这个块，失败信息会变成下一轮生成的约束。

| 失败类型 | 反馈要告诉 LLM 什么 |
|---|---|
| collision | 哪些对象重叠，需要增加距离、换小物体、用容器/支撑减少桌面占用 |
| out of bounds | 哪些对象超出桌面，需要调整坐标或减少对象 |
| grammar issue | 哪些对象缺少 x/y/yaw，或者谓词不完整 |
| physical instability | 哪些对象掉落/移动，需要更稳定支撑或减少堆叠 |
| containment failure | 容器放不下，需要减少内部对象或换更大容器 |

**【绿色标识｜核心直觉】**

这个 feedback block 不是给人看的错误日志，而是给 LLM 的“修题提示”。它把 solver 的低层错误翻译成 LLM 能执行的修复策略。

### 为什么建议“更多 containment / stacking / clustering”

这几个建议都在解决同一个问题：桌面面积有限。

| 修复建议 | 解决什么 |
|---|---|
| MORE containment (`place-in`) | 多个小物体共享一个容器 footprint，减少桌面拥挤 |
| MORE stacking (`place-on`) | 利用 z 方向，把对象放到支撑物上 |
| clustering (`cluster-around`) | 让对象围绕 anchor 局部聚集，而不是每个对象都独立占点 |
| smaller objects | 直接降低碰撞概率和容器/支撑失败概率 |

它和精讲10的 prompt 是一对：精讲10是“第一轮怎么写好”，这张图是“失败后怎么改好”。

## Algorithm 1：Spatial Constraint Solver 回顾

Algorithm 1 的输入输出是：

| 项 | 内容 |
|---|---|
| 输入 | Objects `B`、Predicates `P`、Table Bounds `Lmax` |
| 输出 | base objects 的 2D 坐标 `(x, y, theta)` |

它处理的是基础对象，典型包括：

- bowl、bin、plate、tray、box、mug 等 anchor。
- loose object，如果没有 `place-in` / `place-on` physical relation，也需要直接放到桌面。

### 三个阶段

| 阶段 | 做什么 | 目的 |
|---|---|---|
| Phase 1 Initialization | 随机放 loose objects，处理 `place-on-base` 和 `cluster-around` | 得到初始布局 |
| Phase 2 Relative Constraints | 处理 left/right/front/back/align/facing 等关系 | 满足语言中的相对关系 |
| Phase 3 Collision Resolution | 找碰撞、推开、clamp 到桌面边界、必要时扰动 | 保证 2D footprint 不重叠且在桌面内 |

### 和源码的对应

| 论文概念 | 源码落点 |
|---|---|
| `place-on-base` | `SpatialSolver._apply_place_on_base` |
| relative constraints | `SpatialSolver._apply_relative_position` |
| orientation | `SpatialSolver._apply_orientation` |
| collision resolution | `SpatialSolver._optimize_placement` 及 overlap 相关函数 |
| margin retry | `solve()` 中的 `margins_to_try` |

**【橙色标识｜边界】**

Algorithm 1 不负责“苹果在碗里”的最终 z 坐标，也不负责“香蕉在盘子上”的高度。它只保证 bowl/plate 这些基础对象先有合理的桌面位置。

## 图 2：Algorithm 2 Physical Placement Solver

你第二张图是 Algorithm 2：Physical Placement Solver。它接在空间求解器之后。

输入输出：

| 项 | 内容 |
|---|---|
| 输入 | Objects `B`、Predicates `P`、Solved Base Poses |
| 输出 | 所有对象的 3D 坐标 `(x, y, z)` |

它主要处理两类 physical predicate：

| Predicate | 例子 | 需要解决的问题 |
|---|---|---|
| `place-on` | banana on plate | 在支撑物顶面找一个不重叠位置，并设置正确高度 |
| `place-in` | apple/orange in bowl | 在容器内部/口径范围内 pack 多个对象，并设置 z 高度 |

## Algorithm 2 上半部分：Solve Stacking

截图里的逻辑是：

```text
for all p where p.type == place-on:
    s <- p.support
    B_peers <- objects already on s
    (x, y) <- FindSpot(s, p.object, B_peers)
    p.object.z <- s.z + s.height + p.object.height / 2
    p.object.(x, y) <- (x, y)
```

说人话：

1. 找到支撑物 `s`，比如 plate/tray/shelf。
2. 看这个支撑物上已经放了哪些对象，避免新对象和它们重叠。
3. 在支撑物顶面找一个合适 slot。
4. `x/y` 用 slot 的位置。
5. `z` 设到支撑物顶面之上：支撑物 top + 物体半高 + 小 buffer。

### 源码如何做得更工程化

当前 `physical_solver.py` 里不是只处理一个对象，而是会把同一支撑物上的 `place-on` 分组：

| 源码函数 | 作用 |
|---|---|
| `_solve_place_on_group` | 把同一个 support 上的多个对象联合排布 |
| `_find_joint_support_slots` | 用回溯找多个 sibling 的非重叠 slot |
| `_candidate_support_offsets` | 生成 center、edge、环形候选位置 |
| `_fits_support_rectangle` | 检查 footprint 是否落在支撑物矩形内 |
| `_finish_place_on` | 设置 z/pitch/roll/is_placed |

**【绿色标识｜核心直觉】**

`place-on` 不是简单把对象中心放到 plate 中心。它要考虑对象 footprint、支撑物尺寸、支撑物 yaw、同层 sibling 是否重叠，以及最终 z 高度。

## Algorithm 2 下半部分：Solve Containment

截图里的逻辑是：

```text
for all p where p.type == place-in:
    c <- p.container
    if TotalArea(p.objects) > 0.8 * Area(c):
        p.objects <- SortAndFilter(p.objects, c.capacity)
    (R, C) <- ComputeGridDimensions(c.dims, |p.objects|)
    for i = 0 to |p.objects| - 1:
        (r, c) <- (i // C, i % C)
        (xloc, yloc) <- GridCellCenter(...)
        Jitter(...)
        p.objects[i].(x, y) <- container center + local offset
        p.objects[i].z <- container z + container height / 2 + buffer
```

说人话：

1. 找容器，比如 bowl/bin/box。
2. 看要放进去的对象总体面积是不是太大。
3. 太大就排序和过滤，优先放更合适的对象。
4. 根据容器大小和对象数量划分网格。
5. 每个对象放到一个网格 cell 中心附近，加一点 jitter，避免机械排列。
6. z 设到容器上方一点，后续物理 settle 可以让它落进去。

### 源码如何做得更工程化

当前 `physical_solver.py` 的 `place-in` 逻辑比伪代码更细：

| 源码函数/逻辑 | 作用 |
|---|---|
| `_solve_place_in` | 容器内对象 packing 主函数 |
| `_candidate_local_yaws` | 为对象尝试多个 yaw，降低 footprint 失败概率 |
| `_candidate_container_offsets` | 在容器口径内生成候选局部 offset |
| `_fits_container_ellipse` | 检查对象 footprint 是否放得进容器口径 |
| `_rect_overlaps_layer` | 检查同层对象是否重叠 |
| layers | 如果一层放不下，就向上分层，而不是横向穿出容器 |

**【绿色标识｜核心直觉】**

`place-in` 的本质是 packing，不是简单把所有对象坐标都设成容器中心。否则多个水果会完全重叠。

## Algorithm 1 和 Algorithm 2 如何串起来

用一个 bowl + plate + fruit 例子：

```json
{
  "objects": [
    {"name": "bowl_0"},
    {"name": "plate_large"},
    {"name": "apple_01"},
    {"name": "orange_01"},
    {"name": "banana"}
  ],
  "predicates": [
    {"type": "place-on-base", "object": "bowl_0", "x": 0.40, "y": 0.15, "yaw": 23},
    {"type": "place-on-base", "object": "plate_large", "x": 0.65, "y": -0.10, "yaw": 156},
    {"type": "place-in", "objects": ["apple_01", "orange_01"], "container": "bowl_0"},
    {"type": "place-on", "object": "banana", "support": "plate_large", "position": "center"}
  ]
}
```

执行顺序是：

1. Spatial solver 先把 `bowl_0` 和 `plate_large` 放到桌面上。
2. Physical solver 用 bowl 的 pose 计算 apple/orange 的 `(x, y, z)`。
3. Physical solver 用 plate 的 pose 计算 banana 的 `(x, y, z)`。
4. 如果碰撞、出界或放不下，feedback block 让 LLM 下一轮增加 containment/stacking/clustering 或换小物体。

## 失败反馈为什么要追加到 Prompt，而不是直接自动改

有些错误 solver 可以修：

- 小碰撞可以推开。
- yaw 可以重采样。
- 容器内局部 packing 可以换 slot。

但有些错误需要 LLM 重新规划：

| 错误 | 为什么不能只靠 solver |
|---|---|
| 选了太多大物体 | solver 无法凭空换对象 |
| 缺少 container/support anchor | 需要改 predicate 结构 |
| 所有对象都独立放桌面导致拥挤 | 需要语义上改成 `place-in` / `place-on` |
| 对象名不存在 | 需要回到 catalog 重新选 |
| 任务主题不匹配 | solver 不懂主题语义 |

所以 feedback 不是替代 solver，而是把低层失败转回上游规划。

## 与 Prompt 设计的关系

精讲10讲的是：第一轮 prompt 如何尽量避免坏输出。  
精讲11讲的是：坏输出已经发生后，solver 如何检测，以及怎么把失败变成下一轮 prompt 的修复建议。

可以合起来记：

```text
Prompt 先验 -> Predicate JSON -> Spatial Solver -> Physical Solver -> Feedback -> Prompt 修复
```

这就是 RoboLab 场景生成能规模化的关键：不要求 LLM 一次生成完美场景，而是把生成变成可检查、可反馈、可重试的闭环。

## 小结

两张图的核心含义是：

- Fig.17 是“失败怎么反馈给 LLM”。
- Algorithm 2 是“支撑/容器关系怎么变成 3D 坐标”。
- Algorithm 1 + Algorithm 2 合起来，才是从 typed predicates 到可用 3D scene 的求解过程。

最终目标不是生成看起来热闹的桌面，而是生成：

```text
语义上合理
几何上不碰撞
物理上可 settle
任务上可评测
失败后可自动修复
```
