# 精讲 3：扩展任务生成、验证和自动修复，代码怎么实现

> [!NOTE]
> **颜色标识**：绿色表示核心结论，蓝色表示源码/输入输出路径，橙色表示边界、风险和容易误解的点。

## 先说结论

论文这段讲的是 **TaskGen 的闭环**：

```text
给 LLM 足够上下文
  -> LLM 生成 RoboLab Task Python 代码
  -> 检查 Python 语法
  -> 检查对象/场景/容器/物理可行性
  -> 失败时把原始提示、无效输出、错误信息打包成修复提示
  -> 让 LLM 重写，再重复验证
```

> [!TIP]
> **核心结论**：TaskGen 不是“让 LLM 一次写完就相信它”，而是“生成代码 -> 自动验证 -> 把错误反馈回 LLM -> 重写”，直到语法、资产和物理可行性都过关。

当前 RoboLab checkout 里，这个流程不是一个单独的 `run_taskgen.py` 大脚本，而是分散在几类文件里：

| 功能 | 当前实现位置 | 说明 |
|---|---|---|
| LLM 任务生成提示/模板 | `skills/robolab-taskgen/SKILL.md` | 定义让 LLM 生成什么、问用户什么、输出什么 |
| 任务示例 | `skills/robolab-taskgen/references/examples.md` | 简单 pick/place、多物体排序、有序堆叠 |
| 谓词库说明 | `skills/robolab-taskgen/references/conditionals.md` + `robolab/core/task/conditionals.py` | 成功条件、终止条件、subtask 条件 |
| Python 语法/导入验证 | `compile(...)`、`robolab/core/task/task_utils.py::load_task_from_file` | 检查代码能不能作为 Task 类加载 |
| metadata/难度统计 | `robolab/tasks/_utils/generate_task_metadata.py` + `load_task_info.py` | 生成 `task_metadata.json`、CSV、README |
| 场景资源验证 | `robolab/core/scenes/utils.py::scrape_scene/import_scene` | 检查 USD 场景里有哪些对象 |
| 场景/物理反馈 | `robolab/scene_gen/llm_scene_gen/feedback_system.py` | 给 LLM 返回碰撞、越界、不稳定等反馈 |
| 仿真 smoke | `examples/run_empty.py --task <TaskClassName>` | 真的启动 Isaac，检查注册和运行是否通 |

> [!NOTE]
> **源码入口**：TaskGen 先看 `skills/robolab-taskgen/SKILL.md`、`references/examples.md`、`references/conditionals.md`；验证链路再看 `task_utils.py::load_task_from_file`、`core/scenes/utils.py::scrape_scene/import_scene` 和 `scene_gen/.../feedback_system.py`。

说人话：**LLM 负责编代码，RoboLab 负责把代码变成可运行 Task；验证层负责告诉 LLM 哪个对象不存在、哪个容器装不下、哪个谓词写错了。**

## 1. LLM 输入：TaskGen 给模型什么信息

论文说给 LLM 五类上下文，当前代码/skill 对应如下：

| 论文里的输入 | 当前对应来源 | 用途 |
|---|---|---|
| 场景对象目录和尺寸元数据 | `assets/objects/object_catalog.json`、`assets/scenes/_metadata/scene_metadata.json`、`scrape_scene()` | 知道对象名、尺寸、USD 路径、物理属性 |
| 任务结构示例 | `skills/robolab-taskgen/references/examples.md`、`robolab/tasks/benchmark/*.py` | 让 LLM 模仿 Task 文件格式 |
| 子任务成功/终止谓词库 | `references/conditionals.md`、`conditionals.py` | 把自然语言目标映射成 `object_in_container` 等函数 |
| 能力轴语言模板 | taskgen skill 的 instruction variants、attributes | 生成 default/vague/specific 和 `color/spatial/sorting/stacking` 标签 |
| 难度和物理可行性约束 | `episode_length_s` 规则、`compute_difficulty_score`、容器/堆叠尺寸检查 | 避免生成不可能完成或不可评估的任务 |

`skills/robolab-taskgen/SKILL.md` 对任务文件的定义很明确：

> 一个 task 是 Python 文件，里面有 `Task` dataclass，把 USD 场景绑定到语言指令和 termination criteria。

它给 LLM 的模板核心是：

```python
@configclass
class <TaskName>Terminations:
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    success = DoneTerm(
        func=<conditional_function>,
        params={<params_dict>},
    )

@dataclass
class <TaskName>Task(Task):
    contact_object_list = [<all_object_names>]
    scene = import_scene("<scene_file>.usda", contact_object_list)
    terminations = <TaskName>Terminations
    instruction = {
        "default": "<clear instruction>",
        "vague": "<ambiguous instruction>",
        "specific": "<detailed instruction>",
    }
    episode_length_s: int = <seconds>
    attributes = [<attribute_tags>]
    subtasks = [<optional_subtasks>]
```

## 2. 生成：从能力轴和语言模板到 Task 代码

自然语言目标首先被路由到一个谓词函数：

| 任务描述 | termination 函数 | subtask 写法 |
|---|---|---|
| “Put X in Y” | `object_in_container` | `pick_and_place` |
| “Put X on Y” | `object_on_top` | `pick_and_place_on_surface` |
| “Move X left/right of Y” | `object_left_of` / `object_right_of` | `Subtask(partial(...))` |
| “Sort X into bins” | `object_groups_in_containers` | 多个 `pick_and_place` |
| “Stack X, Y, Z” | `stacked` | 多个 `Subtask(partial(stacked, ...))` |
| “Take X out of Y” | `object_outside_of` | `Subtask(partial(...))` |
| “Stand X upright” | `object_upright` | `Subtask(partial(...))` |

### 示例：生成一个颜色分类任务

输入信息可以组织成这样：

```json
{
  "scene": "rubiks_cube_banana_bowl_mug_bin.usda",
  "objects": ["mug", "bowl", "grey_bin", "banana", "rubiks_cube", "table"],
  "axis": ["visual.color", "relational.sorting"],
  "instruction_template": "Put all the {color} things in the {container}",
  "slots": {
    "color": "red",
    "container": "grey_bin",
    "target_objects": ["mug", "bowl"]
  },
  "difficulty": "moderate",
  "constraints": {
    "all_target_objects_must_fit_container": true,
    "require_gripper_detached": true
  }
}
```

LLM 应输出类似：

```python
@configclass
class RedItemsInBinTerminations:
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    success = DoneTerm(
        func=object_in_container,
        params={
            "object": ["mug", "bowl"],
            "container": "grey_bin",
            "logical": "all",
            "require_gripper_detached": True,
        },
    )

@dataclass
class RedItemsInBinTask(Task):
    contact_object_list = ["mug", "bowl", "grey_bin", "table", "banana", "rubiks_cube"]
    scene = import_scene("rubiks_cube_banana_bowl_mug_bin.usda", contact_object_list)
    terminations = RedItemsInBinTerminations
    instruction = {
        "default": "Put all the red things in the grey bin",
        "vague": "Sort items by color",
        "specific": "Identify every red-colored object on the table and place each one into the grey bin",
    }
    episode_length_s: int = 60
    attributes = ["color", "sorting"]
    subtasks = [
        pick_and_place(object=["mug", "bowl"], container="grey_bin", logical="all", score=1.0)
    ]
```

这个生成结果对应我们已经跑过的 `RedItemsInBinTask`。它在复杂任务实测里失败，失败原因不是 Task 代码无效，而是策略没有在 900 步内完成所有红色物体入盒。

## 3. 语法验证：先保证 Python 文件能被加载

最低成本验证是 Python 编译：

```python
compile(generated_code, "generated_task.py", "exec")
```

它能抓：

- 括号没闭合；
- 缩进错误；
- 字符串引号错误；
- 非法 Python 语法。

更接近 RoboLab 的验证是加载 Task 类：

```python
from robolab.core.task.task_utils import load_task_from_file

task_class = load_task_from_file("generated_task.py", allow_multiple=False)
```

`load_task_from_file()` 会：

1. 用 `importlib.util.spec_from_file_location` 导入 Python 文件。
2. 扫描模块里所有类。
3. 找到 `issubclass(attr, Task)` 且不是基类 `Task` 的类。
4. 没找到就报 `No Task subclass found`。

所以它不只是语法检查，还能发现：

- 没写 `Task` 子类；
- class 名写错；
- import 错；
- `@dataclass` 中可变默认值写法导致导入失败。

## 4. 资源验证：对象是否存在、是否禁用、容器是否装得下

论文里说的资源验证包含两类：

1. **对象引用验证**：任务代码里引用的对象必须存在于场景对象集合中，也不能落入禁用集合。
2. **物理可行性验证**：例如容器任务里，内部对象要能放进容器，并留出 margin。

当前 RoboLab 提供了 `scrape_scene()` / `import_scene()` 从 USD 场景中提取对象：

```python
from robolab.core.scenes.utils import scrape_scene

scene_info = scrape_scene("assets/scenes/rubiks_cube_banana_bowl_mug_bin.usda")
available_objects = set(scene_info["dynamic_bodies"] + scene_info["kinematic_bodies"] + scene_info["static_bodies"])
```

`import_scene(scene_path, objects_of_interest)` 会只把 `objects_of_interest` 里的对象转成 `RigidObjectCfg` / `AssetBaseCfg`。如果对象名不在场景里，后面创建 contact sensor 或 env 时就会失败。

论文提到的“禁用集合”和“容器尺寸 margin”在当前 checkout 里没有看到一个统一的公开 `TaskValidator` 类；实际工程上可以在 LLM 输出落盘前补一个轻量验证层：

> [!WARNING]
> **注意边界**：当前公开 checkout 里 TaskGen 验证能力是分散的，不是一个完整公开的 `TaskValidator` 大类。轻量测试能提前拦截明显错误，但不能替代 Isaac Sim 里的真实注册、接触传感器和物理 smoke。

```python
def validate_objects(task_objects, scene_objects, disabled_objects):
    errors = []
    missing = sorted(set(task_objects) - set(scene_objects))
    disabled = sorted(set(task_objects) & set(disabled_objects))
    if missing:
        errors.append(f"Objects not found in scene: {missing}")
    if disabled:
        errors.append(f"Objects are disabled for task generation: {disabled}")
    return errors

def validate_container_fit(objects, container, dims, margin=0.02):
    errors = []
    cx, cy, cz = dims[container]
    usable_x = cx - 2 * margin
    usable_y = cy - 2 * margin
    for obj in objects:
        ox, oy, oz = dims[obj]
        # 保守检查：允许物体旋转，取较短边对较短边、较长边对较长边。
        obj_short, obj_long = sorted([ox, oy])
        box_short, box_long = sorted([usable_x, usable_y])
        if obj_short > box_short or obj_long > box_long:
            errors.append(
                f"{obj} ({ox:.2f}x{oy:.2f}) does not fit into {container} "
                f"usable opening ({usable_x:.2f}x{usable_y:.2f}) with margin={margin}"
            )
    return errors
```

这个检查不替代 Isaac Sim 物理验证，但可以提前拦掉明显不可能的任务。

## 5. 修复提示：把错误反馈给 LLM

论文里的修复提示可以写成：

```text
Original prompt Q:
<原始任务生成请求>

Invalid output:
<LLM 上一次生成的 Python 代码>

Validation errors E:
1. SyntaxError: '(' was never closed
2. Objects not found in scene: ['apple']
3. mug does not fit into small_box with margin=0.02

Please revise the RoboLab task. Requirements:
- Keep the same scene unless the error says the scene is invalid.
- Use only objects that exist in the scene and are not disabled.
- For container tasks, choose target objects that physically fit.
- Return one complete Python task file only.
```

这个循环和 `scene_gen` 里的 `FeedbackSystem` 思路一致：失败时不要只说“不行”，要告诉 LLM 具体哪个谓词、哪个对象、哪个尺寸或哪段语法错了。

## 6. 完整闭环伪代码

```python
def taskgen_loop(prompt, scene_objects, object_dims, disabled_objects, max_rounds=3):
    q = build_initial_prompt(
        prompt=prompt,
        scene_objects=scene_objects,
        object_dims=object_dims,
        examples=TASK_EXAMPLES,
        conditionals=CONDITIONAL_LIBRARY,
        axis_templates=CAPABILITY_AXIS_TEMPLATES,
        constraints=PHYSICAL_CONSTRAINTS,
    )

    last_output = None
    last_errors = []

    for round_idx in range(max_rounds):
        generated_code = llm(q)
        errors = []

        errors += validate_python_syntax(generated_code)
        if not errors:
            spec = extract_task_spec(generated_code)
            errors += validate_objects(
                task_objects=spec.contact_object_list,
                scene_objects=scene_objects,
                disabled_objects=disabled_objects,
            )
            errors += validate_conditionals(spec)
            errors += validate_container_fit_from_spec(spec, object_dims)

        if not errors:
            return generated_code

        last_output = generated_code
        last_errors = errors
        q = build_repair_prompt(
            original_prompt=prompt,
            invalid_output=last_output,
            errors=last_errors,
        )

    raise RuntimeError(f"Task generation failed after {max_rounds} rounds: {last_errors}")
```

## 7. 和 RoboLab 当前代码逐步对应

| 论文步骤 | 当前代码/可补验证 |
|---|---|
| 生成任务代码 | `skills/robolab-taskgen/SKILL.md` 的模板 + examples + conditionals |
| 验证代码语法 | `compile(...)`，以及 `task_utils.load_task_from_file()` |
| 验证场景资源选择 | `scrape_scene()` / `import_scene()` + `contact_object_list` 对比 |
| 验证容器尺寸 | 可基于 `object_catalog.json` / scene metadata 的 `dims` 增加 margin 检查 |
| 生成任务 metadata | `generate_task_metadata.py`、`load_task_info.py` |
| 仿真 smoke | `examples/run_empty.py --task <TaskClassName>` |
| 失败反馈修复 | `FeedbackSystem` 思路 + repair prompt |

## 8. 额外测试用例设计

下面这些测试不需要启动 Isaac Sim，适合放在 notebook 里快速跑，用来验证 TaskGen 生成前后的“轻量 gate”：

| 测试 | 输入 | 期望 |
|---|---|---|
| `test_valid_spec_passes` | banana、bowl、table 都在 scene，banana 能放进 bowl | 0 个错误 |
| `test_syntax_error_fails` | 少一个右括号的 Python 代码 | 返回 `SyntaxError` |
| `test_missing_object_fails` | task 引用 `apple`，scene 没有 apple | 返回 missing object |
| `test_disabled_object_fails` | task 引用 `knife`，禁用集合含 knife | 返回 disabled object |
| `test_container_too_small_fails` | `large_box` 放进 `small_bowl` | 返回 does not fit |
| `test_repair_prompt_contains_context` | Q、无效代码、错误 E | 修复提示包含三者 |

这些测试验证的是 TaskGen 的前置质量门，不是最终机器人策略成功率。真正要证明任务可运行，还要跑 `examples/run_empty.py --task <TaskClassName>`。
