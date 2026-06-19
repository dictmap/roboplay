# 精讲 10：Scene Generation Prompt 设计分析

> **【绿色标识｜核心结论】** 这几段 prompt 不是为了“写得像提示词工程”，而是在把 LLM 输出压成 RoboLab 可解析、可求解、可验证的中间表示：对象列表 + typed predicates。  
> **【蓝色标识｜源码路径】** 输出会对接 `robolab/scene_gen/llm_scene_gen/predicates.py`、`spatial_solver.py`、`physical_solver.py` 和 `feedback_system.py`。  
> **【橙色标识｜容易误解】** prompt 里让 LLM 写坐标，但不是让 LLM 完成全部几何/物理求解。LLM 负责语义规划和初始关系，solver 负责碰撞、边界、支撑和容器内放置。

## 先说结论

这三张图可以理解成一个三层 prompt 合约：

| 层 | 作用 | 解决的问题 |
|---|---|---|
| System Prompt | 定义“现实机器人桌面场景”的先验和谓词语言 | 防止 LLM 输出网格、纯坐标、不可解析的故事 |
| Output Format + Critical Rules | 定义 JSON schema 和硬规则 | 防止输出 markdown、对象名幻觉、依赖顺序错误 |
| User Prompt Template | 注入当前主题、目标对象数、桌面尺寸、对象目录和策略 | 防止场景和资产目录/桌面容量不匹配 |

一句话：

> System prompt 负责“世界观和语法”，Output prompt 负责“接口契约”，User prompt 负责“本次实例的动态约束”。

## 为什么不让 LLM 直接生成 USD

如果让 LLM 直接写 `.usda`，会遇到几个问题：

| 问题 | 后果 |
|---|---|
| USD 语法细节复杂 | LLM 容易写出不可加载文件 |
| 资产路径必须精确 | 对象名、payload path、prim path 任何一个错都会失败 |
| 物理几何很难靠文本一次写准 | 容易碰撞、悬空、穿模、出界 |
| 关系难以检查 | “苹果在碗里”如果只是一串 transform，很难知道语义是否满足 |

所以 RoboLab 采用分层：

```text
LLM 生成 typed predicates
-> predicate parser 转成 ObjectState/Predicate
-> spatial solver 解 2D 桌面布局
-> physical solver 解 place-in/place-on
-> feedback system 把错误反馈给 LLM 修复
-> 最后再生成 USD scene
```

这就是为什么 prompt 强调 `place-on-base`、`place-in`、`place-on`、`cluster-around`，而不是直接要求 LLM 输出完整 USD。

## 第一张图：System Prompt 为什么这么写

### 1. “scene generation expert”

开头把角色限定为 scene generation expert，目的是让模型优先考虑“生成可用场景”，而不是写故事、写任务说明或写自然语言描述。

它的隐含要求是：

- 输出要服务于机器人 manipulation。
- 场景要能被后续 solver/Isaac 使用。
- 重点是 realistic 和 physically plausible。

### 2. Real-world scene principles

这一段最重要的是反 baseline：

| Prompt 规则 | 为什么写 |
|---|---|
| Objects form clusters, not grids | 避免退化成均匀网格布局；论文 baseline 正是 grid+jitter 思路 |
| Containers have objects inside | 用 3D 容器关系增加语义和空间密度 |
| Supports have objects on top | 让场景有支撑关系，而不是所有物体都摊在桌上 |
| Objects scatter around containers | 模拟真实桌面上的局部聚集 |
| Orientations vary | 避免所有对象 0/90 度，看起来像程序摆拍 |

**【绿色标识｜核心直觉】**

真实桌面不是棋盘。人类会把相关对象聚在一起，碗里有水果，盘子上有食物，工具在容器附近。这个 prompt 是在给 LLM 注入“非网格、有关联、可操作”的场景先验。

### 3. Coordinate system

这段非常工程化：

```text
Table bounds: X=[0.25 to 0.85], Y=[-0.40 to 0.40]
Table center: (0.55, 0.0)
Front=+X, Back=-X, Left=+Y, Right=-Y
```

它解决两个问题：

| 问题 | 为什么必须写清楚 |
|---|---|
| 坐标边界 | 防止 LLM 把对象放出桌子 |
| 左右前后定义 | 防止 LLM 的自然语言方向和 solver 的方向相反 |

源码里的 `spatial_solver.py` 也按这个方向解释相对位置：Front 是 `+X`，Left 是 `+Y`，Right 是 `-Y`。

### 4. Placement types

这其实是给 LLM 的小型 DSL：

| Predicate | 语义 | 后续谁处理 |
|---|---|---|
| `place-on-base` | 对象直接放在桌面上，通常是 anchor 或 loose object | `SpatialSolver` |
| `place-in` | 对象在容器里 | `PhysicalSolver` |
| `place-on` | 对象在支撑物上 | `PhysicalSolver` |
| `cluster-around` | 多个对象围绕 anchor 分布 | Stage I 语义规划 + 空间布局 |

为什么每个类型都配例子？因为 LLM 对“抽象规范”容易跑偏，给 JSON 样例能显著降低格式错误。

### 5. Scene structure

```text
1. Place 1-2 anchor objects
2. Put objects inside containers
3. Put objects on supports
4. Cluster objects around anchors
5. Add loose objects
```

这是一条依赖顺序：

```text
anchor 先存在 -> 才能 place-in / place-on / cluster-around
```

如果 LLM 先写 `place-in apple -> bowl`，但没有先把 `bowl` 放到桌上，solver 就缺 anchor。  
所以 prompt 明确要求 containers/supports must be placed first。

### 6. Realistic spacing

spacing 不是装饰，它直接影响 solver 成功率：

| 间距规则 | 作用 |
|---|---|
| Anchors 0.25-0.35m apart | 防止两个大容器/支撑物互相碰撞 |
| Clustered 0.08-0.15m from anchor | 既像真实聚集，又不完全重叠 |
| Loose objects fill space naturally | 避免所有对象堆在一个点 |

## 第二张图：Output Format + Critical Rules

### JSON only

这条最硬：

```text
OUTPUT FORMAT (JSON only, no markdown)
Return ONLY valid JSON, no markdown
```

原因很简单：后面的程序要 `json.loads()`。  
如果模型输出：

```text
Here is the JSON:
```json
...
```
```

就需要额外清洗，自动管线不稳定。

### objects 数组

```json
"objects": [{"name": "bowl_0"}, {"name": "plate_large"}]
```

这一步的作用是把“本场景要用哪些资产”显式列出来。后续会拿这些名字去对象目录里查 `usd_path`、尺寸、类别。

**【橙色标识｜关键风险】**

对象名必须和 catalog 精确匹配。`bowl`、`bowl_0`、`red_bowl` 可能是三个完全不同的名字；名字错了不是“语义相近”，而是资产加载失败。

### predicates 数组

`predicates` 是场景结构的核心。它不是描述文本，而是 solver 可执行的命令：

```json
{"type": "place-on-base", "object": "bowl_0", "x": 0.40, "y": 0.15, "yaw": 23}
{"type": "place-in", "objects": ["apple_01", "orange_01"], "container": "bowl_0"}
{"type": "place-on", "object": "banana", "support": "plate_large", "position": "center"}
{"type": "cluster-around", "objects": ["mug", "spoon"], "anchor": "bowl_0", "radius": 0.12}
```

这就是论文里 “semantic planning” 的中间层：LLM 不直接做物理，而是选择结构关系。

### Critical rules

| Rule | 为什么必要 |
|---|---|
| Object names must match catalog | 避免资产幻觉 |
| Containers/supports before children | 满足依赖关系 |
| containment + stacking + clustering | 生成比 grid baseline 更丰富的场景 |
| vary yaw | 避免机械网格感 |
| JSON only | 保证可机器解析 |

## 第三张图：User Prompt Template

这张图是运行时注入的动态约束。

### Scene request / target object count

```text
SCENE REQUEST: theme from dataset
TARGET: target object count objects
```

这告诉 LLM：

- 当前主题是什么，比如 kitchen cabinet、office desk、workshop bench。
- 大概要多少对象，不是越多越好。

### Table size

```text
TABLE SIZE: 0.7m x 1.0m = 0.70m2
```

这是给模型一个物理容量感。  
没有这句，LLM 很容易在一张小桌上塞 30 个大物体。

### Size limits

```text
max 1-2 large objects
prefer smaller for 8+ items
```

这条是为了提高 solver 成功率。大物体多了，碰撞和出界会急剧增加。  
如果目标对象数是 10-14，中小物体 + 容器/支撑关系比全是大物体更可行。

### Available objects by category

```text
CONTAINERS
SUPPORTS
FOOD
TOOLS
OTHER
```

这不是为了好看，而是给 LLM 做选择空间裁剪：

| 分类 | 作用 |
|---|---|
| CONTAINERS | 可用于 `place-in` |
| SUPPORTS | 可用于 `place-on` |
| FOOD | 常作为被操作对象 |
| TOOLS | 可作为桌面工具/cluster 对象 |
| OTHER | 补充主题多样性 |

如果只给一个长对象列表，LLM 很难知道哪个能装东西、哪个能当支撑。

### Medium scene strategy

```text
10-14 objects:
- Use 1-2 anchors
- Put 2-4 objects in containers
- Stack 1-2 items on supports
- Cluster 2-3 objects near anchors
- Vary yaw
```

这相当于把目标对象数转成布局配方。  
对 10-14 个对象，最容易失败的是桌面拥挤，所以 prompt 引导 LLM 使用：

- 容器：把多个物体放进一个 footprint。
- 支撑：利用竖直方向。
- cluster：让局部关系自然，但不要求每个对象都有精确坐标。

## 为什么这些 prompt 能提升场景质量

可以从论文 baseline 对比理解：

| Baseline grid+jitter | Predicate prompt 方法 |
|---|---|
| 均匀网格 | 局部聚集 |
| 所有对象基本在桌面上 | 有容器/支撑/围绕关系 |
| 一次 pass | 失败后有反馈修复 |
| 难表达语义结构 | typed predicates 可验证 |
| 容易“分散但无意义” | 更像真实可操作桌面 |

论文 Appendix C 的实验也显示，主方法在 VQA、realism、functionality、layout、completeness、quality 和 GPT preference 上整体优于 baseline。

## Prompt 和代码的对应关系

| Prompt 片段 | 代码落点 |
|---|---|
| `place-on-base`、`place-in`、`place-on` | `predicates.py` 中的 predicate class / enum |
| 坐标边界和 left/right/front/back | `spatial_solver.py` 的相对位置和边界逻辑 |
| 容器/支撑必须先放 | `PhysicalSolver` 需要已有 support/container anchor |
| grammar / solver / physics failure feedback | `feedback_system.py` |
| object catalog exact name | `assets/objects/object_catalog.json` 和 scene generation skill |
| size limits | prompt 阶段减少不可能布局，solver 阶段继续验证 |

## 几个用例如何判断好坏

### 用例 1：好的 medium kitchen prompt 输出

特征：

- JSON 可解析。
- 对象都来自 catalog。
- 1-2 个 anchor 先 `place-on-base`。
- 有 `place-in`，也有 `place-on` 或 `cluster-around`。
- yaw 不是全 0/90/180。
- 坐标在桌面范围内。
- 大物体不超过 1-2 个。

### 用例 2：对象名幻觉

坏输出：

```json
{"name": "beautiful_red_ceramic_bowl"}
```

如果 catalog 里没有这个精确名字，后续无法加载 USD。  
所以 prompt 用 “MUST match EXACTLY from catalog” 约束。

### 用例 3：依赖顺序错误

坏输出：

```json
{"type": "place-in", "objects": ["apple_01"], "container": "bowl_0"}
```

但没有先：

```json
{"type": "place-on-base", "object": "bowl_0", ...}
```

这会让容器没有基础位置。prompt 要求 containers/supports placed first，就是为了避免这个问题。

### 用例 4：网格化和 yaw 单调

坏输出：

- 物体均匀排成 3x4 网格。
- yaw 全是 0、90、180。

这类输出可能可解析，但不像真实桌面，也接近 baseline。  
所以 prompt 强调 clusters、around anchors、vary yaw。

### 用例 5：大物体过多

坏输出：

- 10 个对象里选了 5 个 footprint 很大的箱子/托盘。

即使 JSON 格式正确，也很可能 solver 碰撞或超出桌面。  
所以 user prompt 里动态加入 size warnings 和 “max 1-2 large objects”。

## 怎么把 prompt 写得更稳

如果后续要自己扩展 prompt，我建议保留这几个硬约束：

1. 永远让输出是 JSON only。
2. 永远给可用 object catalog 子集，不要让模型自由编对象名。
3. 永远把 coordinate frame 写清楚，尤其 left/right/front/back。
4. 永远把 dependency order 写清楚：anchor -> in/on -> cluster -> loose。
5. 永远把 table size 和 large object warning 写进去。
6. 对不同 target count 使用不同策略块：sparse、medium、dense。
7. 失败反馈要具体指出是 grammar、solver、physics 还是 intersection failure。

## 小结

这几段 prompt 的核心不是“说服 LLM 生成好看的文字”，而是把 LLM 变成 scene planner：

```text
主题 + 对象目录 + 桌面容量
-> 选择对象
-> 组织成容器/支撑/聚类关系
-> 输出 typed predicate JSON
-> solver/physics/feedback 接管
```

Prompt 写成这样，是为了让生成结果既有真实桌面结构，又能被程序稳定解析、求解和修复。
