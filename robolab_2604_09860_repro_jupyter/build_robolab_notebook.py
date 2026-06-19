from __future__ import annotations

import html
import json
import re
from pathlib import Path
from textwrap import dedent

import nbformat as nbf


# 所有生成文件都放在生成器旁边，便于把整个学习包直接移动或打包。
OUT_DIR = Path(__file__).resolve().parent
NOTEBOOK_NAME = "RoboLab_4090_repro_learning_record.ipynb"
MANIFEST_NAME = "source_manifest.json"
README_NAME = "README.md"

# 固定本次学习材料使用的 RoboLab 源码快照；后续运行证据可以更新，但文档要说明参考的 HEAD。
GENERATED_AT = "2026-06-19T00:00:00+08:00"
ROBOLAB_HEAD = "7d45d74904eade3b578a8eb1f2f9f89bc3d40326"


def md(text: str):
    # 让 Python 源码保持缩进可读，同时写出没有多余缩进的 Markdown cell。
    return nbf.v4.new_markdown_cell(dedent(text).strip())


def code(text: str):
    # 代码 cell 也统一去缩进，避免反复生成 notebook 时出现格式漂移。
    return nbf.v4.new_code_cell(dedent(text).strip())


ALERT_STYLES = {
    "TIP": {
        "box": "border:1px solid #bbf7d0; border-left:6px solid #16a34a; background:#f0fdf4; padding:10px 12px; border-radius:6px; margin:12px 0;",
    },
    "NOTE": {
        "box": "border:1px solid #bfdbfe; border-left:6px solid #2563eb; background:#eff6ff; padding:10px 12px; border-radius:6px; margin:12px 0;",
    },
    "WARNING": {
        "box": "border:1px solid #fed7aa; border-left:6px solid #d97706; background:#fff7ed; padding:10px 12px; border-radius:6px; margin:12px 0;",
    },
}


def _inline_markdown_to_html(text: str) -> str:
    # 只转换 callout 里常用的少量 Markdown：粗体和行内代码。主体 Markdown 仍由 Jupyter 自己渲染。
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def render_alerts_for_notebook(text: str) -> str:
    # Cursor/GitHub 适合看 `> [!TIP]` 这类 Markdown Alert；
    # Jupyter 对 Alert 支持不稳定，所以生成 ipynb 时把它们转换成真正带颜色的 HTML 块。
    lines = text.splitlines()
    rendered = []
    i = 0
    while i < len(lines):
        match = re.match(r"^> \[!(TIP|NOTE|WARNING)\]\s*$", lines[i])
        if not match:
            rendered.append(lines[i])
            i += 1
            continue

        kind = match.group(1)
        i += 1
        body = []
        while i < len(lines):
            if lines[i].startswith("> "):
                body.append(lines[i][2:])
                i += 1
            elif lines[i] == ">":
                body.append("")
                i += 1
            else:
                break

        body_html = "<br>\n".join(_inline_markdown_to_html(line) for line in body)
        rendered.append(f'<div style="{ALERT_STYLES[kind]["box"]}">\n{body_html}\n</div>')

    return "\n".join(rendered)


def md_file(name: str):
    # 把已经整理好的长篇精讲/复现报告直接纳入 notebook，避免同一内容维护两份。
    path = OUT_DIR / name
    if not path.exists():
        return md(
            f"""
            ## 缺失材料：`{name}`

            生成 notebook 时没有找到 `{path}`。请先生成或同步该文件，再重新运行 `build_robolab_notebook.py`。
            """
        )
    return nbf.v4.new_markdown_cell(render_alerts_for_notebook(path.read_text(encoding="utf-8")).strip())


def main() -> None:
    # 每次都从这个生成器重建 notebook，而不是手工改 .ipynb JSON。
    # 这样后续增补注释、证据和章节时更稳定，也更容易审查差异。
    nb = nbf.v4.new_notebook()
    nb.metadata.update(
        {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        }
    )

    cells = [
        md(
            """
            # RoboLab 复现与学习记录（RTX 4090）

            **目标**：在高保真仿真中复现 NVIDIA RoboLab，重点观察通用机器人策略在视觉识别、空间关系推理、多步骤/过程化操作三个维度上的泛化能力。

            **硬件定位**：RTX 4090 24GB VRAM 可以做安装验证、单任务 smoke run、小批量子集评测；完整 RoboLab-120 或较高 `num_envs` 并行需要更谨慎，官方推荐 48GB+ VRAM。

            **本 notebook 的定位**：

            - 先做可记录、可复跑、可交付的复现实验台账。
            - 默认不执行重型安装和仿真命令，避免在非 Ubuntu/非 4090 环境误跑。
            - 搬到 Ubuntu 22.04+ / RTX 4090 机器后，把配置 cell 里的执行开关改为 `True`，按阶段运行。
            - 所有命令输出、指标汇总、图表和学习记录统一写到 `robolab_repro_artifacts/`。

            **来源边界**：本 notebook 只围绕论文、官网、GitHub README/docs 中公开的信息组织复现流程；具体模型权重、策略服务端和许可证按实际使用的模型另行记录。
            """
        ),
        md(
            """
            ## 0. 官方来源与当前事实核对

            复现前先固定来源，避免照着旧命令走偏。

            - 论文：`arXiv:2604.09860v3`，RoboLab-120 包含 120 个任务，覆盖 visual / procedural / relational 三个能力轴。
            - 官网：强调 agentic scene/task generation、结果 dashboard、RoboLab benchmark 和 sensitivity analysis。
            - GitHub README 当前说明：需要 `uv` 与系统 `ffmpeg`；`uv sync` 会自动安装 Isaac Sim 5.0 和 Isaac Lab 2.2.0。
            - GitHub README 当前说明：依赖要求为 Ubuntu 22.04+、Python 3.11、NVIDIA RTX GPU；官方建议 48GB+ VRAM，4090 需要先降并行度。
            - GitHub HEAD（准备 notebook 时）：`7d45d74904eade3b578a8eb1f2f9f89bc3d40326`。

            **执行策略修正**：主路线不先手动 clone/build Isaac Sim。RoboLab 现在的主安装路径是 clone RoboLab 后用 `uv sync` 拉起 Isaac Sim/Lab 依赖。只有做 Isaac Sim 内核开发或官方安装失败时，才单独走 Isaac Sim 源码构建路线。
            """
        ),
        code(
            r"""
            # ===== 1. 导入标准库：这些库负责路径、时间、JSON、系统信息和命令执行 =====
            from pathlib import Path  # 用 Path 统一处理 Windows/Linux 路径，避免手写字符串拼路径。
            import datetime as _dt  # 给日志和学习记录生成带日期/时区的时间戳。
            import json  # 读写 repro_status、远端 summary、命令日志等结构化证据。
            import os  # 读取环境变量，例如 ROBOLAB_WORK_ROOT / ROBOLAB_DIR。
            import platform  # 判断当前是不是 Linux，避免在 Windows 上误启动 Isaac Sim。
            import shlex  # 在展示 shell 命令时安全地转义路径和参数。
            import subprocess  # 真正执行 git、uv、pytest、RoboLab 脚本等外部命令。
            import sys  # 输出当前 Python 版本，便于排查 Python 3.11 要求。
            import time  # 计算命令运行耗时。

            # ===== 2. 导入可选分析库：没有安装也不让 notebook 中断 =====
            try:
                import pandas as pd  # 用来把 episode_results.jsonl 汇总成表格。
            except Exception:
                pd = None  # pandas 不存在时，后面的分析 cell 会退化为打印 JSON。

            try:
                import matplotlib.pyplot as plt  # 用来画成功率柱状图。
            except Exception:
                plt = None  # matplotlib 不存在时跳过绘图，不影响复现记录主体。

            try:
                from IPython.display import Markdown, display  # 在 Jupyter 里渲染 Markdown 表格。
            except Exception:
                Markdown = None  # 非 Jupyter 环境下没有 Markdown 对象时使用 print。
                display = print  # 让脚本模式也能看到输出。

            # ===== 3. 定义 notebook 的工作目录和证据目录 =====
            NOTEBOOK_ROOT = Path.cwd()  # 当前执行 notebook 的目录；建议就是本交付物目录。
            ARTIFACT_DIR = NOTEBOOK_ROOT / "robolab_repro_artifacts"  # 所有本地运行证据统一放这里。
            WORK_ROOT = Path(os.environ.get("ROBOLAB_WORK_ROOT", NOTEBOOK_ROOT / "robolab_workspace")).expanduser()
            # WORK_ROOT 是 RoboLab 仓库的父目录；可通过环境变量改到大磁盘。
            ROBOLAB_DIR = Path(os.environ.get("ROBOLAB_DIR", WORK_ROOT / "RoboLab")).expanduser()
            # ROBOLAB_DIR 是 RoboLab 仓库目录；如果你已经 clone 好，可用环境变量指向它。

            # ===== 4. 判断当前平台，决定哪些 cell 默认可以执行 =====
            IS_LINUX = platform.system().lower() == "linux"  # Isaac Sim/RoboLab 主流程需要 Ubuntu/Linux。

            # ===== 5. 执行开关：默认只允许轻量 preflight，重型步骤必须手动打开 =====
            EXECUTE_PREFLIGHT = IS_LINUX  # Linux 上允许跑系统检查；Windows 上默认 dry-run。
            EXECUTE_INSTALL = False  # 是否真的 clone/uv sync；默认 False 防止误装大依赖。
            EXECUTE_TESTS = False  # 是否真的跑 pytest；Isaac import 很重，所以默认 False。
            EXECUTE_NO_POLICY_SMOKE = False  # 是否跑无策略仿真 smoke；需要 GPU/Isaac 环境。
            EXECUTE_POLICY_SMOKE = False  # 是否跑 Pi0/Pi05 单任务策略；需要 OpenPI server ready。
            EXECUTE_SUBSET_EVAL = False  # 是否跑小子集策略评测；耗时更长，默认关闭。

            # ===== 6. 4090 保守参数：先保证能跑通，再逐步提高并行度 =====
            NUM_ENVS_4090_SMOKE = 1  # 4090 首次策略 smoke 只开 1 个环境，降低 OOM 风险。
            NUM_ENVS_4090_CAUTIOUS = 2  # 小子集评测的保守并行度；确认显存后再提高。
            NUM_RUNS = 1  # 每个任务先跑 1 次，只验证链路，不做统计结论。
            POLICY_NAME = "pi05"  # RoboLab policy runner 使用的策略名。
            SMOKE_TASK = "BananaInBowlTask"  # 第一条闭环任务，简单、低压力、便于排错。
            # SUBSET_TASKS 覆盖 pick/place、语言组合、空间关系、重定向、堆叠五类能力。
            SUBSET_TASKS = [
                "BananaInBowlTask",  # 语义识别 + 基础 pick/place。
                "RubiksCubeAndBananaTask",  # 多目标 conjunction：同时处理 cube 和 banana。
                "RubiksCubeLeftOfBowlTask",  # 空间关系：判断 left of bowl。
                "ReorientWhiteMugsTask",  # 过程/重定向：把白色杯子转正。
                "Stack3RubiksCubeTask",  # 多步骤堆叠：观察长 horizon 失败模式。
            ]

            # ===== 7. Isaac/Kit 运行环境变量 =====
            OMNI_ENV = {"OMNI_KIT_ACCEPT_EULA": "Y"}  # 非交互运行时显式接受 EULA，避免卡在提示界面。
            ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)  # 确保证据目录存在。

            # ===== 8. 打印当前配置，方便截图/日志留档 =====
            print("Notebook root:", NOTEBOOK_ROOT)  # notebook 当前执行位置。
            print("Artifact dir :", ARTIFACT_DIR)  # 本地证据输出目录。
            print("Work root    :", WORK_ROOT)  # RoboLab 工作区父目录。
            print("RoboLab dir  :", ROBOLAB_DIR)  # RoboLab 仓库目录。
            print("Platform     :", platform.platform())  # OS/内核等平台信息。
            print("Python       :", sys.version.replace("\n", " "))  # 当前 Python 解释器版本。
            """
        ),
        code(
            r"""
            COMMAND_LOG = ARTIFACT_DIR / "command_log.jsonl"

            def _now():
                # 生成带时区的时间戳，方便本地日志和远端日志对齐。
                return _dt.datetime.now().astimezone().isoformat(timespec="seconds")

            def _append_jsonl(path: Path, record: dict):
                # JSONL 适合持续追加；dry-run 和真实执行的命令都会留下证据。
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

            def run(cmd, *, cwd=None, env=None, execute=True, check=False, timeout=None, label=None):
                # 统一的命令执行入口：开关关闭时只记录计划，开关打开时执行并记录证据。
                cwd_path = Path(cwd).expanduser() if cwd else NOTEBOOK_ROOT
                record = {
                    "time": _now(),
                    "label": label,
                    "cwd": str(cwd_path),
                    "cmd": cmd if isinstance(cmd, str) else list(cmd),
                    "execute": bool(execute),
                }
                printable = cmd if isinstance(cmd, str) else " ".join(shlex.quote(str(x)) for x in cmd)
                print(f"\n$ cd {cwd_path}")
                print(f"$ {printable}")
                if not execute:
                    # dry-run 也写入 command_log.jsonl，后续能审计“原计划要跑什么”。
                    record.update({"status": "dry_run", "returncode": None, "stdout": "", "stderr": ""})
                    _append_jsonl(COMMAND_LOG, record)
                    print("[dry-run] command recorded only")
                    return record

                # 合并单条命令需要的环境变量，例如 Isaac/Kit 的 EULA 确认变量。
                run_env = os.environ.copy()
                if env:
                    run_env.update(env)
                start = time.time()
                proc = subprocess.run(
                    cmd,
                    cwd=str(cwd_path),
                    env=run_env,
                    shell=isinstance(cmd, str),
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                )
                elapsed = round(time.time() - start, 3)
                record.update(
                    {
                        "status": "completed",
                        "returncode": proc.returncode,
                        "elapsed_s": elapsed,
                        "stdout": proc.stdout[-20000:],
                        "stderr": proc.stderr[-20000:],
                    }
                )
                _append_jsonl(COMMAND_LOG, record)
                # notebook 里只打印尾部，避免输出过长；更完整的尾部保存在 JSONL 里。
                if proc.stdout:
                    print(proc.stdout[-4000:])
                if proc.stderr:
                    print(proc.stderr[-4000:])
                print("returncode:", proc.returncode, "elapsed_s:", elapsed)
                if check and proc.returncode != 0:
                    raise RuntimeError(f"Command failed: {printable}")
                return record

            def write_status(name: str, data: dict):
                # 状态 JSON 是最终 checklist 的机器可读依据，不只靠人眼看日志。
                path = ARTIFACT_DIR / f"{name}.json"
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                print("wrote", path)
                return path
            """
        ),
        md(
            """
            ## 0.0 论文精讲 0：RoboLab 全局总览

            下面这节来自本目录的 [EXPLAIN_00_global_overview.md](./EXPLAIN_00_global_overview.md)。它把之前从精讲 1 里轻量化掉的“全局观”补回来：先从论文动机、系统架构、任务标注、策略接入、证据口径、4090 边界和后续对比路线讲清楚，再进入后面 1-6 的专项深挖。
            """
        ),
        md_file("EXPLAIN_00_global_overview.md"),
        md(
            """
            ## 0.1 2026-06-19 远端 RTX 4090 实测进展

            本节记录一次已完成的远端 4090 复现推进，证据已同步到本目录的 `remote_logs/`。

            已确认：

            - 远端机器：Ubuntu 22.04.4 LTS，RTX 4090 24GB，NVIDIA driver 580.159.03。
            - `uv sync` 已完成，安装到 Python 3.11 环境；`robolab==0.1.0`、`isaacsim==5.0.0.0`、`isaaclab==2.2.0`、`torch==2.7.0+cu128` 均可导入。
            - 当前 GitHub HEAD：`7d45d74904eade3b578a8eb1f2f9f89bc3d40326`。
            - `assets/scenes/`、`assets/robots/`、核心 `assets/fixtures/` 已按需补齐；完整 RoboLab-120 仍需要继续按任务补全更多 object/material LFS 资产。
            - `BananaInBowlTask` 的 headless smoke 已完成 2 step 并导出 episode log。这里的 `success: False` 是空动作/no-policy 运行的预期结果，不代表策略评测失败。
            - 已扩展到累计 21 个 no-policy 初始化 smoke，覆盖语义、颜色、空间关系、顺序组合、重定向、堆叠等任务属性；这些仍是环境初始化与日志导出验证，不是策略成功率。
            - README 中的 `uv run pytest tests/` 在当前 HEAD 返回 4，因为仓库没有 `tests/` 路径；这应记录为 README 与仓库当前文件面的不一致。
            - `policies/pi0_family/run.py` 是 Pi0/Pi05 评测入口；OpenPI Pi05 `pi05_droid_jointpos` checkpoint 已完成下载与 26 个对象大小校验，policy server 已监听 8000。
            - 已完成真实 Pi05 policy 单任务复现：`BananaInBowlTask` 1 episode，`success=True`，`score=1.0`，`episode_step=178`，平均 policy inference `84.2 ms`。
            """
        ),
        code(
            r"""
            import re
            from textwrap import dedent

            # 这些 JSON summary 来自远端 RTX 4090 实测结果，已同步到本地 remote_logs。
            # notebook 直接读取证据文件，避免依赖聊天记录或过期口头描述。
            REMOTE_LOG_DIR = NOTEBOOK_ROOT / "remote_logs"
            REMOTE_SUMMARY_PATH = REMOTE_LOG_DIR / "remote_4090_repro_summary.json"
            REMOTE_SUBSET3_SUMMARY_PATH = REMOTE_LOG_DIR / "remote_4090_subset3_summary.json"
            REMOTE_POLICY_SUBSET21_SUMMARY_PATH = REMOTE_LOG_DIR / "remote_4090_policy_subset21_summary.json"
            REMOTE_POLICY_SUBSET19_SUMMARY_PATH = REMOTE_LOG_DIR / "remote_4090_policy_subset19_summary.json"
            REMOTE_POLICY_SUBSET10_SUMMARY_PATH = REMOTE_LOG_DIR / "remote_4090_policy_subset10_summary.json"
            # 优先使用最新累计 summary；旧 summary 只作为本地文件不完整时的回退。
            REMOTE_POLICY_SUMMARY_CANDIDATES = [
                REMOTE_POLICY_SUBSET21_SUMMARY_PATH,
                REMOTE_POLICY_SUBSET19_SUMMARY_PATH,
                REMOTE_POLICY_SUBSET10_SUMMARY_PATH,
            ]
            REMOTE_POLICY_SUMMARY_PATH = next(
                (path for path in REMOTE_POLICY_SUMMARY_CANDIDATES if path.exists()),
                REMOTE_POLICY_SUBSET10_SUMMARY_PATH,
            )
            REMOTE_PI05_POLICY_SMOKE_DIR = REMOTE_LOG_DIR / "pi05_policy_smoke_20260620_005711"

            if REMOTE_SUMMARY_PATH.exists():
                # 第一份 summary：安装/导入验证 + BananaInBowlTask 无策略 smoke。
                remote_summary = json.loads(REMOTE_SUMMARY_PATH.read_text(encoding="utf-8"))
                smoke = remote_summary.get("smoke", {})
                install = remote_summary.get("installation", {})
                assets = remote_summary.get("assets", {})
                host = remote_summary.get("host", {})
                # Isaac 日志里可能有 ANSI 颜色控制码，写入 Markdown 表格前先清理。
                clean_success = re.sub(r"\x1b\[[0-9;]*m", "", smoke.get("success_line", ""))
                report = f'''
                ### 远端 4090 证据摘要

                | 项目 | 结果 |
                |---|---|
                | Host | `{host.get('hostname')}` |
                | GPU | `{host.get('gpu')}` |
                | Repo HEAD | `{remote_summary.get('repo_head')}` |
                | uv sync | `{install.get('uv_sync_status')}` |
                | pytest tests/ | return code `{install.get('pytest_rc')}`，当前 HEAD 无 `tests/` 路径 |
                | Scenes assets | `{assets.get('scenes_status')}` / {assets.get('scenes_du')} |
                | Core assets | fixtures `{assets.get('core_assets_status')}` / robots {assets.get('robots_du')} |
                | Smoke task | `{smoke.get('task')}` |
                | Smoke setup/export | setup `{smoke.get('completed_setup')}`，episode export `{smoke.get('exported_episode')}`，traceback `{smoke.get('traceback_present')}` |
                | Smoke result line | `{clean_success}` |

                证据文件目录：`{REMOTE_LOG_DIR}`
                '''
                display(Markdown(dedent(report).strip()) if Markdown else dedent(report).strip())
            else:
                print("remote evidence not found:", REMOTE_SUMMARY_PATH)

            if REMOTE_SUBSET3_SUMMARY_PATH.exists():
                # 第二份 summary：在不接策略服务的情况下验证额外 3 个任务可初始化和导出日志。
                subset_summary = json.loads(REMOTE_SUBSET3_SUMMARY_PATH.read_text(encoding="utf-8"))
                task_rows = "\n".join(
                    f"| `{task}` | env_cfg `{info.get('env_cfg_exists')}` | episode log `{info.get('episode_log_exists')}` |"
                    for task, info in subset_summary.get("outputs", {}).items()
                )
                subset_report = f'''
                ### 三任务 no-policy subset smoke

                | 项目 | 结果 |
                |---|---|
                | Command | `{subset_summary.get('command')}` |
                | Return code | `{subset_summary.get('status_file_rc')}` |
                | Traceback | `{subset_summary.get('traceback_present')}` |
                | Completed setup count | `{subset_summary.get('completed_setup_count')}` |
                | Episodes exported count | `{subset_summary.get('episodes_exported_count')}` |
                | Boundary | {subset_summary.get('policy_boundary')} |

                | Task | Output |
                |---|---|
                {task_rows}

                注意：`output/run_empty_env/episode_results.jsonl` 是累计文件，因此 summary 里会同时包含此前的 `BananaInBowlTask` no-policy smoke。
                '''
                display(Markdown(dedent(subset_report).strip()) if Markdown else dedent(subset_report).strip())
            else:
                print("subset evidence not found:", REMOTE_SUBSET3_SUMMARY_PATH)

            if REMOTE_POLICY_SUMMARY_PATH.exists():
                # 第三份 summary：累计 no-policy 任务 + OpenPI/Pi05 准备状态；优先读取最新的 subset21。
                policy_summary = json.loads(REMOTE_POLICY_SUMMARY_PATH.read_text(encoding="utf-8"))
                no_policy = policy_summary.get("no_policy_smoke", {})
                openpi = policy_summary.get("openpi_policy_readiness", {})
                # 按任务名建立 metadata 索引，用于给 episode 结果补充属性和难度。
                meta_by_task = {
                    row.get("task_name"): row
                    for row in no_policy.get("task_metadata", [])
                    if row.get("task_name")
                }

                def _clean_table_text(value):
                    # Markdown 表格遇到竖线或换行会错列，所以展示前做最小清理。
                    return str(value or "").replace("|", "/").replace("\n", " ")

                rows = []
                for rec in no_policy.get("records", []):
                    # episode_results.jsonl 是累计文件，因此逐条渲染，避免误以为只包含本轮任务。
                    task = rec.get("env_name")
                    meta = meta_by_task.get(task, {})
                    rows.append(
                        "| `{}` | {} | {} | `{}` | {} |".format(
                            task,
                            _clean_table_text(meta.get("attributes") or "-"),
                            _clean_table_text(meta.get("difficulty_label") or "-"),
                            rec.get("success"),
                            _clean_table_text(rec.get("instruction")),
                        )
                    )
                task_rows = "\n".join(rows)
                # 候选任务只有在 episode_results.jsonl 真实新增记录且没有 Python Traceback 时才计入累计数。
                successful_probe_tasks = ", ".join(
                    f"`{task}`" for task in no_policy.get("candidate_probe_successful_tasks", [])
                ) or "-"
                failed_probe_rows = []
                for item in no_policy.get("candidate_probe_failed_tasks", []):
                    failed_probe_rows.append(
                        "| `{}` | `{}` | {} |".format(
                            item.get("task"),
                            item.get("records_added"),
                            _clean_table_text(item.get("main_error") or "-"),
                        )
                    )
                failed_probe_table = "\n".join(failed_probe_rows) or "| - | - | - |"
                evidence_name = Path(policy_summary.get("evidence_package", "")).name
                evidence_path = f"remote_logs/{evidence_name}" if evidence_name else "remote_logs/<missing evidence>"
                policy_record_count = no_policy.get("num_records_cumulative")
                # 只有 OpenPI server 监听 8000 后，才算可以开始真实 policy eval。
                openpi_state = "ready" if openpi.get("server_port_8000_ready") else "downloading / not ready"
                policy_report = f'''
                ### {policy_record_count} 任务 no-policy smoke 与 OpenPI/Pi05 准备状态

                | 项目 | 结果 |
                |---|---|
                | no-policy subset10 return code | `{no_policy.get('subset10_status')}` |
                | no-policy subset_more return code | `{no_policy.get('subset_more_status')}` |
                | no-policy cumulative records | `{no_policy.get('num_records_cumulative')}` |
                | counted candidate probes | {successful_probe_tasks} |
                | OpenPI repo HEAD | `{openpi.get('openpi_head')}` |
                | OpenPI client install | `{openpi.get('openpi_client_install_status')}` |
                | OpenPI uv sync | `{openpi.get('openpi_uv_sync_status')}` |
                | OpenPI import/JAX verify | `{openpi.get('openpi_verify_status')}` |
                | Pi05 checkpoint | `{openpi.get('checkpoint_uri')}` |
                | Pi05 download progress | `{openpi.get('last_progress', {}).get('downloaded')}` / `{openpi.get('last_progress', {}).get('total')}` |
                | Pi05 server port 8000 | `{openpi_state}` |
                | Evidence package | `{evidence_path}` |

                | Task | Attributes | Difficulty | no-policy success | Instruction |
                |---|---|---|---|---|
                {task_rows}

                #### 未计入累计的候选任务

                | Task | records added | 主要失败原因 |
                |---|---:|---|
                {failed_probe_table}

                边界：上表的 `success=False` 来自空动作/no-policy run，只证明场景、任务、日志导出链路可跑；未计入任务主要卡在对象 payload/contact reporter 不完整。真实 Pi05 policy score 已在下一节单独读取与展示。
                '''
                display(Markdown(dedent(policy_report).strip()) if Markdown else dedent(policy_report).strip())
            else:
                print("policy readiness evidence not found:", REMOTE_POLICY_SUMMARY_PATH)
            """
        ),
        code(
            r"""
            # ===== 真实 Pi05 policy smoke 结果 =====
            # 这一段读取 4090 上真实跑过的 OpenPI Pi05 + RoboLab 结果，不再是 no-policy 空动作 smoke。
            PI05_POLICY_SMOKE_SUMMARY_PATH = ARTIFACT_DIR / "pi05_policy_smoke_summary.json"

            if REMOTE_PI05_POLICY_SMOKE_DIR.exists():
                # 1. checkpoint_verify 证明 11.58GiB pi05_droid_jointpos 权重文件完整。
                verify_path = REMOTE_PI05_POLICY_SMOKE_DIR / "pi05_droid_jointpos_download_verify.json"
                verify = json.loads(verify_path.read_text(encoding="utf-8")) if verify_path.exists() else {}

                # 2. server_log 证明 OpenPI websocket server 已加载本地 checkpoint 并监听 8000。
                server_log_path = REMOTE_PI05_POLICY_SMOKE_DIR / "openpi_pi05_server_local.log"
                server_log = server_log_path.read_text(encoding="utf-8", errors="replace") if server_log_path.exists() else ""
                server_ready = "server listening on 0.0.0.0:8000" in server_log
                checkpoint_restored = "Finished restoring checkpoint" in server_log

                # 3. smoke_status 为 RoboLab policy runner 的退出码；0 表示脚本正常完成。
                status_path = REMOTE_PI05_POLICY_SMOKE_DIR / "robolab_pi05_banana_smoke.status"
                smoke_status = status_path.read_text(encoding="utf-8").strip() if status_path.exists() else "missing"

                # 4. episode_results.jsonl 是最关键结果：这里才有真实 policy 的 success/score/timing。
                episode_files = sorted(REMOTE_PI05_POLICY_SMOKE_DIR.glob("pi05_banana_smoke_*/episode_results.jsonl"))
                result_rows = []
                for episode_file in episode_files:
                    for line in episode_file.read_text(encoding="utf-8").splitlines():
                        if line.strip():
                            row = json.loads(line)
                            row["_source"] = str(episode_file.relative_to(REMOTE_PI05_POLICY_SMOKE_DIR))
                            result_rows.append(row)

                # 5. task 内部 event log 解释为什么 episode 在 178 step 结束。
                event_log_files = sorted(REMOTE_PI05_POLICY_SMOKE_DIR.glob("pi05_banana_smoke_*/BananaInBowlTask/log_0_env0.json"))
                event_rows = []
                for event_file in event_log_files:
                    event_data = json.loads(event_file.read_text(encoding="utf-8"))
                    for event in event_data.get("events", []):
                        event_rows.append(
                            {
                                "step": event.get("step"),
                                "name": event.get("name"),
                                "score": event.get("score"),
                                "info": event.get("info"),
                            }
                        )

                summary = {
                    "checkpoint_verify_ok": verify.get("ok"),
                    "checkpoint_objects": verify.get("objects"),
                    "checkpoint_total_gib": verify.get("total_gib"),
                    "server_ready": server_ready,
                    "checkpoint_restored": checkpoint_restored,
                    "smoke_status": smoke_status,
                    "num_episode_records": len(result_rows),
                    "episode_records": result_rows,
                    "event_rows": event_rows,
                    "evidence_dir": str(REMOTE_PI05_POLICY_SMOKE_DIR),
                }
                PI05_POLICY_SMOKE_SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

                if result_rows:
                    first = result_rows[0]
                    timing = first.get("timing", {})
                    metrics = first.get("metrics", {})
                    report = f'''
                    ### Pi05 真实策略 smoke：BananaInBowlTask

                    | 项目 | 结果 |
                    |---|---|
                    | Checkpoint verify | `{verify.get('ok')}`，objects `{verify.get('objects')}`，total `{verify.get('total_gib', 0):.3f}` GiB |
                    | Checkpoint restored by OpenPI | `{checkpoint_restored}` |
                    | OpenPI websocket server | `{server_ready}` |
                    | RoboLab runner exit code | `{smoke_status}` |
                    | Task | `{first.get('task_name')}` |
                    | Policy | `{first.get('policy')}` |
                    | Instruction | {first.get('instruction')} |
                    | Success | `{first.get('success')}` |
                    | Score | `{first.get('score')}` |
                    | Episode step | `{first.get('episode_step')}` |
                    | Sim duration | `{first.get('duration')}` s |
                    | Policy inference avg | `{timing.get('policy_inference_avg_ms')}` ms |
                    | Env step avg | `{timing.get('env_step_avg_ms')}` ms |
                    | Reason | {first.get('reason')} |
                    | Evidence | `{REMOTE_PI05_POLICY_SMOKE_DIR}` |

                    结论：这条记录已经越过“环境 smoke”边界，属于真实 VLA/OpenPI policy 通过 websocket 驱动 RoboLab 的单任务复现证据。
                    它仍然只是 1 个任务、1 个 episode，不能外推为 RoboLab-120 完整论文结果。
                    '''
                    display(Markdown(dedent(report).strip()) if Markdown else dedent(report).strip())

                    if pd:
                        display(pd.DataFrame(result_rows)[[
                            "task_name", "policy", "success", "score", "episode_step", "duration", "reason"
                        ]])
                        display(pd.DataFrame(event_rows))
                    else:
                        display(result_rows)
                        display(event_rows)

                    print("wrote", PI05_POLICY_SMOKE_SUMMARY_PATH)
                else:
                    print("Pi05 policy smoke evidence exists, but no episode_results.jsonl record was parsed.")
            else:
                print("Pi05 policy smoke evidence not found:", REMOTE_PI05_POLICY_SMOKE_DIR)
            """
        ),
        md(
            """
            ## 0.2 论文核心机制：这篇论文到底要测什么

            论文不是只提出一个“能跑仿真”的项目，而是提出一个用高保真仿真分析通用机器人策略的 benchmark。
            读代码前先抓住五个核心问题：

            | 论文概念 | 含义 | 复现时对应要看什么 |
            |---|---|---|
            | 高保真评测环境 | 让真实世界训练的策略在逼真的 Isaac/Omniverse 场景里被评测，避免只在训练同域里刷高分 | USD 场景、对象 payload、材质/相机/灯光、Isaac Lab env 创建是否稳定 |
            | RoboLab-120 | 120 个任务，不是一个 pick-place demo；任务按视觉、过程化、关系三类能力轴拆分 | `task_metadata.json`、每个 `robolab/tasks/benchmark/*.py` 的 `attributes` 和 `subtasks` |
            | 任务无关于机器人/策略 | 任务先定义“目标状态”，运行时再绑定 robot、policy、camera、variation | `create_env(...)` 里把任务名解析成 env config，再给 policy runner 使用 |
            | 细粒度指标 | 不只看最终 success，还看 normalized/subtask score、语言变化、错误事件、轨迹质量 | `Subtask`、event log、`episode_results.jsonl`、trajectory metrics |
            | 敏感性分析 | 通过光照、相机、背景、物体位姿扰动观察策略鲁棒性 | `policies/pi0_family/run_*_variation.py` 和 `create_env(..., events=...)` |

            所以当前 notebook 里的 no-policy smoke 只能说明“环境和任务链路可启动、可导出日志”，还不能回答论文里的策略泛化问题。
            真正对齐论文，需要等 Pi05/OpenPI server ready 后跑 policy episodes，再用同一套 task metadata、subtask/event、trajectory metric 做分析。

            参考源：arXiv 论文 `https://arxiv.org/html/2604.09860`，尤其是 Abstract、III RoboLab、III-B Benchmark Design、III-C Metrics、III-D Sensitivity Analysis。
            """
        ),
        md(
            """
            ## 0.3 核心源码地图：论文概念如何落到代码

            下面这一节是读 RoboLab 源码的主线。不要从 100 多个 task 文件平铺看起，先按“入口 -> 环境 -> 任务定义 -> 条件/评分 -> 导出 -> policy”这条链路读。
            """
        ),
        code(
            r"""
            # ===== 论文概念到源码文件的阅读地图 =====
            # 这个表不是运行 RoboLab，而是把“论文里讲的机制”映射到“应该读哪些核心代码”。
            core_code_map = [
                {
                    "论文机制": "RoboLab-120 任务集合与能力轴",
                    "核心文件": "robolab/tasks/_metadata/task_metadata.json",
                    "关键字段/函数": "task_name, scene, instruction, attributes, num_subtasks, difficulty_label",
                    "怎么理解": "这是任务索引表；论文里的 visual/procedural/relational 和 difficulty 在这里落成可统计字段。",
                },
                {
                    "论文机制": "单个任务如何定义目标状态",
                    "核心文件": "robolab/tasks/benchmark/banana_in_bowl_task.py",
                    "关键字段/函数": "contact_object_list, scene, terminations, instruction, attributes, subtasks",
                    "怎么理解": "一个 task 文件不是策略代码，而是目标状态声明：用哪个场景、哪些对象需要 contact sensor、成功条件是什么、拆成哪些 subtask。",
                },
                {
                    "论文机制": "从任务名创建仿真环境",
                    "核心文件": "robolab/core/environments/runtime.py",
                    "关键字段/函数": "create_env, parse_env_cfg, resolve_instruction, merge_events_cfg, gym.make",
                    "怎么理解": "这里把 task name 变成 Isaac Lab env；语言版本、扰动事件、policy 名称都在这个阶段绑定进去。",
                },
                {
                    "论文机制": "评测 episode 的生命周期",
                    "核心文件": "robolab/core/environments/env.py",
                    "关键字段/函数": "RobolabEnv.step, _reset_idx, all_terminated, reset_eval_state",
                    "怎么理解": "评测时环境不应自动重置并丢掉结果；RoboLab 把已终止 env 冻结，记录成功/失败和终止 step，再导出 episode。",
                },
                {
                    "论文机制": "subtask/event 评分",
                    "核心文件": "robolab/core/task/conditionals.py + robolab/core/task/subtask.py",
                    "关键字段/函数": "pick_and_place, object_in_container, object_grabbed, Subtask(score/logical/K)",
                    "怎么理解": "论文说不只看二值 success；这里把任务拆成条件序列，支持 all/any/choose 和子分数。",
                },
                {
                    "论文机制": "no-policy 环境 smoke",
                    "核心文件": "examples/run_empty.py",
                    "关键字段/函数": "auto_register_droid_envs, get_envs, create_env, run_empty_episode, update_experiment_results",
                    "怎么理解": "这是当前 4090 已跑通的主入口：它验证环境能创建和导出日志，但没有调用 VLA policy。",
                },
                {
                    "论文机制": "真实 policy 评测入口",
                    "核心文件": "policies/pi0_family/run.py + robolab/eval/runner.py",
                    "关键字段/函数": "add_common_eval_args, run_evaluation, client_factory, run_episode, summarize_run",
                    "怎么理解": "Pi0/Pi05 入口只负责接 policy server；通用循环在 runner.py 里，按 task/run/env_id 写 episode 结果。",
                },
                {
                    "论文机制": "Pi05 观测打包与动作解包",
                    "核心文件": "policies/pi0_family/client.py",
                    "关键字段/函数": "_extract_observation, _pack_request, _query_server, _unpack_response, open_loop_horizon",
                    "怎么理解": "这里把 RoboLab 的相机图像、关节状态、夹爪状态和语言指令转成 OpenPI server 请求，再把 action chunk 还给环境。",
                },
                {
                    "论文机制": "结果汇总和错误分析",
                    "核心文件": "robolab/core/logging/results.py",
                    "关键字段/函数": "init_experiment, update_experiment_results, summarize_experiment_results, summarize_error_reasons",
                    "怎么理解": "episode_results.jsonl 的写入和汇总在这里；后续按任务、能力轴、错误原因统计都依赖它。",
                },
                {
                    "论文机制": "轨迹质量指标",
                    "核心文件": "robolab/core/metrics/trajectory_metrics.py",
                    "关键字段/函数": "compute_sparc, compute_ee_path_length, compute_*_isj",
                    "怎么理解": "论文里的 motion quality/trajectory metric 在这里落地；没有 policy action 时这些指标没有论文意义。",
                },
            ]

            if pd:
                display(pd.DataFrame(core_code_map))
            else:
                display(core_code_map)

            # 写出机器可读的源码阅读地图，作为 notebook 已补足核心代码讲解的证据。
            core_map_path = ARTIFACT_DIR / "core_code_reading_map.json"
            core_map_path.write_text(json.dumps(core_code_map, ensure_ascii=False, indent=2), encoding="utf-8")
            print("wrote", core_map_path)
            """
        ),
        md(
            """
            ## 0.4 一次 no-policy smoke 的真实调用链

            当前已经在 4090 上跑通的 21 个任务，走的是下面这条链路：

            ```text
            examples/run_empty.py
              -> AppLauncher 启动 Isaac/Kit
              -> auto_register_droid_envs() 注册 RoboLab benchmark tasks
              -> get_envs(task=...) 把任务名筛出来
              -> create_env(task_env, device, num_envs, use_fabric)
              -> parse_env_cfg + gym.make(...) 创建 Isaac Lab 环境
              -> run_empty_episode(...) 执行空动作 steps
              -> get_all_env_events(...) 抓取 event/subtask 记录
              -> end_episode(...) 导出 HDF5 / logs
              -> update_experiment_results(...) 追加 episode_results.jsonl
            ```

            这条链路证明三件事：

            - task 注册和 env config 能解析；
            - Isaac stage、robot、scene、contact sensors 至少在已计入任务上能初始化；
            - episode 结果和日志能落盘。

            它没有证明两件事：

            - policy server 已经产生动作；
            - 模型在视觉、关系、过程化任务上有成功率。
            """
        ),
        md(
            """
            ## 0.5 核心代码逐段讲解

            ### 入口层：`examples/run_empty.py`

            这个文件是环境烟测入口。它先用 `AppLauncher` 启动 Isaac Sim/Isaac Lab，再调用 `auto_register_droid_envs()` 注册任务。
            如果传了 `--task`，`get_envs(task=args_cli.task)` 只选指定任务；没有传 task/tag 时会取默认任务集合。
            对每个任务，它调用 `create_env(...)` 得到 `env` 和 `env_cfg`，再用 `run_empty_episode(...)` 执行空动作。
            最后它把每个 episode 的 `success`、`instruction`、可选 `score/reason` 写入 `episode_results.jsonl`。

            记忆方式：`run_empty.py = 启动 Isaac + 找任务 + 建环境 + 空动作 + 写结果`。

            ### 环境创建层：`robolab/core/environments/runtime.py`

            `create_env` 是任务名进入 Isaac 的关键门口。
            它先清空 stage，再调用 `parse_env_cfg(scene, ...)` 解析 task/env config。
            如果任务有多个语言版本，`resolve_instruction(...)` 会根据 `instruction_type` 选择 default/vague/specific。
            如果要做 camera/light/background 扰动，`merge_events_cfg(...)` 会把 variation event 合并到 env config。
            最后 `gym.make(scene, cfg=env_cfg).unwrapped` 创建真正的 Isaac Lab env，并把 `env_cfg.json` 写到输出目录。

            记忆方式：`create_env = task name -> env_cfg -> Isaac Lab env`。

            ### 任务定义层：`robolab/tasks/benchmark/banana_in_bowl_task.py`

            一个任务类通常包含五块：

            - `contact_object_list`：哪些对象需要 contact sensor；
            - `scene = import_scene(...)`：加载哪个 USD 场景；
            - `terminations`：成功/超时等终止条件；
            - `instruction`：同一任务的多种语言说法；
            - `subtasks`：用于 graded score 和错误分析的子任务结构。

            以 BananaInBowl 为例，最终成功条件是 `object_in_container(object="banana", container="bowl", ...)`。
            subtask 使用 `pick_and_place(object=["banana"], container="bowl", score=1.0)`，也就是“先抓到 banana，再确认 banana 进 bowl”。

            记忆方式：`Task = 场景 + 指令 + 成功条件 + 子任务评分`。

            ### 条件/评分层：`conditionals.py` 与 `subtask.py`

            论文强调不能只看二值 success，所以 RoboLab 把任务拆成 subtask 和 event。
            `pick_and_place(...)` 是 composite condition，会展开成每个目标对象的一组条件，例如 `object_grabbed` 和 `object_in_container`。
            `Subtask` 保存条件组、`logical` 模式和 `score`：`all` 表示全部完成，`any` 表示任一完成，`choose` 表示完成 K 个即可。
            这就是 normalized/subtask score 能算出来的原因。

            记忆方式：`conditionals = 判断事实；Subtask = 给事实排序和打分`。

            ### 评测 env 层：`RobolabEnv`

            RoboLab 继承 Isaac Lab 的 `ManagerBasedRLEnv`，但评测逻辑和训练环境不同。
            在 `_reset_idx` 里，已终止 env 不会立刻自动 reset，而是标记为 frozen，记录 success/truncated 和终止 step，并触发 recorder 导出。
            `step` 会把 frozen env 的 action 置零，避免已结束 episode 被后续动作污染。

            记忆方式：`RobolabEnv = 为评测冻结终局、保护记录`。

            ### policy 层：`policies/pi0_family/run.py` 与 `client.py`

            `run.py` 负责解析 `--policy pi05`、`--remote-host`、`--remote-port`、`--num-envs`、`--enable-subtask` 等参数。
            真正的通用评测循环在 `robolab/eval/runner.py`：创建 env，创建 policy client，调用 `run_episode`，最后 `summarize_run`。
            `Pi0DroidJointposClient` 把 RoboLab observation 转成 OpenPI 请求：外部相机图、腕部相机图、关节位置、夹爪位置和语言 prompt。
            server 返回 action chunk 后，client 按 `open_loop_horizon` 执行一段动作，再请求下一段。

            记忆方式：`policy runner = RoboLab 环境循环；client = 观测/动作协议适配器`。

            ### 指标层：`results.py` 与 `trajectory_metrics.py`

            `results.py` 负责写入和汇总 `episode_results.jsonl`，还能统计错误原因，例如 wrong object、object bumped、target dropped。
            `trajectory_metrics.py` 计算 EE path length、SPARC、ISJ 等运动质量指标。
            这些指标只有在真实 policy 产生动作后才有意义；no-policy 的空动作 smoke 不应拿来和论文里的 policy 表格比较。

            记忆方式：`results = 成败和错误原因；metrics = 动作轨迹质量`。
            """
        ),
        md(
            """
            ## 0.6 交流过程中的核心问题与决策记录

            这一节不是聊天流水账，而是复现过程中反复校准过的“判断口径”。后面看结果时要按这些边界理解。

            | 问题 | 结论 | 对复现实验的影响 |
            |---|---|---|
            | 4090 能不能跑 RoboLab？ | 能跑，但 24GB VRAM 只能保守跑单任务或小子集。复杂任务运行时显存接近 `22.5GB / 24GB`。 | 首轮固定 `--num-envs 1`，不要直接拉高并行数。 |
            | 为什么下载和运行慢？ | 慢点主要来自三类：Git LFS/资产、OpenPI checkpoint、Isaac Sim 首次加载与视频/HDF5 写盘。 | “看起来卡住”不等于失败，要看日志、文件增长、GPU 显存和 episode JSON。 |
            | 能不能加速下载？ | 可以按任务补资产、保留缓存、复用 OpenPI server、避免重复拉 LFS；但完整资产和模型仍然是大文件。 | 当前采用“先跑通必要资产，再逐步扩展任务”的路线。 |
            | `pi` 原来装过，和这次下载的 pi05 有什么区别？ | RoboChallenge 里的 pi 是另一套 benchmark/接口语境下的策略或环境；这次用的是 OpenPI `pi05_droid_jointpos` checkpoint，经 RoboLab `policies/pi0_family/run.py` 调用。 | 公平对比前必须统一 observation/action 协议、任务、相机、成功条件，不能直接把两个仓库的结果混算。 |
            | 视频保存在哪里？ | 远端在 RoboLab `output/<run_id>/`，本地同步到 `remote_outputs/<run_id>/`。每个任务一般有 policy camera 主视频和 viewport 视频。 | 报告里必须给出远端原始路径、本地同步路径和 `ffprobe` 验证信息。 |
            | 为什么有些任务没复现成功？ | 要区分两种失败：环境/资产失败和策略失败。`BlockStackingSpecifiedOrderTask` 是 contact sensor/asset 初始化失败；复杂三任务中的两个失败是策略跑满步数未完成。 | 环境失败不计入策略成功率；策略失败才用于能力分析。 |
            | 120 个任务要不要一次性全跑？ | 不建议先盲跑完整 RoboLab-120。官方量级约几十 GPU 小时，且当前 checkout 还有任务资产完整性问题。 | 先按能力轴抽样，确认资产、成功条件和视频导出稳定，再扩展到 120。 |
            | 代码加中文注释会不会影响运行？ | 注释不影响逻辑，但直接改官方仓库会增加 merge/复现噪声。 | 更稳妥做法是保留原 repo，同时维护 `roboplay_robolab_cn` 注释/讲解版或 notebook 精讲版。 |
            | 所有“看进度”的窗口应该在哪？ | 终端、Cursor、VNC 都应在 4090 上看；本机只做同步和整理。 | 后续不要再启动本机 terminal 作为可视化进度窗口。 |
            | GitHub 仓库能不能推？ | `dictmap/roboplay` 的 SSH key 已在 4090 上测试通过。 | 后续可把注释版代码和 notebook 推到该仓库，但推送前要确认不含大模型权重和无关输出。 |

            记忆方式：先分清四件事：`环境是否可启动`、`策略是否接上`、`任务是否成功`、`证据是否可回放`。这四件事缺一不可，但不能互相替代。
            """
        ),
        md(
            """
            ## 0.7 论文精讲：真实场景到模拟场景的评估

            下面这节来自本目录的 [EXPLAIN_01_real_to_sim_eval.md](./EXPLAIN_01_real_to_sim_eval.md)，已经把论文里“真实场景到模拟场景评估”的说法翻译成代码实现链路。重点看输入、输出和边界：RoboLab 主流程不是逐场景重建真实视频，而是用资产库、USD 场景、程序化布局、任务谓词和扰动矩阵快速生成可交互、可评分的仿真评估场景。
            """
        ),
        md_file("EXPLAIN_01_real_to_sim_eval.md"),
        md(
            """
            ## 0.8 论文精讲：场景、任务和环境生成

            下面这节来自本目录的 [EXPLAIN_02_scene_task_env_generation.md](./EXPLAIN_02_scene_task_env_generation.md)，对应论文里的三步：先定位/定向物体生成场景，再把目标状态写成语言任务，最后选择机器人、策略、摄像头、光照、背景来实例化环境。
            """
        ),
        md_file("EXPLAIN_02_scene_task_env_generation.md"),
        md(
            """
            ## 0.9 论文精讲：扩展任务生成、验证和自动修复

            下面这节来自本目录的 [EXPLAIN_03_task_generation_validation.md](./EXPLAIN_03_task_generation_validation.md)，对应论文里的 TaskGen 闭环：先给 LLM 场景对象、能力轴、任务示例和谓词库，让它生成 Task Python 代码；再做语法、资产、容器尺寸等验证；失败后把原始提示、无效输出和错误信息重新打包给 LLM 修复。
            """
        ),
        md_file("EXPLAIN_03_task_generation_validation.md"),
        code(
            r"""
            # ===== 精讲3：TaskGen 轻量验证测试 =====
            # 这组测试不启动 Isaac Sim，只验证论文 TaskGen 闭环里的前置检查逻辑：
            # 1. Python 代码语法是否有效；
            # 2. 任务引用的对象是否存在于场景中；
            # 3. 是否误用了禁用对象；
            # 4. 容器任务里目标物体是否能放进容器，并留出 margin；
            # 5. 失败时是否能构造包含 Q / invalid output / E 的修复提示。

            def validate_python_syntax(code_text: str) -> list[str]:
                '''检查 LLM 生成的任务文件是否至少是合法 Python 代码。'''
                try:
                    compile(code_text, "generated_task.py", "exec")
                    return []
                except SyntaxError as exc:
                    return [f"SyntaxError: {exc.msg} at line {exc.lineno}"]


            def validate_objects(task_objects, scene_objects, disabled_objects):
                '''检查任务中引用的对象是否存在于场景中，并且不在禁用集合里。'''
                errors = []
                missing = sorted(set(task_objects) - set(scene_objects))
                disabled = sorted(set(task_objects) & set(disabled_objects))
                if missing:
                    errors.append(f"Objects not found in scene: {missing}")
                if disabled:
                    errors.append(f"Objects are disabled for task generation: {disabled}")
                return errors


            def validate_container_fit(objects, container, dims, margin=0.02):
                '''保守检查容器任务是否物理可行：目标物体平面尺寸要小于容器可用开口。'''
                errors = []
                if container not in dims:
                    return [f"Container not found in dims: {container}"]
                cx, cy, _ = dims[container]
                usable_x = cx - 2 * margin
                usable_y = cy - 2 * margin
                for obj in objects:
                    if obj not in dims:
                        errors.append(f"Object dim missing: {obj}")
                        continue
                    ox, oy, _ = dims[obj]
                    # 允许物体在桌面平面旋转，所以短边对短边、长边对长边。
                    obj_short, obj_long = sorted([ox, oy])
                    box_short, box_long = sorted([usable_x, usable_y])
                    if obj_short > box_short or obj_long > box_long:
                        errors.append(
                            f"{obj} ({ox:.2f}x{oy:.2f}) does not fit into {container} "
                            f"usable opening ({usable_x:.2f}x{usable_y:.2f}) with margin={margin}"
                        )
                return errors


            def build_repair_prompt(original_prompt, invalid_output, errors):
                '''把验证失败信息整理成给 LLM 的修复提示，对应论文里的 Q + invalid output + E。'''
                return "\n".join(
                    [
                        "Original prompt Q:",
                        original_prompt.strip(),
                        "",
                        "Invalid output:",
                        invalid_output.strip(),
                        "",
                        "Validation errors E:",
                        *[f"{idx + 1}. {err}" for idx, err in enumerate(errors)],
                        "",
                        "Please revise the RoboLab task. Return one complete Python task file only.",
                    ]
                )


            VALID_CODE = "from dataclasses import dataclass\n@dataclass\nclass DummyTask:\n    pass\n"
            BAD_CODE = "def broken_task(\n    return 1\n"

            SCENE_OBJECTS = {
                "banana",
                "bowl",
                "table",
                "grey_bin",
                "mug",
                "rubiks_cube",
                "knife",
                "large_box",
                "small_bowl",
            }
            DISABLED_OBJECTS = {"knife"}
            DIMS = {
                "banana": (0.18, 0.04, 0.04),
                "bowl": (0.24, 0.24, 0.11),
                "grey_bin": (0.36, 0.28, 0.16),
                "mug": (0.08, 0.08, 0.10),
                "large_box": (0.30, 0.22, 0.12),
                "small_bowl": (0.18, 0.18, 0.08),
            }

            taskgen_tests = []
            taskgen_tests.append(
                (
                    "valid_spec_passes",
                    validate_python_syntax(VALID_CODE) == []
                    and validate_objects(["banana", "bowl"], SCENE_OBJECTS, DISABLED_OBJECTS) == []
                    and validate_container_fit(["banana"], "bowl", DIMS) == [],
                )
            )
            taskgen_tests.append(
                ("syntax_error_fails", any("SyntaxError" in err for err in validate_python_syntax(BAD_CODE)))
            )
            taskgen_tests.append(
                ("missing_object_fails", any("apple" in err for err in validate_objects(["apple"], SCENE_OBJECTS, DISABLED_OBJECTS)))
            )
            taskgen_tests.append(
                ("disabled_object_fails", any("knife" in err for err in validate_objects(["knife"], SCENE_OBJECTS, DISABLED_OBJECTS)))
            )
            taskgen_tests.append(
                ("container_too_small_fails", any("does not fit" in err for err in validate_container_fit(["large_box"], "small_bowl", DIMS)))
            )

            repair_prompt = build_repair_prompt(
                "Generate a RoboLab sorting task.",
                BAD_CODE,
                validate_python_syntax(BAD_CODE),
            )
            taskgen_tests.append(
                (
                    "repair_prompt_contains_context",
                    all(
                        required in repair_prompt
                        for required in ["Original prompt Q", "Invalid output", "Validation errors E", "SyntaxError"]
                    ),
                )
            )

            for test_name, ok in taskgen_tests:
                print(f"{test_name}: {'PASS' if ok else 'FAIL'}")

            assert all(ok for _, ok in taskgen_tests), taskgen_tests
            write_status(
                "taskgen_lightweight_validation_tests",
                {
                    "all_passed": all(ok for _, ok in taskgen_tests),
                    "tests": [{"name": name, "passed": ok} for name, ok in taskgen_tests],
                    "boundary": "This is a lightweight pre-Isaac validation test; it does not replace full simulation smoke.",
                },
            )
            """
        ),
        md(
            """
            ## 0.10 论文精讲：能力轴、任务属性、子任务和难度分数

            下面这节来自本目录的 [EXPLAIN_04_competency_axes_difficulty.md](./EXPLAIN_04_competency_axes_difficulty.md)，对应论文 III-B Benchmark Design：visual / procedural / relational 三条能力轴、多标签任务属性、subtask 并行事件，以及 `difficulty_score = num_subtasks + max(w)` 的难度分数。
            """
        ),
        md_file("EXPLAIN_04_competency_axes_difficulty.md"),
        code(
            r"""
            # ===== 精讲4：能力轴和难度分数轻量验证 =====
            # 这组测试复刻 RoboLab 源码中的核心计算：
            # difficulty_score = num_subtasks + max(skill_weight(attributes))
            # label: simple <= 2, moderate <= 4, complex > 4

            SKILL_WEIGHTS_LIGHT = {
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
            CATEGORY_MAP_LIGHT = {
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

            def difficulty_score_light(num_subtasks: int, attributes: list[str]):
                non_difficulty_attrs = [a for a in attributes if a not in {"simple", "moderate", "complex"}]
                hardest_weight = max((SKILL_WEIGHTS_LIGHT.get(attr, 0) for attr in non_difficulty_attrs), default=0)
                score = num_subtasks + hardest_weight
                if score <= 2:
                    label = "simple"
                elif score <= 4:
                    label = "moderate"
                else:
                    label = "complex"
                return score, label

            def capability_axes_light(attributes: list[str]):
                return sorted({CATEGORY_MAP_LIGHT[attr] for attr in attributes if attr in CATEGORY_MAP_LIGHT})

            # num_subtasks 这里按 subtask_utils.count_subtasks 的直觉复刻：
            # logical=all 计全部对象组，logical=any 计 1，logical=choose 计 K。
            benchmark_examples = [
                {
                    "task": "BananaInBowlTask",
                    "attributes": ["semantics"],
                    "num_subtasks": 1,
                    "expected_axes": ["visual"],
                    "expected_score": 1,
                    "expected_label": "simple",
                },
                {
                    "task": "RubiksCubeLeftOfBowlTask",
                    "attributes": ["spatial"],
                    "num_subtasks": 1,
                    "expected_axes": ["relational"],
                    "expected_score": 2,
                    "expected_label": "simple",
                },
                {
                    "task": "RedItemsInBinTask",
                    "attributes": ["color", "sorting"],
                    "num_subtasks": 2,
                    "expected_axes": ["procedural", "visual"],
                    "expected_score": 4,
                    "expected_label": "moderate",
                },
                {
                    "task": "Stack3RubiksCubeTask",
                    "attributes": ["stacking"],
                    "num_subtasks": 2,
                    "expected_axes": ["procedural"],
                    "expected_score": 4,
                    "expected_label": "moderate",
                },
                {
                    "task": "LongReorientationExample",
                    "attributes": ["reorientation"],
                    "num_subtasks": 3,
                    "expected_axes": ["procedural"],
                    "expected_score": 6,
                    "expected_label": "complex",
                },
            ]

            competency_tests = []
            rows = []
            for example in benchmark_examples:
                score, label = difficulty_score_light(example["num_subtasks"], example["attributes"])
                axes = capability_axes_light(example["attributes"])
                ok = (
                    score == example["expected_score"]
                    and label == example["expected_label"]
                    and axes == example["expected_axes"]
                )
                competency_tests.append((example["task"], ok))
                rows.append(
                    {
                        "task": example["task"],
                        "attributes": example["attributes"],
                        "axes": axes,
                        "num_subtasks": example["num_subtasks"],
                        "score": score,
                        "label": label,
                        "passed": ok,
                    }
                )

            for row in rows:
                print(
                    f"{row['task']}: axes={row['axes']} "
                    f"num_subtasks={row['num_subtasks']} score={row['score']} label={row['label']} "
                    f"{'PASS' if row['passed'] else 'FAIL'}"
                )

            assert all(ok for _, ok in competency_tests), competency_tests
            write_status(
                "competency_difficulty_lightweight_tests",
                {
                    "all_passed": all(ok for _, ok in competency_tests),
                    "rows": rows,
                    "boundary": "This validates the metadata/difficulty formula; it does not measure policy success probability.",
                },
            )
            """
        ),
        md(
            """
            ## 0.11 论文精讲：SPARC 轨迹平滑度指标

            下面这节来自本目录的 [EXPLAIN_05_sparc_trajectory_metric.md](./EXPLAIN_05_sparc_trajectory_metric.md)，对应论文 III-C Trajectory Metrics：SPARC 用末端执行器速度谱的弧长衡量动作平滑度，值越接近 0 越平滑，越负表示速度频谱越复杂、动作越抖。
            """
        ),
        md_file("EXPLAIN_05_sparc_trajectory_metric.md"),
        code(
            r"""
            # ===== 精讲5：SPARC 轻量验证 =====
            # 这组测试复刻 RoboLab trajectory_metrics.py::compute_sparc 的核心逻辑：
            # 1. 平滑速度曲线的 SPARC 应该更接近 0；
            # 2. 抖动速度曲线包含更多高频成分，SPARC 应该更负；
            # 3. 静止轨迹通过 motion gate 返回 NaN，避免把“没动”误判成“很平滑”。

            import math
            import numpy as np

            def compute_sparc_light(
                speed,
                dt,
                padlevel=4,
                fc=10.0,
                amplitude_threshold=0.05,
                min_speed=1e-6,
            ):
                speed = np.asarray(speed, dtype=np.float64)
                if len(speed) < 2 or np.max(np.abs(speed)) < min_speed:
                    return float("nan")

                n_samples = len(speed)
                nfft = int(2 ** np.ceil(np.log2(n_samples)) * padlevel)
                speed_fft = np.fft.rfft(speed, n=nfft)
                freq = np.fft.rfftfreq(nfft, d=dt)

                magnitude = np.abs(speed_fft)
                magnitude = magnitude / magnitude.max() if magnitude.max() > 0 else magnitude

                above_threshold = magnitude >= amplitude_threshold
                if np.any(above_threshold):
                    last_idx = np.max(np.where(above_threshold)[0])
                    fc_adaptive = min(freq[last_idx], fc)
                else:
                    fc_adaptive = fc

                if fc_adaptive <= 0:
                    return float("nan")

                freq_mask = freq <= fc_adaptive
                freq_sel = freq[freq_mask]
                magnitude_sel = magnitude[freq_mask]
                if len(freq_sel) < 2:
                    return 0.0

                d_magnitude = np.diff(magnitude_sel)
                d_freq = np.diff(freq_sel)
                arc_length_elements = np.sqrt((d_freq / fc_adaptive) ** 2 + d_magnitude**2)
                return -float(np.sum(arc_length_elements))

            dt = 1.0 / 100.0
            t = np.arange(0.0, 2.0, dt)

            # 平滑速度：单个低频正弦起伏，频谱集中。
            smooth_speed = 0.5 + 0.2 * np.sin(2 * np.pi * 0.5 * t)

            # 抖动速度：在同样低频趋势上叠加明显高频振荡，频谱更长更复杂。
            jerky_speed = smooth_speed + 0.08 * np.sin(2 * np.pi * 8.0 * t)

            # 静止速度：源码应通过 motion gate 返回 NaN。
            stationary_speed = np.zeros_like(t)

            smooth_sparc = compute_sparc_light(smooth_speed, dt)
            jerky_sparc = compute_sparc_light(jerky_speed, dt)
            stationary_sparc = compute_sparc_light(stationary_speed, dt)

            sparc_tests = [
                ("smooth_is_closer_to_zero", smooth_sparc > jerky_sparc),
                ("jerky_is_more_negative", jerky_sparc < smooth_sparc),
                ("stationary_returns_nan", math.isnan(stationary_sparc)),
            ]

            print(f"smooth_sparc={smooth_sparc:.4f}")
            print(f"jerky_sparc={jerky_sparc:.4f}")
            print(f"stationary_sparc={stationary_sparc}")
            for name, ok in sparc_tests:
                print(f"{name}: {'PASS' if ok else 'FAIL'}")

            assert all(ok for _, ok in sparc_tests), sparc_tests
            write_status(
                "sparc_lightweight_tests",
                {
                    "all_passed": all(ok for _, ok in sparc_tests),
                    "smooth_sparc": smooth_sparc,
                    "jerky_sparc": jerky_sparc,
                    "stationary_sparc_is_nan": math.isnan(stationary_sparc),
                    "tests": [{"name": name, "passed": ok} for name, ok in sparc_tests],
                    "boundary": "This validates SPARC direction and motion gate on synthetic speed profiles; real runs should compute metrics from HDF5.",
                },
            )
            """
        ),
        md(
            """
            ## 0.12 论文精讲：MNPE 敏感性分析

            下面这节来自本目录的 [EXPLAIN_06_mnpe_sensitivity_analysis.md](./EXPLAIN_06_mnpe_sensitivity_analysis.md)，对应论文 III-D Sensitivity Analysis 和 Appendix B：MNPE 用 rollout 后的扰动评测数据学习 `p(theta | x)`，也就是“给定成功/失败结果，哪些相机、光照、材质、物体位姿参数最可能导致这个结果”。
            """
        ),
        md_file("EXPLAIN_06_mnpe_sensitivity_analysis.md"),
        code(
            r"""
            # ===== 精讲6：MNPE 轻量验证 =====
            # 这个测试不依赖 sbi，也不假装替代真正的 MNPE。
            # 它只验证论文里最核心的 posterior 直觉：
            #   prior: camera_offset 在 [0, 1] 上均匀采样；
            #   likelihood: camera_offset 越大，success probability 越低；
            #   posterior p(theta | success=1) 应该更偏向小 camera_offset。

            import numpy as np

            rng = np.random.default_rng(260409860)
            n = 20000

            # theta 的两个维度：一个连续扰动，一个离散光照类别。
            camera_offset = rng.uniform(0.0, 1.0, size=n)
            lighting_category = rng.integers(0, 3, size=n)  # 0=dim, 1=normal, 2=bright
            lighting_bonus = np.array([-1.0, 1.2, 0.0])[lighting_category]

            def sigmoid(z):
                return 1.0 / (1.0 + np.exp(-z))

            # 合成一个“策略对相机偏移敏感”的世界：
            # 相机越偏离参考位姿，成功概率越低；正常光照成功概率更高。
            success_likelihood = sigmoid(2.0 - 5.0 * camera_offset + lighting_bonus)
            posterior_weights = success_likelihood / success_likelihood.sum()

            def weighted_quantile(values, quantiles, weights):
                order = np.argsort(values)
                sorted_values = values[order]
                sorted_weights = weights[order]
                cdf = np.cumsum(sorted_weights)
                cdf = cdf / cdf[-1]
                return np.interp(quantiles, cdf, sorted_values)

            prior_camera_mean = float(camera_offset.mean())
            posterior_camera_mean = float(np.sum(camera_offset * posterior_weights))
            uniform_weights = np.full(n, 1.0 / n)
            prior_camera_ci = weighted_quantile(
                camera_offset,
                np.array([0.025, 0.975]),
                uniform_weights,
            ).tolist()
            posterior_camera_ci = weighted_quantile(
                camera_offset,
                np.array([0.025, 0.975]),
                posterior_weights,
            ).tolist()

            prior_lighting_probs = np.bincount(lighting_category, minlength=3) / n
            posterior_lighting_probs = np.array([
                posterior_weights[lighting_category == i].sum()
                for i in range(3)
            ])

            # 对照组：如果 success 和 camera_offset 无关，posterior 应该基本等于 prior。
            flat_likelihood = np.full(n, 0.45)
            flat_weights = flat_likelihood / flat_likelihood.sum()
            flat_camera_mean = float(np.sum(camera_offset * flat_weights))
            flat_camera_ci = weighted_quantile(
                camera_offset,
                np.array([0.025, 0.975]),
                flat_weights,
            ).tolist()

            mnpe_tests = [
                ("success_posterior_moves_camera_toward_reference", posterior_camera_mean < prior_camera_mean - 0.12),
                ("success_posterior_has_lower_upper_ci", posterior_camera_ci[1] < prior_camera_ci[1] - 0.05),
                ("normal_lighting_more_likely_given_success", posterior_lighting_probs[1] > prior_lighting_probs[1] + 0.12),
                ("uninformative_likelihood_keeps_prior_mean", abs(flat_camera_mean - prior_camera_mean) < 1e-12),
                ("uninformative_likelihood_keeps_prior_ci", np.max(np.abs(np.array(flat_camera_ci) - np.array(prior_camera_ci))) < 1e-12),
            ]

            print(f"prior_camera_mean={prior_camera_mean:.3f}")
            print(f"posterior_camera_mean_given_success={posterior_camera_mean:.3f}")
            print(f"prior_camera_95ci={[round(x, 3) for x in prior_camera_ci]}")
            print(f"posterior_camera_95ci_given_success={[round(x, 3) for x in posterior_camera_ci]}")
            print(f"prior_lighting_probs={[round(float(x), 3) for x in prior_lighting_probs]}")
            print(f"posterior_lighting_probs_given_success={[round(float(x), 3) for x in posterior_lighting_probs]}")
            for name, ok in mnpe_tests:
                print(f"{name}: {'PASS' if ok else 'FAIL'}")

            assert all(ok for _, ok in mnpe_tests), mnpe_tests
            write_status(
                "mnpe_lightweight_tests",
                {
                    "all_passed": all(ok for _, ok in mnpe_tests),
                    "prior_camera_mean": prior_camera_mean,
                    "posterior_camera_mean_given_success": posterior_camera_mean,
                    "prior_camera_95ci": prior_camera_ci,
                    "posterior_camera_95ci_given_success": posterior_camera_ci,
                    "prior_lighting_probs": prior_lighting_probs.tolist(),
                    "posterior_lighting_probs_given_success": posterior_lighting_probs.tolist(),
                    "flat_likelihood_camera_mean": flat_camera_mean,
                    "flat_likelihood_camera_95ci": flat_camera_ci,
                    "tests": [{"name": name, "passed": bool(ok)} for name, ok in mnpe_tests],
                    "boundary": "This validates posterior-conditioning intuition on synthetic data; real RoboLab MNPE requires variation rollout CSV and sbi.",
                },
            )
            """
        ),
        md(
            """
            ## 0.13 论文精讲：Baseline 场景生成方法

            下面这节来自本目录的 [EXPLAIN_07_baseline_method.md](./EXPLAIN_07_baseline_method.md)，对应论文 Appendix C-C Baseline Method：baseline 是 scene generation 对照方法，不是策略 baseline。它用 LLM 选物体和网格布局，再把对象按 cell 顺序摆放并 jitter，一次 pass 后做物理 settle；它能保证基本分散，但缺少 `place-in`、`place-on`、`cluster-around` 和失败反馈修复。
            """
        ),
        md_file("EXPLAIN_07_baseline_method.md"),
        code(
            r"""
            # ===== 精讲7：Baseline scene generation 轻量验证 =====
            # 这个测试复刻论文 Appendix C-C 的核心差异：
            # - baseline: grid cell + jitter + all objects on table
            # - hierarchical/ours: explicit semantic relations such as place-in/place-on/cluster-around

            import math
            import numpy as np

            def grid_baseline_layout(objects, rows, cols, table_bounds=(0.25, 0.85, -0.40, 0.40), jitter_ratio=0.18, seed=7):
                # 单次 grid+jitter baseline：每个 object 占一个桌面 cell，不表达容器/支撑关系。
                if len(objects) > rows * cols:
                    raise ValueError("grid has fewer cells than objects")

                rng = np.random.default_rng(seed)
                x_min, x_max, y_min, y_max = table_bounds
                cell_w = (x_max - x_min) / cols
                cell_h = (y_max - y_min) / rows

                placements = []
                for index, obj in enumerate(objects):
                    row = index // cols
                    col = index % cols
                    cx = x_min + (col + 0.5) * cell_w
                    cy = y_min + (row + 0.5) * cell_h
                    x = cx + rng.uniform(-jitter_ratio * cell_w, jitter_ratio * cell_w)
                    y = cy + rng.uniform(-jitter_ratio * cell_h, jitter_ratio * cell_h)
                    placements.append(
                        {
                            "object": obj,
                            "type": "on-table",
                            "x": float(x),
                            "y": float(y),
                            "z_policy": "safe_height",
                            "yaw": float(rng.uniform(-math.pi, math.pi)),
                        }
                    )
                return placements

            def hierarchical_layout_example():
                # 模拟 RoboLab 主方法能表达的语义谓词结构。
                return [
                    {"object": "bowl", "type": "anchor", "x": 0.52, "y": 0.02},
                    {"object": "plate", "type": "anchor", "x": 0.70, "y": -0.16},
                    {"object": "banana", "type": "place-in", "container": "bowl"},
                    {"object": "apple", "type": "place-in", "container": "bowl"},
                    {"object": "spoon", "type": "place-on", "support": "plate"},
                    {"object": "mug", "type": "cluster-around", "anchor": "bowl", "radius": 0.13},
                ]

            objects = ["bowl", "plate", "banana", "apple", "spoon", "mug"]
            baseline = grid_baseline_layout(objects, rows=2, cols=3)
            hierarchical = hierarchical_layout_example()

            def min_pair_distance(placements):
                coords = np.array([[p["x"], p["y"]] for p in placements], dtype=float)
                best = float("inf")
                for i in range(len(coords)):
                    for j in range(i + 1, len(coords)):
                        best = min(best, float(np.linalg.norm(coords[i] - coords[j])))
                return best

            baseline_min_distance = min_pair_distance(baseline)
            baseline_relation_types = {p["type"] for p in baseline}
            hierarchical_relation_types = {p["type"] for p in hierarchical}

            baseline_top_level_slots = sum(1 for p in baseline if p["type"] == "on-table")
            hierarchical_top_level_slots = sum(1 for p in hierarchical if p["type"] in {"anchor", "cluster-around"})

            baseline_tests = [
                ("baseline_keeps_basic_separation", baseline_min_distance > 0.12),
                ("baseline_all_objects_are_flat_table_items", baseline_relation_types == {"on-table"}),
                ("hierarchical_expresses_containment", "place-in" in hierarchical_relation_types),
                ("hierarchical_expresses_support", "place-on" in hierarchical_relation_types),
                ("hierarchical_expresses_cluster", "cluster-around" in hierarchical_relation_types),
                ("hierarchical_uses_fewer_top_level_table_slots", hierarchical_top_level_slots < baseline_top_level_slots),
            ]

            print(f"baseline_min_distance={baseline_min_distance:.3f} m")
            print(f"baseline_relation_types={sorted(baseline_relation_types)}")
            print(f"hierarchical_relation_types={sorted(hierarchical_relation_types)}")
            print(f"baseline_top_level_slots={baseline_top_level_slots}")
            print(f"hierarchical_top_level_slots={hierarchical_top_level_slots}")
            for name, ok in baseline_tests:
                print(f"{name}: {'PASS' if ok else 'FAIL'}")

            assert all(ok for _, ok in baseline_tests), baseline_tests
            write_status(
                "baseline_method_lightweight_tests",
                {
                    "all_passed": all(ok for _, ok in baseline_tests),
                    "baseline_min_distance": baseline_min_distance,
                    "baseline_relation_types": sorted(baseline_relation_types),
                    "hierarchical_relation_types": sorted(hierarchical_relation_types),
                    "baseline_top_level_slots": baseline_top_level_slots,
                    "hierarchical_top_level_slots": hierarchical_top_level_slots,
                    "baseline_example": baseline,
                    "hierarchical_example": hierarchical,
                    "tests": [{"name": name, "passed": bool(ok)} for name, ok in baseline_tests],
                    "boundary": "This validates the structural difference between grid+jitter baseline and predicate-based scene generation; it does not render or physics-settle a USD scene.",
                },
            )
            """
        ),
        md(
            """
            ## 0.14 论文精讲：论文实验总览与 Algorithm 1

            下面这节来自本目录的 [EXPLAIN_08_paper_experiments.md](./EXPLAIN_08_paper_experiments.md)，对应论文中的实验体系：RoboLab-120 策略评测、细粒度能力分析、扰动敏感性、真实世界相关性、场景生成质量、任务生成质量，以及你截图里的 Algorithm 1 Spatial Constraint Solver。
            """
        ),
        md_file("EXPLAIN_08_paper_experiments.md"),
        code(
            r"""
            # ===== 精讲8：Algorithm 1 Spatial Constraint Solver 轻量验证 =====
            # 这个 toy solver 只复刻论文 Algorithm 1 的结构：
            # 输入：对象 B、谓词 P、桌面边界 Lmax。
            # 输出：每个基础对象的 2D 位姿 (x, y, theta)。
            # 边界：它不是官方 spatial_solver.py，也不做 USD/Isaac 物理 settle。

            import json
            import math
            import numpy as np

            def _clamp(value, lo, hi):
                # 把一个坐标限制在桌面边界内。
                return float(max(lo, min(hi, value)))

            def _pose_array(poses, name):
                # 取对象的 2D 坐标，便于用向量方式算距离和方向。
                return np.array([poses[name]["x"], poses[name]["y"]], dtype=float)

            def find_circle_collisions(poses, radii, margin):
                # 用圆近似对象 footprint；真实 RoboLab 会结合对象尺寸和更复杂的碰撞/物理检查。
                collisions = []
                names = list(poses)
                for i, a in enumerate(names):
                    for b in names[i + 1 :]:
                        pa = _pose_array(poses, a)
                        pb = _pose_array(poses, b)
                        distance = float(np.linalg.norm(pb - pa))
                        required = float(radii[a] + radii[b] + margin)
                        if distance < required:
                            collisions.append(
                                {
                                    "a": a,
                                    "b": b,
                                    "distance": distance,
                                    "required": required,
                                }
                            )
                return collisions

            def solve_toy_spatial_constraints(objects, predicates, table_bounds, mu=0.02, max_iterations=200, seed=42):
                # 论文里的 margin schedule：先用基础安全距离，再尝试更保守的对象间距。
                margins = [mu, 1.25 * mu, 1.5 * mu, 2.0 * mu]
                rng = np.random.default_rng(seed)
                x_min, x_max, y_min, y_max = table_bounds
                radii = {name: float(spec["radius"]) for name, spec in objects.items()}
                last_error = "not started"

                def clamp_pose(poses, name):
                    radius = radii[name]
                    poses[name]["x"] = _clamp(poses[name]["x"], x_min + radius, x_max - radius)
                    poses[name]["y"] = _clamp(poses[name]["y"], y_min + radius, y_max - radius)

                def initialize(margin):
                    # Phase 1a：先把所有 loose objects 随机撒到桌面里。
                    poses = {}
                    for name, spec in objects.items():
                        radius = radii[name]
                        poses[name] = {
                            "x": float(rng.uniform(x_min + radius + margin, x_max - radius - margin)),
                            "y": float(rng.uniform(y_min + radius + margin, y_max - radius - margin)),
                            "theta": 0.0,
                        }

                    fixed = set()
                    for pred in predicates:
                        # Phase 1b：place-on-base 是硬锚点，直接写入指定位置和朝向。
                        if pred["type"] == "place-on-base":
                            name = pred["object"]
                            poses[name]["x"] = float(pred["x"])
                            poses[name]["y"] = float(pred["y"])
                            poses[name]["theta"] = float(pred.get("theta", 0.0))
                            clamp_pose(poses, name)
                            fixed.add(name)

                    for pred in predicates:
                        # Phase 1c：cluster-around 用极坐标把目标围绕 anchor 摆开。
                        if pred["type"] == "cluster-around":
                            anchor = pred["anchor"]
                            targets = list(pred["targets"])
                            radius = float(pred["radius"])
                            start_angle = float(pred.get("start_angle", 0.0))
                            for index, target in enumerate(targets):
                                angle = start_angle + 2.0 * math.pi * index / max(1, len(targets))
                                poses[target]["x"] = poses[anchor]["x"] + radius * math.cos(angle)
                                poses[target]["y"] = poses[anchor]["y"] + radius * math.sin(angle)
                                clamp_pose(poses, target)
                    return poses, fixed

                def apply_relative_constraints(poses):
                    # Phase 2：把语言里的 left/right/front/back 约束变成几何偏移。
                    changed = False
                    for pred in predicates:
                        kind = pred["type"]
                        if kind not in {"left-of", "right-of", "front-of", "behind"}:
                            continue
                        name = pred["object"]
                        ref = pred["reference"]
                        distance = float(pred.get("distance", 0.16))
                        old = (poses[name]["x"], poses[name]["y"])
                        if kind == "left-of":
                            poses[name]["x"] = poses[ref]["x"]
                            poses[name]["y"] = poses[ref]["y"] + distance
                        elif kind == "right-of":
                            poses[name]["x"] = poses[ref]["x"]
                            poses[name]["y"] = poses[ref]["y"] - distance
                        elif kind == "front-of":
                            poses[name]["x"] = poses[ref]["x"] + distance
                            poses[name]["y"] = poses[ref]["y"]
                        elif kind == "behind":
                            poses[name]["x"] = poses[ref]["x"] - distance
                            poses[name]["y"] = poses[ref]["y"]
                        clamp_pose(poses, name)
                        changed = changed or old != (poses[name]["x"], poses[name]["y"])
                    return changed

                def apply_orientations(poses):
                    # Phase 2 的朝向部分：把 facing-* 约束写成 theta。
                    theta_by_type = {
                        "facing-front": 0.0,
                        "facing-back": math.pi,
                        "facing-left": math.pi / 2.0,
                        "facing-right": -math.pi / 2.0,
                    }
                    for pred in predicates:
                        if pred["type"] in theta_by_type:
                            poses[pred["object"]]["theta"] = float(theta_by_type[pred["type"]])

                def resolve_overlap(poses, collision, fixed, margin):
                    # Phase 3：把碰撞对象沿连线方向推开；固定锚点不移动。
                    a = collision["a"]
                    b = collision["b"]
                    pa = _pose_array(poses, a)
                    pb = _pose_array(poses, b)
                    direction = pb - pa
                    distance = float(np.linalg.norm(direction))
                    if distance < 1e-9:
                        direction = rng.normal(size=2)
                        distance = float(np.linalg.norm(direction))
                    direction = direction / distance
                    required = radii[a] + radii[b] + margin
                    push = float(required - distance + 1e-4)

                    if a in fixed and b in fixed:
                        return
                    if a in fixed:
                        poses[b]["x"] += float(direction[0] * push)
                        poses[b]["y"] += float(direction[1] * push)
                        clamp_pose(poses, b)
                    elif b in fixed:
                        poses[a]["x"] -= float(direction[0] * push)
                        poses[a]["y"] -= float(direction[1] * push)
                        clamp_pose(poses, a)
                    else:
                        poses[a]["x"] -= float(direction[0] * push / 2.0)
                        poses[a]["y"] -= float(direction[1] * push / 2.0)
                        poses[b]["x"] += float(direction[0] * push / 2.0)
                        poses[b]["y"] += float(direction[1] * push / 2.0)
                        clamp_pose(poses, a)
                        clamp_pose(poses, b)

                for margin in margins:
                    poses, fixed = initialize(margin)
                    phase_log = [f"margin={margin:.3f}: initialized"]

                    for _ in range(8):
                        if not apply_relative_constraints(poses):
                            break
                    apply_orientations(poses)
                    phase_log.append("relative constraints and orientations applied")

                    collision_counts = []
                    for iteration in range(max_iterations):
                        collisions = find_circle_collisions(poses, radii, margin)
                        if not collisions:
                            return {
                                "success": True,
                                "margin": float(margin),
                                "iterations": iteration,
                                "poses": poses,
                                "phase_log": phase_log + ["collision resolution succeeded"],
                            }

                        collision_counts.append(len(collisions))
                        if len(collision_counts) >= 10 and len(set(collision_counts[-10:])) == 1:
                            # 如果碰撞数量长时间不下降，轻微扰动非固定对象，避免卡死。
                            for name in poses:
                                if name not in fixed:
                                    poses[name]["x"] += float(rng.normal(0.0, 0.01))
                                    poses[name]["y"] += float(rng.normal(0.0, 0.01))
                                    clamp_pose(poses, name)

                        for collision in collisions:
                            resolve_overlap(poses, collision, fixed, margin)

                    last_error = f"failed at margin={margin:.3f} with {len(collisions)} collisions"

                return {
                    "success": False,
                    "margin": None,
                    "iterations": max_iterations,
                    "poses": poses,
                    "phase_log": [last_error],
                }

            toy_objects = {
                "bowl_anchor": {"radius": 0.055},
                "red_mug": {"radius": 0.045},
                "blue_mug": {"radius": 0.045},
                "cube": {"radius": 0.040},
                "spoon": {"radius": 0.035},
            }
            toy_predicates = [
                {"type": "place-on-base", "object": "bowl_anchor", "x": 0.55, "y": 0.00, "theta": 0.0},
                {"type": "cluster-around", "anchor": "bowl_anchor", "targets": ["red_mug", "blue_mug"], "radius": 0.13},
                {"type": "left-of", "object": "cube", "reference": "bowl_anchor", "distance": 0.18},
                {"type": "facing-front", "object": "spoon"},
            ]
            toy_table_bounds = (0.25, 0.85, -0.40, 0.40)
            toy_result = solve_toy_spatial_constraints(
                toy_objects,
                toy_predicates,
                toy_table_bounds,
                mu=0.02,
                max_iterations=200,
                seed=2604,
            )

            poses = toy_result["poses"]
            radii = {name: spec["radius"] for name, spec in toy_objects.items()}
            final_margin = toy_result["margin"] if toy_result["margin"] is not None else 0.02
            final_collisions = find_circle_collisions(poses, radii, final_margin)

            def in_bounds(name):
                x_min, x_max, y_min, y_max = toy_table_bounds
                radius = radii[name]
                return (
                    x_min + radius <= poses[name]["x"] <= x_max - radius
                    and y_min + radius <= poses[name]["y"] <= y_max - radius
                )

            def xy_distance(a, b):
                return float(np.linalg.norm(_pose_array(poses, a) - _pose_array(poses, b)))

            experiment_taxonomy = {
                "policy_benchmark": ["success", "score", "episode_results.jsonl"],
                "granular_analysis": ["attributes", "difficulty", "num_objects", "num_subtasks"],
                "sensitivity": ["lighting", "background", "table", "camera", "object_pose"],
                "real_world": ["RoboLab score", "RoboArena/Elo correlation"],
                "scene_generation": ["VQA", "GPT preference", "Real", "Func", "Lay", "Compl", "Qual"],
                "task_generation": ["alignment", "clarity", "feasibility", "match", "coverage"],
            }

            paper_experiment_tests = [
                ("algorithm_returns_success", toy_result["success"]),
                ("all_objects_within_table_bounds", all(in_bounds(name) for name in poses)),
                ("no_final_circle_collisions", len(final_collisions) == 0),
                ("cluster_red_mug_near_anchor", abs(xy_distance("red_mug", "bowl_anchor") - 0.13) < 0.04),
                ("cluster_blue_mug_near_anchor", abs(xy_distance("blue_mug", "bowl_anchor") - 0.13) < 0.04),
                ("left_of_constraint_satisfied", poses["cube"]["y"] - poses["bowl_anchor"]["y"] >= 0.16),
                ("orientation_constraint_satisfied", abs(poses["spoon"]["theta"] - 0.0) < 1e-9),
                (
                    "experiment_taxonomy_complete",
                    {"policy_benchmark", "sensitivity", "real_world", "scene_generation", "task_generation"}.issubset(
                        experiment_taxonomy
                    ),
                ),
            ]

            print(json.dumps(toy_result, ensure_ascii=False, indent=2))
            for name, ok in paper_experiment_tests:
                print(f"{name}: {'PASS' if ok else 'FAIL'}")

            assert all(ok for _, ok in paper_experiment_tests), paper_experiment_tests
            write_status(
                "paper_experiments_algorithm_lightweight_tests",
                {
                    "all_passed": all(ok for _, ok in paper_experiment_tests),
                    "toy_result": toy_result,
                    "final_collisions": final_collisions,
                    "experiment_taxonomy": experiment_taxonomy,
                    "tests": [{"name": name, "passed": bool(ok)} for name, ok in paper_experiment_tests],
                    "boundary": "This validates Algorithm 1 structure on a toy 2D layout; it is not a replacement for RoboLab spatial_solver.py or Isaac physics settle.",
                },
            )
            """
        ),
        md(
            """
            ## 0.15 论文精讲：DTGE - 任务生成质量评估

            下面这节来自本目录的 [EXPLAIN_09_dtge.md](./EXPLAIN_09_dtge.md)。这里的 DTGE 指论文 Appendix D 的 Details on Task Generation Evaluation：它不是策略跑分，而是评估 LLM 自动生成的任务代码是否“指令清楚、成功条件匹配、物理可行、对象/谓词覆盖合理”。
            """
        ),
        md_file("EXPLAIN_09_dtge.md"),
        code(
            r"""
            # ===== 精讲9：DTGE 轻量验证 =====
            # 这个 cell 模拟论文 Appendix D 的核心口径：
            # 1. 从生成的 task Python 代码中静态抽取 instruction 和 terminations.success。
            # 2. 用简化规则模拟 LLM-as-judge 的 6 个维度。
            # 3. 统计 object coverage / predicate coverage。
            # 边界：这里不是论文使用的 o1 judge，也不是官方评测脚本；它只验证 DTGE 的数据流和判定口径。

            import ast
            import json
            import re
            from collections import Counter

            def ast_literal(node):
                # 安全地把 AST 常量、列表、字典还原成 Python 值；遇到函数名则返回名字字符串。
                if isinstance(node, ast.Constant):
                    return node.value
                if isinstance(node, ast.List):
                    return [ast_literal(item) for item in node.elts]
                if isinstance(node, ast.Tuple):
                    return [ast_literal(item) for item in node.elts]
                if isinstance(node, ast.Dict):
                    return {ast_literal(k): ast_literal(v) for k, v in zip(node.keys, node.values)}
                if isinstance(node, ast.Name):
                    return node.id
                if isinstance(node, ast.Attribute):
                    return node.attr
                return None

            def extract_task_features(source):
                # DTGE 的“静态抽取”：不跑 Isaac，不跑 policy，只读 task code 的结构。
                tree = ast.parse(source)
                features = {
                    "task_class": None,
                    "instruction": "",
                    "attributes": [],
                    "success_func": None,
                    "success_params": {},
                }
                for node in tree.body:
                    if not isinstance(node, ast.ClassDef):
                        continue
                    if node.name.endswith("Task"):
                        features["task_class"] = node.name
                        for stmt in node.body:
                            target_names = []
                            if isinstance(stmt, ast.Assign):
                                target_names = [target.id for target in stmt.targets if isinstance(target, ast.Name)]
                            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                                target_names = [stmt.target.id]
                            if "instruction" in target_names:
                                value = ast_literal(stmt.value)
                                if isinstance(value, dict):
                                    features["instruction"] = value.get("default", next(iter(value.values())))
                                else:
                                    features["instruction"] = value
                            if "attributes" in target_names:
                                features["attributes"] = ast_literal(stmt.value) or []
                    if node.name.endswith("Terminations"):
                        for stmt in node.body:
                            if not isinstance(stmt, ast.Assign):
                                continue
                            targets = [target.id for target in stmt.targets if isinstance(target, ast.Name)]
                            if "success" not in targets or not isinstance(stmt.value, ast.Call):
                                continue
                            for keyword in stmt.value.keywords:
                                if keyword.arg == "func":
                                    features["success_func"] = ast_literal(keyword.value)
                                if keyword.arg == "params":
                                    features["success_params"] = ast_literal(keyword.value) or {}
                return features

            def flatten_values(value):
                # 把 params 中的 object/container/surface/reference 等值拍平，便于比较指令里出现的对象名。
                if value is None:
                    return []
                if isinstance(value, str):
                    return [value]
                if isinstance(value, (list, tuple, set)):
                    out = []
                    for item in value:
                        out.extend(flatten_values(item))
                    return out
                if isinstance(value, dict):
                    out = []
                    for item in value.values():
                        out.extend(flatten_values(item))
                    return out
                return []

            def infer_relation_from_instruction(text):
                # 简化版 relation parser：真实论文用 LLM judge，这里只用关键词验证数据流。
                lower = text.lower()
                if "left of" in lower or "to the left" in lower:
                    return "object_left_of"
                if "right of" in lower or "to the right" in lower:
                    return "object_right_of"
                if "stack" in lower:
                    return "stacked"
                if "sort" in lower:
                    return "object_groups_in_containers"
                if " on " in f" {lower} " or "onto" in lower:
                    return "object_on_top"
                if " in " in f" {lower} " or "inside" in lower or "into" in lower:
                    return "object_in_container"
                return None

            def infer_quantifier_from_instruction(text):
                lower = text.lower()
                if re.search(r"\ball\b", lower):
                    return "all"
                if re.search(r"\bany\b", lower):
                    return "any"
                if re.search(r"\b(two|three|four|2|3|4)\b", lower):
                    return "count"
                return "single"

            def judge_task_alignment(features, scene_objects, object_sizes=None, container_sizes=None):
                # 简化 judge：输出和论文对应的 relation/target/object/quantifier/clarity/feasibility 维度。
                instruction = features["instruction"] or ""
                lower = instruction.lower()
                expected_relation = infer_relation_from_instruction(instruction)
                actual_func = features["success_func"]
                params = features["success_params"]
                referenced_in_code = set(flatten_values(params))
                mentioned_in_text = {obj for obj in scene_objects if obj.replace("_", " ") in lower or obj in lower}

                relation_match = 1.0 if expected_relation == actual_func else 0.0
                if expected_relation is None and actual_func is None:
                    relation_match = 0.0

                target_keys = ["container", "reference_object", "surface"]
                target_values = {params.get(key) for key in target_keys if params.get(key)}
                target_match = 1.0 if not target_values or target_values.issubset(mentioned_in_text) else 0.0

                object_match = 1.0
                if mentioned_in_text:
                    object_match = len(mentioned_in_text & referenced_in_code) / len(mentioned_in_text)

                expected_quantifier = infer_quantifier_from_instruction(instruction)
                actual_logical = params.get("logical", "single")
                if expected_quantifier == "single":
                    quantifier_match = 1.0 if actual_logical in {"single", "all"} else 0.5
                elif expected_quantifier == "count":
                    quantifier_match = 1.0 if "K" in params or "count" in params else 0.5
                else:
                    quantifier_match = 1.0 if actual_logical == expected_quantifier else 0.0

                clarity = 1.0
                if len(instruction.split()) < 4 or instruction.lower() in {"put it there", "move it"}:
                    clarity = 0.3
                if not mentioned_in_text:
                    clarity = min(clarity, 0.5)

                feasibility = 1.0
                if object_sizes and container_sizes and actual_func == "object_in_container":
                    obj = params.get("object")
                    container = params.get("container")
                    if isinstance(obj, list):
                        obj = obj[0] if obj else None
                    if obj in object_sizes and container in container_sizes:
                        feasibility = 1.0 if object_sizes[obj] <= container_sizes[container] else 0.0

                semantic_match = (relation_match + target_match + object_match + quantifier_match) / 4.0
                alignment = (
                    0.20 * relation_match
                    + 0.20 * target_match
                    + 0.20 * object_match
                    + 0.15 * quantifier_match
                    + 0.10 * clarity
                    + 0.15 * feasibility
                )
                if min(relation_match, target_match, object_match, quantifier_match, clarity, feasibility) >= 0.99:
                    verdict = "aligned"
                elif semantic_match >= 0.5 and clarity >= 0.5 and feasibility >= 0.5:
                    verdict = "partial"
                else:
                    verdict = "misaligned"

                return {
                    "relation_match": relation_match,
                    "target_match": target_match,
                    "object_match": object_match,
                    "quantifier_match": quantifier_match,
                    "clarity": clarity,
                    "feasibility": feasibility,
                    "semantic_match": semantic_match,
                    "alignment": alignment,
                    "verdict": verdict,
                    "mentioned_in_text": sorted(mentioned_in_text),
                    "referenced_in_code": sorted(referenced_in_code),
                    "expected_relation": expected_relation,
                    "actual_func": actual_func,
                }

            def coverage_metrics(task_features, scene_objects, available_predicates):
                # DTGE 的 coverage：对象是否被任务覆盖，谓词库是否被充分使用。
                used_objects = set()
                used_predicates = set()
                for features in task_features:
                    used_objects.update(obj for obj in flatten_values(features["success_params"]) if obj in scene_objects)
                    if features["success_func"]:
                        used_predicates.add(features["success_func"])
                return {
                    "object_coverage": len(used_objects) / len(scene_objects),
                    "predicate_coverage": len(used_predicates) / len(available_predicates),
                    "used_objects": sorted(used_objects),
                    "used_predicates": sorted(used_predicates),
                }

            aligned_task_code = (
                "class AppleInBowlTerminations:\n"
                "    success = DoneTerm(func=object_in_container, params={\"object\": \"apple\", \"container\": \"bowl\", \"logical\": \"all\"})\n"
                "\n"
                "class AppleInBowlTask(Task):\n"
                "    instruction = {\"default\": \"Place the apple in the bowl\"}\n"
                "    attributes = [\"semantics\"]\n"
            )

            mismatched_task_code = (
                "class AppleInBowlTerminations:\n"
                "    success = DoneTerm(func=object_in_container, params={\"object\": \"banana\", \"container\": \"bowl\", \"logical\": \"all\"})\n"
                "\n"
                "class AppleInBowlTask(Task):\n"
                "    instruction = {\"default\": \"Place the apple in the bowl\"}\n"
                "    attributes = [\"semantics\"]\n"
            )

            infeasible_task_code = (
                "class BoxInSmallBowlTerminations:\n"
                "    success = DoneTerm(func=object_in_container, params={\"object\": \"large_box\", \"container\": \"small_bowl\", \"logical\": \"all\"})\n"
                "\n"
                "class BoxInSmallBowlTask(Task):\n"
                "    instruction = {\"default\": \"Place the large_box in the small_bowl\"}\n"
                "    attributes = [\"spatial\"]\n"
            )

            scene_objects = ["apple", "banana", "bowl", "plate", "large_box", "small_bowl"]
            available_predicates = [
                "object_in_container",
                "object_on_top",
                "object_left_of",
                "object_right_of",
                "stacked",
                "object_groups_in_containers",
                "object_upright",
            ]
            object_sizes = {"apple": 0.07, "banana": 0.12, "large_box": 0.30}
            container_sizes = {"bowl": 0.18, "small_bowl": 0.12}

            extracted = [extract_task_features(code) for code in [aligned_task_code, mismatched_task_code, infeasible_task_code]]
            judged = [
                judge_task_alignment(features, scene_objects, object_sizes=object_sizes, container_sizes=container_sizes)
                for features in extracted
            ]
            coverage = coverage_metrics(extracted, scene_objects, available_predicates)

            dtge_table = {
                "color": {"count": 116, "alignment": 0.81, "clarity": 0.94, "feasibility": 0.80, "match": 0.90, "aligned_pct": 57, "partial_pct": 40, "object_coverage": 0.88, "predicate_coverage": 0.29},
                "conjunction": {"count": 116, "alignment": 0.97, "clarity": 0.98, "feasibility": 1.00, "match": 0.98, "aligned_pct": 91, "partial_pct": 9, "object_coverage": 0.88, "predicate_coverage": 0.29},
                "counting": {"count": 116, "alignment": 0.87, "clarity": 0.97, "feasibility": 0.90, "match": 0.92, "aligned_pct": 60, "partial_pct": 38, "object_coverage": 0.88, "predicate_coverage": 0.29},
                "recognition": {"count": 116, "alignment": 0.96, "clarity": 0.97, "feasibility": 0.96, "match": 0.97, "aligned_pct": 85, "partial_pct": 15, "object_coverage": 0.88, "predicate_coverage": 0.29},
                "semantics": {"count": 116, "alignment": 0.89, "clarity": 0.95, "feasibility": 0.94, "match": 0.94, "aligned_pct": 72, "partial_pct": 27, "object_coverage": 0.88, "predicate_coverage": 0.29},
                "sorting": {"count": 116, "alignment": 0.94, "clarity": 0.95, "feasibility": 0.97, "match": 0.96, "aligned_pct": 86, "partial_pct": 14, "object_coverage": 0.88, "predicate_coverage": 0.29},
                "spatial": {"count": 116, "alignment": 0.92, "clarity": 0.98, "feasibility": 0.89, "match": 0.95, "aligned_pct": 80, "partial_pct": 17, "object_coverage": 0.88, "predicate_coverage": 0.29},
                "overall": {"count": 812, "alignment": 0.91, "clarity": 0.96, "feasibility": 0.92, "match": 0.95, "aligned_pct": 76, "partial_pct": 23, "object_coverage": 0.88, "predicate_coverage": 0.29},
            }

            dtge_tests = [
                ("static_extraction_gets_instruction", extracted[0]["instruction"] == "Place the apple in the bowl"),
                ("static_extraction_gets_success_predicate", extracted[0]["success_func"] == "object_in_container"),
                ("aligned_task_verdict_aligned", judged[0]["verdict"] == "aligned" and judged[0]["alignment"] > 0.95),
                ("object_mismatch_detected", judged[1]["object_match"] < 1.0 and judged[1]["verdict"] != "aligned"),
                ("physical_infeasibility_detected", judged[2]["feasibility"] == 0.0 and judged[2]["verdict"] != "aligned"),
                ("coverage_metrics_in_range", 0.0 <= coverage["object_coverage"] <= 1.0 and 0.0 <= coverage["predicate_coverage"] <= 1.0),
                ("predicate_coverage_is_conservative", coverage["predicate_coverage"] < 0.5),
                ("paper_table_total_is_812", sum(v["count"] for k, v in dtge_table.items() if k != "overall") == dtge_table["overall"]["count"]),
                ("paper_overall_alignment_matches_appendix_d", dtge_table["overall"]["alignment"] == 0.91),
            ]

            print("Extracted features:")
            print(json.dumps(extracted, ensure_ascii=False, indent=2))
            print("Judged examples:")
            print(json.dumps(judged, ensure_ascii=False, indent=2))
            print("Coverage:")
            print(json.dumps(coverage, ensure_ascii=False, indent=2))
            for name, ok in dtge_tests:
                print(f"{name}: {'PASS' if ok else 'FAIL'}")

            assert all(ok for _, ok in dtge_tests), dtge_tests
            write_status(
                "dtge_lightweight_tests",
                {
                    "all_passed": all(ok for _, ok in dtge_tests),
                    "extracted": extracted,
                    "judged": judged,
                    "coverage": coverage,
                    "paper_table": dtge_table,
                    "tests": [{"name": name, "passed": bool(ok)} for name, ok in dtge_tests],
                    "boundary": "This simulates DTGE static extraction and judge dimensions; real reproduction requires the paper's exact LLM prompts/model settings and generated task corpus.",
                },
            )
            """
        ),
        md(
            """
            ## 0.16 论文精讲：Scene Generation Prompt 设计

            下面这节来自本目录的 [EXPLAIN_10_prompt_design.md](./EXPLAIN_10_prompt_design.md)，对应论文 Appendix C 的 Stage I Semantic Planning prompt：为什么要写现实场景原则、坐标系统、placement types、JSON only、对象目录、尺寸限制和 medium scene strategy，以及这些约束如何对接 `predicates.py`、`spatial_solver.py`、`physical_solver.py` 和 `feedback_system.py`。
            """
        ),
        md_file("EXPLAIN_10_prompt_design.md"),
        code(
            r"""
            # ===== 精讲10：Scene generation prompt 轻量验证 =====
            # 这个 cell 不调用 LLM，而是模拟 prompt 期望得到的 JSON 输出，
            # 并检查几类常见错误：对象名幻觉、依赖顺序错误、网格化 yaw、大物体过多、非 JSON 输出。

            import json
            import math
            from collections import Counter

            catalog = {
                "bowl_0": {"category": "container", "footprint": 0.045, "can_contain": True, "can_support": False},
                "plate_large": {"category": "support", "footprint": 0.060, "can_contain": False, "can_support": True},
                "apple_01": {"category": "food", "footprint": 0.010, "can_contain": False, "can_support": False},
                "orange_01": {"category": "food", "footprint": 0.012, "can_contain": False, "can_support": False},
                "banana": {"category": "food", "footprint": 0.018, "can_contain": False, "can_support": False},
                "mug": {"category": "other", "footprint": 0.015, "can_contain": True, "can_support": False},
                "spoon": {"category": "tool", "footprint": 0.006, "can_contain": False, "can_support": False},
                "tray": {"category": "support", "footprint": 0.095, "can_contain": False, "can_support": True},
                "storage_bin": {"category": "container", "footprint": 0.110, "can_contain": True, "can_support": False},
                "large_box": {"category": "other", "footprint": 0.120, "can_contain": True, "can_support": True},
            }

            good_output = {
                "objects": [
                    {"name": "bowl_0"},
                    {"name": "plate_large"},
                    {"name": "apple_01"},
                    {"name": "orange_01"},
                    {"name": "banana"},
                    {"name": "mug"},
                    {"name": "spoon"},
                ],
                "predicates": [
                    {"type": "place-on-base", "object": "bowl_0", "x": 0.40, "y": 0.15, "yaw": 23},
                    {"type": "place-on-base", "object": "plate_large", "x": 0.65, "y": -0.10, "yaw": 156},
                    {"type": "place-in", "objects": ["apple_01", "orange_01"], "container": "bowl_0"},
                    {"type": "place-on", "object": "banana", "support": "plate_large", "position": "center"},
                    {"type": "cluster-around", "objects": ["mug", "spoon"], "anchor": "bowl_0", "radius": 0.12},
                ],
            }

            hallucinated_object_output = {
                "objects": [{"name": "beautiful_red_ceramic_bowl"}, {"name": "apple_01"}],
                "predicates": [
                    {"type": "place-on-base", "object": "beautiful_red_ceramic_bowl", "x": 0.55, "y": 0.0, "yaw": 30},
                    {"type": "place-in", "objects": ["apple_01"], "container": "beautiful_red_ceramic_bowl"},
                ],
            }

            dependency_error_output = {
                "objects": [{"name": "bowl_0"}, {"name": "apple_01"}],
                "predicates": [
                    {"type": "place-in", "objects": ["apple_01"], "container": "bowl_0"},
                ],
            }

            grid_like_output = {
                "objects": [{"name": name} for name in ["bowl_0", "plate_large", "apple_01", "orange_01"]],
                "predicates": [
                    {"type": "place-on-base", "object": "bowl_0", "x": 0.35, "y": -0.20, "yaw": 0},
                    {"type": "place-on-base", "object": "plate_large", "x": 0.55, "y": -0.20, "yaw": 90},
                    {"type": "place-on-base", "object": "apple_01", "x": 0.35, "y": 0.00, "yaw": 180},
                    {"type": "place-on-base", "object": "orange_01", "x": 0.55, "y": 0.00, "yaw": 270},
                ],
            }

            too_many_large_objects_output = {
                "objects": [{"name": name} for name in ["tray", "storage_bin", "large_box", "plate_large", "bowl_0"]],
                "predicates": [
                    {"type": "place-on-base", "object": "tray", "x": 0.35, "y": -0.25, "yaw": 19},
                    {"type": "place-on-base", "object": "storage_bin", "x": 0.50, "y": 0.00, "yaw": 71},
                    {"type": "place-on-base", "object": "large_box", "x": 0.70, "y": 0.22, "yaw": 133},
                    {"type": "place-on-base", "object": "plate_large", "x": 0.65, "y": -0.18, "yaw": 44},
                    {"type": "place-on-base", "object": "bowl_0", "x": 0.43, "y": 0.20, "yaw": 28},
                ],
            }

            markdown_wrapped_output = "Here is the JSON:\\n```json\\n" + json.dumps(good_output) + "\\n```"

            def parse_json_only(candidate):
                # Prompt 要求 JSON only：字符串必须直接是 JSON 对象，不能有 markdown 包裹。
                if isinstance(candidate, dict):
                    return candidate, []
                if not isinstance(candidate, str):
                    return None, ["output is neither dict nor JSON string"]
                stripped = candidate.strip()
                if not stripped.startswith("{") or not stripped.endswith("}"):
                    return None, ["output is not JSON-only; likely contains prose or markdown"]
                try:
                    return json.loads(stripped), []
                except json.JSONDecodeError as exc:
                    return None, [f"invalid JSON: {exc}"]

            def validate_scene_prompt_output(candidate, catalog, table_bounds=(0.25, 0.85, -0.40, 0.40)):
                parsed, issues = parse_json_only(candidate)
                if parsed is None:
                    return {"valid": False, "issues": issues}

                names = [obj.get("name") for obj in parsed.get("objects", [])]
                name_set = set(names)
                predicates = parsed.get("predicates", [])
                x_min, x_max, y_min, y_max = table_bounds

                if not names:
                    issues.append("objects list is empty")
                if not isinstance(predicates, list) or not predicates:
                    issues.append("predicates list is empty")

                missing = sorted(name for name in name_set if name not in catalog)
                if missing:
                    issues.append(f"catalog name mismatch: {missing}")

                placed_base = set()
                yaw_values = []
                predicate_types = Counter()
                for pred in predicates:
                    pred_type = pred.get("type")
                    predicate_types[pred_type] += 1
                    if pred_type == "place-on-base":
                        obj = pred.get("object")
                        if obj not in name_set:
                            issues.append(f"predicate references object not in objects list: {obj}")
                        x = pred.get("x")
                        y = pred.get("y")
                        yaw = pred.get("yaw")
                        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                            issues.append(f"place-on-base missing numeric x/y for {obj}")
                        elif not (x_min <= x <= x_max and y_min <= y <= y_max):
                            issues.append(f"object out of table bounds: {obj}")
                        if isinstance(yaw, (int, float)):
                            yaw_values.append(float(yaw) % 360)
                        else:
                            issues.append(f"place-on-base missing numeric yaw for {obj}")
                        placed_base.add(obj)
                    elif pred_type == "place-in":
                        container = pred.get("container")
                        if container not in placed_base:
                            issues.append(f"container/support must be placed first: {container}")
                        if container in catalog and not catalog[container].get("can_contain"):
                            issues.append(f"object is not a container: {container}")
                        for obj in pred.get("objects", []):
                            if obj not in name_set:
                                issues.append(f"place-in references missing object: {obj}")
                    elif pred_type == "place-on":
                        support = pred.get("support")
                        if support not in placed_base:
                            issues.append(f"container/support must be placed first: {support}")
                        if support in catalog and not catalog[support].get("can_support"):
                            issues.append(f"object is not a support: {support}")
                        if pred.get("object") not in name_set:
                            issues.append(f"place-on references missing object: {pred.get('object')}")
                    elif pred_type == "cluster-around":
                        anchor = pred.get("anchor")
                        radius = pred.get("radius")
                        if anchor not in placed_base:
                            issues.append(f"cluster anchor must be placed first: {anchor}")
                        if not isinstance(radius, (int, float)) or not (0.08 <= radius <= 0.20):
                            issues.append(f"cluster radius outside prompt range: {radius}")
                        for obj in pred.get("objects", []):
                            if obj not in name_set:
                                issues.append(f"cluster-around references missing object: {obj}")
                    else:
                        issues.append(f"unknown predicate type: {pred_type}")

                large_objects = [name for name in name_set if name in catalog and catalog[name]["footprint"] > 0.08]
                if len(large_objects) > 2:
                    issues.append(f"too many large objects for medium scene: {large_objects}")

                if yaw_values:
                    cardinal_count = sum(1 for yaw in yaw_values if min(abs(yaw - c) for c in [0, 90, 180, 270, 360]) < 1e-6)
                    if cardinal_count == len(yaw_values):
                        issues.append("all yaw angles are cardinal grid angles")

                has_semantic_structure = any(t in predicate_types for t in ["place-in", "place-on", "cluster-around"])
                if len(names) >= 5 and not has_semantic_structure:
                    issues.append("medium scene lacks containment/support/clustering structure")

                return {
                    "valid": len(issues) == 0,
                    "issues": issues,
                    "object_count": len(names),
                    "predicate_types": dict(predicate_types),
                    "large_objects": large_objects,
                    "yaw_values": yaw_values,
                }

            def render_medium_user_prompt(theme, target_count, catalog, suggested):
                # 模拟第三张图里的 runtime user prompt：把 catalog 子集和策略注入给 LLM。
                by_category = {}
                for name, meta in catalog.items():
                    by_category.setdefault(meta["category"], []).append(name)
                large = [name for name, meta in catalog.items() if meta["footprint"] > 0.08]
                return {
                    "scene_request": theme,
                    "target_count": target_count,
                    "table_size": "0.7m x 1.0m = 0.70m^2",
                    "size_limits": {
                        "large_objects": large,
                        "rule": "max 1-2 large objects; prefer smaller for 8+ items",
                    },
                    "available_objects": {
                        "containers": sorted([name for name, meta in catalog.items() if meta["can_contain"]]),
                        "supports": sorted([name for name, meta in catalog.items() if meta["can_support"]]),
                        "food": sorted(by_category.get("food", [])),
                        "tools": sorted(by_category.get("tool", [])),
                        "other": sorted(by_category.get("other", [])),
                    },
                    "medium_scene_strategy": [
                        "Use 1-2 containers/supports as anchors",
                        "Put 2-4 objects in containers",
                        "Stack 1-2 items on supports",
                        "Cluster 2-3 objects near anchors",
                        "Vary yaw angles",
                    ],
                    "suggested_for_diversity": suggested,
                }

            validations = {
                "good_output": validate_scene_prompt_output(good_output, catalog),
                "hallucinated_object_output": validate_scene_prompt_output(hallucinated_object_output, catalog),
                "dependency_error_output": validate_scene_prompt_output(dependency_error_output, catalog),
                "grid_like_output": validate_scene_prompt_output(grid_like_output, catalog),
                "too_many_large_objects_output": validate_scene_prompt_output(too_many_large_objects_output, catalog),
                "markdown_wrapped_output": validate_scene_prompt_output(markdown_wrapped_output, catalog),
            }
            rendered_prompt = render_medium_user_prompt(
                "kitchen counter with fruit and utensils",
                10,
                catalog,
                ["bowl_0", "plate_large", "banana", "spoon"],
            )

            prompt_design_tests = [
                ("good_output_is_valid", validations["good_output"]["valid"]),
                ("good_output_uses_semantic_predicates", {"place-in", "place-on", "cluster-around"}.issubset(validations["good_output"]["predicate_types"])),
                ("hallucinated_object_detected", any("catalog name mismatch" in issue for issue in validations["hallucinated_object_output"]["issues"])),
                ("dependency_error_detected", any("placed first" in issue for issue in validations["dependency_error_output"]["issues"])),
                ("grid_yaw_detected", any("cardinal grid angles" in issue for issue in validations["grid_like_output"]["issues"])),
                ("too_many_large_objects_detected", any("too many large objects" in issue for issue in validations["too_many_large_objects_output"]["issues"])),
                ("markdown_wrapper_rejected", any("JSON-only" in issue for issue in validations["markdown_wrapped_output"]["issues"])),
                ("runtime_prompt_has_catalog_categories", bool(rendered_prompt["available_objects"]["containers"]) and bool(rendered_prompt["available_objects"]["supports"])),
                ("runtime_prompt_has_size_warning", "max 1-2 large objects" in rendered_prompt["size_limits"]["rule"]),
            ]

            print(json.dumps(validations, ensure_ascii=False, indent=2))
            print(json.dumps(rendered_prompt, ensure_ascii=False, indent=2))
            for name, ok in prompt_design_tests:
                print(f"{name}: {'PASS' if ok else 'FAIL'}")

            assert all(ok for _, ok in prompt_design_tests), prompt_design_tests
            write_status(
                "prompt_design_lightweight_tests",
                {
                    "all_passed": all(ok for _, ok in prompt_design_tests),
                    "validations": validations,
                    "rendered_prompt": rendered_prompt,
                    "tests": [{"name": name, "passed": bool(ok)} for name, ok in prompt_design_tests],
                    "boundary": "These tests validate prompt-output constraints and runtime prompt structure with synthetic examples; they do not call the paper's LLM or render USD scenes.",
                },
            )
            """
        ),
        md(
            """
            ## 0.17 论文精讲：空间求解器、物理放置求解器与失败反馈

            下面这节来自本目录的 [EXPLAIN_11_spatial_physical_solver_feedback.md](./EXPLAIN_11_spatial_physical_solver_feedback.md)，对应论文 Appendix C 的 Algorithm 1 Spatial Constraint Solver、你截图里的 Figure 17 feedback block，以及 Algorithm 2 Physical Placement Solver。重点是理解：空间求解器先解基础对象 2D 位姿，物理放置求解器再解 `place-on` / `place-in` 的 3D 坐标，失败反馈再回到下一轮 prompt。
            """
        ),
        md_file("EXPLAIN_11_spatial_physical_solver_feedback.md"),
        code(
            r"""
            # ===== 精讲11：Spatial + Physical solver + feedback 轻量验证 =====
            # 这个 cell 用纯 Python 模拟 Algorithm 1/2 的核心数据流：
            # - spatial: 先放 bowl/plate 这类 base objects
            # - physical: 再把 banana 放到 plate 上，把 apple/orange 放进 bowl
            # - feedback: 对碰撞/拥挤失败生成下一轮 prompt 修复建议
            # 边界：这是教学用 toy solver，不替代 RoboLab 的 physical_solver.py/Isaac physics settle。

            import json
            import math

            object_dims = {
                "bowl_0": (0.18, 0.18, 0.08),
                "plate_large": (0.26, 0.20, 0.025),
                "apple_01": (0.055, 0.055, 0.055),
                "orange_01": (0.060, 0.060, 0.060),
                "banana": (0.14, 0.045, 0.035),
                "large_box": (0.32, 0.24, 0.16),
                "storage_bin": (0.24, 0.18, 0.12),
            }

            def base_pose_from_place_on_base(predicates, dims):
                # Algorithm 1 的简化版：只处理 place-on-base，并把 z 设为对象半高。
                poses = {}
                for pred in predicates:
                    if pred["type"] != "place-on-base":
                        continue
                    name = pred["object"]
                    sx, sy, sz = dims[name]
                    poses[name] = {
                        "x": float(pred["x"]),
                        "y": float(pred["y"]),
                        "z": sz / 2.0,
                        "yaw": float(pred.get("yaw", 0.0)),
                        "source": "spatial/place-on-base",
                    }
                return poses

            def support_offsets(position):
                # Algorithm 2 的 FindSpot 教学版：center 优先，edge 给几个候选点。
                if position == "edge":
                    return [(0.08, 0.0), (-0.08, 0.0), (0.0, 0.06), (0.0, -0.06), (0.0, 0.0)]
                return [(0.0, 0.0), (0.04, 0.0), (-0.04, 0.0), (0.0, 0.04), (0.0, -0.04)]

            def rect_fits_support(local_x, local_y, obj_dim, support_dim):
                return (
                    abs(local_x) + obj_dim[0] / 2.0 <= support_dim[0] / 2.0
                    and abs(local_y) + obj_dim[1] / 2.0 <= support_dim[1] / 2.0
                )

            def solve_place_on(pred, poses, dims, occupied_by_support):
                # Algorithm 2 上半部分：在 support 顶面找 slot，并设置 z。
                obj = pred["object"]
                support = pred["support"]
                support_pose = poses.get(support)
                if support_pose is None:
                    return False, f"support {support} has no solved base pose"
                support_dim = dims[support]
                obj_dim = dims[obj]
                support_slots = occupied_by_support.setdefault(support, [])
                for local_x, local_y in support_offsets(pred.get("position", "center")):
                    if not rect_fits_support(local_x, local_y, obj_dim, support_dim):
                        continue
                    # 简化的同层 overlap 检查：slot 中心不要太近。
                    too_close = any(abs(local_x - sx) < (obj_dim[0] + sw) / 2.0 and abs(local_y - sy) < (obj_dim[1] + sh) / 2.0 for sx, sy, sw, sh in support_slots)
                    if too_close:
                        continue
                    support_slots.append((local_x, local_y, obj_dim[0], obj_dim[1]))
                    poses[obj] = {
                        "x": support_pose["x"] + local_x,
                        "y": support_pose["y"] + local_y,
                        "z": support_pose["z"] + support_dim[2] / 2.0 + obj_dim[2] / 2.0 + 0.001,
                        "yaw": support_pose.get("yaw", 0.0),
                        "source": f"physical/place-on/{support}",
                    }
                    return True, "placed on support"
                return False, f"no support slot found for {obj} on {support}"

            def solve_place_in(pred, poses, dims, area_limit_ratio=0.80):
                # Algorithm 2 下半部分：在容器口径内做简单网格 packing，并设置 z。
                container = pred["container"]
                container_pose = poses.get(container)
                if container_pose is None:
                    return False, f"container {container} has no solved base pose"
                container_dim = dims[container]
                objects = list(pred["objects"])
                total_area = sum(dims[obj][0] * dims[obj][1] for obj in objects)
                container_area = container_dim[0] * container_dim[1]
                if total_area > area_limit_ratio * container_area:
                    return False, f"container crowding: total object area {total_area:.3f} > {area_limit_ratio:.1f} * container area {container_area:.3f}"

                count = len(objects)
                cols = max(1, math.ceil(math.sqrt(count)))
                rows = max(1, math.ceil(count / cols))
                usable_x = container_dim[0] * 0.65
                usable_y = container_dim[1] * 0.65
                for index, obj in enumerate(objects):
                    row = index // cols
                    col = index % cols
                    local_x = (col + 0.5) * usable_x / cols - usable_x / 2.0
                    local_y = (row + 0.5) * usable_y / rows - usable_y / 2.0
                    # 小 jitter，模拟论文 Algorithm 2 的 Jitter(...)
                    local_x += (index - (count - 1) / 2.0) * 0.004
                    local_y += ((index % 2) - 0.5) * 0.004
                    poses[obj] = {
                        "x": container_pose["x"] + local_x,
                        "y": container_pose["y"] + local_y,
                        "z": container_pose["z"] + container_dim[2] / 2.0 + dims[obj][2] / 2.0 + 0.01,
                        "yaw": container_pose.get("yaw", 0.0) + index * 23.0,
                        "source": f"physical/place-in/{container}",
                    }
                return True, "placed in container"

            def compact_scene_feedback(failure_message, collisions=None, out_of_bounds=None):
                # 模拟 Figure 17：把底层失败转成下一轮 prompt 的修复建议。
                lines = [
                    "PREVIOUS ATTEMPT FAILED:",
                    failure_message,
                    "",
                    "Please fix the issues. Common fixes:",
                    "- Use MORE containment (place-in) to reduce table crowding",
                    "- Use MORE stacking (place-on) to utilize vertical space",
                    "- Use clustering (cluster-around) instead of individual placements",
                    "- Select SMALLER objects if collisions persist",
                ]
                if collisions:
                    lines.insert(2, "Collisions: " + ", ".join(f"{a}/{b}" for a, b in collisions))
                if out_of_bounds:
                    lines.insert(2, "Out of bounds: " + ", ".join(out_of_bounds))
                return "\n".join(lines)

            predicates_ok = [
                {"type": "place-on-base", "object": "bowl_0", "x": 0.40, "y": 0.15, "yaw": 23},
                {"type": "place-on-base", "object": "plate_large", "x": 0.65, "y": -0.10, "yaw": 156},
                {"type": "place-in", "objects": ["apple_01", "orange_01"], "container": "bowl_0"},
                {"type": "place-on", "object": "banana", "support": "plate_large", "position": "center"},
            ]
            poses = base_pose_from_place_on_base(predicates_ok, object_dims)
            occupied_by_support = {}
            physical_messages = []
            for pred in predicates_ok:
                if pred["type"] == "place-on":
                    ok, msg = solve_place_on(pred, poses, object_dims, occupied_by_support)
                    physical_messages.append((pred["type"], ok, msg))
                if pred["type"] == "place-in":
                    ok, msg = solve_place_in(pred, poses, object_dims)
                    physical_messages.append((pred["type"], ok, msg))

            crowded_pred = {"type": "place-in", "objects": ["large_box", "storage_bin", "banana"], "container": "bowl_0"}
            crowded_ok, crowded_msg = solve_place_in(crowded_pred, dict(poses), object_dims)
            feedback = compact_scene_feedback(crowded_msg, collisions=[("large_box", "bowl_0")])

            spatial_physical_tests = [
                ("base_anchors_have_2d_and_z_pose", all(name in poses and poses[name]["z"] > 0 for name in ["bowl_0", "plate_large"])),
                ("place_on_sets_banana_above_plate", poses["banana"]["z"] > poses["plate_large"]["z"]),
                ("place_in_sets_fruit_above_bowl", poses["apple_01"]["z"] > poses["bowl_0"]["z"] and poses["orange_01"]["z"] > poses["bowl_0"]["z"]),
                ("container_objects_have_distinct_xy", (poses["apple_01"]["x"], poses["apple_01"]["y"]) != (poses["orange_01"]["x"], poses["orange_01"]["y"])),
                ("physical_messages_successful", all(ok for _kind, ok, _msg in physical_messages)),
                ("crowded_container_failure_detected", not crowded_ok and "container crowding" in crowded_msg),
                ("feedback_mentions_previous_attempt_failed", feedback.startswith("PREVIOUS ATTEMPT FAILED")),
                ("feedback_suggests_containment_stacking_clustering", all(term in feedback for term in ["place-in", "place-on", "cluster-around"])),
                ("feedback_suggests_smaller_objects", "SMALLER objects" in feedback),
            ]

            print("Solved poses:")
            print(json.dumps(poses, ensure_ascii=False, indent=2))
            print("Physical messages:")
            print(json.dumps(physical_messages, ensure_ascii=False, indent=2))
            print("Crowded failure message:", crowded_msg)
            print("Feedback block:")
            print(feedback)
            for name, ok in spatial_physical_tests:
                print(f"{name}: {'PASS' if ok else 'FAIL'}")

            assert all(ok for _, ok in spatial_physical_tests), spatial_physical_tests
            write_status(
                "spatial_physical_feedback_lightweight_tests",
                {
                    "all_passed": all(ok for _, ok in spatial_physical_tests),
                    "poses": poses,
                    "physical_messages": physical_messages,
                    "crowded_ok": crowded_ok,
                    "crowded_message": crowded_msg,
                    "feedback": feedback,
                    "tests": [{"name": name, "passed": bool(ok)} for name, ok in spatial_physical_tests],
                    "boundary": "This is a toy implementation for explaining Algorithm 1/2 and Figure 17; real RoboLab placement uses spatial_solver.py, physical_solver.py, and Isaac/physics validation.",
                },
            )
            """
        ),
        md(
            """
            ## 0.18 论文精讲：Gaussian 方法与 NVIDIA 2026 前沿路线

            下面这节来自本目录的 [EXPLAIN_12_gaussian_sim_methods.md](./EXPLAIN_12_gaussian_sim_methods.md)，回答两个问题：

            - RoboLab 本文到底用了哪些 “Gaussian” 方法，它们分别负责视觉、物理还是统计分析。
            - 2026 年 NVIDIA 在 NuRec、3DGUT/3DGRT、Lyra、Physically Embodied Gaussians 等方向上，怎么把高斯重建推进到可交互仿真。
            """
        ),
        md_file("EXPLAIN_12_gaussian_sim_methods.md"),
        code(
            r"""
            # ===== 精讲12：Gaussian 仿真路线轻量验证 =====
            # 这个 cell 不跑 3DGS/NuRec 重建，而是把论文和 NVIDIA 2026 前沿路线
            # 拆成可检查的数据结构，避免把“视觉高斯”“物理碰撞”“统计高斯核”混在一起。

            import json

            robolab_gaussian_stack = {
                "gaussian_splat_background": {
                    "direct_in_paper": True,
                    "input": ["images_or_reconstructed_scene"],
                    "output": ["photorealistic_background_rendering"],
                    "role": "visual_rendering",
                    "physics_contact": False,
                    "plain_cn": "负责让背景看起来真实，但本身不是机器人碰撞体。",
                },
                "collision_mesh_for_splat": {
                    "direct_in_paper": True,
                    "input": ["reconstructed_or_estimated_geometry"],
                    "output": ["collider_proxy_for_physics"],
                    "role": "physical_collision",
                    "physics_contact": True,
                    "plain_cn": "负责让机器人和背景几何发生碰撞，避免只看得到却穿过去。",
                },
                "mesh_foreground_objects": {
                    "direct_in_paper": True,
                    "input": ["SimReady_or_catalog_assets"],
                    "output": ["interactive_visual_mesh_and_collision_mesh"],
                    "role": "manipulable_objects",
                    "physics_contact": True,
                    "plain_cn": "负责桌面上的可抓取、可放置、可堆叠前景对象。",
                },
                "vomp_mass_density": {
                    "direct_in_paper": True,
                    "input": ["object_geometry_and_mechanical_property_estimate"],
                    "output": ["mass_density_or_mass_proxy"],
                    "role": "mechanical_properties",
                    "physics_contact": "supports_dynamics",
                    "plain_cn": "补质量/密度这类物理参数，不是渲染方法。",
                },
                "mnpe_gaussian_kde": {
                    "direct_in_paper": True,
                    "input": ["sampled_variation_parameters"],
                    "output": ["importance_sampling_density_weight"],
                    "role": "statistical_density_estimation",
                    "physics_contact": False,
                    "plain_cn": "这是 MNPE 统计分析里的高斯核密度估计，不是 3D Gaussian Splatting。",
                },
            }

            nvidia_frontiers_2026 = {
                "omniverse_nurec": {
                    "status": "frontier_engineering",
                    "url": "https://developer.nvidia.com/omniverse/nurec",
                    "source_title": "NVIDIA Omniverse NuRec",
                    "input": ["camera_data", "lidar_data"],
                    "output": ["OpenUSD_scene", "interactive_gaussian_rendering"],
                    "why_relevant": "把真实数据重建成 Isaac/Omniverse 可用的神经重建场景。",
                    "read_focus": ["NCore data standard", "USD scene", "gRPC rendering", "Isaac Sim integration"],
                },
                "3dgut_3dgrt": {
                    "status": "research_to_tooling",
                    "url": "https://research.nvidia.com/labs/toronto-ai/3DGUT/",
                    "source_title": "NVIDIA Research 3DGUT",
                    "input": ["3D_Gaussians"],
                    "output": ["nonlinear_camera_rendering", "rolling_shutter", "secondary_rays"],
                    "why_relevant": "让高斯渲染支持复杂相机和反射/折射等 secondary rays。",
                    "read_focus": ["nonlinear camera projections", "rolling shutter", "reflections/refractions", "3DGRT alignment"],
                },
                "isaac_sim_6_nurec": {
                    "status": "2026_early_developer_release",
                    "url": "https://forums.developer.nvidia.com/t/announcement-isaac-sim-6-0-early-developer-release-for-gtc26/363709",
                    "source_title": "Isaac Sim 6.0 Early Developer Release for GTC'26",
                    "input": ["NuRec_3DGS_scene"],
                    "output": ["Fabric_Scene_Delegate_integration"],
                    "why_relevant": "把 NuRec/3DGS 更直接地放进 Isaac Sim 工程栈。",
                    "read_focus": ["NuRec 3DGS libraries", "Fabric Scene Delegate", "PhysX/Newton", "Warp-based Core API"],
                },
                "lyra_2": {
                    "status": "2026_generative_world_model",
                    "url": "https://research.nvidia.com/labs/toronto-ai/lyra/",
                    "source_title": "NVIDIA Research Lyra",
                    "input": ["text", "single_image", "video"],
                    "output": ["3DGS_world", "explorable_long_horizon_world"],
                    "why_relevant": "从生成式输入产生 3DGS 世界，适合未来快速构造仿真场景。",
                    "read_focus": ["3DGS decoder", "text/image/video-to-3D", "Isaac Sim import", "dynamic 3D/4D scenes"],
                },
                "physically_embodied_gaussians": {
                    "status": "adjacent_frontier_research",
                    "url": "https://developer.nvidia.com/blog/building-robotic-mental-models-with-nvidia-warp-and-gaussian-splatting/",
                    "source_title": "NVIDIA Blog: Building Robotic Mental Models with NVIDIA Warp and Gaussian Splatting",
                    "input": ["few_camera_views", "robot_priors", "interaction_feedback"],
                    "output": ["particles_plus_3D_Gaussians_live_world_model"],
                    "why_relevant": "把视觉高斯和物理粒子绑定，让机器人边看边更新物理世界模型。",
                    "read_focus": ["particles + Gaussians dual representation", "differentiable rendering", "NVIDIA Warp", "gsplat"],
                },
                "marble_isaac_nurec_workflow": {
                    "status": "integration_workflow",
                    "url": "https://developer.nvidia.com/blog/simulate-robotic-environments-faster-with-nvidia-isaac-sim-and-world-labs-marble/",
                    "source_title": "NVIDIA Blog: Simulate Robotic Environments Faster with NVIDIA Isaac Sim and World Labs Marble",
                    "input": ["Gaussian_splat_PLY", "collider_GLB"],
                    "output": ["USDZ_or_Isaac_Sim_scene"],
                    "why_relevant": "工程上展示了 photoreal splat 与 collider mesh 必须对齐。",
                    "read_focus": ["Gaussian splat PLY", "collider GLB", "PLY-to-USDZ", "Gaussian/collider alignment"],
                },
            }

            nvidia_frontier_link_map = {
                name: {
                    "source_title": record["source_title"],
                    "url": record["url"],
                    "read_focus": record["read_focus"],
                }
                for name, record in nvidia_frontiers_2026.items()
            }

            def classify_gaussian_method(name, record):
                # 把“高斯”按职责拆开，防止把视觉表示、碰撞几何、统计 KDE 混为一谈。
                if record["role"] == "visual_rendering":
                    return "视觉层"
                if record["role"] in {"physical_collision", "manipulable_objects", "mechanical_properties"}:
                    return "物理/几何层"
                if record["role"] == "statistical_density_estimation":
                    return "统计分析层"
                return "其他"

            layer_map = {
                name: classify_gaussian_method(name, record)
                for name, record in robolab_gaussian_stack.items()
            }

            gaussian_method_tests = [
                (
                    "paper_has_visual_splat_and_physics_mesh",
                    robolab_gaussian_stack["gaussian_splat_background"]["direct_in_paper"]
                    and robolab_gaussian_stack["collision_mesh_for_splat"]["direct_in_paper"],
                ),
                (
                    "gaussian_splat_not_claimed_as_physics",
                    robolab_gaussian_stack["gaussian_splat_background"]["physics_contact"] is False,
                ),
                (
                    "collision_mesh_is_contact_layer",
                    robolab_gaussian_stack["collision_mesh_for_splat"]["physics_contact"] is True,
                ),
                (
                    "foreground_mesh_is_manipulation_layer",
                    robolab_gaussian_stack["mesh_foreground_objects"]["role"] == "manipulable_objects",
                ),
                (
                    "vomp_is_mechanical_not_rendering",
                    robolab_gaussian_stack["vomp_mass_density"]["role"] == "mechanical_properties",
                ),
                (
                    "mnpe_kde_is_statistical_not_3dgs",
                    layer_map["mnpe_gaussian_kde"] == "统计分析层",
                ),
                (
                    "frontiers_cover_nurec_3dgut_lyra",
                    all(key in nvidia_frontiers_2026 for key in ["omniverse_nurec", "3dgut_3dgrt", "lyra_2"]),
                ),
                (
                    "each_frontier_has_url",
                    all(record["url"].startswith("https://") for record in nvidia_frontiers_2026.values()),
                ),
                (
                    "each_frontier_has_read_focus",
                    all(record["read_focus"] for record in nvidia_frontiers_2026.values()),
                ),
                (
                    "frontier_link_map_includes_marble_workflow",
                    "marble_isaac_nurec_workflow" in nvidia_frontier_link_map,
                ),
                (
                    "each_frontier_has_input_and_output",
                    all(record["input"] and record["output"] for record in nvidia_frontiers_2026.values()),
                ),
                (
                    "isaac_sim_6_marked_as_2026_integration",
                    nvidia_frontiers_2026["isaac_sim_6_nurec"]["status"] == "2026_early_developer_release",
                ),
                (
                    "not_all_frontiers_claimed_as_robolab_direct_use",
                    nvidia_frontiers_2026["physically_embodied_gaussians"]["status"] == "adjacent_frontier_research",
                ),
            ]

            report = {
                "robolab_gaussian_stack": robolab_gaussian_stack,
                "layer_map": layer_map,
                "nvidia_frontiers_2026": nvidia_frontiers_2026,
                "nvidia_frontier_link_map": nvidia_frontier_link_map,
                "tests": [{"name": name, "passed": bool(ok)} for name, ok in gaussian_method_tests],
                "all_passed": all(ok for _, ok in gaussian_method_tests),
                "boundary": "This is a source-grounded conceptual test. It does not run NuRec/3DGS rendering or Isaac Sim physics.",
            }

            print(json.dumps(report, ensure_ascii=False, indent=2))
            for name, ok in gaussian_method_tests:
                print(f"{name}: {'PASS' if ok else 'FAIL'}")

            assert report["all_passed"], gaussian_method_tests
            write_status("gaussian_sim_methods_lightweight_tests", report)
            """
        ),
        md(
            """
            ## 0.19 论文精讲：剩余核心内容与评测证据链

            下面这节来自本目录的 [EXPLAIN_13_remaining_core_topics.md](./EXPLAIN_13_remaining_core_topics.md)。它不是重复前面的 scene/task/solver/MNPE/Gaussian，而是补论文里还没系统讲透的评测侧核心：实验协议、`success` 与 `score` 的区别、语言变体、复杂度 sweep、事件追踪、真实世界相关性、统计置信和限制边界。
            """
        ),
        md_file("EXPLAIN_13_remaining_core_topics.md"),
        code(
            r"""
            # ===== 精讲13：剩余核心内容覆盖轻量验证 =====
            # 这个 cell 把“还有哪些论文核心内容没讲透”变成一份可检查 coverage map。
            # 它不替代论文实验，只验证 notebook 新增章节确实覆盖评测证据链的关键节点。

            import json
            from math import sqrt

            remaining_core_topics = {
                "evaluation_protocol": {
                    "paper_section": "IV-A Experiment Setup",
                    "input": ["task", "scene", "instruction", "robot", "policy", "camera_config", "variation_seed"],
                    "output": ["episode_results", "HDF5", "videos", "event_logs"],
                    "why": "定义什么才算论文级 rollout，而不是单个好看的仿真视频。",
                    "covered_in_explain13": True,
                },
                "success_vs_score_gap": {
                    "paper_section": "III-C Metrics / IV-B Task Results",
                    "input": ["subtask_state", "termination_state"],
                    "output": ["strict_success", "partial_score"],
                    "why": "success 看最终完成，score 看中间能力；二者差距暴露模型部分理解。",
                    "covered_in_explain13": True,
                },
                "language_variations": {
                    "paper_section": "III-C Language Variations / IV-B instruction specificity",
                    "input": ["default_instruction", "vague_instruction", "specific_instruction"],
                    "output": ["success_by_instruction_type"],
                    "why": "验证策略是否理解目标状态，而不是只记住固定语言模板。",
                    "covered_in_explain13": True,
                },
                "complexity_sweeps": {
                    "paper_section": "IV-B instruction specificity / scene complexity / task horizon",
                    "input": ["instruction_specificity", "visible_object_count", "subtask_count"],
                    "output": ["performance_degradation_curve"],
                    "why": "定位失败来自语言抽象、视觉干扰还是长时序规划。",
                    "covered_in_explain13": True,
                },
                "event_tracking_failures": {
                    "paper_section": "Figure 3 and docs/event_tracking.md",
                    "input": ["world_state", "contact_state", "target_object_list"],
                    "output": ["wrong_object", "dropped_target", "hit_table", "object_moved"],
                    "why": "把失败从一个 False 拆成可诊断的行为错误。",
                    "covered_in_explain13": True,
                },
                "real_world_verification": {
                    "paper_section": "IV-D Real-World Verification",
                    "input": ["robolab_success_rate_by_policy", "roboarena_elo_by_policy"],
                    "output": ["rank_correlation", "proxy_interpretation"],
                    "why": "解释 RoboLab 为什么可以作为真实评测 proxy，但不是逐任务等价证明。",
                    "covered_in_explain13": True,
                },
                "statistical_confidence_dashboard": {
                    "paper_section": "Appendix A-A and dashboard docs",
                    "input": ["episode_results_jsonl", "score_samples", "success_samples"],
                    "output": ["CI", "dashboard_tables", "analysis_csv"],
                    "why": "防止用一条 episode 视频替代多 episode 统计结论。",
                    "covered_in_explain13": True,
                },
                "limitations_boundary": {
                    "paper_section": "V Limitations",
                    "input": ["task_type", "object_physics", "instruction_ambiguity"],
                    "output": ["benchmark_scope_judgment"],
                    "why": "区分策略失败、环境失败和 benchmark 当前不擅长回答的问题。",
                    "covered_in_explain13": True,
                },
            }

            def strict_success(final_state):
                # 论文里的 success 是最终状态是否满足 termination，不关心中途做到多少。
                return bool(final_state.get("termination_success", False))

            def partial_score(group_progress):
                # 教学版 score：每个对象有 4 步，返回平均完成比例。
                return sum(done / total for done, total in group_progress.values()) / len(group_progress)

            def spearman_rank(xs, ys):
                # 简化 Spearman：输入无并列名次时，计算两个排序的 Pearson。
                x_rank = {item: rank for rank, item in enumerate(sorted(xs, key=xs.get), start=1)}
                y_rank = {item: rank for rank, item in enumerate(sorted(ys, key=ys.get), start=1)}
                common = list(x_rank)
                xr = [x_rank[k] for k in common]
                yr = [y_rank[k] for k in common]
                mean_x = sum(xr) / len(xr)
                mean_y = sum(yr) / len(yr)
                cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(xr, yr))
                var_x = sum((a - mean_x) ** 2 for a in xr)
                var_y = sum((b - mean_y) ** 2 for b in yr)
                return cov / sqrt(var_x * var_y)

            def route_failure_case(case):
                # 把失败归因到复现问题、策略问题、证据规模问题或 benchmark 边界。
                if case.get("asset_missing") or case.get("env_crash"):
                    return "复现环境问题"
                if case.get("deformable") or case.get("force_control"):
                    return "RoboLab 当前边界"
                if case.get("single_episode_only"):
                    return "证据规模不足"
                if case.get("wrong_object") or case.get("dropped_target"):
                    return "策略泛化/执行问题"
                return "需要查看 event/HDF5/video"

            score_example = {
                "banana": (4, 4),
                "rubiks_cube": (1, 4),
            }
            strict_example = strict_success({"termination_success": False})
            score_value = partial_score(score_example)

            robolab_policy_rank = {"pi05": 0.28, "pi0": 0.155, "groot": 0.072, "paligemma": 0.034}
            roboarena_policy_rank = {"pi05": 1300, "pi0": 1200, "groot": 1100, "paligemma": 1000}
            rank_corr = spearman_rank(robolab_policy_rank, roboarena_policy_rank)

            explain13_tests = [
                ("all_remaining_topics_marked_covered", all(topic["covered_in_explain13"] for topic in remaining_core_topics.values())),
                ("each_topic_has_input_output_why", all(topic["input"] and topic["output"] and topic["why"] for topic in remaining_core_topics.values())),
                ("success_can_be_false_while_score_positive", strict_example is False and 0.0 < score_value < 1.0),
                ("language_variations_include_three_types", set(remaining_core_topics["language_variations"]["input"]) == {"default_instruction", "vague_instruction", "specific_instruction"}),
                ("complexity_sweeps_cover_three_axes", set(remaining_core_topics["complexity_sweeps"]["input"]) == {"instruction_specificity", "visible_object_count", "subtask_count"}),
                ("event_tracking_covers_wrong_and_dropped", {"wrong_object", "dropped_target"}.issubset(set(remaining_core_topics["event_tracking_failures"]["output"]))),
                ("real_world_proxy_uses_rank_correlation", remaining_core_topics["real_world_verification"]["output"][0] == "rank_correlation" and rank_corr > 0.99),
                ("limitation_router_detects_deformable_boundary", route_failure_case({"deformable": True}) == "RoboLab 当前边界"),
                ("limitation_router_detects_single_episode_gap", route_failure_case({"single_episode_only": True}) == "证据规模不足"),
                ("environment_failure_not_confused_with_policy_failure", route_failure_case({"asset_missing": True}) == "复现环境问题"),
            ]

            report = {
                "remaining_core_topics": remaining_core_topics,
                "score_example": {
                    "group_progress": score_example,
                    "strict_success": strict_example,
                    "partial_score": score_value,
                    "interpretation": "模型做完 banana 但 cube 只完成抓取，所以最终失败但有部分分数。",
                },
                "rank_correlation_example": {
                    "robolab_policy_rank": robolab_policy_rank,
                    "roboarena_policy_rank": roboarena_policy_rank,
                    "spearman": rank_corr,
                    "boundary": "Toy ranking example for explaining proxy interpretation, not a fresh RoboArena result.",
                },
                "failure_routing_examples": {
                    "asset_missing": route_failure_case({"asset_missing": True}),
                    "deformable": route_failure_case({"deformable": True}),
                    "single_episode": route_failure_case({"single_episode_only": True}),
                    "wrong_object": route_failure_case({"wrong_object": True}),
                },
                "tests": [{"name": name, "passed": bool(ok)} for name, ok in explain13_tests],
                "all_passed": all(ok for _, ok in explain13_tests),
                "boundary": "This coverage check validates the explanation map. It does not rerun RoboLab-120 or compute new policy statistics.",
            }

            print(json.dumps(report, ensure_ascii=False, indent=2))
            for name, ok in explain13_tests:
                print(f"{name}: {'PASS' if ok else 'FAIL'}")

            assert report["all_passed"], explain13_tests
            write_status("remaining_core_topics_lightweight_tests", report)
            """
        ),
        md(
            """
            ## 0.20 代码精讲：policy rollout 到证据链

            下面这节来自本目录的 [EXPLAIN_14_core_code_runtime_chain.md](./EXPLAIN_14_core_code_runtime_chain.md)。它补的是前面还没系统讲透的源码主干：`runner.py` 如何调度任务，`episode.py` 如何逐步执行 policy，`InferenceClient` / `Pi0DroidJointposClient` 如何把观测转成模型请求，`WorldState` / `EventTracker` / `RecorderManager` / `summarize_run` / `dashboard loader` 如何把 rollout 变成可分析证据。
            """
        ),
        md_file("EXPLAIN_14_core_code_runtime_chain.md"),
        code(
            r"""
            # ===== 精讲14：核心代码运行链路轻量验证 =====
            # 这个 cell 不启动 Isaac，也不连 OpenPI server。
            # 它把源码主干拆成可检查的节点与接口，验证 runner -> episode -> client -> env/world
            # -> event -> recorder -> summarize -> dashboard 这条证据链完整闭合。

            import json

            runtime_code_chain = [
                {
                    "stage": "runner",
                    "files": ["robolab/eval/runner.py", "policies/pi0_family/run.py"],
                    "core_functions": ["add_common_eval_args", "run_evaluation", "client_factory"],
                    "input": ["task_or_tag", "num_envs", "num_runs", "instruction_type", "video_mode", "policy_name"],
                    "output": ["output_dir", "task_envs", "episode_results_jsonl", "env_cfg"],
                    "failure_hint": "任务没跑、续跑跳过、num_envs OOM、输出目录不对，优先查这里。",
                },
                {
                    "stage": "episode_loop",
                    "files": ["robolab/eval/episode.py"],
                    "core_functions": ["run_episode", "TimingStats"],
                    "input": ["env", "env_cfg", "episode_index", "InferenceClient", "video_mode"],
                    "output": ["env_results", "subtask_status", "timing", "videos", "run_hdf5"],
                    "failure_hint": "动作没进 env、视频不写、已终止 env 还在动，优先查这里。",
                },
                {
                    "stage": "inference_client_contract",
                    "files": ["robolab/eval/base_client.py"],
                    "core_functions": ["infer", "_extract_observation", "_pack_request", "_query_server", "_unpack_response", "_postprocess_chunk"],
                    "input": ["raw_obs", "instruction", "env_id"],
                    "output": ["action", "viz"],
                    "failure_hint": "接新模型/新机器人时，先确认这五个 hook 的输入输出。",
                },
                {
                    "stage": "pi05_client_adapter",
                    "files": ["policies/pi0_family/client.py"],
                    "core_functions": ["Pi0DroidJointposClient", "_extract_observation", "_pack_request", "_infer_with_retry", "_postprocess_chunk"],
                    "input": ["over_shoulder_left_camera", "wrist_cam", "arm_joint_pos", "gripper_pos", "prompt"],
                    "output": ["openpi_request", "action_chunk", "binary_gripper_action"],
                    "failure_hint": "server 连上但动作怪，重点查 OpenPI request key、图像 resize、action horizon、gripper 二值化。",
                },
                {
                    "stage": "env_world_conditionals",
                    "files": ["robolab/core/environments/env.py", "robolab/core/world/world_state.py", "robolab/core/task/conditionals.py"],
                    "core_functions": ["RobolabEnv.step", "get_world", "WorldState", "object_in_container", "object_grabbed"],
                    "input": ["actions", "scene_entities", "contact_sensors", "object_poses"],
                    "output": ["termination_state", "subtask_state", "spatial_relations", "contact_relations"],
                    "failure_hint": "视频看着成功但 success=False，重点查 WorldState、contact、bbox、tolerance、detached 条件。",
                },
                {
                    "stage": "event_tracking",
                    "files": ["robolab/core/task/event_tracker.py"],
                    "core_functions": ["EventTracker", "check_events", "reset_envs"],
                    "input": ["per_env_intended_targets", "frozen_mask", "world_state"],
                    "output": ["wrong_object", "target_dropped", "hit_table", "object_moved", "env_mask"],
                    "failure_hint": "失败原因空或不准，查 event tracker 是否触发和 recorder 是否导出事件。",
                },
                {
                    "stage": "recording",
                    "files": ["robolab/core/logging/recorder_manager.py", "robolab/core/logging/streaming_hdf5_handler.py"],
                    "core_functions": ["RobolabRecorderManager", "set_hdf5_file", "set_episode_index", "flush_buffer"],
                    "input": ["per_step_state", "actions", "obs", "env_ids"],
                    "output": ["run_0.hdf5", "demo_0", "demo_1"],
                    "failure_hint": "HDF5 空、demo 缺失、长 episode 内存涨，优先查 recorder manager。",
                },
                {
                    "stage": "summarize_results",
                    "files": ["robolab/eval/summarize.py", "robolab/core/logging/results.py"],
                    "core_functions": ["summarize_run", "build_run_summary", "update_experiment_results", "summarize_experiment_results"],
                    "input": ["env_results", "events", "HDF5", "env_cfg", "timing"],
                    "output": ["log_0_env0.json", "episode_results.jsonl", "trajectory_metrics", "score"],
                    "failure_hint": "视频/HDF5 有了但 JSONL 没新增，查 summarize_run 和 update_experiment_results。",
                },
                {
                    "stage": "dashboard_loader",
                    "files": ["dashboard/loaders/local.py"],
                    "core_functions": ["_cached_load_episodes", "_sr_beta_ci", "_score_ci", "EpisodeRow", "TaskSummary"],
                    "input": ["episode_results.jsonl", "task_folders", "HDF5", "videos", "logs"],
                    "output": ["dashboard_rows", "success_rate_CI", "score_CI", "video_links"],
                    "failure_hint": "Dashboard 看不到结果，查路径、mtime cache、JSONL/HDF5/video 是否齐全。",
                },
            ]

            stage_order = [item["stage"] for item in runtime_code_chain]

            def route_runtime_issue(symptom):
                # 教学版故障路由，用来把复现问题快速定位到代码层。
                text = symptom.lower()
                if "task" in text or "skip" in text or "oom" in text:
                    return "runner"
                if "server" in text or "request" in text or "action horizon" in text or "gripper" in text:
                    return "pi05_client_adapter"
                if "success=false" in text or "condition" in text or "contact" in text:
                    return "env_world_conditionals"
                if "wrong object" in text or "dropped" in text or "hit table" in text:
                    return "event_tracking"
                if "hdf5" in text or "demo" in text:
                    return "recording"
                if "jsonl" in text or "summary" in text:
                    return "summarize_results"
                if "dashboard" in text or "ci" in text:
                    return "dashboard_loader"
                return "episode_loop"

            expected_contract_hooks = {
                "_extract_observation",
                "_pack_request",
                "_query_server",
                "_unpack_response",
                "_postprocess_chunk",
            }
            client_hooks = set(runtime_code_chain[2]["core_functions"])

            code_chain_tests = [
                ("chain_starts_with_runner", stage_order[0] == "runner"),
                ("chain_ends_with_dashboard_loader", stage_order[-1] == "dashboard_loader"),
                ("episode_loop_between_runner_and_client", stage_order.index("runner") < stage_order.index("episode_loop") < stage_order.index("inference_client_contract")),
                ("client_contract_has_required_hooks", expected_contract_hooks.issubset(client_hooks)),
                ("pi05_client_exposes_droid_observation_keys", {"over_shoulder_left_camera", "wrist_cam", "arm_joint_pos", "gripper_pos", "prompt"}.issubset(set(runtime_code_chain[3]["input"]))),
                ("world_layer_outputs_conditions", {"termination_state", "subtask_state", "contact_relations"}.issubset(set(runtime_code_chain[4]["output"]))),
                ("event_layer_outputs_failure_taxonomy", {"wrong_object", "target_dropped", "hit_table"}.issubset(set(runtime_code_chain[5]["output"]))),
                ("recording_layer_outputs_hdf5_demos", {"run_0.hdf5", "demo_0"}.issubset(set(runtime_code_chain[6]["output"]))),
                ("summarize_layer_outputs_jsonl", "episode_results.jsonl" in runtime_code_chain[7]["output"]),
                ("issue_router_maps_hdf5_to_recording", route_runtime_issue("HDF5 demo_0 is empty") == "recording"),
                ("issue_router_maps_success_false_to_world", route_runtime_issue("video success but success=False contact mismatch") == "env_world_conditionals"),
                ("issue_router_maps_server_to_client", route_runtime_issue("OpenPI server request action horizon wrong") == "pi05_client_adapter"),
            ]

            report = {
                "runtime_code_chain": runtime_code_chain,
                "stage_order": stage_order,
                "issue_routing_examples": {
                    "hdf5_empty": route_runtime_issue("HDF5 demo_0 is empty"),
                    "success_false": route_runtime_issue("video success but success=False contact mismatch"),
                    "server_request": route_runtime_issue("OpenPI server request action horizon wrong"),
                    "dashboard_missing": route_runtime_issue("dashboard cannot find CI rows"),
                },
                "tests": [{"name": name, "passed": bool(ok)} for name, ok in code_chain_tests],
                "all_passed": all(ok for _, ok in code_chain_tests),
                "boundary": "This validates the source-code mental model only. It does not import Isaac Sim or call a policy server.",
            }

            print(json.dumps(report, ensure_ascii=False, indent=2))
            for name, ok in code_chain_tests:
                print(f"{name}: {'PASS' if ok else 'FAIL'}")

            assert report["all_passed"], code_chain_tests
            write_status("core_code_runtime_chain_lightweight_tests", report)
            """
        ),
        md(
            """
            ## 0.21 全文精讲：审稿人视角评价与未来创新方向

            下面这节来自本目录的 [EXPLAIN_15_reviewer_synthesis.md](./EXPLAIN_15_reviewer_synthesis.md)。它把论文从头到尾重新串起来，并换成“审稿人视角”看它到底强在哪里、主要风险在哪里、复现侧应该优先优化什么，以及未来可以往哪些创新方向继续做。
            """
        ),
        md_file("EXPLAIN_15_reviewer_synthesis.md"),
        code(
            r"""
            # ===== 精讲15：全文审稿视角轻量验证 =====
            # 这个 cell 不代表正式审稿意见，也不新增论文实验。
            # 它的作用是把“全文总梳理 + 审稿人评价 + 未来创新方向”变成可检查的结构化记录，
            # 防止精讲只停留在长文本，后续复盘时可以直接检查覆盖面。

            import json

            reviewer_synthesis = {
                "paper_type": "benchmark_system_evaluation",
                "provisional_verdict": "weak_accept_to_accept_boundary_for_learning_review",
                "summary": (
                    "RoboLab 最强的贡献不是单点策略算法，而是把高保真仿真、任务/场景生成、"
                    "策略接入、细粒度诊断、扰动敏感性和真实世界相关性组织成一个可运行的评测框架。"
                ),
                "contributions": {
                    "framework": "提供从 scene/task/env 到 policy rollout、日志、视频、指标和 dashboard 的完整评测闭环。",
                    "benchmark": "构建 RoboLab-120，用 visual、procedural、relational 能力轴组织任务。",
                    "diagnostics": "不只报告 success rate，还记录 score、事件失败、任务属性、对象数和子任务数。",
                    "sensitivity": "用 MNPE/NPE 分析相机、光照、背景、纹理等扰动对策略表现的影响。",
                    "generation": "用 LLM 生成语义场景和任务，再通过语法、资源、空间和物理检查做修复。",
                    "real_world_proxy": "用 RoboArena 等真实机器人结果检查仿真 benchmark 的外部相关性。",
                    "toolchain": "公开 GitHub、运行入口、dashboard、策略客户端和复现所需工程结构。",
                },
                "strengths": [
                    "诊断粒度比只看二值成功率更高，能解释失败类型和能力短板。",
                    "任务覆盖更接近真实桌面操作中的多对象、多属性、多步骤组合。",
                    "generation + validation + feedback loop 让 benchmark 可扩展，而不是手写少量固定场景。",
                    "同一框架能比较策略、扰动敏感性、任务难度和真实世界 proxy 排名。",
                    "工程链路较完整，复现时可以追踪到视频、HDF5、JSONL、event log 和 dashboard。",
                ],
                "major_concerns": {
                    "real_world_correlation_depth": (
                        "真实世界相关性是重要亮点，但还需要更细粒度地说明哪些任务、哪些能力轴、"
                        "哪些失败类型能稳定预测真实机器人表现。"
                    ),
                    "rigid_tabletop_scope": (
                        "当前主要是刚体桌面操作，离软体、铰链、液体、工具使用和长程导航还有距离。"
                    ),
                    "task_generation_governance": (
                        "LLM 生成任务很有扩展性，但需要更系统的版本控制、去重、难度校准和无效任务审计。"
                    ),
                    "sim_fidelity_audit": (
                        "论文强调视觉/几何保真，但需要更多关于接触、摩擦、遮挡、质量、反光和 collision mesh 的误差分析。"
                    ),
                    "evaluation_cost": (
                        "完整 RoboLab-120 对 24GB 4090 用户成本较高，需要官方级 subset、early-stop 和低成本统计协议。"
                    ),
                },
                "minor_concerns": [
                    "README 的测试命令和当前仓库文件面不完全一致，需要记录版本差异。",
                    "资产 LFS 下载慢会影响复现体验，建议提供按任务解析依赖的 manifest。",
                    "4090 复现需要明确 num_envs、视频开关、headless 和缓存策略。",
                    "prompt、solver、validator 的版本最好和任务元数据一起固化。",
                ],
                "future_directions": {
                    "real_correlation": "建立 RoboLab-RealCorrelation：按任务属性/失败类型预测真实机器人表现，而不是只做总体排名相关。",
                    "adversarial_task_generation": "让 LLM/搜索器主动生成能区分策略能力边界的 hard cases，并用 validator 控制物理可行性。",
                    "causal_mnpe": "把 MNPE 从相关性敏感分析推进到因果扰动设计，回答哪个场景因素真正导致失败。",
                    "deformable_contact_rich": "加入软体、铰链、工具、液体、推拉旋拧等接触密集任务，突破刚体 tabletop 边界。",
                    "neural_scene_nurec": "结合 NuRec、3DGS/3DGUT/3DGRT 等 neural scene 方法，让真实场景外观进入可交互评测闭环。",
                    "low_cost_24gb_protocol": "设计 24GB GPU 友好的分层评测：single-env smoke、能力轴 subset、adaptive sampling、失败优先重跑。",
                    "unified_policy_adapter": "统一 Pi0/Pi05、RoboChallenge、ReKep、RT-2/ACT 等策略的观测/action adapter 和结果 schema。",
                    "failure_report_generator": "自动把 video、event、HDF5、trajectory metric 和 task metadata 汇总成可读 failure report。",
                },
                "our_next_routes": {
                    "reproduction": [
                        "保持 BananaInBowlTask 完整成功闭环作为 sanity baseline。",
                        "继续按能力轴挑复杂任务补资产、跑视频、记录 failure reason。",
                        "不要在资产未齐、策略 server 未稳、并行度未校准前盲跑完整 RoboLab-120。",
                    ],
                    "comparison": [
                        "把 OpenPI pi05、RoboChallenge pi、ReKep 统一成同一张任务/输入/输出/失败类型表。",
                        "先比较少量代表任务，再扩展到能力轴 subset。",
                    ],
                    "innovation": [
                        "优先做 4090 低成本评测协议和自动 failure report。",
                        "其次做 adversarial task generation 和真实世界相关性细分分析。",
                    ],
                },
                "boundary": (
                    "This is a learning-oriented reviewer synthesis, not an official peer-review decision "
                    "and not a new experiment."
                ),
            }

            required_major_concerns = {
                "real_world_correlation_depth",
                "rigid_tabletop_scope",
                "task_generation_governance",
                "sim_fidelity_audit",
                "evaluation_cost",
            }
            required_future_routes = {
                "real_correlation",
                "adversarial_task_generation",
                "causal_mnpe",
                "deformable_contact_rich",
                "neural_scene_nurec",
                "low_cost_24gb_protocol",
                "unified_policy_adapter",
                "failure_report_generator",
            }

            review_tests = [
                ("classified_as_benchmark_system_paper", reviewer_synthesis["paper_type"] == "benchmark_system_evaluation"),
                ("has_seven_contribution_buckets", len(reviewer_synthesis["contributions"]) >= 7),
                (
                    "strengths_cover_diagnostics_and_toolchain",
                    any("诊断" in item for item in reviewer_synthesis["strengths"])
                    and "toolchain" in reviewer_synthesis["contributions"],
                ),
                (
                    "major_concerns_cover_five_review_axes",
                    required_major_concerns.issubset(set(reviewer_synthesis["major_concerns"])),
                ),
                (
                    "future_directions_cover_eight_routes",
                    required_future_routes.issubset(set(reviewer_synthesis["future_directions"])),
                ),
                ("future_includes_24gb_protocol", "low_cost_24gb_protocol" in reviewer_synthesis["future_directions"]),
                ("future_includes_nurec_or_gaussian", "neural_scene_nurec" in reviewer_synthesis["future_directions"]),
                (
                    "roadmap_has_reproduction_comparison_innovation",
                    set(reviewer_synthesis["our_next_routes"]) == {"reproduction", "comparison", "innovation"},
                ),
                ("boundary_not_official_review", "not an official" in reviewer_synthesis["boundary"]),
                ("boundary_not_new_experiment", "not a new experiment" in reviewer_synthesis["boundary"]),
            ]

            report = {
                "reviewer_synthesis": reviewer_synthesis,
                "tests": [{"name": name, "passed": bool(ok)} for name, ok in review_tests],
                "all_passed": all(ok for _, ok in review_tests),
                "boundary": "Coverage check for EXPLAIN_15 only; it does not execute Isaac Sim, policies, or RoboLab-120.",
            }

            print(json.dumps(report, ensure_ascii=False, indent=2))
            for name, ok in review_tests:
                print(f"{name}: {'PASS' if ok else 'FAIL'}")

            assert report["all_passed"], review_tests
            write_status("reviewer_synthesis_lightweight_tests", report)
            """
        ),
        md(
            """
            ## 0.22 推荐阅读：论文、开源仓库与学习路线

            下面这节来自本目录的 [EXPLAIN_16_recommended_reading.md](./EXPLAIN_16_recommended_reading.md)。它不是泛泛书单，而是基于 RoboLab 的模块来推荐下一步该读的论文和开源项目，并新增 2026-first 阅读层：先看 RoboLab、RoboCasa365、RDT2、GR00T N1.7、Isaac Lab-Arena、Lightwheel LW-BenchHub、Lyra 和 NVIDIA 2026 Physical AI stack，再把 Stanford/Fei-Fei/OmniGibson、DROID、OpenVLA/Octo、ReKep 等作为基础背景。
            """
        ),
        md_file("EXPLAIN_16_recommended_reading.md"),
        code(
            r"""
            # ===== 精讲16：推荐阅读路线轻量验证 =====
            # 这个 cell 把推荐阅读做成结构化 study map。
            # 它不下载论文、模型或数据，只检查推荐列表是否覆盖 RoboLab 后续学习所需的关键方向。

            import json

            reading_items = [
                {
                    "id": "robolab",
                    "title": "NVIDIA RoboLab",
                    "group": "main_paper",
                    "priority": "P0",
                    "urls": ["https://arxiv.org/html/2604.09860", "https://github.com/NVlabs/RoboLab"],
                    "why": "主线论文和代码，定义 scene/task/env/policy/result/dashboard 评测闭环。",
                    "study_focus": ["competency_axes", "task_generation", "policy_eval", "dashboard"],
                    "robolab_link": "source_of_truth",
                },
                {
                    "id": "behavior_1k_omnigibson",
                    "title": "BEHAVIOR-1K / OmniGibson",
                    "group": "stanford_feifei_omnigibson",
                    "priority": "P0",
                    "urls": ["https://proceedings.mlr.press/v205/li23a.html", "https://behavior.stanford.edu/", "https://github.com/StanfordVL/BEHAVIOR-1K"],
                    "why": "人类真实需求驱动的 embodied benchmark，包含长程 household tasks 和 OmniGibson 仿真。",
                    "study_focus": ["long_horizon", "household_tasks", "object_states", "sim_to_real_gap"],
                    "robolab_link": "extends_task_scope",
                },
                {
                    "id": "droid",
                    "title": "DROID",
                    "group": "stanford_real_world_data",
                    "priority": "P0",
                    "urls": ["https://droid-dataset.github.io/", "https://github.com/droid-dataset/droid_policy_learning"],
                    "why": "真实机器人、多地点、多任务 demonstration 数据，是理解 VLA 泛化训练数据的重要来源。",
                    "study_focus": ["real_robot_data", "multi_scene", "policy_learning", "data_schema"],
                    "robolab_link": "real_data_context",
                },
                {
                    "id": "roboarena",
                    "title": "RoboArena",
                    "group": "sim_real_evaluation",
                    "priority": "P0",
                    "urls": ["https://robo-arena.github.io/", "https://arxiv.org/html/2506.18123v1"],
                    "why": "真实世界 generalist robot policy 分布式评测，用来理解 RoboLab 的 real-world correlation。",
                    "study_focus": ["real_world_eval", "ranking", "pairwise_comparison", "correlation"],
                    "robolab_link": "external_validity",
                },
                {
                    "id": "rekep",
                    "title": "ReKep",
                    "group": "constraint_planning",
                    "priority": "P1",
                    "urls": ["https://rekep-robot.github.io/", "https://github.com/huangwl18/ReKep"],
                    "why": "把语言任务变成 3D keypoint constraints，适合作为 VLA 端到端策略的对照路线。",
                    "study_focus": ["keypoint_constraints", "hierarchical_optimization", "closed_loop_control"],
                    "robolab_link": "baseline_contrast",
                },
                {
                    "id": "openpi_pi05",
                    "title": "OpenPI / pi0 / pi0.5",
                    "group": "policy_models",
                    "priority": "P0",
                    "urls": ["https://github.com/Physical-Intelligence/openpi", "https://arxiv.org/abs/2504.16054"],
                    "why": "当前复现使用的 Pi05 系列策略，直接对应 RoboLab policy client 和 action chunk。",
                    "study_focus": ["vla", "action_chunk", "observation_schema", "server_client"],
                    "robolab_link": "current_policy",
                },
                {
                    "id": "isaac_lab_arena",
                    "title": "Isaac Lab / Isaac Lab-Arena",
                    "group": "nvidia_simulation",
                    "priority": "P0",
                    "urls": ["https://github.com/isaac-sim/IsaacLab", "https://github.com/isaac-sim/IsaacLab-Arena"],
                    "why": "RoboLab 的底层仿真生态和未来可组合 benchmark 方向。",
                    "study_focus": ["simulation_framework", "scene_embodiment_task", "sensors", "parallel_envs"],
                    "robolab_link": "runtime_foundation",
                },
                {
                    "id": "lightwheel_lw_benchhub",
                    "title": "Lightwheel / LW-BenchHub / SimReady Assets",
                    "group": "lightwheel_simready",
                    "priority": "P0",
                    "urls": ["https://github.com/LightwheelAI", "https://lightwheel.ai/release/lwlab", "https://docs.lightwheel.net/"],
                    "why": "光轮的 SimReady 资产、场景和 benchmark hub 方向可直接缓解 RoboLab 资产和场景规模化瓶颈。",
                    "study_focus": ["simready_assets", "benchmark_hub", "teleoperation", "vla_finetuning"],
                    "robolab_link": "asset_and_benchmark_scaling",
                },
                {
                    "id": "rdt_1b",
                    "title": "RDT-1B",
                    "group": "tsinghua_embodied",
                    "priority": "P0",
                    "urls": ["https://github.com/thu-ml/RoboticsDiffusionTransformer", "https://rdt-robotics.github.io/rdt-robotics/", "https://arxiv.org/html/2410.07864v1"],
                    "why": "清华 THU-ML/TSAIL 的 diffusion transformer 机器人 foundation model，适合作为 OpenPI/GR00T 的策略路线对照。",
                    "study_focus": ["diffusion_transformer", "unified_action_space", "bimanual", "multi_robot_data"],
                    "robolab_link": "candidate_policy_family",
                },
                {
                    "id": "rdt2",
                    "title": "RDT2",
                    "group": "tsinghua_embodied",
                    "priority": "P1",
                    "urls": ["https://github.com/thu-ml/RDT2", "https://arxiv.org/abs/2602.03310"],
                    "why": "2026 RDT 续作，强调 unseen embodiment zero-shot、RDT2-VQ/RDT2-FM 和 open-world instruction following。",
                    "study_focus": ["unseen_embodiment", "action_tokenizer", "flow_matching", "zero_shot", "umi_video_scale"],
                    "robolab_link": "future_cross_embodiment_eval",
                },
                {
                    "id": "robotwin",
                    "title": "RoboTwin / RoboTwin 2.0",
                    "group": "domestic_generation_benchmark",
                    "priority": "P0",
                    "urls": ["https://robotwin-platform.github.io/", "https://github.com/robotwin-Platform/robotwin"],
                    "why": "双臂 manipulation、generative digital twins、自动任务和 expert data generation，适合对照 RoboLab scene/task generation。",
                    "study_focus": ["bimanual", "digital_twin", "task_program_synthesis", "domain_randomization"],
                    "robolab_link": "generation_pipeline_reference",
                },
                {
                    "id": "robomind",
                    "title": "RoboMIND",
                    "group": "domestic_real_world_data",
                    "priority": "P1",
                    "urls": ["https://x-humanoid-robomind.github.io/", "https://arxiv.org/abs/2412.13877"],
                    "why": "多 embodiment 真实 teleoperation 数据和 failure demonstrations，可启发 RoboLab failure report。",
                    "study_focus": ["multi_embodiment", "failure_demos", "digital_twin", "teleoperation"],
                    "robolab_link": "failure_dataset_inspiration",
                },
                {
                    "id": "rh20t",
                    "title": "RH20T",
                    "group": "contact_rich_data",
                    "priority": "P1",
                    "urls": ["https://rh20t.github.io/", "https://github.com/rh20t/rh20t_api"],
                    "why": "接触丰富、多模态真实机器人数据，补 RoboLab 当前刚体桌面任务的边界。",
                    "study_focus": ["contact_rich", "force", "audio", "multi_modal"],
                    "robolab_link": "future_contact_rich_extension",
                },
                {
                    "id": "groot",
                    "title": "NVIDIA Isaac GR00T N1.7",
                    "group": "nvidia_policy_models",
                    "priority": "P0",
                    "urls": ["https://github.com/NVIDIA/Isaac-GR00T", "https://research.nvidia.com/labs/gear/gr00t-n1_5/"],
                    "why": "2026 当前 GitHub 指向 GR00T N1.7 EA：新 VLM backbone、20K 小时 EgoScale human video、relative EEF action space。",
                    "study_focus": ["vla", "humanoid", "lerobot_format", "finetuning", "relative_eef_action"],
                    "robolab_link": "candidate_policy_family",
                },
                {
                    "id": "cosmos",
                    "title": "NVIDIA Cosmos",
                    "group": "nvidia_world_models",
                    "priority": "P1",
                    "urls": ["https://github.com/nvidia-cosmos", "https://github.com/nvidia-cosmos/cosmos-predict2.5", "https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Releases-New-Physical-AI-Models-as-Global-Partners-Unveil-Next-Generation-Robots/default.aspx"],
                    "why": "2026 NVIDIA Physical AI stack 的 world model 方向，适合未来做场景扰动、合成数据和 world model 预演。",
                    "study_focus": ["world_foundation_model", "synthetic_data", "physical_ai", "video_prediction", "cosmos_transfer_predict_reason"],
                    "robolab_link": "future_scene_generation_and_augmentation",
                },
                {
                    "id": "nvidia_physical_ai_2026_release",
                    "title": "NVIDIA 2026 Physical AI Release",
                    "group": "nvidia_physical_ai_ecosystem",
                    "priority": "P0",
                    "urls": ["https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Releases-New-Physical-AI-Models-as-Global-Partners-Unveil-Next-Generation-Robots/default.aspx"],
                    "why": "2026-01-05 官方发布把 Cosmos、GR00T、Isaac Lab-Arena、OSMO 和 LeRobot integration 放到同一条 physical AI workflow。",
                    "study_focus": ["physical_ai_stack", "cosmos", "groot", "isaac_lab_arena", "lerobot"],
                    "robolab_link": "ecosystem_roadmap",
                },
                {
                    "id": "lyra_2026",
                    "title": "NVIDIA Research Lyra",
                    "group": "nvidia_world_models",
                    "priority": "P1",
                    "urls": ["https://research.nvidia.com/labs/toronto-ai/lyra/"],
                    "why": "ICLR 2026 生成式 3D/4D Gaussian 场景方向，可作为 RoboLab 未来快速生成候选场景的前沿参照。",
                    "study_focus": ["3d_gaussian_scene_generation", "text_image_video_to_3d", "isaac_sim_import", "world_model"],
                    "robolab_link": "future_scene_generation_and_augmentation",
                },
                {
                    "id": "simready_foundation",
                    "title": "NVIDIA SimReady Foundation",
                    "group": "nvidia_simready",
                    "priority": "P0",
                    "urls": ["https://github.com/NVIDIA/simready-foundation"],
                    "why": "学习可仿真 USD/SimReady 资产规范，解释 RoboLab LFS、collision、physics、scale、semantic label 问题。",
                    "study_focus": ["usd", "lfs", "asset_validation", "physics_properties"],
                    "robolab_link": "asset_preflight",
                },
                {
                    "id": "robocasa365",
                    "title": "RoboCasa / RoboCasa365",
                    "group": "nvidia_related_household_benchmark",
                    "priority": "P1",
                    "urls": ["https://robocasa.ai/", "https://github.com/robocasa/robocasa", "https://github.com/robocasa/robocasa/releases", "https://arxiv.org/html/2603.04356v1"],
                    "why": "ICLR 2026 / v1.0 release 的大规模 kitchen/household simulation benchmark，可对照 RoboLab 的桌面操作和任务规模。",
                    "study_focus": ["kitchen_tasks", "household_simulation", "demonstrations", "benchmarking", "365_tasks"],
                    "robolab_link": "household_scale_reference",
                },
                {
                    "id": "openvla",
                    "title": "OpenVLA",
                    "group": "policy_models",
                    "priority": "P1",
                    "urls": ["https://github.com/openvla/openvla", "https://arxiv.org/html/2406.09246v1"],
                    "why": "开源 7B VLA 代表，适合对照 OpenPI/GR00T/RDT 的 policy adapter 设计。",
                    "study_focus": ["rlds", "finetuning", "libero_eval", "bridge_data"],
                    "robolab_link": "candidate_policy_family",
                },
                {
                    "id": "octo",
                    "title": "Octo",
                    "group": "policy_models",
                    "priority": "P1",
                    "urls": ["https://octo-models.github.io/", "https://github.com/octo-models/octo"],
                    "why": "开源 generalist robot policy，基于 transformer/diffusion policy，适合做非 OpenPI 基线。",
                    "study_focus": ["diffusion_policy", "generalist_policy", "finetuning", "multi_robot"],
                    "robolab_link": "candidate_policy_family",
                },
                {
                    "id": "lerobot",
                    "title": "LeRobot",
                    "group": "tooling_and_dataset_format",
                    "priority": "P1",
                    "urls": ["https://github.com/huggingface/lerobot", "https://huggingface.co/docs/lerobot/en/index"],
                    "why": "工程化机器人学习工具链，统一 dataset、policy、训练和评测，可作为 RoboLab 输出转数据集的参考。",
                    "study_focus": ["dataset_format", "video_parquet", "policy_training", "hub"],
                    "robolab_link": "data_format_bridge",
                },
                {
                    "id": "simpler",
                    "title": "SIMPLER",
                    "group": "sim_real_evaluation",
                    "priority": "P1",
                    "urls": ["https://simpler-env.github.io/", "https://github.com/simpler-env/SimplerEnv"],
                    "why": "仿真评测预测真实机器人表现的代表工作，可对照 RoboLab 的 real-world correlation。",
                    "study_focus": ["sim_to_real_proxy", "paired_eval", "correlation_metrics", "mmrv"],
                    "robolab_link": "external_validity_reference",
                },
                {
                    "id": "vlabench",
                    "title": "VLABench",
                    "group": "language_conditioned_benchmarks",
                    "priority": "P1",
                    "urls": ["https://vlabench.github.io/", "https://github.com/OpenMOSS/VLABench", "https://arxiv.org/abs/2412.18194"],
                    "why": "长程语言条件机器人 manipulation benchmark，补 RoboLab 的语言理解和常识推理视角。",
                    "study_focus": ["language_conditioned_manipulation", "long_horizon", "spatial_reasoning", "common_sense"],
                    "robolab_link": "competency_axis_reference",
                },
            ]

            # 2026-first 层：把真正当前的前沿源头单独抽出来，避免和历史背景混成一张平表。
            for item in reading_items:
                item.setdefault("release_year", "pre_2026_or_background")
                item.setdefault("recency_tier", "foundation_background")

            for item in reading_items:
                if item["id"] in {
                    "robolab",
                    "rdt2",
                    "groot",
                    "cosmos",
                    "nvidia_physical_ai_2026_release",
                    "lyra_2026",
                    "robocasa365",
                    "isaac_lab_arena",
                    "lightwheel_lw_benchhub",
                }:
                    item["release_year"] = 2026
                    item["recency_tier"] = "2026_frontier"

            fresh_2026_reading_track = [
                {
                    "id": "robolab",
                    "date_or_version": "arXiv:2604.09860v3, 2026-05-14",
                    "role": "主评测系统",
                    "why_updated": "RoboLab-120、三类能力轴、任务生成、扰动敏感性和真实世界相关性是本次复现主线。",
                    "url": "https://arxiv.org/html/2604.09860",
                },
                {
                    "id": "robocasa365",
                    "date_or_version": "ICLR 2026 / RoboCasa v1.0 release",
                    "role": "household/kitchen benchmark",
                    "why_updated": "365 个任务、2500+ 厨房场景、3200+ 3D 对象、600+ 小时人类示范、1600+ 小时机器人数据，并支持 Pi/GR00T 等评测。",
                    "url": "https://github.com/robocasa/robocasa/releases",
                },
                {
                    "id": "rdt2",
                    "date_or_version": "arXiv:2602.03310, 2026-02",
                    "role": "清华 VLA / diffusion policy",
                    "why_updated": "强调 unseen embodiment zero-shot、RDT2-VQ/RDT2-FM 和 10,000+ 小时 UMI 人类操作视频。",
                    "url": "https://github.com/thu-ml/RDT2",
                },
                {
                    "id": "groot",
                    "date_or_version": "GR00T N1.7 Early Access, 2026 current GitHub",
                    "role": "NVIDIA open VLA policy",
                    "why_updated": "新 VLM backbone、20K 小时 EgoScale human video、relative EEF action space，并标出 16GB+ VRAM inference。",
                    "url": "https://github.com/NVIDIA/Isaac-GR00T",
                },
                {
                    "id": "nvidia_physical_ai_2026_release",
                    "date_or_version": "NVIDIA release, 2026-01-05",
                    "role": "physical AI ecosystem roadmap",
                    "why_updated": "同一官方发布里出现 Cosmos、GR00T、Isaac Lab-Arena、OSMO 和 LeRobot integration。",
                    "url": "https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Releases-New-Physical-AI-Models-as-Global-Partners-Unveil-Next-Generation-Robots/default.aspx",
                },
                {
                    "id": "isaac_lab_arena",
                    "date_or_version": "2026 NVIDIA Technical Blog",
                    "role": "可组合仿真评测框架",
                    "why_updated": "NVIDIA 与 Lightwheel 共建，用于 scalable policy evaluation、task creation、diversification 和 parallel benchmarking。",
                    "url": "https://developer.nvidia.com/blog/simplify-generalist-robot-policy-evaluation-in-simulation-with-nvidia-isaac-lab-arena/",
                },
                {
                    "id": "lightwheel_lw_benchhub",
                    "date_or_version": "2026 active GitHub / LW-BenchHub release page",
                    "role": "benchmark hub / SimReady asset pipeline",
                    "why_updated": "覆盖 SimReady scenes/assets、teleoperation、policy training/evaluation，GitHub 组织下多项目在 2026 持续更新。",
                    "url": "https://lightwheel.ai/release/lwlab",
                },
                {
                    "id": "lyra_2026",
                    "date_or_version": "ICLR 2026",
                    "role": "生成式 3D/4D Gaussian 场景",
                    "why_updated": "text/image/video 到 3D/4D Gaussian 场景，并展示导入 Isaac Sim 的未来路线。",
                    "url": "https://research.nvidia.com/labs/toronto-ai/lyra/",
                },
            ]

            historical_background_track = [
                {
                    "id": "behavior_1k_omnigibson",
                    "why_keep": "仍是家庭任务和 object state 的基础参照，但不是 2026 前沿主线。",
                },
                {
                    "id": "droid",
                    "why_keep": "仍用于理解真实机器人数据分布和 policy 数据源。",
                },
                {
                    "id": "roboarena",
                    "why_keep": "仍用于理解真实世界 ranking 和仿真-真实相关性边界。",
                },
                {
                    "id": "simpler",
                    "why_keep": "仍用于理解 paired sim-real evaluation。",
                },
                {
                    "id": "openvla",
                    "why_keep": "仍是开放 VLA adapter 和 fine-tuning 的基础背景。",
                },
                {
                    "id": "octo",
                    "why_keep": "仍是 generalist diffusion policy 的早期基线。",
                },
                {
                    "id": "rekep",
                    "why_keep": "仍适合作为显式约束规划对照。",
                },
                {
                    "id": "robotwin",
                    "why_keep": "仍可参考 generative digital twins 和自动任务/数据生成。",
                },
                {
                    "id": "robomind",
                    "why_keep": "仍可参考 failure demonstrations 和多 embodiment 数据。",
                },
            ]

            source_evidence_map = {
                "robolab": {
                    "core_problem": "真实 generalist robot policy 的仿真评测是否能揭示泛化、失败模式和扰动敏感性。",
                    "source_content": "高保真仿真、RoboLab-120、能力轴、任务生成、指标、MNPE、真实世界相关性。",
                    "reading_question": "先看 scene -> task -> env -> policy -> event -> result -> dashboard。",
                },
                "behavior_1k_omnigibson": {
                    "core_problem": "机器人 benchmark 是否应从真实人类家庭需求出发。",
                    "source_content": "1000 个日常 household activities、OmniGibson、长程移动操作和 richer object states。",
                    "reading_question": "看 long-horizon task、object state 和 sim-to-real gap。",
                },
                "droid": {
                    "core_problem": "VLA/generalist policy 的真实机器人训练数据从哪里来。",
                    "source_content": "大规模 in-the-wild robot manipulation demonstrations，覆盖多场景、多任务、多采集者。",
                    "reading_question": "看 camera/robot/action schema，不先下载全量数据。",
                },
                "roboarena": {
                    "core_problem": "真实机器人评测如何从单点 success 走向分布式 ranking。",
                    "source_content": "真实世界 generalist policy pairwise comparison 和 ranking 评测。",
                    "reading_question": "看仿真结果和真实 ranking 之间能比较什么、不能比较什么。",
                },
                "rekep": {
                    "core_problem": "关系推理能否用显式 3D keypoint constraints 表达，而不是只靠端到端动作生成。",
                    "source_content": "Relational Keypoint Constraints 和层级优化闭环控制。",
                    "reading_question": "看 keypoint function、constraint cost、hierarchical optimization。",
                },
                "openpi_pi05": {
                    "core_problem": "当前 Pi05 策略如何把多相机、语言和状态转成 action chunk。",
                    "source_content": "openpi 模型和工具包，包含 pi0、pi0-FAST、pi0.5 等 VLA 系列。",
                    "reading_question": "看 server-client、observation schema、action horizon、gripper postprocess。",
                },
                "isaac_lab_arena": {
                    "core_problem": "评测环境如何工程化、组合化、并行化。",
                    "source_content": "Isaac Lab 机器人学习框架，2026 Isaac Lab-Arena 由 NVIDIA 与 Lightwheel 共建，面向 task creation、diversification、parallel benchmarking 和 LeRobot/GR00T/pi0/SmolVLA 集成。",
                    "reading_question": "看 Scene/Embodiment/Task 抽象、parallel env 和 policy evaluation pipeline。",
                },
                "lightwheel_lw_benchhub": {
                    "core_problem": "SimReady 资产和 benchmark hub 如何支撑大规模具身评测。",
                    "source_content": "Lightwheel SimReady assets、LW-BenchHub、teleoperation、policy training/eval pipeline；2026 GitHub 组织页显示 LW-BenchHub、LeIsaac、AutoDataGen 等持续更新。",
                    "reading_question": "看资产规范、benchmark skeleton、teleop、VLA fine-tuning 和 268-task benchmark hub。",
                },
                "simready_foundation": {
                    "core_problem": "普通 3D 模型为什么不能直接用于机器人仿真评测。",
                    "source_content": "OpenUSD content profiles、features、requirements 和 validation workflow。",
                    "reading_question": "看 LFS、default prim、scale、physics、profile validation。",
                },
                "rdt_1b": {
                    "core_problem": "国内 diffusion transformer 路线如何做机器人 foundation policy。",
                    "source_content": "RDT-1B、1M+ 多机器人 episodes、统一动作空间、双臂 manipulation。",
                    "reading_question": "看 unified action space 和 diffusion action generation。",
                },
                "rdt2": {
                    "core_problem": "foundation policy 能否跨 unseen embodiment zero-shot。",
                    "source_content": "arXiv 2602.03310；RDT2-VQ / RDT2-FM、Residual VQ action tokenizer、flow matching、open-world instruction following、10,000+ 小时 UMI 人类操作视频。",
                    "reading_question": "看 action tokenization、flow-matching action expert、4090 推理条件和 unseen embodiment 约束。",
                },
                "robotwin": {
                    "core_problem": "如何自动生成双臂任务、数字孪生资产和专家数据。",
                    "source_content": "RoboTwin 2.0、generative digital twins、object dataset、task program synthesis、domain randomization。",
                    "reading_question": "看 task program synthesis 和 expert data generation。",
                },
                "robomind": {
                    "core_problem": "真实机器人数据是否应该记录失败原因。",
                    "source_content": "多 embodiment teleoperation、failure demonstrations、Isaac Sim digital twin。",
                    "reading_question": "看 failure demos 如何转成反思和修正信号。",
                },
                "rh20t": {
                    "core_problem": "接触丰富 manipulation 需要哪些额外传感。",
                    "source_content": "视觉、力、音频、动作、人类示范视频的 contact-rich robot manipulation 数据。",
                    "reading_question": "看 force/audio/action 对齐和 contact-rich skill taxonomy。",
                },
                "groot": {
                    "core_problem": "NVIDIA generalist robot VLA 如何训练、微调和部署。",
                    "source_content": "Isaac GR00T N1.7 EA、Cosmos-Reason2/Qwen3-VL backbone、20K 小时 EgoScale human video、relative EEF action space、Apache-2.0、16GB+ VRAM inference。",
                    "reading_question": "看 fine-tuning、inference、relative EEF action 和 LeRobot/Policy API 接口。",
                },
                "cosmos": {
                    "core_problem": "世界模型如何补充仿真评测和合成数据生成。",
                    "source_content": "2026 NVIDIA Physical AI 发布中的 Cosmos Transfer/Predict 2.5、Cosmos Reason 2 和 world foundation model route。",
                    "reading_question": "看 world model 如何生成扰动、视频和训练数据。",
                },
                "nvidia_physical_ai_2026_release": {
                    "core_problem": "RoboLab 之外的 2026 NVIDIA physical AI 生态如何把模型、仿真、评测和训练编排连接起来。",
                    "source_content": "2026-01-05 官方发布：Cosmos/GR00T open models、Isaac Lab-Arena、OSMO、HuggingFace LeRobot integration、Jetson Thor/edge compute。",
                    "reading_question": "看它如何把 RoboLab 所在的评测问题放入 end-to-end robot development lifecycle。",
                },
                "lyra_2026": {
                    "core_problem": "能否从 text/image/video 快速生成可导入仿真的 3D/4D 场景。",
                    "source_content": "ICLR 2026 Lyra：video diffusion self-distillation 到 3D/4D Gaussian scenes，并展示 3D Gaussians 导入 Isaac Sim / NuRec 可视化。",
                    "reading_question": "看视觉真实场景生成如何接 OpenUSD/Isaac Sim，以及还缺哪些物理交互层。",
                },
                "robocasa365": {
                    "core_problem": "kitchen/household generalist benchmark 如何大规模组织。",
                    "source_content": "ICLR 2026 / RoboCasa v1.0 release：365 tasks、2500+ kitchen scenes、3200+ 3D objects、600+ 小时人类示范、1600+ 小时机器人数据，并支持 Diffusion Policy、Pi、GR00T benchmarking。",
                    "reading_question": "看 task diversity、scene diversity、demo 数据来源和 policy benchmark protocol。",
                },
                "openvla": {
                    "core_problem": "开源 VLA 如何训练、fine-tune 和评测。",
                    "source_content": "OpenVLA、RLDS 数据混合、LoRA/full fine-tuning、LIBERO/BridgeData eval。",
                    "reading_question": "看 dataset mixture 和 fine-tuning protocol。",
                },
                "octo": {
                    "core_problem": "generalist diffusion policy 如何适配多机器人多任务。",
                    "source_content": "Octo transformer-based diffusion policy，800k robot trajectories。",
                    "reading_question": "看 observation/action flexibility 和 finetuning。",
                },
                "lerobot": {
                    "core_problem": "机器人学习数据、训练、评测如何工程化。",
                    "source_content": "LeRobotDataset、视频/Parquet、HF Hub、policy training/evaluation tools。",
                    "reading_question": "看数据格式桥接 RoboLab HDF5/video 的可能性。",
                },
                "simpler": {
                    "core_problem": "仿真评测如何预测真实机器人表现。",
                    "source_content": "SIMPLER paired sim-real manipulation policy evaluation 和相关性指标。",
                    "reading_question": "看 correlation metrics 和 paired setup。",
                },
                "vlabench": {
                    "core_problem": "语言条件、长程、常识和空间推理如何压测 VLA。",
                    "source_content": "100 task categories、2000+ objects、language-conditioned long-horizon manipulation。",
                    "reading_question": "看 language-conditioned task design 和 competence dimensions。",
                },
            }

            source_groups = {item["group"] for item in reading_items}
            priority_counts = {
                level: sum(1 for item in reading_items if item["priority"] == level)
                for level in ["P0", "P1", "P2"]
            }

            robolab_module_to_reading = {
                "policy_client": ["openpi_pi05", "groot", "rdt2", "openvla", "octo", "rdt_1b", "lerobot"],
                "scene_task_generation": ["robolab", "robotwin", "robocasa365", "lightwheel_lw_benchhub", "cosmos", "lyra_2026", "behavior_1k_omnigibson"],
                "asset_preflight": ["simready_foundation", "lightwheel_lw_benchhub", "isaac_lab_arena"],
                "real_world_correlation": ["droid", "roboarena", "simpler", "robomind"],
                "long_horizon_reasoning": ["behavior_1k_omnigibson", "vlabench", "robocasa365", "robotwin"],
                "failure_analysis": ["robomind", "rh20t", "rekep", "simpler"],
                "4090_practical_repro": ["robolab", "openpi_pi05", "groot", "rdt2", "isaac_lab_arena", "lightwheel_lw_benchhub"],
            }

            required_groups = {
                "stanford_feifei_omnigibson",
                "tsinghua_embodied",
                "lightwheel_simready",
                "nvidia_simulation",
                "policy_models",
                "sim_real_evaluation",
            }
            required_modules = {
                "policy_client",
                "scene_task_generation",
                "asset_preflight",
                "real_world_correlation",
                "long_horizon_reasoning",
                "failure_analysis",
                "4090_practical_repro",
            }

            reading_tests = [
                ("has_at_least_20_items", len(reading_items) >= 20),
                ("covers_required_source_groups", required_groups.issubset(source_groups)),
                ("has_p0_items", priority_counts["P0"] >= 8),
                ("every_item_has_url", all(item["urls"] for item in reading_items)),
                ("every_item_has_robolab_link", all(item["robolab_link"] for item in reading_items)),
                ("source_evidence_covers_every_item", {item["id"] for item in reading_items}.issubset(set(source_evidence_map))),
                ("source_evidence_has_problem_content_question", all({"core_problem", "source_content", "reading_question"}.issubset(entry) for entry in source_evidence_map.values())),
                ("source_evidence_mentions_robolab_main_problem", "仿真评测" in source_evidence_map["robolab"]["core_problem"]),
                ("module_map_covers_key_robolab_topics", required_modules.issubset(set(robolab_module_to_reading))),
                ("policy_client_has_current_policy", "openpi_pi05" in robolab_module_to_reading["policy_client"]),
                ("asset_preflight_has_simready", "simready_foundation" in robolab_module_to_reading["asset_preflight"]),
                ("real_correlation_has_roboarena", "roboarena" in robolab_module_to_reading["real_world_correlation"]),
                ("4090_route_has_robolab_openpi_isaac_lightwheel", {"robolab", "openpi_pi05", "isaac_lab_arena", "lightwheel_lw_benchhub"}.issubset(robolab_module_to_reading["4090_practical_repro"])),
                ("has_2026_frontier_track", len(fresh_2026_reading_track) >= 8),
                ("2026_track_has_robolab_rdt2_groot_robocasa365", {"robolab", "rdt2", "groot", "robocasa365"}.issubset({entry["id"] for entry in fresh_2026_reading_track})),
                ("2026_track_has_lightwheel_isaac_arena_lyra", {"lightwheel_lw_benchhub", "isaac_lab_arena", "lyra_2026"}.issubset({entry["id"] for entry in fresh_2026_reading_track})),
                ("2026_track_has_links", all(entry["url"].startswith("https://") for entry in fresh_2026_reading_track)),
                ("historical_track_explicitly_downgraded", len(historical_background_track) >= 8),
                ("frontier_items_marked_2026", sum(1 for item in reading_items if item["recency_tier"] == "2026_frontier") >= 8),
            ]

            report = {
                "reading_items": reading_items,
                "source_groups": sorted(source_groups),
                "priority_counts": priority_counts,
                "source_evidence_map": source_evidence_map,
                "robolab_module_to_reading": robolab_module_to_reading,
                "fresh_2026_reading_track": fresh_2026_reading_track,
                "historical_background_track": historical_background_track,
                "tests": [{"name": name, "passed": bool(ok)} for name, ok in reading_tests],
                "all_passed": all(ok for _, ok in reading_tests),
                "boundary": "This is a curated reading map with live-checked public URLs. It does not mirror papers, clone repos, download datasets, or validate licenses beyond link-level notes.",
            }

            print(json.dumps(report, ensure_ascii=False, indent=2))
            for name, ok in reading_tests:
                print(f"{name}: {'PASS' if ok else 'FAIL'}")

            assert report["all_passed"], reading_tests
            write_status("recommended_reading_lightweight_tests", report)
            """
        ),
        md(
            """
            ## 0.23 已完成复现：简单任务闭环与复杂任务抽样

            下面两份记录是当前最重要的实测证据：

            - `COMPLETE_REPRO_pi05_banana_20260620.md`：一条完整成功闭环，证明 OpenPI pi05 -> RoboLab -> Isaac Sim -> 视频/HDF5/JSON 输出链路是通的。
            - `COMPLEX_TASKS_pi05_20260620.md`：三个更复杂任务的抽样，证明模型在多物体、长时序、集合式目标上会明显变难。

            读这两节时不要只看 success。更重要的是看输入指令、输出文件、步数、墙钟耗时、policy inference、视频规格和失败类型。
            """
        ),
        md_file("COMPLETE_REPRO_pi05_banana_20260620.md"),
        md_file("COMPLEX_TASKS_pi05_20260620.md"),
        md(
            """
            ## 1. 阶段一：4090 机器前置检查

            目标不是一次性证明能跑完整 benchmark，而是先确认系统符合 RoboLab 当前 README 的基础条件。

            记录点：

            - Ubuntu 版本、内核、Python、CUDA driver。
            - RTX 4090 是否被 `nvidia-smi` 识别，空闲显存是多少。
            - 磁盘空间。官方资产约 7GB，但视频、HDF5、缓存和模型权重会快速增长；建议仍预留 100GB+，完整实验最好 300GB 级别。
            - `uv`、`ffmpeg`、`git-lfs`、`gcc-11` / `g++-11` 是否可用。
            """
        ),
        code(
            r"""
            # ===== 1. 定义前置检查命令 =====
            # 每个 tuple 的第 1 项是日志标签，第 2 项是真正执行的 shell 命令。
            preflight_commands = [
                ("os_release", "cat /etc/os-release"),  # 查看 Ubuntu 版本，RoboLab 要求 Ubuntu 22.04+。
                ("kernel", "uname -a"),  # 记录内核版本，方便排查驱动/Isaac 兼容性问题。
                ("disk", "df -h ."),  # 查看当前磁盘剩余空间，资产和模型权重会占用大量空间。
                ("gpu", "nvidia-smi"),  # 查看 GPU、驱动、显存占用和已有进程。
                ("driver_query", "nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv"),  # 提取关键 GPU 字段，便于写入报告。
                ("python", "python3 --version"),  # RoboLab 当前要求 Python 3.11。
                ("uv", "uv --version"),  # uv 是官方推荐的依赖同步工具。
                ("ffmpeg", "ffmpeg -version | head -n 2"),  # ffmpeg 用于视频/渲染输出相关流程。
                ("git_lfs", "git lfs version"),  # RoboLab 大量资产走 Git LFS。
                ("gcc", "gcc-11 --version | head -n 1"),  # 记录 gcc-11，便于排查编译型依赖。
                ("gpp", "g++-11 --version | head -n 1"),  # 记录 g++-11，便于排查 C++ 扩展编译问题。
            ]

            # ===== 2. 逐条执行或 dry-run 前置检查 =====
            preflight_results = []
            for label, cmd in preflight_commands:
                preflight_results.append(
                    run(cmd, execute=EXECUTE_PREFLIGHT, timeout=60, label=f"preflight:{label}")
                )

            # ===== 3. 写出 preflight 状态文件 =====
            # 即使命令是 dry-run，也会记录“计划检查哪些项目”，方便复现流程审计。
            write_status(
                "preflight_status",
                {
                    "execute_preflight": EXECUTE_PREFLIGHT,
                    "is_linux": IS_LINUX,
                    "commands": [{"label": label, "cmd": cmd} for label, cmd in preflight_commands],
                },
            )
            """
        ),
        md(
            """
            ## 2. 阶段二：安装 RoboLab

            当前推荐路线：

            ```bash
            sudo apt install ffmpeg
            git clone https://github.com/NVlabs/RoboLab
            cd RoboLab
            uv venv --python 3.11
            source .venv/bin/activate
            uv sync
            uv run pytest tests/
            ```

            注意：

            - `uv sync` 会自动处理 Isaac Sim 5.0 + Isaac Lab 2.2.0。
            - 首次运行非测试入口时设置 `OMNI_KIT_ACCEPT_EULA=Y`，避免 GUI/EULA 提示卡住。
            - 4090 只有 24GB VRAM，不要直接照官方示例从 `--num-envs 10` 起步；先 `1`，确认输出完整后再试 `2/4`。
            """
        ),
        code(
            r"""
            # 把安装步骤集中在一个列表里，保证 dry-run 展示和真实执行使用同一套命令。
            install_steps = [
                ("make_work_root", f"mkdir -p {shlex.quote(str(WORK_ROOT))}"),  # 创建 RoboLab 工作区父目录。
                ("clone_robolab", "git clone https://github.com/NVlabs/RoboLab"),  # 拉取 RoboLab 官方仓库。
                ("git_lfs_install", "git lfs install"),  # 启用 Git LFS 支持。
                ("git_lfs_pull", "git lfs pull"),  # 拉取 USD 场景、对象、机器人等大资产。
                ("uv_venv", "uv venv --python 3.11"),  # 创建 Python 3.11 虚拟环境。
                ("uv_sync", "uv sync"),  # 按 pyproject/lock 同步依赖，包括 Isaac Sim/Lab。
                ("freeze", "uv pip freeze"),  # 导出实际安装版本，作为复现证据。
            ]

            if EXECUTE_INSTALL:
                # 真实安装路径：clone/更新仓库 -> 拉 LFS 资产 -> 用 uv 安装 Isaac/RoboLab 依赖。
                WORK_ROOT.mkdir(parents=True, exist_ok=True)
                if not ROBOLAB_DIR.exists():
                    run("git clone https://github.com/NVlabs/RoboLab", cwd=WORK_ROOT, execute=True, check=True, timeout=1800)
                else:
                    # 已存在的仓库只做 fast-forward 更新，避免悄悄覆盖本地修改。
                    run("git rev-parse HEAD", cwd=ROBOLAB_DIR, execute=True, timeout=60, label="repo:current_head")
                    run("git pull --ff-only", cwd=ROBOLAB_DIR, execute=True, check=False, timeout=600, label="repo:pull")
                run("git lfs install", cwd=ROBOLAB_DIR, execute=True, timeout=120, label="install:git_lfs_install")
                run("git lfs pull", cwd=ROBOLAB_DIR, execute=True, timeout=1800, label="install:git_lfs_pull")
                run("uv venv --python 3.11", cwd=ROBOLAB_DIR, execute=True, check=True, timeout=600, label="install:uv_venv")
                run("uv sync", cwd=ROBOLAB_DIR, env=OMNI_ENV, execute=True, check=True, timeout=7200, label="install:uv_sync")
                freeze = run("uv pip freeze", cwd=ROBOLAB_DIR, execute=True, timeout=300, label="install:freeze")
                (ARTIFACT_DIR / "uv_freeze.txt").write_text(freeze.get("stdout", ""), encoding="utf-8")
            else:
                # dry-run 路径只记录命令，不修改本机文件和环境。
                for label, cmd in install_steps:
                    target = WORK_ROOT if label in {"make_work_root", "clone_robolab"} else ROBOLAB_DIR
                    run(cmd, cwd=target, execute=False, label=f"install:{label}")

            write_status(
                "install_plan",
                {
                    "execute_install": EXECUTE_INSTALL,
                    "robolab_dir": str(ROBOLAB_DIR),
                    "notes": [
                        "Main path uses uv sync; do not build Isaac Sim from source unless debugging or developing Isaac Sim itself.",
                        "Record uv sync duration and uv_freeze.txt after a real run.",
                    ],
                },
            )
            """
        ),
        md(
            """
            ## 3. 阶段三：安装验证

            验证目标：

            - Isaac Lab 可以 import。
            - 任务定义有效。
            - env factory 可用。
            - 至少一个完整 episode 可以 headless 跑完。

            通过标准：`uv run pytest tests/` 返回 0，并把完整 stdout/stderr 写入 `command_log.jsonl`。
            """
        ),
        code(
            r"""
            # 测试默认关闭，因为导入 Isaac/Kit 很慢且依赖 GPU/驱动环境。
            run(
                "uv run pytest tests/",
                cwd=ROBOLAB_DIR,
                env=OMNI_ENV,
                execute=EXECUTE_TESTS,
                check=EXECUTE_TESTS,
                timeout=7200,
                label="verify:pytest",
            )
            """
        ),
        md(
            """
            ## 4. 阶段四：无策略 smoke run

            在接入 VLA / Pi0.5 / 自定义策略之前，先跑不依赖策略服务端的 sanity check。

            记录点：

            - 是否能 headless 启动。
            - 是否生成 `output/` 目录、HDF5、subtask log、视频。
            - GPU 显存峰值和每秒迭代数。
            """
        ),
        code(
            r"""
            # 这些示例先验证仿真、任务注册、日志导出链路，不涉及 VLA 策略。
            no_policy_commands = [
                ("empty_episode", "python examples/run_empty.py --headless"),  # 最基础的环境初始化和空动作 episode。
                ("recorded_playback", "python examples/run_recorded.py --headless"),  # 检查录制轨迹回放入口。
                ("gripper_toggle", f"python examples/run_gripper_toggle.py --task {SMOKE_TASK} --headless"),  # 检查指定任务和夹爪动作入口。
            ]

            for label, cmd in no_policy_commands:
                # check=False 表示即使某条 smoke 失败，也保留日志并继续看其它探针结果。
                run(
                    cmd,
                    cwd=ROBOLAB_DIR,
                    env=OMNI_ENV,
                    execute=EXECUTE_NO_POLICY_SMOKE,
                    check=False,
                    timeout=3600,
                    label=f"smoke_no_policy:{label}",
                )
            """
        ),
        md(
            """
            ## 5. 阶段五：接入策略并运行单任务

            RoboLab 使用 server-client 架构：模型/策略作为独立服务运行，RoboLab 通过轻量 inference client 调用它。

            官方 quick run 示例使用 `--num-envs 10`。在 RTX 4090 上先用 `--num-envs 1`：

            - 先确认策略服务端能启动。
            - 再确认 RoboLab client 能拿到动作。
            - 最后再逐步增加 `num_envs`。

            建议第一任务：`BananaInBowlTask`。它在官方 VRAM guide 中属于较低压力任务，适合作为 4090 的第一条闭环验证。
            """
        ),
        code(
            r"""
            # RoboLab 这里是 client；Pi0/Pi05 模型本体需要单独的 OpenPI server。
            policy_smoke_cmd = (
                f"uv run python policies/pi0_family/run.py "  # 使用 RoboLab 自带的 Pi0/Pi05 family runner。
                f"--policy {POLICY_NAME} "  # 选择策略名，例如 pi05。
                f"--task {SMOKE_TASK} "  # 指定第一条 smoke 任务。
                f"--num-envs {NUM_ENVS_4090_SMOKE} "  # 4090 首轮只开 1 个并行环境，降低 OOM 风险。
                f"--num-runs {NUM_RUNS} "  # 每个任务先跑 1 次，验证链路而不是做统计。
                f"--enable-subtask "  # 开启 subtask 进度记录，便于分析失败发生在哪一步。
                f"--headless"  # 无 GUI 运行，适合远端服务器。
            )

            # 在 OpenPI 权重下载完成、8000 端口 ready 前，这一步保持关闭。
            run(
                policy_smoke_cmd,
                cwd=ROBOLAB_DIR,
                env=OMNI_ENV,
                execute=EXECUTE_POLICY_SMOKE,
                check=False,
                timeout=7200,
                label="policy_smoke:single_task",
            )
            """
        ),
        md(
            """
            ## 6. 阶段六：4090 小子集评测计划

            不要把完整 RoboLab-120 当成第一天目标。建议先做 5 个任务，覆盖三个能力轴：

            | 任务 | 主要观察点 | 为什么放入第一批 |
            |---|---|---|
            | `BananaInBowlTask` | 语义识别 + pick/place | 低压力 smoke task |
            | `RubiksCubeAndBananaTask` | conjunction / 多目标 | 检查语言组合是否稳定 |
            | `RubiksCubeLeftOfBowlTask` | spatial relation | 观察左右空间关系推理 |
            | `ReorientWhiteMugsTask` | procedural / reorientation | 检查重定向操作 |
            | `Stack3RubiksCubeTask` | stacking / 多步骤 | 检查长 horizon 与失败模式 |

            评测顺序：

            1. `num_envs=1`，每个任务 1 run，确认不 OOM、输出完整。
            2. 仍是 `num_envs=1`，每个任务 3-5 runs，观察方差。
            3. 按显存余量尝试 `num_envs=2/4`。
            4. 扩展到 visual / procedural / relational 各 10 个任务。
            """
        ),
        code(
            r"""
            # RoboLab 的 --task 接收多个任务名；这里拼成命令行参数。
            subset_task_args = " ".join(SUBSET_TASKS)
            subset_cmd = (
                f"uv run python policies/pi0_family/run.py "  # 使用同一个策略 runner，便于和单任务 smoke 对比。
                f"--policy {POLICY_NAME} "  # 使用同一个 policy，避免策略差异影响观察。
                f"--task {subset_task_args} "  # 一次传入多个任务名，形成小子集评测。
                f"--num-envs {NUM_ENVS_4090_CAUTIOUS} "  # 小子集可尝试 2 个并行环境，但仍保持保守。
                f"--num-runs {NUM_RUNS} "  # 先每个任务 1 run，确认稳定后再提高 run 数。
                f"--enable-subtask "  # 保存子任务进度，方便看 score 和失败阶段。
                f"--headless"  # 远端无桌面/节省资源时使用 headless。
            )

            print("Subset command:")
            print(subset_cmd)
            # 首次加载 Isaac、资产和模型可能很久，所以 timeout 留得比较长。
            run(
                subset_cmd,
                cwd=ROBOLAB_DIR,
                env=OMNI_ENV,
                execute=EXECUTE_SUBSET_EVAL,
                check=False,
                timeout=24 * 3600,
                label="eval:subset_4090",
            )
            """
        ),
        md(
            """
            ## 7. 结果读取与可视化

            RoboLab 主要结果文件是 `episode_results.jsonl`。每行对应一个 episode，包含任务、策略、instruction、成功状态、score、耗时、轨迹指标和事件计数。

            下面的 cell 会：

            - 搜索 `ROBOLAB_DIR/output/**/episode_results.jsonl`。
            - 没有真实结果时使用样例数据，确保 notebook 的图表流程可检查。
            - 汇总任务成功率、能力轴/属性、难度、失败事件。
            """
        ),
        code(
            r"""
            def find_episode_results(root: Path):
                # RoboLab 可能把结果写到不同 output 子目录，所以递归查找。
                if not root.exists():
                    return []
                return sorted(root.glob("output/**/episode_results.jsonl"))

            def load_jsonl(path: Path):
                # 合并多个结果文件时保留来源路径，方便追溯每条记录来自哪里。
                rows = []
                with path.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        row = json.loads(line)
                        row["_source_file"] = str(path)
                        rows.append(row)
                return rows

            result_files = find_episode_results(ROBOLAB_DIR)
            rows = []
            for path in result_files:
                rows.extend(load_jsonl(path))

            if not rows:
                # 没有真实 policy 结果时，用样例数据保证表格/绘图 cell 可执行。
                # 注意：这些样例只验证 notebook 数据流，不代表真实 RoboLab 成绩。
                print("No real RoboLab results found yet. Using sample rows for visualization checks.")
                rows = [
                    {
                        "task_name": "BananaInBowlTask",
                        "env_name": "BananaInBowlTask",
                        "policy": POLICY_NAME,
                        "instruction_type": "default",
                        "attributes": ["visual", "semantics", "simple"],
                        "success": True,
                        "score": 1.0,
                        "duration": 14.8,
                        "episode_step": 222,
                        "metrics": {"ee_sparc": -5.2, "ee_path_length": 1.1, "ee_speed_mean": 0.08},
                        "events": {},
                    },
                    {
                        "task_name": "RubiksCubeLeftOfBowlTask",
                        "env_name": "RubiksCubeLeftOfBowlTask",
                        "policy": POLICY_NAME,
                        "instruction_type": "default",
                        "attributes": ["relational", "spatial", "moderate"],
                        "success": False,
                        "score": 0.4,
                        "duration": 50.0,
                        "episode_step": 750,
                        "metrics": {"ee_sparc": -8.9, "ee_path_length": 2.3, "ee_speed_mean": 0.05},
                        "events": {"WRONG_OBJECT_GRABBED": 1},
                    },
                    {
                        "task_name": "ReorientWhiteMugsTask",
                        "env_name": "ReorientWhiteMugsTask",
                        "policy": POLICY_NAME,
                        "instruction_type": "specific",
                        "attributes": ["procedural", "reorientation", "complex"],
                        "success": False,
                        "score": 0.2,
                        "duration": 60.0,
                        "episode_step": 900,
                        "metrics": {"ee_sparc": -9.4, "ee_path_length": 3.0, "ee_speed_mean": 0.04},
                        "events": {"TARGET_OBJECT_DROPPED": 2},
                    },
                ]

            def normalize_rows(rows):
                # 把嵌套的 metrics/events 拉平成普通列，便于 pandas 分组和绘图。
                flat = []
                for row in rows:
                    metrics = row.get("metrics") or {}
                    events = row.get("events") or {}
                    attrs = row.get("attributes") or []
                    flat.append(
                        {
                            "task_name": row.get("task_name") or row.get("env_name"),  # 任务名，用于按任务聚合成功率。
                            "env_name": row.get("env_name"),  # RoboLab 注册环境名，通常和任务名一致。
                            "policy": row.get("policy"),  # 本轮使用的策略名，例如 pi05。
                            "instruction_type": row.get("instruction_type"),  # 指令类型：default/vague/specific 等。
                            "attributes": ",".join(attrs) if isinstance(attrs, list) else str(attrs),  # 任务属性，如 spatial/color/stacking。
                            "difficulty": next((x for x in attrs if x in {"simple", "moderate", "complex"}), "unknown") if isinstance(attrs, list) else "unknown",  # 从属性里抽取难度标签。
                            "success": bool(row.get("success")),  # episode 是否整体成功。
                            "score": row.get("score"),  # 子任务或进度分数，失败时也能反映部分完成度。
                            "duration": row.get("duration"),  # episode 耗时。
                            "episode_step": row.get("episode_step"),  # episode 实际步数。
                            "ee_sparc": metrics.get("ee_sparc"),  # 末端执行器轨迹平滑度指标。
                            "ee_path_length": metrics.get("ee_path_length"),  # 末端执行器轨迹长度。
                            "ee_speed_mean": metrics.get("ee_speed_mean"),  # 末端执行器平均速度。
                            "wrong_object_grabbed": events.get("WRONG_OBJECT_GRABBED", 0),  # 抓错物体次数。
                            "target_object_dropped": events.get("TARGET_OBJECT_DROPPED", 0),  # 目标物体掉落次数。
                        }
                    )
                return flat

            flat_rows = normalize_rows(rows)
            if pd is None:
                print(json.dumps(flat_rows[:5], ensure_ascii=False, indent=2))
            else:
                df = pd.DataFrame(flat_rows)
                display(df.head())
                # 先按任务聚合；后续可以再按属性、难度或能力轴继续聚合。
                summary = (
                    df.groupby("task_name", dropna=False)
                    .agg(
                        episodes=("success", "size"),  # 每个任务累计 episode 数。
                        success_rate=("success", "mean"),  # bool 均值就是成功率。
                        mean_score=("score", "mean"),  # 平均进度/子任务分数。
                        mean_duration_s=("duration", "mean"),  # 平均耗时。
                        wrong_grabs=("wrong_object_grabbed", "sum"),  # 抓错物体总次数。
                        dropped=("target_object_dropped", "sum"),  # 掉落总次数。
                    )
                    .reset_index()
                    .sort_values("success_rate")
                )
                display(summary)
                summary.to_csv(ARTIFACT_DIR / "task_summary.csv", index=False)
                print("wrote", ARTIFACT_DIR / "task_summary.csv")
            """
        ),
        code(
            r"""
            if pd is not None and plt is not None:
                # 横向柱状图在任务数从几个扩展到几十个时仍然比较可读。
                plot_df = summary.copy()
                fig, ax = plt.subplots(figsize=(9, max(3, 0.45 * len(plot_df))))
                ax.barh(plot_df["task_name"], plot_df["success_rate"] * 100)
                ax.set_xlabel("Success rate (%)")
                ax.set_xlim(0, 100)
                ax.set_title("RoboLab subset success rate")
                for i, value in enumerate(plot_df["success_rate"] * 100):
                    ax.text(min(value + 1, 98), i, f"{value:.1f}%", va="center")
                fig.tight_layout()
                out = ARTIFACT_DIR / "success_rate_by_task.png"
                fig.savefig(out, dpi=160)
                print("wrote", out)
            else:
                # 没装绘图库时跳过绘图，保证 notebook 仍能执行完。
                print("Install pandas and matplotlib to render plots in this notebook.")
            """
        ),
        md(
            """
            ## 8. 与论文结果对照

            对照时不要只看一个总成功率。建议至少拆成四层：

            - overall：整体成功率、平均 score。
            - ability axis：visual / procedural / relational。
            - difficulty：simple / moderate / complex。
            - failure mode：wrong object、drop、table hit、object out of scene、timeout。

            论文表格给的是大规模基准上的整体趋势。你的 4090 小子集只是 smoke/subset，不应直接宣称复现了完整论文结论；只有完整任务覆盖、足够 episodes、相同/等价策略配置后，才做严格对比。
            """
        ),
        code(
            r"""
            # 把论文中的数值保存为参照锚点；小规模 smoke 不能直接对标完整 RoboLab-120。
            paper_reference = [
                {
                    "source": "arXiv 2604.09860v3 Table I",
                    "label": "best reported policy row in table",
                    "overall_success_pct": 28.0,
                    "overall_score": 0.43,
                    "note": "Use as a coarse orientation only; verify exact model identity and setup before formal comparison.",
                },
                {
                    "source": "arXiv 2604.09860v3 Table I",
                    "label": "GR00T N1.6",
                    "overall_success_pct": 7.2,
                    "overall_score": 0.17,
                    "note": "Paper-scale baseline, not a target for a 5-task smoke subset.",
                },
            ]
            ref_path = ARTIFACT_DIR / "paper_reference_orientation.json"
            ref_path.write_text(json.dumps(paper_reference, ensure_ascii=False, indent=2), encoding="utf-8")
            print("wrote", ref_path)

            if pd is not None and "summary" in globals():
                # 这里的加权成功率只覆盖当前加载到的子集，不代表完整 benchmark。
                observed = {
                    "subset_tasks": int(summary.shape[0]),
                    "subset_episodes": int(summary["episodes"].sum()),
                    "subset_success_pct": float(summary.eval("success_rate * episodes").sum() / summary["episodes"].sum() * 100),
                    "warning": "This is a subset/smoke metric, not full RoboLab-120 reproduction.",
                }
                write_status("observed_vs_paper_orientation", observed)
                observed
            """
        ),
        md(
            """
            ## 9. 每日学习记录模板

            每次执行后，把真实命令、报错、截图、指标写下来。复现类任务的关键不是“跑过”，而是能回放证据链。
            """
        ),
        code(
            r"""
            def append_learning_log(
                stage: str,
                goals=None,
                commands=None,
                problems=None,
                outputs=None,
                insights=None,
            ):
                # 每天/每阶段追加一段学习记录；marker 防止重复执行 notebook 时重复写入。
                goals = goals or []
                commands = commands or []
                problems = problems or []
                outputs = outputs or []
                insights = insights or []
                date = _dt.datetime.now().strftime("%Y-%m-%d")
                path = ARTIFACT_DIR / "learning_log.md"
                marker = f"## {date} - {stage}"
                if path.exists() and marker in path.read_text(encoding="utf-8"):
                    print("learning log already contains", marker)
                    return path
                block = []
                # 固定日志格式，后续可以直接粘贴到复现报告或做阶段对比。
                block.append(f"\n{marker}\n")
                block.append("### 今日目标\n")
                block.extend([f"- [ ] {x}\n" for x in goals] or ["- [ ] \n"])
                block.append("\n### 执行记录\n")
                if commands:
                    block.append("```bash\n" + "\n".join(commands) + "\n```\n")
                else:
                    block.append("```bash\n# command here\n```\n")
                block.append("\n### 遇到的问题及解决方案\n")
                block.append("| 问题 | 解决方案 |\n|---|---|\n")
                block.extend([f"| {p.get('problem', '')} | {p.get('solution', '')} |\n" for p in problems] or ["|  |  |\n"])
                block.append("\n### 关键输出/截图\n")
                block.extend([f"- {x}\n" for x in outputs] or ["- \n"])
                block.append("\n### 学习心得\n")
                block.extend([f"- {x}\n" for x in insights] or ["- \n"])
                path.open("a", encoding="utf-8").write("".join(block))
                print("appended", path)
                return path

            append_learning_log(
                "环境配置准备",
                goals=["确认 Ubuntu / 驱动 / 4090 / Python 3.11 / uv / ffmpeg / git-lfs", "记录 RoboLab 当前 commit 与依赖版本"],
                commands=["nvidia-smi", "uv venv --python 3.11", "uv sync", "uv run pytest tests/"],
                insights=["4090 第一轮只跑 num_envs=1；完整 RoboLab-120 不作为安装当天目标。"],
            )
            """
        ),
        md(
            """
            ## 10. 常见问题预案

            | 问题 | 判断方式 | 处理 |
            |---|---|---|
            | `uv sync` 失败 | 看 `command_log.jsonl` 里的 stderr | 确认 Python 3.11、网络、磁盘、`uv` 版本；重试前保留日志 |
            | 首次启动卡住 | 没有新日志、GPU 有占用 | 设置 `OMNI_KIT_ACCEPT_EULA=Y`，首次资产加载耐心等待 |
            | OOM | `nvidia-smi` 显存接近 24GB，日志出现 CUDA/Vulkan OOM | `--num-envs 1`，关闭桌面重负载，减少视频/图像记录 |
            | 渲染空白 | HDF5 有数据但视频空白 | 检查驱动、headless/EGL、Isaac Sim Vulkan 日志 |
            | 任务失败率很高 | success 低但 score 有进展 | 拆看 subtask、wrong object、drop、timeout，不只看二元成功 |
            | 小子集结果看似优于论文 | 任务太少或任务偏简单 | 标注为 subset smoke，不和论文完整 benchmark 直接比较 |
            """
        ),
        code(
            r"""
            # 最终 gate 同时检查本地 artifact 和远端 4090 证据。
            # 判断标准故意保守：只有文件存在不算通过，还要看返回码、traceback 和导出结果。
            remote_summary_for_status = {}
            if REMOTE_SUMMARY_PATH.exists():
                remote_summary_for_status = json.loads(REMOTE_SUMMARY_PATH.read_text(encoding="utf-8"))
            remote_install_ok = remote_summary_for_status.get("installation", {}).get("uv_sync_status") == "ok"
            remote_smoke = remote_summary_for_status.get("smoke", {})
            remote_smoke_ok = bool(
                # 无策略 smoke 只有在环境 setup、episode 导出都完成且没有 traceback 时才算通过。
                remote_smoke.get("completed_setup")
                and remote_smoke.get("exported_episode")
                and not remote_smoke.get("traceback_present")
            )
            remote_subset3_summary_for_status = {}
            if REMOTE_SUBSET3_SUMMARY_PATH.exists():
                remote_subset3_summary_for_status = json.loads(REMOTE_SUBSET3_SUMMARY_PATH.read_text(encoding="utf-8"))
            remote_subset3_ok = bool(
                # subset3 要求进程返回码干净，并至少导出 3 条 episode 记录。
                remote_subset3_summary_for_status.get("status_file_rc") == "0"
                and not remote_subset3_summary_for_status.get("traceback_present")
                and remote_subset3_summary_for_status.get("episodes_exported_count", 0) >= 3
            )
            remote_policy_summary_for_status = {}
            if REMOTE_POLICY_SUMMARY_PATH.exists():
                remote_policy_summary_for_status = json.loads(REMOTE_POLICY_SUMMARY_PATH.read_text(encoding="utf-8"))
            remote_no_policy = remote_policy_summary_for_status.get("no_policy_smoke", {})
            remote_openpi = remote_policy_summary_for_status.get("openpi_policy_readiness", {})
            remote_subset21_ok = bool(
                # subset21 的 summary 是累计文件，应该包含早先 Banana/subset3/subset10/subset19 的记录。
                remote_no_policy.get("subset10_status") == "0"
                and remote_no_policy.get("subset_more_status") == "0"
                and remote_no_policy.get("num_records_cumulative", 0) >= 21
                and {"PickDrillTask", "Stack3RubiksCubeTask"}.issubset(
                    set(remote_no_policy.get("candidate_probe_successful_tasks", []))
                )
            )
            remote_openpi_env_ok = bool(
                # 这个 gate 只表示 OpenPI 环境、导入和 CLI 可用，不表示策略已经跑过。
                remote_openpi.get("openpi_client_install_status") == "0"
                and remote_openpi.get("openpi_uv_sync_status") == "0"
                and remote_openpi.get("openpi_verify_status") == "0"
            )
            pi05_policy_smoke_summary_for_status = {}
            if (ARTIFACT_DIR / "pi05_policy_smoke_summary.json").exists():
                pi05_policy_smoke_summary_for_status = json.loads(
                    (ARTIFACT_DIR / "pi05_policy_smoke_summary.json").read_text(encoding="utf-8")
                )
            # 和 G9 分开：环境装好后，Pi05 checkpoint 下载/加载仍可能需要很多小时。
            pi05_server_ready = bool(
                remote_openpi.get("server_port_8000_ready")
                or pi05_policy_smoke_summary_for_status.get("server_ready")
            )
            pi05_policy_smoke_ok = bool(
                pi05_policy_smoke_summary_for_status.get("checkpoint_verify_ok")
                and pi05_policy_smoke_summary_for_status.get("checkpoint_restored")
                and pi05_policy_smoke_summary_for_status.get("server_ready")
                and pi05_policy_smoke_summary_for_status.get("smoke_status") == "0"
                and any(row.get("success") is True for row in pi05_policy_smoke_summary_for_status.get("episode_records", []))
            )

            final_checklist = {
                # 本地 notebook 和记录文件 gate。
                "G0_preflight_saved": (ARTIFACT_DIR / "preflight_status.json").exists(),
                "G1_command_log_exists": COMMAND_LOG.exists(),
                "G2_local_install_freeze_saved_after_real_run": (ARTIFACT_DIR / "uv_freeze.txt").exists(),
                # 来自远端 RTX 4090 证据包的运行 gate。
                "G2_remote_4090_install_verified": remote_install_ok,
                "G3_task_summary_exists": (ARTIFACT_DIR / "task_summary.csv").exists(),
                "G4_learning_log_exists": (ARTIFACT_DIR / "learning_log.md").exists(),
                "G5_paper_reference_saved": (ARTIFACT_DIR / "paper_reference_orientation.json").exists(),
                "G6_remote_4090_no_policy_smoke_completed": remote_smoke_ok,
                "G7_remote_4090_subset3_no_policy_smoke_completed": remote_subset3_ok,
                "G8_remote_4090_subset21_no_policy_smoke_completed": remote_subset21_ok,
                # 策略准备 gate；只有 8000 端口真实监听后，G10 才能变为 true。
                "G9_openpi_environment_verified": remote_openpi_env_ok,
                "G10_pi05_policy_server_ready": pi05_server_ready,
                "G11_core_code_explanation_saved": (ARTIFACT_DIR / "core_code_reading_map.json").exists(),
                "G12_remote_4090_pi05_policy_smoke_success": pi05_policy_smoke_ok,
                "G13_real_to_sim_explain_saved": (NOTEBOOK_ROOT / "EXPLAIN_01_real_to_sim_eval.md").exists(),
                "G14_complete_pi05_banana_report_saved": (NOTEBOOK_ROOT / "COMPLETE_REPRO_pi05_banana_20260620.md").exists(),
                "G15_complex_task_report_saved": (NOTEBOOK_ROOT / "COMPLEX_TASKS_pi05_20260620.md").exists(),
                "G16_scene_task_env_explain_saved": (NOTEBOOK_ROOT / "EXPLAIN_02_scene_task_env_generation.md").exists(),
                "G17_task_generation_validation_explain_saved": (NOTEBOOK_ROOT / "EXPLAIN_03_task_generation_validation.md").exists(),
                "G18_taskgen_lightweight_tests_passed": (
                    ARTIFACT_DIR / "taskgen_lightweight_validation_tests.json"
                ).exists(),
                "G19_competency_axes_difficulty_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_04_competency_axes_difficulty.md"
                ).exists(),
                "G20_competency_difficulty_tests_passed": (
                    ARTIFACT_DIR / "competency_difficulty_lightweight_tests.json"
                ).exists(),
                "G21_sparc_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_05_sparc_trajectory_metric.md"
                ).exists(),
                "G22_sparc_lightweight_tests_passed": (
                    ARTIFACT_DIR / "sparc_lightweight_tests.json"
                ).exists(),
                "G23_mnpe_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_06_mnpe_sensitivity_analysis.md"
                ).exists(),
                "G24_mnpe_lightweight_tests_passed": (
                    ARTIFACT_DIR / "mnpe_lightweight_tests.json"
                ).exists(),
                "G25_global_overview_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_00_global_overview.md"
                ).exists(),
                "G26_baseline_method_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_07_baseline_method.md"
                ).exists(),
                "G27_baseline_method_lightweight_tests_passed": (
                    ARTIFACT_DIR / "baseline_method_lightweight_tests.json"
                ).exists(),
                "G28_paper_experiments_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_08_paper_experiments.md"
                ).exists(),
                "G29_paper_experiments_algorithm_tests_passed": (
                    ARTIFACT_DIR / "paper_experiments_algorithm_lightweight_tests.json"
                ).exists(),
                "G30_dtge_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_09_dtge.md"
                ).exists(),
                "G31_dtge_lightweight_tests_passed": (
                    ARTIFACT_DIR / "dtge_lightweight_tests.json"
                ).exists(),
                "G32_prompt_design_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_10_prompt_design.md"
                ).exists(),
                "G33_prompt_design_lightweight_tests_passed": (
                    ARTIFACT_DIR / "prompt_design_lightweight_tests.json"
                ).exists(),
                "G34_spatial_physical_feedback_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_11_spatial_physical_solver_feedback.md"
                ).exists(),
                "G35_spatial_physical_feedback_tests_passed": (
                    ARTIFACT_DIR / "spatial_physical_feedback_lightweight_tests.json"
                ).exists(),
                "G36_gaussian_sim_methods_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_12_gaussian_sim_methods.md"
                ).exists(),
                "G37_gaussian_sim_methods_tests_passed": (
                    ARTIFACT_DIR / "gaussian_sim_methods_lightweight_tests.json"
                ).exists(),
                "G38_remaining_core_topics_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_13_remaining_core_topics.md"
                ).exists(),
                "G39_remaining_core_topics_tests_passed": (
                    ARTIFACT_DIR / "remaining_core_topics_lightweight_tests.json"
                ).exists(),
                "G40_core_code_runtime_chain_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_14_core_code_runtime_chain.md"
                ).exists(),
                "G41_core_code_runtime_chain_tests_passed": (
                    ARTIFACT_DIR / "core_code_runtime_chain_lightweight_tests.json"
                ).exists(),
                "G42_reviewer_synthesis_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_15_reviewer_synthesis.md"
                ).exists(),
                "G43_reviewer_synthesis_tests_passed": (
                    ARTIFACT_DIR / "reviewer_synthesis_lightweight_tests.json"
                ).exists(),
                "G44_recommended_reading_explain_saved": (
                    NOTEBOOK_ROOT / "EXPLAIN_16_recommended_reading.md"
                ).exists(),
                "G45_recommended_reading_tests_passed": (
                    ARTIFACT_DIR / "recommended_reading_lightweight_tests.json"
                ).exists(),
                "note": "Local install gates depend on EXECUTE_INSTALL. Remote 4090 evidence is read from remote_logs/. G12 is a single-task Pi05 policy smoke, not a full RoboLab-120 benchmark.",
            }
            write_status("repro_status", final_checklist)
            final_checklist
            """
        ),
    ]

    nb.cells = cells
    nbf.write(nb, OUT_DIR / NOTEBOOK_NAME)

    manifest = {
        "generated_at": GENERATED_AT,
        "artifact": NOTEBOOK_NAME,
        "robolab_github_head_at_generation": ROBOLAB_HEAD,
        "sources": [
            {
                "title": "RoboLab paper",
                "url": "https://arxiv.org/html/2604.09860",
                "used_for": [
                    "benchmark purpose",
                    "RoboLab-120 competency axes",
                    "metrics and comparison framing",
                    "paper reference orientation values",
                    "core mechanism explanation for scene/task generation, metrics, and sensitivity analysis",
                    "scaling task generation validation and repair loop",
                    "benchmark design: competency axes, subtasks, and difficulty scoring",
                    "trajectory metrics: SPARC smoothness, speed, path length, and ISJ",
                    "MNPE sensitivity analysis and posterior interpretation",
                    "global RoboLab architecture, evaluation intent, and reproduction boundary framing",
                    "Appendix C-C baseline scene generation method and Appendix C-D scene generation comparison metrics",
                    "paper experiments: RoboLab-120 policy benchmark, granular analysis, sensitivity analysis, real-world verification, scene generation evaluation, task generation evaluation, and Algorithm 1 spatial solver",
                    "Appendix D Details on Task Generation Evaluation: LLM-as-judge dimensions, Table IX metrics, object coverage, and predicate coverage",
                    "Appendix C Stage I Semantic Planning prompts: system prompt, JSON-only output contract, user prompt template, feedback block, and scene generation prompt rationale",
                    "Appendix C Stage II geometric and physical solving: Algorithm 1 spatial constraint solver, Figure 17 feedback block, and Algorithm 2 physical placement solver",
                    "Figure 13 Gaussian Splat + Mesh scene, collision mesh, mesh foreground, VoMP mass/density, 3DGRT/3DGUT references, and MNPE Gaussian KDE distinction",
                    "EXPLAIN_12 frontier source table: NuRec, 3DGUT, Isaac Sim 6.0 EDR, Lyra, Physically Embodied Gaussians, and Marble+Isaac Sim links with read-focus notes",
                    "remaining core evaluation topics: IV-A experiment setup, success-vs-score interpretation, language variations, complexity sweeps, event-driven failure analysis, RoboArena real-world verification, statistical confidence, and limitations",
                    "EXPLAIN_15 whole-paper reviewer synthesis: contributions, strengths, weaknesses, limitations, real-world verification, optimization directions, and future innovation routes",
                    "EXPLAIN_16 source-linked reading map: what to read after RoboLab for simulation benchmarks, real-world data, VLA policies, SimReady assets, and sim-to-real evaluation",
                    "EXPLAIN_16 core source-and-content evidence table: the originating problem, source content, and reading question behind each recommendation",
                ],
                "observed": "arXiv:2604.09860v3, 14 May 2026",
            },
            {
                "title": "NVIDIA Omniverse NuRec",
                "url": "https://developer.nvidia.com/omniverse/nurec",
                "used_for": [
                    "2026 NVIDIA frontier route: camera/lidar neural reconstruction to OpenUSD scene",
                    "NuRec gsplat rendering and gRPC/Isaac Sim integration framing",
                    "distinguishing photoreal Gaussian rendering from collider/physics requirements",
                    "EXPLAIN_12 clickable frontier source table and nvidia_frontier_link_map",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "NVIDIA Research 3DGUT",
                "url": "https://research.nvidia.com/labs/toronto-ai/3DGUT/",
                "used_for": [
                    "3D Gaussian rendering with nonlinear camera models",
                    "rolling shutter and secondary ray support such as reflection/refraction",
                    "relationship between RoboLab Figure 13 references and current NVIDIA Gaussian rendering research",
                    "EXPLAIN_12 3DGUT source link and read-focus notes",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "NVIDIA Isaac Sim",
                "url": "https://developer.nvidia.com/isaac/sim",
                "used_for": [
                    "Isaac Sim neural reconstruction / NuRec framing",
                    "Isaac Sim as the physics and sensor layer around Gaussian-reconstructed visuals",
                    "EXPLAIN_12 Isaac Sim source link for NuRec, OpenUSD, physics, sensor, and synthetic-data context",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "Isaac Sim 6.0 Early Developer Release for GTC'26",
                "url": "https://forums.developer.nvidia.com/t/announcement-isaac-sim-6-0-early-developer-release-for-gtc26/363709",
                "used_for": [
                    "2026 Isaac Sim 6.0 EDR NuRec 3DGS library and Fabric Scene Delegate context",
                    "multiple physics backends and Warp-based API frontier note",
                    "EXPLAIN_12 Isaac Sim 6.0 EDR source link and read-focus notes",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "NVIDIA Research Lyra",
                "url": "https://research.nvidia.com/labs/toronto-ai/lyra/",
                "used_for": [
                    "2026 generative 3DGS world route from text, image, or video",
                    "Lyra/Lyra 2.0 relationship to future fast scene generation for simulation",
                    "EXPLAIN_12 Lyra source link and read-focus notes",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "NVIDIA Technical Blog: Building Robotic Mental Models with NVIDIA Warp and Gaussian Splatting",
                "url": "https://developer.nvidia.com/blog/building-robotic-mental-models-with-nvidia-warp-and-gaussian-splatting/",
                "used_for": [
                    "Physically Embodied Gaussians as adjacent frontier",
                    "particle plus 3D Gaussian dual representation and differentiable rendering feedback loop",
                    "EXPLAIN_12 Physically Embodied Gaussians source link and read-focus notes",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "NVIDIA Technical Blog: Simulate Robotic Environments Faster with NVIDIA Isaac Sim and World Labs Marble",
                "url": "https://developer.nvidia.com/blog/simulate-robotic-environments-faster-with-nvidia-isaac-sim-and-world-labs-marble/",
                "used_for": [
                    "Gaussian splat PLY plus collider GLB to NuRec/USDZ/Isaac Sim workflow",
                    "engineering example of aligning photoreal splat visuals with physics collider mesh",
                    "EXPLAIN_12 Marble+Isaac Sim+NuRec workflow source link and read-focus notes",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "RoboLab project page",
                "url": "https://research.nvidia.com/labs/srl/projects/robolab/",
                "used_for": [
                    "project overview",
                    "agentic scene/task generation",
                    "dashboard and benchmark description",
                    "sensitivity analysis framing",
                    "EXPLAIN_15 overview framing for benchmark/system-paper reviewer interpretation",
                    "EXPLAIN_16 reading-route anchor for RoboLab's benchmark, dashboard, agentic generation, and evaluation ecosystem",
                    "EXPLAIN_16 source evidence table anchor for the central problem: simulation evaluation of real-world task-generalist policies",
                ],
            },
            {
                "title": "NVlabs/RoboLab README",
                "url": "https://github.com/NVlabs/RoboLab",
                "used_for": [
                    "installation commands",
                    "Isaac Sim 5.0 and Isaac Lab 2.2.0 via uv sync",
                    "Python 3.11 and Ubuntu 22.04+ requirements",
                    "GPU/VRAM and speed caveats",
                    "quick run commands",
                    "source tree orientation for task/env/policy/eval modules",
                    "EXPLAIN_15 engineering and reproducibility reviewer perspective: install, policy server-client, multi-env, dashboard, hardware cost, and subset protocol recommendations",
                    "EXPLAIN_16 practical reading order for continuing from RoboLab install/repro into policies, assets, and benchmark extensions",
                    "EXPLAIN_16 source content map for README-to-learning-route traceability",
                ],
            },
            {
                "title": "Stanford / Fei-Fei / OmniGibson reading track",
                "url": "https://proceedings.mlr.press/v205/li23a.html",
                "used_for": [
                    "EXPLAIN_16 recommended reading: BEHAVIOR-1K / OmniGibson as the human-centered household benchmark line",
                    "EXPLAIN_16 related sources: https://behavior.stanford.edu/ and https://github.com/StanfordVL/BEHAVIOR-1K",
                    "EXPLAIN_16 Stanford real-world/evaluation context: DROID, RoboArena, and ReKep as adjacent sources",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "Open VLA policy reading track",
                "url": "https://github.com/Physical-Intelligence/openpi",
                "used_for": [
                    "EXPLAIN_16 recommended reading: OpenPI / pi0 / pi0.5 as the current RoboLab policy stack",
                    "EXPLAIN_16 related policy sources: OpenVLA, Octo, GR00T, LeRobot, and RDT/RDT2",
                    "EXPLAIN_16 policy adapter study questions: observation schema, action chunk, server-client, fine-tuning, dataset format",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "Tsinghua embodied policy reading track",
                "url": "https://github.com/thu-ml/RoboticsDiffusionTransformer",
                "used_for": [
                    "EXPLAIN_16 recommended reading: RDT-1B and RDT2 as Tsinghua THU-ML/TSAIL embodied foundation model sources",
                    "EXPLAIN_16 comparison route: diffusion transformer, unified action space, bimanual manipulation, unseen embodiment",
                    "EXPLAIN_16 2026-first reading track: RDT2 arXiv 2602.03310, zero-shot cross-embodiment, RDT2-VQ/RDT2-FM, UMI data scaling, and RTX 4090 inference note",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "Domestic embodied benchmark and data reading track",
                "url": "https://robotwin-platform.github.io/",
                "used_for": [
                    "EXPLAIN_16 recommended reading: RoboTwin / RoboTwin 2.0 for generative digital twins and bimanual benchmark generation",
                    "EXPLAIN_16 related sources: RoboMIND for multi-embodiment data and failure demos, RH20T for contact-rich multimodal data, VLABench for language-conditioned long-horizon manipulation",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "Lightwheel / SimReady reading track",
                "url": "https://github.com/LightwheelAI",
                "used_for": [
                    "EXPLAIN_16 recommended reading: LightwheelAI GitHub, LW-BenchHub, Lightwheel SimReady assets, Lightwheel_Kitchen, and mjcf2usd",
                    "EXPLAIN_16 source for asset-scale learning route: SimReady assets, benchmark hub, teleoperation, VLA fine-tuning, Isaac ecosystem integration",
                    "EXPLAIN_16 2026-first reading track: LW-BenchHub, LeIsaac, AutoDataGen, SimReady assets, 268-task benchmark hub, and Isaac Lab-Arena alignment",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "NVIDIA Physical AI reading track",
                "url": "https://github.com/NVIDIA/Isaac-GR00T",
                "used_for": [
                    "EXPLAIN_16 recommended reading: Isaac GR00T, Isaac Lab, Isaac Lab-Arena, Cosmos, SimReady Foundation, and RoboCasa365",
                    "EXPLAIN_16 future route: VLA model evaluation, world models, SimReady assets, composable task/env benchmark engineering",
                    "EXPLAIN_16 2026-first reading track: GR00T N1.7, 20K hours EgoScale, relative EEF action, Cosmos 2.5, Isaac Lab-Arena, and LeRobot integration",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "RoboCasa365 release",
                "url": "https://github.com/robocasa/robocasa/releases",
                "used_for": [
                    "EXPLAIN_16 2026-first reading track: ICLR 2026 household/kitchen benchmark",
                    "RoboCasa365 v1.0 release facts: 365 tasks, 2500+ kitchen scenes, 3200+ 3D objects, 600+ human demonstration hours, 1600+ robot dataset hours, and Diffusion Policy/Pi/GR00T benchmarking support",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "RDT2 GitHub",
                "url": "https://github.com/thu-ml/RDT2",
                "used_for": [
                    "EXPLAIN_16 2026-first reading track: arXiv 2602.03310 and RDT2 release",
                    "RDT2 source facts: unseen embodiment zero-shot, RDT2-VQ/RDT2-FM, 10000+ hours UMI human manipulation videos, and 16GB RTX 4090 inference note",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "NVIDIA Isaac GR00T N1.7",
                "url": "https://github.com/NVIDIA/Isaac-GR00T",
                "used_for": [
                    "EXPLAIN_16 2026-first reading track: GR00T N1.7 Early Access",
                    "GR00T source facts: new VLM backbone, 20K hours EgoScale human video, relative EEF action space, Apache-2.0 license, and 16GB+ VRAM inference requirement",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "NVIDIA 2026 Physical AI release",
                "url": "https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Releases-New-Physical-AI-Models-as-Global-Partners-Unveil-Next-Generation-Robots/default.aspx",
                "used_for": [
                    "EXPLAIN_16 2026-first reading track: official physical AI ecosystem update",
                    "Release facts: Cosmos and GR00T open models, Isaac Lab-Arena, OSMO, Hugging Face LeRobot integration, and Jetson Thor context",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "NVIDIA Isaac Lab-Arena technical blog",
                "url": "https://developer.nvidia.com/blog/simplify-generalist-robot-policy-evaluation-in-simulation-with-nvidia-isaac-lab-arena/",
                "used_for": [
                    "EXPLAIN_16 2026-first reading track: scalable policy evaluation in simulation",
                    "Isaac Lab-Arena source facts: co-developed with Lightwheel, modular task creation, automated diversification, large-scale parallel benchmarking, and LeRobot/GR00T/pi0/SmolVLA integration",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "NVIDIA Research Lyra",
                "url": "https://research.nvidia.com/labs/toronto-ai/lyra/",
                "used_for": [
                    "EXPLAIN_16 2026-first reading track: ICLR 2026 generative 3D/4D Gaussian scene route",
                    "Lyra source facts: text/image/video to 3D/4D Gaussian scenes, generated 3D Gaussians imported into Isaac Sim, and future RoboLab scene generation reference",
                ],
                "observed": "checked 2026-06-20",
            },
            {
                "title": "RoboLab source files inspected on remote RTX 4090 checkout",
                "url": "https://github.com/NVlabs/RoboLab/tree/7d45d74904eade3b578a8eb1f2f9f89bc3d40326",
                "used_for": [
                    "core code walkthrough",
                    "global source tree map for EXPLAIN_00",
                    "scene generation predicates, spatial solver, and physical solver",
                    "examples/run_empty.py no-policy call flow",
                    "robolab/core/environments/runtime.py create_env explanation",
                    "robolab/core/environments/config.py and factory.py dynamic environment config generation",
                    "robolab/registrations/droid/auto_env_registrations_jointpos.py robot/camera/background registration flow",
                    "robolab/tasks/benchmark/banana_in_bowl_task.py task definition explanation",
                    "robolab/tasks/benchmark/rubiks_cube_left_of_bowl.py relational task example",
                    "robolab/tasks/benchmark/red_items_in_bin.py multi-object sorting task example",
                    "robolab/tasks/benchmark/rubiks_cube_stacking_task.py stacking subtask example",
                    "robolab/core/task/conditionals.py and subtask.py scoring explanation",
                    "robolab/core/task/task_utils.py load_task_from_file task import validation",
                    "robolab/tasks/_utils/generate_task_metadata.py and load_task_info.py metadata/difficulty extraction",
                    "robolab/core/scenes/utils.py scrape_scene/import_scene scene object validation",
                    "robolab/scene_gen/llm_scene_gen/feedback_system.py feedback loop pattern",
                    "robolab/constants.py SKILL_WEIGHTS, DIFFICULTY_THRESHOLDS, BENCHMARK_TASK_CATEGORIES",
                    "robolab/core/task/task.py Task.attributes and Task.subtasks fields",
                    "robolab/core/task/subtask.py parallel conditions and logical modes",
                    "robolab/core/task/subtask_utils.py count_subtasks and compute_difficulty_score",
                    "robolab/core/metrics/trajectory_metrics.py SPARC, ISJ, speed, and path length metrics",
                    "robolab/core/metrics/compute_metrics.py HDF5-to-episode_metrics trajectory metric pipeline",
                    "analysis/sensitivity_analysis/posterior_inference.py MNPE/NPE posterior inference pipeline",
                    "analysis/sensitivity_analysis/README_posterior_inference.md MNPE CLI usage and output interpretation",
                    "policies/pi0_family/run_camera_pose_variation.py camera pose variation data generation",
                    "policies/pi0_family/run_background_variation.py background variation data generation",
                    "policies/pi0_family/run_table_variation.py table material variation data generation",
                    "robolab/variations/camera.py camera configuration source for sensitivity parameters",
                    "robolab/variations/backgrounds.py HDR/EXR background variation source",
                    "robolab/variations/lighting.py lighting variation source",
                    "policies/pi0_family/run.py and client.py policy interface explanation",
                    "task annotation schema: scene, instruction, terminations, subtasks, attributes, and episode outputs",
                    "robolab/scene_gen/llm_scene_gen/predicates.py predicate vocabulary for scene generation",
                    "robolab/scene_gen/llm_scene_gen/spatial_solver.py geometric constraint solving contrast with grid baseline",
                    "robolab/scene_gen/llm_scene_gen/physical_solver.py place-in/place-on physical relation contrast with grid baseline",
                    "robolab/scene_gen/llm_scene_gen/feedback_system.py solver and physics feedback loop contrast with one-pass baseline",
                    "robolab/scene_gen/llm_scene_gen/spatial_solver.py Algorithm 1 spatial constraint solver implementation",
                    "robolab/eval/runner.py shared policy evaluation loop for paper-style experiments",
                    "robolab/core/logging/results.py grouping by attributes, object count, and subtask count",
                    "policies/pi0_family/run_lighting.py, run_background_variation.py, run_table_variation.py, and run_camera_pose_variation.py variation experiment runners",
                    "robolab/core/task/task.py Task schema, resolve_instruction, and verify_task_valid static validation fields used to explain DTGE",
                    "robolab/scene_gen/llm_scene_gen/predicates.py predicate grammar targeted by the Stage I prompts",
                    "robolab/scene_gen/llm_scene_gen/feedback_system.py solver and physics feedback messages that feed prompt repair",
                    "robolab/scene_gen/llm_scene_gen/physical_solver.py place-on grouping, support slot search, place-in container packing, and z-height assignment",
                    "robolab/scene_gen/llm_scene_gen/spatial_solver.py base-pose solving before physical placement",
                    "EXPLAIN_14 source-code runtime chain: robolab/eval/runner.py task selection, resume, adaptive sampling, output directory, and call into run_episode/summarize_run",
                    "EXPLAIN_14 source-code runtime chain: robolab/eval/episode.py policy-controlled step loop, active env filtering, HDF5 run file selection, video writers, timing, and client reset",
                    "EXPLAIN_14 source-code runtime chain: robolab/eval/base_client.py InferenceClient hook contract and per-env action chunk cache",
                    "EXPLAIN_14 source-code runtime chain: policies/pi0_family/client.py OpenPI/Pi05 observation extraction, request schema, websocket retry, action chunk unpacking, and gripper binarization",
                    "EXPLAIN_14 source-code runtime chain: robolab/core/world/world_state.py unified object/geometry/contact query layer and predicate state cache",
                    "EXPLAIN_14 source-code runtime chain: robolab/core/task/event_tracker.py wrong object, dropped target, hit table, moved object, tipped object, and env-mask failure events",
                    "EXPLAIN_14 source-code runtime chain: robolab/core/logging/recorder_manager.py streaming HDF5 recorder, per-env EpisodeData, run_<idx>.hdf5, and demo_<env_id> indexing",
                    "EXPLAIN_14 source-code runtime chain: robolab/eval/summarize.py and robolab/core/logging/results.py event log writing, trajectory metric folding, final score extraction, and episode_results.jsonl append",
                    "EXPLAIN_14 source-code runtime chain: dashboard/loaders/local.py offline result loading, HDF5/video/log discovery, and SR/Score confidence interval display",
                    "EXPLAIN_15 reviewer synthesis source grounding: evaluation runners, dashboard, policy adapters, event logs, result schema, and 4090-cost reproduction constraints",
                    "EXPLAIN_16 reading-route grounding: RoboLab modules used to organize external recommended reading by policy client, scene/task generation, asset preflight, real-world correlation, long-horizon reasoning, and failure analysis",
                ],
            },
            {
                "title": "RoboLab scene generation skill notes in remote checkout",
                "url": "local:/home/yjl/codex_robolab_4090_20260619/RoboLab/skills/robolab-scenegen/SKILL.md",
                "used_for": [
                    "predicate JSON examples",
                    "scene file generation pattern",
                    "base_empty.usda payload insertion and settle workflow",
                    "scene generation prompt design: object catalog exact naming, predicate JSON, solver pipeline, and medium-scene constraints",
                ],
            },
            {
                "title": "RoboLab task generation skill notes in remote checkout",
                "url": "local:/home/yjl/codex_robolab_4090_20260619/RoboLab/skills/robolab-taskgen/SKILL.md",
                "used_for": [
                    "Task dataclass generation template",
                    "task examples for pick/place, sorting, and stacking",
                    "conditionals predicate library mapping",
                    "syntax/resource validation and repair-prompt explanation",
                    "DTGE static extraction targets: instruction, terminations.success, attributes, subtasks, and predicate parameters",
                ],
                "related_files": [
                    "local:/home/yjl/codex_robolab_4090_20260619/RoboLab/skills/robolab-taskgen/references/examples.md",
                    "local:/home/yjl/codex_robolab_4090_20260619/RoboLab/skills/robolab-taskgen/references/conditionals.md",
                ],
            },
            {
                "title": "RoboLab docs: Analysis and Results Parsing",
                "url": "https://raw.githubusercontent.com/NVlabs/RoboLab/main/docs/analysis.md",
                "used_for": [
                    "result parsing commands",
                    "summary dimensions",
                    "confidence interval caveat",
                    "paper experiment result parsing by attributes, difficulty, instruction type, scene, wrong objects, and beta credible interval",
                    "EXPLAIN_13 analysis commands for score/success, instruction type, wrong objects, and episode aggregation",
                ],
            },
            {
                "title": "RoboLab docs: Data Storage and Output",
                "url": "https://raw.githubusercontent.com/NVlabs/RoboLab/main/docs/data.md",
                "used_for": [
                    "episode_results.jsonl fields",
                    "HDF5/video output structure",
                    "EXPLAIN_13 evidence chain: videos for human inspection and JSON/HDF5/event logs for paper-style statistics",
                ],
            },
            {
                "title": "RoboLab docs: Event Tracking",
                "url": "https://raw.githubusercontent.com/NVlabs/RoboLab/main/docs/event_tracking.md",
                "used_for": [
                    "EXPLAIN_13 failure taxonomy: wrong object, gripper hit table, dropped target, object moved, tipped, and out-of-scene events",
                ],
            },
            {
                "title": "RoboLab docs: Subtask Checking",
                "url": "https://raw.githubusercontent.com/NVlabs/RoboLab/main/docs/subtask.md",
                "used_for": [
                    "EXPLAIN_13 success-vs-score explanation and hierarchical subtask/condition state machine interpretation",
                ],
            },
            {
                "title": "RoboLab docs: Dashboard",
                "url": "https://raw.githubusercontent.com/NVlabs/RoboLab/main/docs/dashboard.md",
                "used_for": [
                    "EXPLAIN_13 dashboard evidence and confidence interval explanation: SR Beta credible interval and Score Student-t interval",
                ],
            },
            {
                "title": "RoboLab docs: num_envs VRAM guide",
                "url": "https://raw.githubusercontent.com/NVlabs/RoboLab/main/docs/env_vram_size_guide.md",
                "used_for": ["task names and VRAM caution; L40 48GB values treated only as upper-bound orientation"],
            },
        ],
    }
    (OUT_DIR / MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    readme = f"""# RoboLab 4090 复现与学习记录

本目录是 RoboLab 复现学习用的 Jupyter 交付物。

## 文件

- `{NOTEBOOK_NAME}`：主 notebook，按阶段记录环境检查、安装、验证、smoke run、4090 小子集评测、论文机制、核心源码讲解、结果解析和学习日志。
- `{MANIFEST_NAME}`：准备 notebook 时核对过的官方来源。
- `build_robolab_notebook.py`：生成 notebook 和来源清单的脚本。
- `EXPLAIN_00_global_overview.md`：论文与复现全局总览精讲，补回系统架构、任务标注、策略接入、证据口径和后续路线，已内嵌进 notebook。
- `EXPLAIN_01_real_to_sim_eval.md`：论文“真实场景到模拟场景评估”的代码实现精讲，已内嵌进 notebook。
- `EXPLAIN_02_scene_task_env_generation.md`：论文“场景、任务和环境生成”的代码实现精讲，已内嵌进 notebook。
- `EXPLAIN_03_task_generation_validation.md`：论文“扩展任务生成、验证和自动修复”的代码实现精讲，已内嵌进 notebook，并配有轻量测试用例。
- `EXPLAIN_04_competency_axes_difficulty.md`：论文“能力轴、任务属性、子任务和难度分数”的代码实现精讲，已内嵌进 notebook，并配有难度公式轻量测试用例。
- `EXPLAIN_05_sparc_trajectory_metric.md`：论文“SPARC 轨迹平滑度指标”的代码实现精讲，已内嵌进 notebook，并配有 SPARC 方向性轻量测试用例。
- `EXPLAIN_06_mnpe_sensitivity_analysis.md`：论文“MNPE 敏感性分析”的代码实现精讲，已内嵌进 notebook，并配有 posterior 直觉轻量测试用例。
- `EXPLAIN_07_baseline_method.md`：论文 Appendix C-C “Baseline Method”的代码实现精讲，已内嵌进 notebook，并配有 grid+jitter baseline 轻量测试用例。
- `EXPLAIN_08_paper_experiments.md`：论文实验体系与 Algorithm 1 Spatial Constraint Solver 精讲，已内嵌进 notebook，并配有 2D 空间约束求解轻量测试用例。
- `EXPLAIN_09_dtge.md`：论文 Appendix D “Details on Task Generation Evaluation / DTGE”的精讲，已内嵌进 notebook，并配有 AST 静态抽取与简化 judge 轻量测试用例。
- `EXPLAIN_10_prompt_design.md`：论文 Appendix C Stage I scene generation prompt 精讲，已内嵌进 notebook，并配有 prompt 输出格式/依赖/对象目录/尺寸限制轻量测试用例。
- `EXPLAIN_11_spatial_physical_solver_feedback.md`：论文 Appendix C 空间求解器、物理放置求解器和失败反馈块精讲，已内嵌进 notebook，并配有支撑/容器/反馈轻量测试用例。
- `EXPLAIN_12_gaussian_sim_methods.md`：论文中 Gaussian Splat + Mesh、collision mesh、VoMP、MNPE Gaussian KDE 与 NVIDIA 2026 NuRec/3DGUT/Lyra 等前沿路线精讲，已补前沿来源链接速查表，已内嵌进 notebook，并配有分层职责和链接覆盖轻量测试用例。
- `EXPLAIN_13_remaining_core_topics.md`：对照论文后补充的剩余核心内容精讲，覆盖实验协议、success/score gap、语言变体、复杂度 sweep、事件追踪、真实世界相关性、统计置信和限制边界，已内嵌进 notebook，并配有覆盖差分轻量测试用例。
- `EXPLAIN_14_core_code_runtime_chain.md`：RoboLab policy rollout 到证据链的核心代码精讲，覆盖 `runner.py`、`episode.py`、`InferenceClient`、Pi05 client、`WorldState`、`EventTracker`、HDF5 recorder、`summarize_run`、results 和 dashboard loader，已内嵌进 notebook，并配有源码链路轻量测试用例。
- `EXPLAIN_15_reviewer_synthesis.md`：全文总梳理与审稿人视角精讲，覆盖贡献、优点、主要问题、优化点和未来创新方向，已内嵌进 notebook，并配有 reviewer rubric 轻量测试用例。
- `EXPLAIN_16_recommended_reading.md`：基于 RoboLab 的推荐阅读与开源学习路线，已改成 2026-first：优先补 RoboLab、RoboCasa365、RDT2、GR00T N1.7、Isaac Lab-Arena、Lightwheel LW-BenchHub、Lyra 和 NVIDIA 2026 Physical AI stack；BEHAVIOR/DROID/OpenVLA/Octo/ReKep 等降级为基础背景，已内嵌进 notebook，并配有 reading map 轻量测试用例。
- `COMPLETE_REPRO_pi05_banana_20260620.md`：Pi05 / BananaInBowlTask 成功闭环记录，已内嵌进 notebook。
- `COMPLEX_TASKS_pi05_20260620.md`：Pi05 三个复杂任务抽样复现记录，已内嵌进 notebook。
- `remote_logs/`：2026-06-19 远端 RTX 4090 实测证据，包含安装日志、依赖版本、资产下载日志、no-policy smoke 日志和 episode 输出。

## 当前状态

- 已在远端 RTX 4090 / Ubuntu 22.04.4 上完成 `uv sync`，并确认 `robolab==0.1.0`、`isaacsim==5.0.0.0`、`isaaclab==2.2.0`、`torch==2.7.0+cu128` 可导入。
- 已补齐 `assets/scenes/`、`assets/robots/` 和核心 `assets/fixtures/`，足够运行 `BananaInBowlTask` 的 no-policy smoke。
- `BananaInBowlTask` headless smoke 已完成 2 step 并导出 episode log；`success: False` 是空动作运行的预期结果，不是 VLA 策略评测。
- 已追加三任务 no-policy subset smoke：`RubiksCubeAndBananaTask`、`RubiksCubeLeftOfBowlTask`、`ReorientWhiteMugsTask`，三者均完成环境初始化、2 step 和 episode log 导出。
- 已扩展到累计 21 个 no-policy 初始化 smoke，覆盖语义、颜色、空间关系、顺序组合、重定向、堆叠等任务属性；额外候选任务失败原因已记录，证据包为 `remote_logs/robolab_remote_policy_subset21_evidence_20260619_223200.tar.gz`。
- 已新增论文与核心源码讲解章节，并生成 `robolab_repro_artifacts/core_code_reading_map.json`，用于追踪论文概念到源码文件的映射。
- 已新增“精讲0：RoboLab 全局总览”，把论文动机、系统架构、任务标注、策略接入、4090 复现边界、RoboChallenge/OpenPI/ReKep 对比前提和完整复现分级串成一张总图。
- 已新增“场景、任务和环境生成”精讲，覆盖 `scene_gen` 谓词求解、`Task` 语言/成功条件、registration/runtime 环境装配，并包含场景 JSON、任务类、背景随机化等示例。
- 已新增“扩展任务生成、验证和自动修复”精讲，覆盖 taskgen skill、谓词库、`load_task_from_file`、场景对象验证、容器尺寸检查和失败修复提示，并在 notebook 里加入 6 个轻量测试用例。
- 已轻量化三篇精讲之间的重复内容：精讲1聚焦 real-to-sim 评估闭环，精讲2深讲 scene/task/env 装配，精讲3深讲 TaskGen 验证与修复。
- 已新增“能力轴、任务属性、子任务和难度分数”精讲，覆盖 visual/procedural/relational、多标签属性、`Subtask` 并行事件、`compute_difficulty_score` 和 metadata 生成，并在 notebook 里加入难度公式轻量测试。
- 已新增“SPARC 轨迹平滑度指标”精讲，覆盖论文 III-C Trajectory Metrics、`compute_sparc`、HDF5 到 `episode_metrics.json` 的离线指标链路，并在 notebook 里加入平滑/抖动/静止速度曲线测试。
- 已新增“MNPE 敏感性分析”精讲，覆盖论文 III-D 与 Appendix B、`posterior_inference.py` 的 CSV -> `theta/x` -> MNPE/NPE -> posterior 采样链路，并在 notebook 里加入 success posterior 直觉测试。
- 已新增“Baseline 场景生成方法”精讲，覆盖论文 Appendix C-C 的 grid+jitter 单次布局 baseline、与谓词/solver/feedback 主方法的差异，并在 notebook 里加入 baseline vs hierarchical semantic relation 轻量测试。
- 已新增“论文实验总览与 Algorithm 1”精讲，覆盖 RoboLab-120 策略评测、细粒度能力分析、扰动敏感性、真实世界相关性、场景/任务生成质量实验，并在 notebook 里加入 Spatial Constraint Solver 三阶段轻量测试。
- 已新增“DTGE 任务生成质量评估”精讲，覆盖 Appendix D 的 LLM-as-judge、instruction-code alignment、relation/target/object/quantifier/clarity/feasibility 六维评分、object/predicate coverage，并在 notebook 里加入 AST 静态抽取轻量测试。
- 已新增“Scene Generation Prompt 设计”精讲，覆盖 Appendix C 三段 prompt 的系统约束、JSON-only 合约、对象目录注入、medium scene strategy、失败反馈思路，并在 notebook 里加入 6 类 prompt 输出校验用例。
- 已新增“空间求解器、物理放置求解器与失败反馈”精讲，覆盖 Algorithm 1、Figure 17 和 Algorithm 2，解释 `place-on-base`、`place-on`、`place-in` 如何从谓词变成 2D/3D 位姿，并在 notebook 里加入 toy physical placement 与 feedback block 测试。
- 已增强“Gaussian 方法与 NVIDIA 2026 前沿路线”精讲，区分 RoboLab 本文里的 Gaussian Splat + Mesh、collision mesh、mesh foreground、VoMP、MNPE Gaussian KDE，并补充 NuRec、3DGUT/3DGRT、Isaac Sim 6、Lyra 2.0、Physically Embodied Gaussians、Marble+Isaac Sim 工作流的来源链接和重点阅读项。
- 已新增“剩余核心内容与评测证据链”精讲，补齐实验协议、`success` 与 `score` 的差异、语言变体、复杂度 sweep、事件追踪、RoboArena 真实世界相关性、统计置信区间和论文限制边界。
- 已新增“policy rollout 到证据链”代码精讲，补齐真实策略评测时 `runner -> episode -> client -> env/world -> event -> recorder -> summarize -> dashboard` 的源码主干和故障定位路径。
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
jupyter lab {NOTEBOOK_NAME}
```

先执行配置与 preflight cell。确认机器正确后，再逐步打开：

1. `EXECUTE_INSTALL = True`
2. `EXECUTE_TESTS = True`
3. `EXECUTE_NO_POLICY_SMOKE = True`
4. `EXECUTE_POLICY_SMOKE = True`
5. `EXECUTE_SUBSET_EVAL = True`

4090 首轮保持 `NUM_ENVS_4090_SMOKE = 1`。确认没有 OOM、输出完整后，再尝试更高并行度。

## 生成时间

{GENERATED_AT}
"""
    (OUT_DIR / README_NAME).write_text(readme, encoding="utf-8")

    print("wrote", OUT_DIR / NOTEBOOK_NAME)
    print("wrote", OUT_DIR / MANIFEST_NAME)
    print("wrote", OUT_DIR / README_NAME)


if __name__ == "__main__":
    main()
