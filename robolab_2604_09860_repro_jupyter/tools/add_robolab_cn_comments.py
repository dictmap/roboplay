#!/usr/bin/env python3
"""Add Chinese learning comments to RoboLab core source files.

This script intentionally inserts line comments only. It does not change
functions, signatures, imports, control flow, or runtime string constants.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, rel: str) -> str:
    if old not in text:
        raise RuntimeError(f"missing context in {rel}: {old[:120]!r}")
    return text.replace(old, new, 1)


def apply_replacements(root: Path, replacements: dict[str, list[tuple[str, str]]]) -> list[str]:
    changed: list[str] = []
    for rel, items in replacements.items():
        path = root / rel
        text = path.read_text(encoding="utf-8")
        new_text = text
        for old, new in items:
            new_text = replace_once(new_text, old, new, rel)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed.append(rel)
    return changed


REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "robolab/constants.py": [
        (
            "import os\nfrom datetime import datetime\n\n# Get the robolab package root directory (repo root)\n",
            "import os\nfrom datetime import datetime\n\n# 中文阅读提示：constants.py 是全局路径、输出目录、调试开关和 benchmark 分类的集中配置。\n# Get the robolab package root directory (repo root)\n",
        ),
        (
            "# Get the robolab package root directory (repo root)\nPACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # robolab (repo root)\n",
            "# 中文阅读提示：PACKAGE_DIR 指向仓库根目录，资产、输出和任务扫描都会基于它拼绝对路径。\n# Get the robolab package root directory (repo root)\nPACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # robolab (repo root)\n",
        ),
        (
            "# Get children of package directory\nDEFAULT_OUTPUT_DIR = os.path.join(PACKAGE_DIR, \"output\")\n",
            "# 中文阅读提示：这些目录约定连接了源码、USD 资产、机器人模型和实验输出，是复现路径排错第一入口。\n# Get children of package directory\nDEFAULT_OUTPUT_DIR = os.path.join(PACKAGE_DIR, \"output\")\n",
        ),
        (
            "# Get children of source directory\nTASK_DIR = os.path.join(SOURCE_DIR, \"tasks\")\n",
            "# 中文阅读提示：TASK_DIR 和 DEFAULT_TASK_SUBFOLDERS 决定自动注册时默认扫描哪些 benchmark 任务。\n# Get children of source directory\nTASK_DIR = os.path.join(SOURCE_DIR, \"tasks\")\n",
        ),
        (
            "def resolve_catalog_path(relative_path: str) -> str:\n    \"\"\"\n",
            "def resolve_catalog_path(relative_path: str) -> str:\n    # 中文阅读提示：object_catalog.json 里的路径通常是相对仓库根目录，这里统一转成绝对路径。\n    \"\"\"\n",
        ),
        (
            "# Output directory\n_output_dir = None\n",
            "# 中文阅读提示：_output_dir 是当前任务的动态输出目录，runner 会在每个 task 前调用 set_output_dir。\n# Output directory\n_output_dir = None\n",
        ),
        (
            "def set_output_dir(path: str):\n    \"\"\"Set the global output directory.\"\"\"\n",
            "def set_output_dir(path: str):\n    \"\"\"Set the global output directory.\"\"\"\n    # 中文阅读提示：所有 recorder、视频、env_cfg 和日志都会写到这个目录下。\n",
        ),
        (
            "DEBUG = False\nVERBOSE = False\n",
            "# 中文阅读提示：这些全局开关由各 policy/run.py 的命令行参数设置，控制日志、可视化和记录粒度。\nDEBUG = False\nVERBOSE = False\n",
        ),
        (
            "# Difficulty scoring constants (authoritative source for compute_difficulty_score in subtask_utils.py)\nSKILL_WEIGHTS: dict[str, int] = {\n",
            "# 中文阅读提示：难度分数把任务属性映射为 simple/moderate/complex，论文结果可按难度分组比较。\n# Difficulty scoring constants (authoritative source for compute_difficulty_score in subtask_utils.py)\nSKILL_WEIGHTS: dict[str, int] = {\n",
        ),
        (
            "# Task category remap: maps fine-grained attributes to higher-level categories\nBENCHMARK_TASK_CATEGORIES = {\n",
            "# 中文阅读提示：这里把细粒度属性归并到 visual/relational/procedural 三条能力轴。\n# Task category remap: maps fine-grained attributes to higher-level categories\nBENCHMARK_TASK_CATEGORIES = {\n",
        ),
    ],
    "robolab/core/environments/base.py": [
        (
            "@configclass\nclass BaseRecorderManagerCfg(RecorderManagerBaseCfg):\n",
            "@configclass\nclass BaseRecorderManagerCfg(RecorderManagerBaseCfg):\n    # 中文阅读提示：这里定义默认记录项，决定 HDF5 里会保存初始状态、动作、bbox、末端位姿等证据。\n",
        ),
        (
            "def create_recorder_config(\n    include_policy_observations: bool = False,\n",
            "def create_recorder_config(\n    # 中文阅读提示：runner 通过全局开关决定是否额外记录策略图像观测和 subtask 进度。\n    include_policy_observations: bool = False,\n",
        ),
        (
            "class RobolabDefaultEnvCfg(ManagerBasedRLEnvCfg):\n    observations = None\n",
            "class RobolabDefaultEnvCfg(ManagerBasedRLEnvCfg):\n    # 中文阅读提示：所有自动生成的任务 EnvCfg 都继承这个默认配置，再填入任务专属 scene/termination。\n    observations = None\n",
        ),
        (
            "        if self.recorders is None:\n            # Determine recorder configuration based on flags\n",
            "        if self.recorders is None:\n            # 中文阅读提示：recorders 延迟到 __post_init__ 创建，这样命令行开关已经写入 robolab.constants。\n            # Determine recorder configuration based on flags\n",
        ),
        (
            "        self.viewer.cam_prim_path = \"/OmniverseKit_Persp\"\n        self.viewer.eye = (1.5, 0.0, 1.0)\n",
            "        # 中文阅读提示：下面是默认视角和仿真频率；论文复现里视频和步长都受这些参数影响。\n        self.viewer.cam_prim_path = \"/OmniverseKit_Persp\"\n        self.viewer.eye = (1.5, 0.0, 1.0)\n",
        ),
        (
            "        # PhysX settings\n        self.sim.physx.gpu_temp_buffer_capacity = 2**30\n",
            "        # 中文阅读提示：PhysX GPU 缓冲区和迭代次数直接影响 4090 上的稳定性、显存和接触质量。\n        # PhysX settings\n        self.sim.physx.gpu_temp_buffer_capacity = 2**30\n",
        ),
    ],
    "robolab/core/environments/config.py": [
        (
            "def generate_scene_env_cfg(task_class: Task,\n                          robot_cfg,\n",
            "def generate_scene_env_cfg(task_class: Task,\n                          # 中文阅读提示：把任务 scene、机器人、相机、灯光、背景 mixin 合成一个 Isaac Lab SceneCfg。\n                          robot_cfg,\n",
        ),
        (
            "    bases = [task_class.scene, robot_cfg, InteractiveSceneCfg]\n\n    # Add optionals only if not None\n",
            "    # 中文阅读提示：type 动态继承的顺序决定 dataclass 字段顺序，机器人/相机 spawn 顺序也会受影响。\n    bases = [task_class.scene, robot_cfg, InteractiveSceneCfg]\n\n    # Add optionals only if not None\n",
        ),
        (
            "    from robolab.core.task.subtask_utils import compute_difficulty_score, count_subtasks\n    attributes = getattr(task_class, \"attributes\", []) or []\n",
            "    # 中文阅读提示：根据属性和 subtask 数量自动补 difficulty label，后续结果表可按难度聚合。\n    from robolab.core.task.subtask_utils import compute_difficulty_score, count_subtasks\n    attributes = getattr(task_class, \"attributes\", []) or []\n",
        ),
        (
            "        def __post_init__(self):\n            super().__post_init__()  # Set all defaults first\n",
            "        def __post_init__(self):\n            # 中文阅读提示：先跑默认配置，再覆盖任务 episode 长度、控制频率、scene 和 termination。\n            super().__post_init__()  # Set all defaults first\n",
        ),
        (
            "            # Set task-specific configs\n            self.scene = scene_env_cfg(num_envs=num_envs, env_spacing=env_spacing)\n",
            "            # 中文阅读提示：这里把 Task 类声明的 scene/instruction/termination/contact list 写入实际 EnvCfg。\n            # Set task-specific configs\n            self.scene = scene_env_cfg(num_envs=num_envs, env_spacing=env_spacing)\n",
        ),
        (
            "            # Must specify this after the scene is set.\n            create_contact_sensors(self)\n",
            "            # 中文阅读提示：接触传感器依赖 scene/contact_object_list，必须在 scene 设置完成后创建。\n            # Must specify this after the scene is set.\n            create_contact_sensors(self)\n",
        ),
        (
            "    # Load the task class from the file\n    task_class = load_task_from_file(task_file_path)\n",
            "    # 中文阅读提示：自动注册的第一步是从任务 py 文件里加载唯一的 Task 子类。\n    # Load the task class from the file\n    task_class = load_task_from_file(task_file_path)\n",
        ),
        (
            "def register_generated_env(task_env_cfg: RobolabDefaultEnvCfg, env_name: str = None):\n    \"\"\"\n",
            "def register_generated_env(task_env_cfg: RobolabDefaultEnvCfg, env_name: str = None):\n    # 中文阅读提示：把生成的 EnvCfg 注册成 Gymnasium ID，create_env 后续用这个 ID 创建环境。\n    \"\"\"\n",
        ),
    ],
    "robolab/core/environments/factory.py": [
        (
            "_RESOLVABLE_CFG_KEYS = {\n    \"background_cfg\", \"camera_cfg\", \"lighting_cfg\",\n",
            "# 中文阅读提示：这些 cfg 可以是类，也可以是工厂函数；背景随机化就是靠每个 task 调一次工厂实现。\n_RESOLVABLE_CFG_KEYS = {\n    \"background_cfg\", \"camera_cfg\", \"lighting_cfg\",\n",
        ),
        (
            "def _resolve_per_task_kwargs(env_kwargs: dict) -> dict:\n    \"\"\"Invoke per-task cfg factories; pass classes/instances/scalars through unchanged.\"\"\"\n",
            "def _resolve_per_task_kwargs(env_kwargs: dict) -> dict:\n    \"\"\"Invoke per-task cfg factories; pass classes/instances/scalars through unchanged.\"\"\"\n    # 中文阅读提示：只对可解析 cfg 调用工厂，普通数值参数例如 dt/seed 保持原样。\n",
        ),
        (
            "        self.task_dir = Path(task_dir)\n\n        # Structured environment storage\n",
            "        self.task_dir = Path(task_dir)\n\n        # 中文阅读提示：factory 维护 env_name -> task/config/tags 的索引，get_envs 按这个索引筛选任务。\n        # Structured environment storage\n",
        ),
        (
            "        env_kwargs = _resolve_per_task_kwargs(env_kwargs)\n        task_file_path, task_name = resolve_task_path(task, self.task_dir)\n",
            "        # 中文阅读提示：每个任务单独解析 cfg kwargs，保证随机背景/相机变体按任务固定下来。\n        env_kwargs = _resolve_per_task_kwargs(env_kwargs)\n        task_file_path, task_name = resolve_task_path(task, self.task_dir)\n",
        ),
        (
            "        # Attributes will be automatically added to tags\n        if hasattr(env_cfg_class, \"_task_attributes\") and env_cfg_class._task_attributes is not None:\n",
            "        # 中文阅读提示：任务 attributes 自动成为 tags，所以可以用 --tag visual/spatial/simple 等筛选。\n        # Attributes will be automatically added to tags\n        if hasattr(env_cfg_class, \"_task_attributes\") and env_cfg_class._task_attributes is not None:\n",
        ),
        (
            "        generated_envs = {}\n\n        # If task_subdirs is provided, build a mapping of task names to file paths\n",
            "        generated_envs = {}\n\n        # 中文阅读提示：批量创建用于 RoboLab-120；单任务调试时建议传 tasks 限制范围。\n        # If task_subdirs is provided, build a mapping of task names to file paths\n",
        ),
    ],
    "robolab/registrations/droid/auto_env_registrations_jointpos.py": [
        (
            "from robolab.constants import DEFAULT_TASK_SUBFOLDERS, TASK_DIR\n\n\"\"\"\nScene registration:\n",
            "from robolab.constants import DEFAULT_TASK_SUBFOLDERS, TASK_DIR\n\n# 中文阅读提示：这个文件把 DROID 机器人、joint position action、相机观测和 benchmark 任务批量注册成 Gym env。\n\"\"\"\nScene registration:\n",
        ),
        (
            "    if cameras is None:\n        cameras = WRIST_LEFT\n",
            "    # 中文阅读提示：默认只给策略腕部左相机；如果模型需要多视角，要从 camera_presets 传入更多相机。\n    if cameras is None:\n        cameras = WRIST_LEFT\n",
        ),
        (
            "    ImageObsCfg = generate_image_obs_from_cameras(cameras)\n    ViewportCameraCfg = generate_image_obs_from_cameras([EgocentricMirroredCameraCfg])\n",
            "    # 中文阅读提示：policy image_obs 和 viewport_cam 分开，前者给模型，后者主要用于视频记录/人眼查看。\n    ImageObsCfg = generate_image_obs_from_cameras(cameras)\n    ViewportCameraCfg = generate_image_obs_from_cameras([EgocentricMirroredCameraCfg])\n",
        ),
        (
            "    # WristCameraCfg is robot-mounted (wrist_cam is already attached via DroidCfg).\n    # Including it as a scene mixin puts wrist_cam before robot in dataclass field\n",
            "    # 中文阅读提示：腕部相机跟随 robot 配置生成，不能再作为 scene mixin 提前 spawn。\n    # WristCameraCfg is robot-mounted (wrist_cam is already attached via DroidCfg).\n    # Including it as a scene mixin puts wrist_cam before robot in dataclass field\n",
        ),
        (
            "        rng = random.Random(background_seed)\n        all_bgs = find_background_files()\n",
            "        # 中文阅读提示：背景随机化在注册时抽样；每个 env 的背景固定写入 env_cfg，便于复现实验对照。\n        rng = random.Random(background_seed)\n        all_bgs = find_background_files()\n",
        ),
        (
            "    auto_discover_and_create_cfgs(\n        task_dir=TASK_DIR,\n",
            "    # 中文阅读提示：最终把任务扫描、EnvCfg 生成和 Gym 注册串起来，runner 的 get_envs 就从这里拿任务。\n    auto_discover_and_create_cfgs(\n        task_dir=TASK_DIR,\n",
        ),
    ],
    "robolab/core/world/world_state.py": [
        (
            "# Global factory instance for easy access\n_global_world = None\n",
            "# 中文阅读提示：WorldState 是仿真查询统一入口，谓词函数都通过它读物体、机器人、几何和接触状态。\n# Global factory instance for easy access\n_global_world = None\n",
        ),
        (
            "    if _global_world is None or _global_world.env != env:\n        _global_world = WorldState(env)\n",
            "    # 中文阅读提示：同一个 env 复用 WorldState 缓存；换 env 时重建，避免跨场景状态污染。\n    if _global_world is None or _global_world.env != env:\n        _global_world = WorldState(env)\n",
        ),
        (
            "        self._local_geometry_cache: dict[str, dict] = {}\n        # Stateful predicate storage. Outer key identifies the predicate +\n",
            "        # 中文阅读提示：局部几何缓存只存静态形状信息，减少每步重复从 USD 计算 bbox。\n        self._local_geometry_cache: dict[str, dict] = {}\n        # Stateful predicate storage. Outer key identifies the predicate +\n",
        ),
        (
            "            self.env = env\n            self._local_geometry_cache.clear()\n",
            "            self.env = env\n            # 中文阅读提示：切换 env 时清空几何缓存和有状态谓词，保证新任务从干净状态开始。\n            self._local_geometry_cache.clear()\n",
        ),
        (
            "        entities = {}\n        entities.update(self.objects)\n",
            "        # 中文阅读提示：把刚体、关节体、变形体和 extras 合并成一个名字空间，方便谓词按名字查找。\n        entities = {}\n        entities.update(self.objects)\n",
        ),
        (
            "        if body_name in self._local_geometry_cache:\n            return self._local_geometry_cache[body_name]\n",
            "        # 中文阅读提示：同一物体的本地 bbox 在 episode 内不变，命中缓存后无需再访问 USD prim。\n        if body_name in self._local_geometry_cache:\n            return self._local_geometry_cache[body_name]\n",
        ),
        (
            "    def get_or_init_predicate_state(self, key: str, factory: Callable[[], dict]) -> dict:\n        \"\"\"Return the storage bag for a stateful predicate, allocating it on first call.\"\"\"\n",
            "    def get_or_init_predicate_state(self, key: str, factory: Callable[[], dict]) -> dict:\n        \"\"\"Return the storage bag for a stateful predicate, allocating it on first call.\"\"\"\n        # 中文阅读提示：顺序放置等谓词需要跨 step 记忆，状态按 key 懒创建。\n",
        ),
        (
            "        if not self._predicate_state:\n            return\n",
            "        # 中文阅读提示：只有真正 reset 的 env 会清状态；冻结终止的 env 保留最终判定证据。\n        if not self._predicate_state:\n            return\n",
        ),
    ],
    "examples/run_empty.py": [
        (
            "import argparse\nimport cv2 # Must import this before isaaclab. Do not remove\n",
            "import argparse\n# 中文阅读提示：Isaac Lab 依赖 OpenCV 的动态库加载顺序，cv2 必须在 isaaclab 前导入。\nimport cv2 # Must import this before isaaclab. Do not remove\n",
        ),
        (
            "# add argparse arguments\nparser = argparse.ArgumentParser(description=\"\")\n",
            "# 中文阅读提示：这个脚本是“无策略 smoke test”，只验证任务能创建、step、记录和汇总。\n# add argparse arguments\nparser = argparse.ArgumentParser(description=\"\")\n",
        ),
        (
            "# parse the arguments\nargs_cli, _= parser.parse_known_args()\n",
            "# 中文阅读提示：先解析命令行，再启动 Isaac Sim；后面的 robolab/isaaclab 导入依赖 app 已经起来。\n# parse the arguments\nargs_cli, _= parser.parse_known_args()\n",
        ),
        (
            "# Run automatic factory generation before main\nauto_register_droid_envs()\n",
            "# 中文阅读提示：自动扫描并注册 DROID/JointPos 任务，否则 get_envs 找不到 benchmark env。\n# Run automatic factory generation before main\nauto_register_droid_envs()\n",
        ),
        (
            "def main():\n    \"\"\"Main function.\"\"\"\n    num_episodes = 1\n",
            "def main():\n    \"\"\"Main function.\"\"\"\n    # 中文阅读提示：每个任务只跑 1 个 episode，用来快速暴露环境配置/资产/记录链路问题。\n    num_episodes = 1\n",
        ),
        (
            "    if args_cli.task:\n        task_envs = get_envs(task=args_cli.task)\n",
            "    # 中文阅读提示：任务选择优先级为 --task、--tag、全部；复现时建议先指定单任务降低调试成本。\n    if args_cli.task:\n        task_envs = get_envs(task=args_cli.task)\n",
        ),
        (
            "    episode_results_file, episode_results = init_experiment(output_dir)\n\n    for task_env in task_envs:\n",
            "    # 中文阅读提示：episode_results.jsonl 是本轮实验的事实表，后续成功率统计都从这里读。\n    episode_results_file, episode_results = init_experiment(output_dir)\n\n    for task_env in task_envs:\n",
        ),
        (
            "        env, env_cfg = create_env(task_env,\n            device=args_cli.device,\n",
            "        # 中文阅读提示：create_env 会新建 USD stage、解析任务配置、写 env_cfg.json，并返回 Isaac Lab env。\n        env, env_cfg = create_env(task_env,\n            device=args_cli.device,\n",
        ),
        (
            "            succ, msgs = run_empty_episode(env,\n                env_cfg=env_cfg,\n",
            "            # 中文阅读提示：这里不调用 VLA/策略，只用空动作推进仿真，验证 termination/recorder 是否工作。\n            succ, msgs = run_empty_episode(env,\n                env_cfg=env_cfg,\n",
        ),
        (
            "            # Pull events before end_episode (which may reset the env)\n            per_env_events = get_all_env_events(env) or []\n",
            "            # 中文阅读提示：end_episode 可能清理 recorder，所以必须先取出每个 env 的事件日志。\n            # Pull events before end_episode (which may reset the env)\n            per_env_events = get_all_env_events(env) or []\n",
        ),
        (
            "            # Write v2 per-env event logs\n            for eid in range(args_cli.num_envs):\n",
            "            # 中文阅读提示：多并行环境时，每个 env 单独写 log_<run>_env<id>.json，方便定位失败轨迹。\n            # Write v2 per-env event logs\n            for eid in range(args_cli.num_envs):\n",
        ),
        (
            "            # Update run results\n            if robolab.constants.ENABLE_SUBTASK_PROGRESS_CHECKING:\n",
            "            # 中文阅读提示：开启 subtask 后，结果里会额外记录分数和失败原因；论文分析会用这些字段解释失败类型。\n            # Update run results\n            if robolab.constants.ENABLE_SUBTASK_PROGRESS_CHECKING:\n",
        ),
    ],
    "policies/pi0_family/run.py": [
        (
            "import cv2  # noqa: F401 -- must import this before isaaclab. Do not remove\nfrom isaaclab.app import AppLauncher\n",
            "# 中文阅读提示：cv2 导入顺序是 Isaac/Omniverse 环境的稳定性要求，不要移动到 AppLauncher 后面。\nimport cv2  # noqa: F401 -- must import this before isaaclab. Do not remove\nfrom isaaclab.app import AppLauncher\n",
        ),
        (
            "PI0_VARIANTS = [\"pi0\", \"pi0_fast\", \"pi05\", \"paligemma\", \"paligemma_fast\"]\n\nparser = argparse.ArgumentParser(description=\"Evaluate a Pi0-family policy backend.\")\n",
            "# 中文阅读提示：这一组名字对应 OpenPI 服务端加载的 checkpoint/config，RoboLab 侧只负责选择客户端默认参数。\nPI0_VARIANTS = [\"pi0\", \"pi0_fast\", \"pi05\", \"paligemma\", \"paligemma_fast\"]\n\n# 中文阅读提示：本文件是 Pi0/OpenPI 评测入口，真正的环境循环在 robolab.eval.runner.run_evaluation。\nparser = argparse.ArgumentParser(description=\"Evaluate a Pi0-family policy backend.\")\n",
        ),
        (
            "from robolab.eval.runner import add_common_eval_args, run_evaluation  # noqa: E402\n\nadd_common_eval_args(parser)\nAppLauncher.add_app_launcher_args(parser)\n",
            "from robolab.eval.runner import add_common_eval_args, run_evaluation  # noqa: E402\n\n# 中文阅读提示：先合并通用评测参数，再让 AppLauncher 注入 Isaac Sim 参数，例如 --headless/--device。\nadd_common_eval_args(parser)\nAppLauncher.add_app_launcher_args(parser)\n",
        ),
        (
            "args_cli, _ = parser.parse_known_args()\nargs_cli.enable_cameras = True\n\napp_launcher = AppLauncher(args_cli)\n",
            "args_cli, _ = parser.parse_known_args()\nargs_cli.enable_cameras = True\n\n# 中文阅读提示：Isaac Sim 必须在多数 isaaclab/robolab 模块导入前启动，否则插件和仿真上下文未初始化。\napp_launcher = AppLauncher(args_cli)\n",
        ),
        (
            "robolab.constants.ENABLE_SUBTASK_PROGRESS_CHECKING = args_cli.enable_subtask\nrobolab.constants.RECORD_IMAGE_DATA = args_cli.record_image_data\n",
            "# 中文阅读提示：这些全局开关控制记录粒度和调试输出，不改变策略推理本身。\nrobolab.constants.ENABLE_SUBTASK_PROGRESS_CHECKING = args_cli.enable_subtask\nrobolab.constants.RECORD_IMAGE_DATA = args_cli.record_image_data\n",
        ),
        (
            "auto_register_droid_envs(\n    task_dirs=args_cli.task_dirs,\n",
            "# 中文阅读提示：注册阶段会把任务类转换成 gym env；背景随机化也在这里绑定到每个任务配置。\nauto_register_droid_envs(\n    task_dirs=args_cli.task_dirs,\n",
        ),
        (
            "def make_client(args: argparse.Namespace) -> Pi0DroidJointposClient:\n    kwargs = dict(\n",
            "def make_client(args: argparse.Namespace) -> Pi0DroidJointposClient:\n    # 中文阅读提示：客户端连接已经在外部启动的 OpenPI websocket server，本进程不加载模型权重。\n    kwargs = dict(\n",
        ),
        (
            "def main() -> None:\n    run_evaluation(args_cli, policy=args_cli.policy, client_factory=make_client)\n",
            "def main() -> None:\n    # 中文阅读提示：policy 名称会写入输出目录和 env_cfg，便于之后区分 pi05/pi0_fast 等结果。\n    run_evaluation(args_cli, policy=args_cli.policy, client_factory=make_client)\n",
        ),
    ],
    "policies/pi0_family/client.py": [
        (
            "class Pi0DroidJointposClient(InferenceClient):\n    # Per-variant action horizons. One Pi0 server class serves multiple trained\n",
            "class Pi0DroidJointposClient(InferenceClient):\n    # 中文阅读提示：这个类是 RoboLab 和 OpenPI 服务端之间的适配层。\n    # 输入侧把 RoboLab observation 改成 OpenPI 训练时的 key；输出侧把 action chunk 改回 env action。\n    # Per-variant action horizons. One Pi0 server class serves multiple trained\n",
        ),
        (
            "        super().__init__()\n        if open_loop_horizon is None:\n",
            "        super().__init__()\n        # 中文阅读提示：open_loop_horizon 表示一次推理返回的动作块里连续执行多少步，必须接近训练配置。\n        if open_loop_horizon is None:\n",
        ),
        (
            "        print(f\"[{self.__class__.__name__}] Awaiting for server on {self._display} to be ready...\")\n        self.client = self._connect()\n",
            "        # 中文阅读提示：这里连接的是已在 4090 上启动的 OpenPI websocket 服务；模型不在 RoboLab 进程里加载。\n        print(f\"[{self.__class__.__name__}] Awaiting for server on {self._display} to be ready...\")\n        self.client = self._connect()\n",
        ),
        (
            "    def _connect(self):\n        if self._remote_uri is not None:\n",
            "    def _connect(self):\n        # 中文阅读提示：remote_uri 用于云端/反代 websocket；本机 4090 常用 host+port。\n        if self._remote_uri is not None:\n",
        ),
        (
            "                self.client = self._connect()\n                # Flush chunk cache so all envs re-request on next step\n",
            "                self.client = self._connect()\n                # 中文阅读提示：重连后旧动作块可能来自断线前的观测，必须清空缓存强制重新推理。\n                # Flush chunk cache so all envs re-request on next step\n",
        ),
        (
            "    def _extract_observation(self, raw_obs: dict, *, env_id: int = 0) -> dict:\n        right_image = raw_obs[\"image_obs\"][\"over_shoulder_left_camera\"][env_id].clone().detach().cpu().numpy()\n",
            "    def _extract_observation(self, raw_obs: dict, *, env_id: int = 0) -> dict:\n        # 中文阅读提示：RoboLab 的 tensor 在 GPU 上；发给 OpenPI 前转成 CPU numpy，并按 env_id 取单个并行环境。\n        right_image = raw_obs[\"image_obs\"][\"over_shoulder_left_camera\"][env_id].clone().detach().cpu().numpy()\n",
        ),
        (
            "    def _pack_request(self, extracted_obs: dict, instruction: str) -> dict:\n        return {\n",
            "    def _pack_request(self, extracted_obs: dict, instruction: str) -> dict:\n        # 中文阅读提示：这些 key 必须匹配 OpenPI DROID checkpoint 的训练数据 schema，不能随意改名。\n        return {\n",
        ),
        (
            "    def _query_server(self, request: dict) -> dict:\n        return self._infer_with_retry(request)\n\n    def _unpack_response(self, response: dict) -> np.ndarray:\n        return np.asarray(response[\"actions\"])\n",
            "    def _query_server(self, request: dict) -> dict:\n        # 中文阅读提示：真正的 VLA 推理发生在服务端，这里只做 websocket RPC 和断线重试。\n        return self._infer_with_retry(request)\n\n    def _unpack_response(self, response: dict) -> np.ndarray:\n        # 中文阅读提示：OpenPI 返回一段 action chunk，父类 InferenceClient 会按 open_loop_horizon 消费。\n        return np.asarray(response[\"actions\"])\n",
        ),
        (
            "    def _postprocess_chunk(self, chunk: np.ndarray) -> np.ndarray:\n        chunk = chunk.copy()\n",
            "    def _postprocess_chunk(self, chunk: np.ndarray) -> np.ndarray:\n        # 中文阅读提示：最后一维是夹爪动作，把连续值二值化，避免半开半合造成物理接触不稳定。\n        chunk = chunk.copy()\n",
        ),
    ],
    "robolab/eval/base_client.py": [
        (
            "class InferenceClient(ABC):\n    \"\"\"Root client for policy inference.\n",
            "class InferenceClient(ABC):\n    # 中文阅读提示：所有策略客户端的共同抽象；RoboLab 只要求它能把 obs+instruction 变成下一步 action。\n    \"\"\"Root client for policy inference.\n",
        ),
        (
            "    def __init__(self) -> None:\n        # Per-env chunking state. Subclasses may ignore and manage state however\n",
            "    def __init__(self) -> None:\n        # 中文阅读提示：并行仿真时每个 env 都有自己的动作块缓存，避免 env 之间串动作。\n        # Per-env chunking state. Subclasses may ignore and manage state however\n",
        ),
        (
            "        extracted = self._extract_observation(obs, env_id=env_id)\n\n        if self._needs_refresh(env_id):\n",
            "        # 中文阅读提示：标准推理链路是 extract -> pack -> query -> unpack -> postprocess -> 按步消费动作块。\n        extracted = self._extract_observation(obs, env_id=env_id)\n\n        if self._needs_refresh(env_id):\n",
        ),
        (
            "    def reset(self, *, env_id: int | None = None) -> None:\n        \"\"\"Clear per-episode state. ``env_id=None`` resets all envs.\n",
            "    def reset(self, *, env_id: int | None = None) -> None:\n        # 中文阅读提示：episode 结束后清空动作缓存，防止下一条轨迹继续执行旧预测。\n        \"\"\"Clear per-episode state. ``env_id=None`` resets all envs.\n",
        ),
        (
            "    def _needs_refresh(self, env_id: int) -> bool:\n        return env_id not in self._chunks or self._counters[env_id] >= self.open_loop_horizon\n",
            "    def _needs_refresh(self, env_id: int) -> bool:\n        # 中文阅读提示：只有当前动作块耗尽时才重新请求模型，复现论文时这会显著影响推理频率和耗时。\n        return env_id not in self._chunks or self._counters[env_id] >= self.open_loop_horizon\n",
        ),
    ],
    "robolab/eval/runner.py": [
        (
            "def _unit_interval(s: str) -> float:\n    v = float(s)\n",
            "def _unit_interval(s: str) -> float:\n    # 中文阅读提示：自适应采样用成功率置信区间宽度作为停止条件，这里限制参数范围。\n    v = float(s)\n",
        ),
        (
            "def add_common_eval_args(parser: argparse.ArgumentParser) -> None:\n    \"\"\"Add the shared eval flags. Call this once per runner script.\"\"\"\n",
            "def add_common_eval_args(parser: argparse.ArgumentParser) -> None:\n    \"\"\"Add the shared eval flags. Call this once per runner script.\"\"\"\n    # 中文阅读提示：所有策略入口共用这些参数，保证 pi0/gr00t/空策略等输出格式一致。\n",
        ),
        (
            "    import os\n\n    import robolab.constants\n",
            "    import os\n\n    # 中文阅读提示：这些导入依赖 Isaac Sim 已启动，所以故意放在函数内部，避免 AppLauncher 前触发插件加载。\n    import robolab.constants\n",
        ),
        (
            "    if args.output_folder_name is not None:\n        output_folder_name = args.output_folder_name\n",
            "    # 中文阅读提示：输出目录名是复现实验的主索引；指定旧目录时会续跑并跳过已完成 episode。\n    if args.output_folder_name is not None:\n        output_folder_name = args.output_folder_name\n",
        ),
        (
            "    if args.task:\n        task_envs = get_envs(task=args.task)\n",
            "    # 中文阅读提示：任务筛选优先级为显式 task、tag、全部；4090 调试建议先单任务 num_envs=1。\n    if args.task:\n        task_envs = get_envs(task=args.task)\n",
        ),
        (
            "    num_envs = args.num_envs\n    num_runs = args.num_runs\n",
            "    # 中文阅读提示：num_envs 决定并行仿真数量，24GB 4090 上 OOM 时优先降低它。\n    num_envs = args.num_envs\n    num_runs = args.num_runs\n",
        ),
        (
            "    episode_results_file, episode_results = init_experiment(output_dir)\n\n    save_videos = args.video_mode != \"none\"\n",
            "    # 中文阅读提示：episode_results.jsonl 是 append-only 结果账本，汇总/续跑都依赖它。\n    episode_results_file, episode_results = init_experiment(output_dir)\n\n    save_videos = args.video_mode != \"none\"\n",
        ),
        (
            "    for task_env in task_envs:\n        scene_output_dir = os.path.join(output_dir, task_env)\n",
            "    for task_env in task_envs:\n        # 中文阅读提示：每个 task 单独一个目录，里面包含 env_cfg、视频、HDF5、事件日志。\n        scene_output_dir = os.path.join(output_dir, task_env)\n",
        ),
        (
            "        if check_all_episodes_complete(\n            episode_results=episode_results, env_name=task_env, num_episodes=total_episodes\n",
            "        # 中文阅读提示：续跑保护，避免因为中断后重新执行而覆盖或重复统计已有 episode。\n        if check_all_episodes_complete(\n            episode_results=episode_results, env_name=task_env, num_episodes=total_episodes\n",
        ),
        (
            "        env, env_cfg = create_env(\n            task_env,\n",
            "        # 中文阅读提示：这里才真正创建 Isaac Lab 环境，并把 policy 名称写入 env_cfg 作为证据。\n        env, env_cfg = create_env(\n            task_env,\n",
        ),
        (
            "        client = client_factory(args)\n\n        run_idx = 0\n",
            "        # 中文阅读提示：每个 task 创建一次推理客户端，避免每个 episode 反复连接/加载策略。\n        client = client_factory(args)\n\n        run_idx = 0\n",
        ),
        (
            "            if is_adaptive:\n                k_so_far, n_so_far = count_task_episodes(episode_results, task_env)\n",
            "            if is_adaptive:\n                # 中文阅读提示：自适应采样按当前成功数/总数决定是否继续，目标是节省完整 RoboLab-120 成本。\n                k_so_far, n_so_far = count_task_episodes(episode_results, task_env)\n",
        ),
        (
            "            run_episode_ids = [run_idx * num_envs + eid for eid in range(num_envs)]\n            if all(\n",
            "            # 中文阅读提示：并行 env 的 episode id 按 run_idx*num_envs+env_id 展开，保证结果可去重。\n            run_episode_ids = [run_idx * num_envs + eid for eid in range(num_envs)]\n            if all(\n",
        ),
        (
            "            env_results, msgs, timing = run_episode(\n                env=env,\n",
            "            # 中文阅读提示：run_episode 执行“观测 -> 策略推理 -> env.step -> 终止检测”的核心闭环。\n            env_results, msgs, timing = run_episode(\n                env=env,\n",
        ),
        (
            "            episode_results = summarize_run(\n                env_results=env_results,\n",
            "            # 中文阅读提示：summarize_run 把每个 env 的成功/失败、步数、耗时、原因写回 JSONL。\n            episode_results = summarize_run(\n                env_results=env_results,\n",
        ),
        (
            "            env.reset_eval_state()\n            run_idx += 1\n",
            "            # 中文阅读提示：RoboLab 会冻结已终止 env；下一批 episode 前必须清掉冻结和结果缓存。\n            env.reset_eval_state()\n            run_idx += 1\n",
        ),
    ],
    "robolab/eval/episode.py": [
        (
            "class TimingStats:\n    \"\"\"Simple timing utility for profiling code sections.\"\"\"\n",
            "class TimingStats:\n    # 中文阅读提示：计时器把 policy/env/video 三段耗时分开，方便判断瓶颈在模型还是仿真。\n    \"\"\"Simple timing utility for profiling code sections.\"\"\"\n",
        ),
        (
            "    timer = TimingStats()\n\n    obs, _ = env.reset()\n",
            "    timer = TimingStats()\n\n    # 中文阅读提示：这里 reset 两次沿用原项目流程，用于确保 Isaac/recorder 初始状态稳定。\n    obs, _ = env.reset()\n",
        ),
        (
            "    action_dim = getattr(\n        getattr(env, \"action_manager\", None),\n",
            "    # 中文阅读提示：动作维度优先从 Isaac Lab action_manager 读取，确保和当前机器人控制器一致。\n    action_dim = getattr(\n        getattr(env, \"action_manager\", None),\n",
        ),
        (
            "    clients = [client] * env.num_envs\n\n    # Set up per-run HDF5 file and per-env demo indices\n",
            "    # 中文阅读提示：同一个 websocket client 共享给所有 env，动作块缓存由 env_id 区分。\n    clients = [client] * env.num_envs\n\n    # Set up per-run HDF5 file and per-env demo indices\n",
        ),
        (
            "    if env.recorder_manager is not None and hasattr(env.recorder_manager, 'set_hdf5_file'):\n        env.recorder_manager.set_hdf5_file(f\"run_{episode}.hdf5\")\n",
            "    if env.recorder_manager is not None and hasattr(env.recorder_manager, 'set_hdf5_file'):\n        # 中文阅读提示：每个 run 一个 HDF5，里面按 demo_<env_id> 存并行环境轨迹。\n        env.recorder_manager.set_hdf5_file(f\"run_{episode}.hdf5\")\n",
        ),
        (
            "            timer.start(\"policy_inference\")\n            # Infer actions for all active (non-frozen) envs\n",
            "            timer.start(\"policy_inference\")\n            # 中文阅读提示：只对还没终止的 env 请求策略，已冻结 env 的 action 保持 0。\n            # Infer actions for all active (non-frozen) envs\n",
        ),
        (
            "            timer.start(\"env_step\")\n            obs, reward, term, trunc, info = env.step(actions)\n",
            "            timer.start(\"env_step\")\n            # 中文阅读提示：env.step 是仿真推进点，termination、recorder、subtask 也会在这一步被触发。\n            obs, reward, term, trunc, info = env.step(actions)\n",
        ),
        (
            "            # Collect per-env subtask info (list of dicts, one per env)\n            per_env_infos = get_all_env_subtask_infos(env)\n",
            "            # 中文阅读提示：每步抓取 subtask 状态，后续可解释“抓到了/放下了/失败在哪个谓词”。\n            # Collect per-env subtask info (list of dicts, one per env)\n            per_env_infos = get_all_env_subtask_infos(env)\n",
        ),
        (
            "            # RobolabEnv freezes terminated envs and exports recordings automatically\n            if env.all_terminated:\n",
            "            # 中文阅读提示：所有并行 env 都终止后提前退出，不再浪费步数跑到 max_episode_length。\n            # RobolabEnv freezes terminated envs and exports recordings automatically\n            if env.all_terminated:\n",
        ),
        (
            "        try:\n            client.reset()\n",
            "        try:\n            # 中文阅读提示：清空策略端 episode 状态，尤其是 OpenPI action chunk 缓存。\n            client.reset()\n",
        ),
    ],
    "robolab/eval/summarize.py": [
        (
            "def _read_final_score_from_hdf5(hdf5_path: str, env_id: int) -> float | None:\n    \"\"\"Return the canonical final-step SM score for an env from\n",
            "def _read_final_score_from_hdf5(hdf5_path: str, env_id: int) -> float | None:\n    # 中文阅读提示：最终 subtask 分数以 HDF5 里的最后一步为准，避免事件日志缺边时分数不一致。\n    \"\"\"Return the canonical final-step SM score for an env from\n",
        ),
        (
            "def _tally_events(events: list[dict]) -> dict:\n    \"\"\"Tally a v2 events list (each entry has ``code``, ``info``, ...) and\n",
            "def _tally_events(events: list[dict]) -> dict:\n    # 中文阅读提示：把稀疏事件流压成计数字典，例如 WRONG_OBJECT_GRABBED 出现几次。\n    \"\"\"Tally a v2 events list (each entry has ``code``, ``info``, ...) and\n",
        ),
        (
            "    episode_id = run_idx * num_envs + env_id\n\n    summary: dict = {\n",
            "    # 中文阅读提示：episode_id 展开并行 env，确保 num_envs>1 时每条轨迹有唯一编号。\n    episode_id = run_idx * num_envs + env_id\n\n    summary: dict = {\n",
        ),
        (
            "    if enable_subtask_progress:\n        # Score: HDF5 subtask/score[final_step] is canonical (matches\n",
            "    if enable_subtask_progress:\n        # 中文阅读提示：开启 subtask 后，summary 会多出 score/reason，是失败分析最关键的字段。\n        # Score: HDF5 subtask/score[final_step] is canonical (matches\n",
        ),
        (
            "    final_infos = get_final_subtask_info(env, env_id=None)\n\n    dt = env_cfg.sim.dt * env_cfg.decimation\n",
            "    # 中文阅读提示：final_infos 保存未完成 episode 的最终失败原因；成功 episode 通常依赖 events_list 解释。\n    final_infos = get_final_subtask_info(env, env_id=None)\n\n    dt = env_cfg.sim.dt * env_cfg.decimation\n",
        ),
        (
            "    per_env_events_list = get_all_env_events(env) or [[] for _ in range(num_envs)]\n    env_results_by_id = {r[\"env_id\"]: r for r in env_results}\n",
            "    # 中文阅读提示：先取出 recorder 内存中的 v2 事件，落盘后再用于统计，避免重新读文件。\n    per_env_events_list = get_all_env_events(env) or [[] for _ in range(num_envs)]\n    env_results_by_id = {r[\"env_id\"]: r for r in env_results}\n",
        ),
        (
            "        log_file = os.path.join(scene_output_dir, f\"log_{run_idx}_env{eid}.json\")\n        dump_results_to_file(log_file, log_obj, append=False)\n",
            "        log_file = os.path.join(scene_output_dir, f\"log_{run_idx}_env{eid}.json\")\n        # 中文阅读提示：每个 env 的事件单独写 JSON，便于和视频/HDF5 的 demo_<env_id> 对齐。\n        dump_results_to_file(log_file, log_obj, append=False)\n",
        ),
        (
            "        traj_data = load_demo_data(hdf5_path, f\"demo_{env_id}\")\n        traj_metrics = compute_episode_metrics(traj_data, dt=dt) if traj_data else None\n",
            "        # 中文阅读提示：轨迹指标从 HDF5 计算，用于比较速度、路径长度和平滑度等行为质量。\n        traj_data = load_demo_data(hdf5_path, f\"demo_{env_id}\")\n        traj_metrics = compute_episode_metrics(traj_data, dt=dt) if traj_data else None\n",
        ),
    ],
    "robolab/core/environments/runtime.py": [
        (
            "def check_scene_valid(env: ManagerBasedEnv) -> bool:\n    \"\"\"\n    Checks the scene has all the required fields for RoboLab.\n    \"\"\"\n",
            "def check_scene_valid(env: ManagerBasedEnv) -> bool:\n    \"\"\"\n    Checks the scene has all the required fields for RoboLab.\n    \"\"\"\n    # 中文阅读提示：RoboLab 任务默认围绕名为 robot 的 articulation 写观测、控制和接触判断。\n",
        ),
        (
            "    env = None\n\n    if isinstance(scene, str):\n",
            "    env = None\n\n    # 中文阅读提示：scene 可以是 gym 注册名，也可以是已经构造好的 Isaac Lab 配置对象。\n    if isinstance(scene, str):\n",
        ),
        (
            "        # create a new stage\n        omni.usd.get_context().new_stage()\n",
            "        # 中文阅读提示：每个任务新开 USD stage，避免上一个任务的 prim/物理状态泄漏到当前任务。\n        # create a new stage\n        omni.usd.get_context().new_stage()\n",
        ),
        (
            "            # Initialize the env for current scene\n            env_cfg = parse_env_cfg(\n",
            "            # 中文阅读提示：parse_env_cfg 会把任务名解析成 Isaac Lab ManagerBasedEnvCfg，并注入 device/seed/num_envs。\n            # Initialize the env for current scene\n            env_cfg = parse_env_cfg(\n",
        ),
        (
            "            env_cfg._instruction_variants = env_cfg.instruction\n            env_cfg.instruction = resolve_instruction(env_cfg.instruction, instruction_type)\n",
            "            # 中文阅读提示：保留原始 instruction 字典，同时把本轮使用的 default/vague/specific 文本解析成字符串。\n            env_cfg._instruction_variants = env_cfg.instruction\n            env_cfg.instruction = resolve_instruction(env_cfg.instruction, instruction_type)\n",
        ),
        (
            "            # Create new environment\n            env = gym.make(scene, cfg=env_cfg).unwrapped\n",
            "            # 中文阅读提示：这里进入 gym/Isaac Lab 创建真实仿真环境，后续 env.step 都走这个对象。\n            # Create new environment\n            env = gym.make(scene, cfg=env_cfg).unwrapped\n",
        ),
        (
            "        env = RobolabEnv(env_cfg)\n    else:\n",
            "        # 中文阅读提示：直接传 cfg 时使用 RoboLab 自定义 env 类，保留冻结终止 env 和按 env 导出记录的能力。\n        env = RobolabEnv(env_cfg)\n    else:\n",
        ),
        (
            "    check_scene_valid(env)\n\n    # disable control on stop\n",
            "    # 中文阅读提示：统一校验任务是否满足 RoboLab 最小约定，例如必须有 robot articulation。\n    check_scene_valid(env)\n\n    # disable control on stop\n",
        ),
        (
            "    if policy is not None:\n        env_cfg.policy = policy\n",
            "    if policy is not None:\n        # 中文阅读提示：把策略名写进 env_cfg.json，之后看结果文件就能知道是哪种 VLA/策略跑的。\n        env_cfg.policy = policy\n",
        ),
        (
            "    # Save env_cfg as json for metadata\n    with open(os.path.join(env.output_dir, \"env_cfg.json\"), \"w\") as f:\n",
            "    # 中文阅读提示：env_cfg.json 是复现证据，记录场景、指令、seed、任务属性和策略名。\n    # Save env_cfg as json for metadata\n    with open(os.path.join(env.output_dir, \"env_cfg.json\"), \"w\") as f:\n",
        ),
        (
            "def end_episode(env: ManagerBasedRLEnv):\n    from robolab.core.logging.recorder_manager import RobolabRecorderManager\n",
            "def end_episode(env: ManagerBasedRLEnv):\n    # 中文阅读提示：episode 结束时导出 HDF5/视频/事件记录，然后清理 recorder，为下一轮做准备。\n    from robolab.core.logging.recorder_manager import RobolabRecorderManager\n",
        ),
    ],
    "robolab/core/environments/env.py": [
        (
            "    def __init__(self, cfg, **kwargs):\n        super().__init__(cfg, **kwargs)\n",
            "    def __init__(self, cfg, **kwargs):\n        super().__init__(cfg, **kwargs)\n        # 中文阅读提示：RoboLab 评测不希望成功/失败的 env 自动 reset，所以用 frozen mask 锁住终止状态。\n",
        ),
        (
            "        recorders_cfg = self.cfg.recorders\n        self.cfg.recorders = None\n",
            "        # 中文阅读提示：先禁用上游 recorder 的 eager HDF5 创建，再替换成 RoboLab 的按 run 懒加载 recorder。\n        recorders_cfg = self.cfg.recorders\n        self.cfg.recorders = None\n",
        ),
        (
            "        self._has_stepped = True\n        # Snapshot frozen state before step so recorder can detect newly-frozen envs\n",
            "        self._has_stepped = True\n        # 中文阅读提示：step 前保留冻结快照，recorder 可据此判断哪些 env 是刚刚终止的。\n        # Snapshot frozen state before step so recorder can detect newly-frozen envs\n",
        ),
        (
            "        if self._frozen_envs.any():\n            action = action.clone()\n",
            "        if self._frozen_envs.any():\n            # 中文阅读提示：已终止 env 的动作强制置零，防止继续移动影响最终状态和视频。\n            action = action.clone()\n",
        ),
        (
            "        if not self._has_stepped:\n            # Initial reset — let all envs reset normally\n",
            "        if not self._has_stepped:\n            # 中文阅读提示：首次 reset 仍按 Isaac Lab 正常流程初始化所有 env。\n            # Initial reset — let all envs reset normally\n",
        ),
        (
            "        # During stepping — freeze newly terminated envs\n        for eid in env_ids.tolist():\n",
            "        # 中文阅读提示：运行中被 reset 的 env 其实是刚终止的 env；这里记录结果并冻结，而不是重新开始。\n        # During stepping — freeze newly terminated envs\n        for eid in env_ids.tolist():\n",
        ),
        (
            "                if ep_len <= 2:\n                    # Physics artifact: terminated before the robot could act.\n",
            "                if ep_len <= 2:\n                    # 中文阅读提示：极早终止通常是物理初始化抖动，不计入真实策略表现，直接正常 reset。\n                    # Physics artifact: terminated before the robot could act.\n",
        ),
        (
            "                # Auto-export recording for this env\n                if self.recorder_manager is not None:\n",
            "                # 中文阅读提示：单个 env 一终止就导出，避免并行评测中其它 env 继续跑导致该 env 轨迹丢失。\n                # Auto-export recording for this env\n                if self.recorder_manager is not None:\n",
        ),
        (
            "        # Only reset non-frozen envs (typically none in eval)\n        mask = ~self._frozen_envs[env_ids]\n",
            "        # 中文阅读提示：只有非冻结 env 才允许真正 reset；评测中通常全部被冻结等待汇总。\n        # Only reset non-frozen envs (typically none in eval)\n        mask = ~self._frozen_envs[env_ids]\n",
        ),
        (
            "    def get_env_results(self) -> list[dict]:\n        \"\"\"Get per-env results after termination.\"\"\"\n",
            "    def get_env_results(self) -> list[dict]:\n        \"\"\"Get per-env results after termination.\"\"\"\n        # 中文阅读提示：summarize_run 会读取这里的 success/step，写入 episode_results.jsonl。\n",
        ),
        (
            "    def reset_eval_state(self):\n        \"\"\"Reset frozen state for next episode batch.\"\"\"\n",
            "    def reset_eval_state(self):\n        \"\"\"Reset frozen state for next episode batch.\"\"\"\n        # 中文阅读提示：同一个 env 对象会复用多轮 run，下一轮前必须清空冻结和结果缓存。\n",
        ),
    ],
    "robolab/core/task/task.py": [
        (
            "class Task:\n    \"\"\"Base task configuration with scene, terminations, and instruction.\n",
            "class Task:\n    # 中文阅读提示：每个 benchmark 任务本质上都是 Task 子类，声明场景、指令、终止条件和 subtasks。\n    \"\"\"Base task configuration with scene, terminations, and instruction.\n",
        ),
        (
            "def resolve_instruction(instruction: str | dict[str, str], instruction_type: str = \"default\") -> str:\n    \"\"\"Resolve an instruction field to a plain string.\n",
            "def resolve_instruction(instruction: str | dict[str, str], instruction_type: str = \"default\") -> str:\n    # 中文阅读提示：论文里的 vague/specific/default 指令差异，在这里被解析成当前 episode 使用的文本。\n    \"\"\"Resolve an instruction field to a plain string.\n",
        ),
        (
            "def verify_task_valid(task_class: type[Task]) -> tuple[bool, str]:\n    \"\"\"\n    Verify if a task file is valid.\n    \"\"\"\n",
            "def verify_task_valid(task_class: type[Task]) -> tuple[bool, str]:\n    \"\"\"\n    Verify if a task file is valid.\n    \"\"\"\n    # 中文阅读提示：注册任务前做静态校验，避免跑到 Isaac Sim 里才发现缺 termination 或物体名写错。\n",
        ),
        (
            "    # Check terminations\n    terminations = task_class.terminations()\n",
            "    # 中文阅读提示：成功 termination 的参数必须和谓词函数签名、contact_object_list 同时匹配。\n    # Check terminations\n    terminations = task_class.terminations()\n",
        ),
        (
            "def verify_contact_objects_in_scene(task_class: type[Task]) -> tuple[bool, str]:\n    \"\"\"\n    Verify that all objects in the task's contact_object_list are present in the scene.\n",
            "def verify_contact_objects_in_scene(task_class: type[Task]) -> tuple[bool, str]:\n    # 中文阅读提示：contact_object_list 必须能在 USD scene 中找到，否则接触传感和错误抓取统计都不可靠。\n    \"\"\"\n    Verify that all objects in the task's contact_object_list are present in the scene.\n",
        ),
    ],
    "robolab/core/task/subtask.py": [
        (
            "    def __post_init__(self):\n        \"\"\"Validate the subtask group configuration.\"\"\"\n",
            "    def __post_init__(self):\n        \"\"\"Validate the subtask group configuration.\"\"\"\n        # 中文阅读提示：任务作者可以用多种写法定义条件，这里统一规范成 {group: [(func, score), ...]}。\n",
        ),
        (
            "        # Normalize the scores of the conditions within each group to sum to 1.0.\n        self.conditions = normalize_conditions_scores(self.conditions)\n",
            "        # 中文阅读提示：组内条件分数归一化后，subtask 进度/失败分数才可跨任务比较。\n        # Normalize the scores of the conditions within each group to sum to 1.0.\n        self.conditions = normalize_conditions_scores(self.conditions)\n",
        ),
        (
            "        if self.logical == \"choose\":\n            if self.K is None:\n",
            "        if self.logical == \"choose\":\n            # 中文阅读提示：choose 表示“从多个对象/组里完成 K 个即可”，必须显式给 K 防止歧义。\n            if self.K is None:\n",
        ),
        (
            "        if not verbose:\n            return\n",
            "        if not verbose:\n            # 中文阅读提示：非 verbose 模式只打印 subtask 摘要，避免长 benchmark 输出过噪。\n            return\n",
        ),
    ],
    "robolab/core/task/conditionals.py": [
        (
            "#########################################################\n# Composite conditions\n#########################################################\n",
            "#########################################################\n# Composite conditions\n#########################################################\n# 中文阅读提示：composite 条件负责把“抓起并放入”等自然任务拆成若干 atomic 谓词序列。\n",
        ),
        (
            "    if isinstance(object, str):\n        objects = [object]\n",
            "    # 中文阅读提示：单对象和多对象统一成列表，后续每个对象各自维护一条条件链。\n    if isinstance(object, str):\n        objects = [object]\n",
        ),
        (
            "    conditions = {}\n    for obj in objects:\n        conditions[obj] = [\n",
            "    conditions = {}\n    for obj in objects:\n        # 中文阅读提示：每个对象先满足 object_grabbed，再满足 object_in_container，最终分数由放置条件给出。\n        conditions[obj] = [\n",
        ),
        (
            "#########################################################\n# Atomic conditions - Contact\n#########################################################\n",
            "#########################################################\n# Atomic conditions - Contact\n#########################################################\n# 中文阅读提示：atomic 条件是 Isaac Lab termination/subtask state machine 直接调用的最小判断单元。\n",
        ),
        (
            "    world = get_world(env)\n    result = in_contact(world, object1, object2, force_threshold=0.1, env_id=env_id)\n",
            "    world = get_world(env)\n    # 中文阅读提示：env_id=None 返回 num_envs 向量；传入 env_id 时返回单个环境的 bool。\n    result = in_contact(world, object1, object2, force_threshold=0.1, env_id=env_id)\n",
        ),
        (
            "    def condition(world, obj, env_id=None):\n        result = in_opentop_container(\n",
            "    def condition(world, obj, env_id=None):\n        # 中文阅读提示：先做几何开口容器判断，再按参数追加接触、松爪、静止等约束。\n        result = in_opentop_container(\n",
        ),
        (
            "    result = evaluate_spatial_condition(env, object, condition, logical, K, env_id=env_id)\n    if robolab.constants.DEBUG:\n",
            "    # 中文阅读提示：evaluate_spatial_condition 统一处理 object 是单个/多个以及 all/any/choose 逻辑。\n    result = evaluate_spatial_condition(env, object, condition, logical, K, env_id=env_id)\n    if robolab.constants.DEBUG:\n",
        ),
        (
            "    def condition(world, obj, env_id=None):\n        result = world.is_supported_on_surface(obj, reference_object, env_id=env_id)\n",
            "    def condition(world, obj, env_id=None):\n        # 中文阅读提示：on_top 不只看位置，还要看支撑力方向，避免悬空但投影落在表面内被误判。\n        result = world.is_supported_on_surface(obj, reference_object, env_id=env_id)\n",
        ),
        (
            "    if groups is None or len(groups) == 0:\n        if env_id is not None:\n",
            "    # 中文阅读提示：用于多组物体分别放入多个容器的任务；所有 group 都满足才整体成功。\n    if groups is None or len(groups) == 0:\n        if env_id is not None:\n",
        ),
        (
            "    if isinstance(object, str):\n        intended_set = {object}\n",
            "    # 中文阅读提示：错误抓取检测会扫描接触列表中除目标和忽略物体外的其它物体。\n    if isinstance(object, str):\n        intended_set = {object}\n",
        ),
        (
            "    def _make_state():\n        N, dev = env.num_envs, env.device\n",
            "    def _make_state():\n        # 中文阅读提示：顺序谓词需要跨 step 记忆“第一次放入”的时刻，所以状态存在 WorldState 中。\n        N, dev = env.num_envs, env.device\n",
        ),
        (
            "    # Build the same per-object placement predicate as object_in_container.\n    def _currently_placed(obj: str, eid: int | None):\n",
            "    # 中文阅读提示：这里复用 object_in_container 的放置语义，确保顺序任务和普通放置任务判定一致。\n    # Build the same per-object placement predicate as object_in_container.\n    def _currently_placed(obj: str, eid: int | None):\n",
        ),
        (
            "        # Batched path used by IsaacLab TerminationManager.\n        currently = {obj: _currently_placed(obj, None) for obj in objects}\n",
            "        # 中文阅读提示：批量路径服务 Isaac Lab TerminationManager，一次返回所有并行 env 的 bool tensor。\n        # Batched path used by IsaacLab TerminationManager.\n        currently = {obj: _currently_placed(obj, None) for obj in objects}\n",
        ),
    ],
    "robolab/core/task/subtask_state_machine.py": [
        (
            "        self.initialized = False\n        self.env = env\n",
            "        # 中文阅读提示：这是“多步任务”的外层状态机，按顺序推进 subtasks 列表。\n        self.initialized = False\n        self.env = env\n",
        ),
        (
            "    def _initialize_state_machine(self) -> None:\n        \"\"\"Create a new SubtaskGroupStateMachine for the current subtask.\"\"\"\n",
            "    def _initialize_state_machine(self) -> None:\n        \"\"\"Create a new SubtaskGroupStateMachine for the current subtask.\"\"\"\n        # 中文阅读提示：当前 subtask 内部可能有多个对象并行推进，由 ConditionalsStateMachine 负责。\n",
        ),
        (
            "        complete, info, status_code, all_status_codes = self.conditionals_state_machine.step(env_events=env_events)\n\n\n        if complete and not self.is_complete():\n",
            "        complete, info, status_code, all_status_codes = self.conditionals_state_machine.step(env_events=env_events)\n\n\n        # 中文阅读提示：当前 subtask 完成后才进入下一个，这对应论文关注的多步骤操作顺序。\n        if complete and not self.is_complete():\n",
        ),
        (
            "        # Calculate overall progress: completed subtasks + current progress\n        completed_portion = 0.0\n",
            "        # 中文阅读提示：总分 = 已完成 subtask 权重 + 当前 subtask 内部进度，用来描述部分完成程度。\n        # Calculate overall progress: completed subtasks + current progress\n        completed_portion = 0.0\n",
        ),
        (
            "        if self.conditionals_state_machine is not None:\n            return self.conditionals_state_machine.get_final_error_code()\n",
            "        if self.conditionals_state_machine is not None:\n            # 中文阅读提示：失败原因下钻到当前未满足的 atomic condition，便于解释模型卡点。\n            return self.conditionals_state_machine.get_final_error_code()\n",
        ),
    ],
    "robolab/core/task/conditionals_state_machine.py": [
        (
            "        self.env = env\n        self.env_id = env_id\n",
            "        # 中文阅读提示：这是单个 subtask 内部的状态机，按对象分别追踪条件链进度。\n        self.env = env\n        self.env_id = env_id\n",
        ),
        (
            "        # Validate k parameter for \"choose\" mode\n        if self.subtask.logical == \"choose\":\n",
            "        # 中文阅读提示：choose 模式表示完成 K 个对象即可，常用于“任选一个/任选 K 个”的任务。\n        # Validate k parameter for \"choose\" mode\n        if self.subtask.logical == \"choose\":\n",
        ),
        (
            "        # Per-step condition cache to avoid duplicate evaluations\n        self._condition_cache: dict[int, tuple[bool, str]] = {}\n",
            "        # 中文阅读提示：同一步里同一个谓词可能被多处查询，缓存能减少物理/几何状态读取开销。\n        # Per-step condition cache to avoid duplicate evaluations\n        self._condition_cache: dict[int, tuple[bool, str]] = {}\n",
        ),
        (
            "        # Add environment parameters and evaluate\n        params_with_env = {'env': self.env, 'env_id': self.env_id}\n",
            "        # 中文阅读提示：所有 atomic 谓词统一接收 env/env_id，因此可同时支持批量和单 env 解释。\n        # Add environment parameters and evaluate\n        params_with_env = {'env': self.env, 'env_id': self.env_id}\n",
        ),
        (
            "        # Check forward: scan ALL remaining conditions from current_idx onward.\n        # Do NOT break on unsatisfied conditions — a later condition may be\n",
            "        # 中文阅读提示：向前扫描允许“抓起”这种瞬时条件消失后，仍然通过后续“已放入”条件推进。\n        # Check forward: scan ALL remaining conditions from current_idx onward.\n        # Do NOT break on unsatisfied conditions — a later condition may be\n",
        ),
        (
            "        # No forward progress — check backward for regression.\n        # Only regress when the current condition is NOT satisfied and no later\n",
            "        # 中文阅读提示：没有前进时再检查回退，能发现物体掉落/移出容器等状态退化。\n        # No forward progress — check backward for regression.\n        # Only regress when the current condition is NOT satisfied and no later\n",
        ),
        (
            "        # Clear per-step condition cache to ensure fresh evaluations\n        self._condition_cache.clear()\n",
            "        # 中文阅读提示：每个仿真 step 都重新评估物理世界状态，不能复用上一帧缓存。\n        # Clear per-step condition cache to ensure fresh evaluations\n        self._condition_cache.clear()\n",
        ),
        (
            "        # Append pre-computed events from the shared EventTracker\n        if env_events:\n",
            "        # 中文阅读提示：EventTracker 负责错误抓取/碰撞等跨条件事件，这里并入 subtask 事件流。\n        # Append pre-computed events from the shared EventTracker\n        if env_events:\n",
        ),
        (
            "        if target_idx < current_idx:\n            # REGRESSION: Need to regress to an earlier condition\n",
            "        if target_idx < current_idx:\n            # 中文阅读提示：回退意味着之前完成的条件又不成立了，进度和分数都要撤回。\n            # REGRESSION: Need to regress to an earlier condition\n",
        ),
        (
            "        elif target_idx >= current_idx and is_advancement:\n            # ADVANCEMENT: One or more conditions satisfied, advance past target\n",
            "        elif target_idx >= current_idx and is_advancement:\n            # 中文阅读提示：前进可能一次跨多个条件，因此 all_status_codes 会把中间成功也记录下来。\n            # ADVANCEMENT: One or more conditions satisfied, advance past target\n",
        ),
        (
            "        if self.subtask.logical == \"all\":\n            # For \"all\" mode, normalize total score to 1.0\n",
            "        if self.subtask.logical == \"all\":\n            # 中文阅读提示：all/any/choose 三种逻辑不仅决定完成条件，也决定部分分数怎么聚合。\n            # For \"all\" mode, normalize total score to 1.0\n",
        ),
        (
            "        # Collect incomplete objects and their states\n        incomplete_objects = []\n",
            "        # 中文阅读提示：episode 结束仍未完成时，用当前未满足条件生成 reason 字段。\n        # Collect incomplete objects and their states\n        incomplete_objects = []\n",
        ),
    ],
    "robolab/core/events/subtask_recorder.py": [
        (
            "class SubtaskCompletionRecorderTerm(RecorderTerm):\n    subtasks: list[dict[str, Any]] | None = None\n",
            "class SubtaskCompletionRecorderTerm(RecorderTerm):\n    # 中文阅读提示：这是 Isaac Lab recorder term，负责把 subtask 状态机输出写进 HDF5 和事件日志。\n    subtasks: list[dict[str, Any]] | None = None\n",
        ),
        (
            "        if self.subtasks is None:\n            self.subtask_state_machines = []\n",
            "        if self.subtasks is None:\n            # 中文阅读提示：没有定义 subtasks 的任务仍可运行，只是不记录过程进度。\n            self.subtask_state_machines = []\n",
        ),
        (
            "            # One SubtaskStateMachine per env, each tracking independently\n            self.subtask_state_machines = [\n",
            "            # 中文阅读提示：每个并行 env 都有独立状态机，避免 A 环境抓到物体影响 B 环境进度。\n            # One SubtaskStateMachine per env, each tracking independently\n            self.subtask_state_machines = [\n",
        ),
        (
            "        # v2 event log: sparse, edge-triggered. One list per env. Each entry:\n        # {\"step\": int, \"code\": int, \"name\": str, \"info\": str, \"score\": float}.\n",
            "        # 中文阅读提示：v2 事件日志只记录变化点，不保存每帧重复状态，适合长时间 benchmark 分析。\n        # v2 event log: sparse, edge-triggered. One list per env. Each entry:\n        # {\"step\": int, \"code\": int, \"name\": str, \"info\": str, \"score\": float}.\n",
        ),
        (
            "        # Detect envs that were frozen THIS step (newly terminated) — they still\n        # need one final SM step to capture the success condition on the termination frame.\n",
            "        # 中文阅读提示：刚终止的 env 还要再记录一次状态机，才能捕捉成功发生的那一帧。\n        # Detect envs that were frozen THIS step (newly terminated) — they still\n        # need one final SM step to capture the success condition on the termination frame.\n",
        ),
        (
            "        # Batch-check events across all envs (newly-frozen envs are still active for this step)\n        all_events = self._event_tracker.check_events(\n",
            "        # 中文阅读提示：错误抓取、碰撞等事件批量检查一次，再分发给各 env 的状态机。\n        # Batch-check events across all envs (newly-frozen envs are still active for this step)\n        all_events = self._event_tracker.check_events(\n",
        ),
        (
            "            # Emit v2 events: tracker firings + SM transitions, all tagged with\n            # this step's post-update score.\n",
            "            # 中文阅读提示：事件包含 tracker 事件和状态机转移，并附带当前 score 便于画进度曲线。\n            # Emit v2 events: tracker firings + SM transitions, all tagged with\n            # this step's post-update score.\n",
        ),
        (
            "            # Capture error info before auto-reset can cause regression\n            if not sm.is_complete():\n",
            "            # 中文阅读提示：提前保存最佳失败原因，避免自动 reset/回退后丢掉真正的卡点。\n            # Capture error info before auto-reset can cause regression\n            if not sm.is_complete():\n",
        ),
        (
            "        for eid in env_ids:\n            self.subtask_state_machines[eid].reset()\n",
            "        for eid in env_ids:\n            # 中文阅读提示：新 episode 开始时清空状态机和事件列表，但不影响其它并行 env。\n            self.subtask_state_machines[eid].reset()\n",
        ),
        (
            "        for eid in range(self._num_envs):\n            sm = self.subtask_state_machines[eid]\n",
            "        for eid in range(self._num_envs):\n            # 中文阅读提示：超时或未完成时，把当前未满足条件写成最终失败状态。\n            sm = self.subtask_state_machines[eid]\n",
        ),
    ],
    "robolab/core/logging/recorder_manager.py": [
        (
            "def _slice_to_envs(value, env_ids):\n    \"\"\"Slice a recorder-term value (tensor or nested dict of tensors) to a subset of envs.\n",
            "def _slice_to_envs(value, env_ids):\n    # 中文阅读提示：并行 env 中只导出部分 env 时，所有 recorder tensor 都要按 env_ids 切片。\n    \"\"\"Slice a recorder-term value (tensor or nested dict of tensors) to a subset of envs.\n",
        ),
        (
            "class RobolabRecorderManager(RecorderManager):\n    \"\"\"Custom recorder manager with streaming HDF5 support for memory-efficient long episodes.\n",
            "class RobolabRecorderManager(RecorderManager):\n    # 中文阅读提示：RoboLab 自定义 recorder manager，用流式 HDF5 降低长 episode 内存占用。\n    \"\"\"Custom recorder manager with streaming HDF5 support for memory-efficient long episodes.\n",
        ),
        (
            "        # Track streaming state per environment\n        self._streaming_active: dict[int, bool] = {}\n",
            "        # 中文阅读提示：每个 env 独立跟踪是否已经开始流式写入，避免并行轨迹互相污染。\n        # Track streaming state per environment\n        self._streaming_active: dict[int, bool] = {}\n",
        ),
        (
            "        # HDF5 file handlers — created lazily on first write or when set_hdf5_file() is called.\n        # This avoids creating empty data.hdf5 files that are never written to.\n",
            "        # 中文阅读提示：HDF5 handler 懒创建，只有真正记录时才打开文件，减少空文件和句柄泄漏。\n        # HDF5 file handlers — created lazily on first write or when set_hdf5_file() is called.\n        # This avoids creating empty data.hdf5 files that are never written to.\n",
        ),
        (
            "        active = self._active_env_ids()\n        if not active:\n",
            "        # 中文阅读提示：冻结 env 已经完成导出，不再继续写 recorder，防止跨 run 数据串入。\n        active = self._active_env_ids()\n        if not active:\n",
        ),
        (
            "        if self._flush_interval > 0:\n            for env_id in active:\n",
            "        if self._flush_interval > 0:\n            # 中文阅读提示：长 episode 周期性 flush，4090 上跑完整 benchmark 时能降低内存峰值。\n            for env_id in active:\n",
        ),
        (
            "        active_set = set(self._active_env_ids())\n        env_ids = [e for e in env_ids if e in active_set]\n",
            "        # 中文阅读提示：reset 前过滤掉冻结 env，避免已完成轨迹被上游 recorder 再记录一次。\n        active_set = set(self._active_env_ids())\n        env_ids = [e for e in env_ids if e in active_set]\n",
        ),
        (
            "        # Lazy-init HDF5 on first write\n        if not self._hdf5_initialized:\n",
            "        # 中文阅读提示：第一次 flush/export 才真正建 HDF5，文件名通常由 run_episode 设置为 run_N.hdf5。\n        # Lazy-init HDF5 on first write\n        if not self._hdf5_initialized:\n",
        ),
        (
            "        # Record final status for incomplete tasks BEFORE exporting. Scoped to\n        # env_ids being exported — record_final_status returns data for all envs\n",
            "        # 中文阅读提示：导出前先写最终 subtask 状态，保证失败 episode 的 reason/score 进入 HDF5。\n        # Record final status for incomplete tasks BEFORE exporting. Scoped to\n        # env_ids being exported — record_final_status returns data for all envs\n",
        ),
        (
            "            if is_streaming:\n                # Streaming mode: append any remaining data and finalize\n",
            "            if is_streaming:\n                # 中文阅读提示：流式模式最后补写剩余 buffer，并调用 end_episode 写 success 标记。\n                # Streaming mode: append any remaining data and finalize\n",
        ),
    ],
    "robolab/core/logging/results.py": [
        (
            "def beta_ci_bounds(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:\n    \"\"\"95% Beta(k+1, n-k+1) credible interval bounds for a binomial success rate.\n",
            "def beta_ci_bounds(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:\n    # 中文阅读提示：成功率不是只看均值，置信区间能体现样本数不足时的不确定性。\n    \"\"\"95% Beta(k+1, n-k+1) credible interval bounds for a binomial success rate.\n",
        ),
        (
            "    if tasks is None:\n        return episode_results\n",
            "    # 中文阅读提示：结果文件里所有分析都先从 episode_results 过滤出目标任务子集。\n    if tasks is None:\n        return episode_results\n",
        ),
        (
            "def summarize_error_reasons(episode_results: list[dict], indent: str = \"  \") -> None:\n    \"\"\"\n",
            "def summarize_error_reasons(episode_results: list[dict], indent: str = \"  \") -> None:\n    # 中文阅读提示：只统计失败 episode 的 reason，用来快速定位是抓错、碰撞还是没完成。\n    \"\"\"\n",
        ),
        (
            "def _resolve_log_file(ep: dict) -> str | None:\n    \"\"\"Resolve the log file path for an episode result, supporting per-env and legacy formats.\"\"\"\n",
            "def _resolve_log_file(ep: dict) -> str | None:\n    \"\"\"Resolve the log file path for an episode result, supporting per-env and legacy formats.\"\"\"\n    # 中文阅读提示：新格式优先找 log_<run>_env<id>.json，旧单环境结果回退到 log_<run>.json。\n",
        ),
        (
            "def get_wrong_object_stats(episode_results: list[dict], exclude_containers: bool = False) -> dict:\n    \"\"\"\n",
            "def get_wrong_object_stats(episode_results: list[dict], exclude_containers: bool = False) -> dict:\n    # 中文阅读提示：从事件日志里重算错误抓取次数，比只看最终 success/failure 更能解释模型失败模式。\n    \"\"\"\n",
        ),
        (
            "def load_event_log(log_file: str) -> list[dict]:\n    \"\"\"Load a per-env event log and return a v1-shaped ``status_changes`` list\n",
            "def load_event_log(log_file: str) -> list[dict]:\n    # 中文阅读提示：兼容 v1 密集逐步日志和 v2 稀疏事件日志，统一成 status_changes 供统计函数使用。\n    \"\"\"Load a per-env event log and return a v1-shaped ``status_changes`` list\n",
        ),
        (
            "def get_all_env_events(env) -> list[list[dict]] | None:\n    \"\"\"Get the per-env v2 event log accumulated by the recorder term.\n",
            "def get_all_env_events(env) -> list[list[dict]] | None:\n    # 中文阅读提示：run_empty/run_episode 在 end_episode 前调用它，把 recorder 中的事件取出来落盘。\n    \"\"\"Get the per-env v2 event log accumulated by the recorder term.\n",
        ),
        (
            "def init_experiment(output_dir: str) -> tuple[str, list[dict]]:\n    \"\"\"Initialize or load existing experiment results.\"\"\"\n",
            "def init_experiment(output_dir: str) -> tuple[str, list[dict]]:\n    \"\"\"Initialize or load existing experiment results.\"\"\"\n    # 中文阅读提示：如果 output_dir 已有 episode_results，会加载旧结果以支持中断续跑。\n",
        ),
        (
            "def update_experiment_results(run_summary: dict, episode_results_file: str, episode_results: list[dict] = None):\n    if run_summary is None:\n",
            "def update_experiment_results(run_summary: dict, episode_results_file: str, episode_results: list[dict] = None):\n    # 中文阅读提示：每个 episode 完成后立即 append 到 JSONL，减少长时间 benchmark 中断造成的数据损失。\n    if run_summary is None:\n",
        ),
        (
            "def append_episode_to_jsonl(file_path: str, episode: dict):\n    \"\"\"Append a single episode result as one JSON line (append-only, no read-modify-write).\"\"\"\n",
            "def append_episode_to_jsonl(file_path: str, episode: dict):\n    \"\"\"Append a single episode result as one JSON line (append-only, no read-modify-write).\"\"\"\n    # 中文阅读提示：append-only 让多小时评测更抗中断，也方便用 tail 实时看进度。\n",
        ),
        (
            "def load_episode_results(folder_path: str) -> list[dict]:\n    \"\"\"Load episode results from either JSONL (new) or JSON (legacy) format.\n",
            "def load_episode_results(folder_path: str) -> list[dict]:\n    # 中文阅读提示：优先读 JSONL，新旧结果格式共存时避免误读旧 summary。\n    \"\"\"Load episode results from either JSONL (new) or JSON (legacy) format.\n",
        ),
        (
            "def get_avg_score(episode_results: list[dict], task_name=None, fail_only=False):\n    \"\"\"\n",
            "def get_avg_score(episode_results: list[dict], task_name=None, fail_only=False):\n    # 中文阅读提示：score 用于描述部分完成程度；成功 episode 统一按 1.0 计，避免旧日志缺分数。\n    \"\"\"\n",
        ),
        (
            "def get_task_based_results(episode_data: list[dict]) -> dict:\n    \"\"\"Get task-based results from episode data.\"\"\"\n",
            "def get_task_based_results(episode_data: list[dict]) -> dict:\n    \"\"\"Get task-based results from episode data.\"\"\"\n    # 中文阅读提示：把扁平 episode 列表聚合成按任务统计的 success/failure 桶。\n",
        ),
        (
            "def extract_subtask_status_changes(log_data: list[dict]) -> list[dict]:\n    \"\"\"\n",
            "def extract_subtask_status_changes(log_data: list[dict]) -> list[dict]:\n    # 中文阅读提示：从逐 step recorder 日志中抽取“状态变化点”，让失败分析表更短、更可读。\n    \"\"\"\n",
        ),
        (
            "    # Group episodes by the specified field\n    if group_by == \"task\":\n",
            "    # 中文阅读提示：这里是论文复现结果表的核心，按 task/属性/场景/对象数等维度汇总成功率。\n    # Group episodes by the specified field\n    if group_by == \"task\":\n",
        ),
        (
            "            lcb, ucb = beta_ci_bounds(num_success, num_total)\n            success_ci_str = f\"[{lcb*100:.1f}-{ucb*100:.1f}]\"\n",
            "            # 中文阅读提示：每个分组都输出成功率和 95% CI，避免小样本成功率被过度解读。\n            lcb, ucb = beta_ci_bounds(num_success, num_total)\n            success_ci_str = f\"[{lcb*100:.1f}-{ucb*100:.1f}]\"\n",
        ),
    ],
    "robolab/tasks/benchmark/banana_in_bowl_task.py": [
        (
            "class BananaInBowlTerminations:\n    \"\"\"Termination configuration for banana task.\"\"\"\n",
            "class BananaInBowlTerminations:\n    \"\"\"Termination configuration for banana task.\"\"\"\n    # 中文阅读提示：time_out 是失败/截断边界，success 是物理谓词；二者由 Isaac Lab termination manager 判断。\n",
        ),
        (
            "    success = DoneTerm(\n        func=object_in_container,\n",
            "    success = DoneTerm(\n        # 中文阅读提示：成功要求香蕉在碗里、与碗接触、并且夹爪已松开，避免“拿着悬在碗里”被算成功。\n        func=object_in_container,\n",
        ),
        (
            "class BananaInBowlTask(Task):\n    contact_object_list = [\"banana\", \"bowl\", \"table\"]\n",
            "class BananaInBowlTask(Task):\n    # 中文阅读提示：contact_object_list 决定哪些物体会进入接触/错误抓取等谓词检测。\n    contact_object_list = [\"banana\", \"bowl\", \"table\"]\n",
        ),
        (
            "    instruction = {\n        \"default\": \"Pick up the banana and place it in the bowl\",\n",
            "    # 中文阅读提示：同一任务提供不同语言粒度，用来评测 VLA 对指令具体程度的鲁棒性。\n    instruction = {\n        \"default\": \"Pick up the banana and place it in the bowl\",\n",
        ),
        (
            "    # Updated to use new clean API\n    subtasks = [\n",
            "    # 中文阅读提示：subtasks 是过程化评测的进度尺；成功谓词只看终点，subtask 还能解释卡在哪一步。\n    # Updated to use new clean API\n    subtasks = [\n",
        ),
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", type=Path)
    args = parser.parse_args()

    root = args.repo_root.expanduser().resolve()
    changed = apply_replacements(root, REPLACEMENTS)
    print("COMMENTED_FILES")
    for rel in changed:
        print(rel)


if __name__ == "__main__":
    main()
