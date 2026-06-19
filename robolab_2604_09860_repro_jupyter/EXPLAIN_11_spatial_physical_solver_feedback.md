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

## 深挖 A：这两个 solver 共同操作的“中间表示”是什么

Spatial 和 Physical 不是直接操作自然语言，也不是直接操作 USD 场景。它们操作的是 LLM 生成后的 typed predicates 和对象状态。

可以把数据结构理解成四张表：

| 数据 | 说人话解释 | 主要由谁用 |
|---|---|---|
| `object_states` | 每个对象当前解到哪里了：`x/y/z/yaw`、是否已放置、挂了哪些 predicates | Spatial + Physical |
| `object_dims` | 每个对象的宽、深、高 | 碰撞、边界、支撑、容器 packing |
| `predicates` | `place-on-base`、`left-of`、`place-on`、`place-in` 等结构化约束 | 两个 solver 分阶段消费 |
| `object_metadata/object_paths` | USD 路径、类别、容器/支撑能力、物理属性等 | Physical/后续场景实例化 |

**【绿色标识｜核心结论】**

这一步的关键不是“LLM 直接生成坐标”，而是“LLM 生成可检查的约束”。坐标由 solver 根据约束、尺寸和桌面边界解出来。

一个典型对象会经历这样的状态变化：

```text
初始：ObjectState(name="apple_01", x=None, y=None, z=None, yaw=None)
LLM：给它 place-in(container="bowl_0") predicate
Spatial：发现它有 physical predicate，所以暂时不强行解桌面 2D pose
Physical：等 bowl_0 的 base pose 解好后，再把 apple_01 放进 bowl_0 内部
输出：ObjectState(x=..., y=..., z=..., yaw=..., is_placed=True)
```

**【橙色标识｜容易误解】**

`place-in` / `place-on` 对象通常不是 Algorithm 1 的主要求解对象。Algorithm 1 主要先把 container/support/loose base objects 放好；Algorithm 2 再处理依附在它们上面的对象。

## 深挖 B：Spatial Solver 不是“随机撒点”，而是带回退的约束满足

Algorithm 1 看起来短，但源码里有几层工程保护。

### B1. 它会根据场景密度调整模式

源码里会根据对象数量、平均 footprint、大对象数量进入不同模式：

| 模式 | 触发直觉 | 策略 |
|---|---|---|
| normal | 对象少，尺寸普通 | 使用默认 collision margin |
| hard/container | 对象较多，或大容器/大支撑多 | 缩小 margin、增加迭代数 |
| ultra-dense | 18 个以上对象 | 更小 margin、更高迭代次数 |

这件事很重要，因为桌面任务不是数学竞赛里的干净约束。真实 benchmark 场景会有 bowl、plate、bin、mug、tool、food 混在一起，大对象多时，默认 5cm 间距可能直接无解。

### B2. `margins_to_try` 不是“越放越松”，而是多次重启搜索

源码里的 `margins_to_try` 会在失败时调整 collision margin 并重新随机化未固定对象。它的目的不是保证一定变好，而是避免卡在某个坏初始化。

可以把它理解成：

```text
attempt 0: 用当前 margin 初始化并优化
失败 -> 换 margin + 重新随机未固定对象
attempt 1: 再解一次
失败 -> 再换 margin + 再随机
...
```

**【绿色标识｜核心直觉】**

这是 sampling + local repair，不是一次解析式求解。RoboLab 追求的是几分钟内批量生成“足够好、可评测”的场景，而不是求全局最优布局。

### B3. 相对关系在 RoboLab 坐标系里有明确方向

源码注释里有一个非常关键的约定：

```text
Front = +X
Back  = -X
Left  = +Y
Right = -Y
```

所以：

| 语言关系 | 坐标变化 |
|---|---|
| `left-of(A, B)` | `A.y = B.y + distance` |
| `right-of(A, B)` | `A.y = B.y - distance` |
| `front-of(A, B)` | `A.x = B.x + distance` |
| `back-of(A, B)` | `A.x = B.x - distance` |

这和很多人直觉里的屏幕坐标不同。看视频时“左/右”还会受到相机视角影响，所以 debug spatial relation 时应该优先看世界坐标，而不是只看截图。

### B4. collision resolution 是局部推开，不是全局重排

源码里的 `_check_collisions` 用 footprint 半径近似检测重叠，`_resolve_collision` 根据两物体中心连线把它们推开，再 clamp 回桌面边界。

这类方法的优点是快，缺点是可能局部卡住。于是又加了两个机制：

- 如果 collision 数量长期不下降，就随机扰动位置打破僵局。
- 如果碰到 fixed object，例如 rack fixture，只移动非固定对象。

### B5. 为什么 physical predicate 要被跳过

Spatial Solver 检查“未完全求解对象”时，会跳过带 `place-on` / `place-in` / `place-anywhere` 等 physical predicate 的对象。否则 apple/orange 这类要放进 bowl 的对象会被误认为“还没有桌面坐标，所以 spatial solve 失败”。

**【橙色标识｜常见错误】**

如果你自己写任务生成器，把所有物体都强行 `place-on-base`，再额外给 `place-in`，会造成语义冲突：对象既被要求在桌面固定位置，又被要求在容器内部。更合理的做法是让 container/support 有 base pose，让内部对象只带 physical predicate。

## 深挖 C：Physical Solver 的核心是“局部坐标系里的 packing”

Algorithm 2 解决的不是“z 加一下”这么简单。真正麻烦的是：支撑物有 yaw，容器有口径，多个 sibling 会互相重叠，对象本身也有 yaw。

### C1. `place-on` 为什么要按 support 分组

如果有三个对象都放在同一个 tray 上，不能逐个独立求解：

```text
place-on(spoon, tray)
place-on(fork, tray)
place-on(mug, tray)
```

如果每个对象都单独“优先放 center”，它们都会抢 tray 中心。源码会把同一 support 上的 `place-on` predicate 分组，再联合找多个 slot。

说人话：

> `place-on` 的难点不是把一个对象放上去，而是把同一层 sibling 放得下、分得开、还落在支撑物 footprint 内。

### C2. 支撑物局部坐标要随 yaw 旋转回世界坐标

`_candidate_support_offsets` 这类函数生成的是 support 局部坐标里的候选点，例如 center、边缘、环形点。真正写回对象 pose 时，要把局部 offset 按 support yaw 旋转到世界坐标。

否则会出现：

- plate 旋转了，但 banana 仍按世界 x/y 放，看起来偏到 plate 外。
- tray 斜着放，但上面的 spoon/fork 仍按未旋转矩形判断，实际渲染会穿出边界。

### C3. `place-in` 不是矩形网格就够，容器经常更像椭圆口径

bowl、cup、round bin 这类容器不能只用矩形 bounding box 判断。源码里会用类似 `_fits_container_ellipse` 的检查：对象 footprint 要落在容器口径的有效椭圆区域内。

这解释了为什么有时从 top view 看对象似乎在 bowl 的 bounding box 里，但仍被判定为不合格：它可能落在矩形角落，而那个角落实际上在圆形/椭圆口径之外。

### C4. 多层 packing 是最后手段，不是默认堆叠

当容器一层放不下时，solver 可以考虑 layers。这个设计的意义是：优先让容器内部对象在同一层分开；只有实在放不下时才向上分层。

但是 layers 也会引入风险：

- 上层对象更容易物理 settle 后滚动。
- 容器浅时，z 太高会导致对象看起来像浮在外面。
- 对于任务评测来说，层数过多会让抓取和可见性变差。

所以 prompt 里才会建议：如果碰撞持续，优先选更小对象或减少内部对象，而不是盲目把所有东西塞进容器。

### C5. stability threshold 是从“看起来放上去了”到“物理上稳定”的边界

`physical_solver.py` 的初始化参数里有 `stability_threshold`。这代表一个思想：场景初始位姿写出来后，还需要物理 settle。对象最大位移超过阈值，就说明这个放置不稳定。

**【绿色标识｜核心结论】**

RoboLab 的 physical placement 不是只做几何 packing。几何 packing 只是初始条件；最终还要考虑物理 settle 后对象是否还在合理位置。

## 深挖 D：失败反馈其实是“诊断信息压缩器”

Figure 17 的 feedback block 看起来简单，但它背后做了一个重要转译：把 solver 看得懂的失败，翻译成 LLM 能改的语言。

| solver 失败 | 原始含义 | 给 LLM 的修复策略 |
|---|---|---|
| collision unresolved | footprint 放不下或局部优化卡死 | 换小物体、减少 base objects、增加 `place-in` / `place-on` |
| out of bounds | 对象中心或 footprint 超出桌面 | 调整 anchor 坐标，减少边缘放置 |
| support slot not found | 支撑物太小或 sibling 太多 | 换更大 support，减少 `place-on` 数量 |
| container crowding | 容器口径/面积不足 | 换更大 container，减少内部对象，选小物体 |
| unstable after settle | 初始几何可行但物理不稳定 | 降低堆叠高度、换平面支撑、减少层数 |
| invalid object name | 不在 catalog | 只能回到对象目录重选 |

这也是为什么反馈里出现的建议是“MORE containment / MORE stacking / clustering / smaller objects”。它们不是随口建议，而是在压缩几类最常见失败：

- 桌面面积不够：用 containment/stacking 节省 base footprint。
- 对象太分散：用 clustering 生成局部自然组合。
- 物体过大：选 smaller objects 降低碰撞、容器和支撑失败概率。

**【橙色标识｜边界】**

反馈不能保证下一轮一定成功。它只是把失败信号加入 prompt，提高下一轮 LLM 生成可解 predicates 的概率。真正的成功仍然要经过 grammar check、spatial solve、physical solve、intersection validation 和物理 settle。

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
