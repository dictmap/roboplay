# RoboLab 远端实测证据清单

这个文件用于解释为什么 GitHub 页面看起来不像“完整提交”：当前仓库提交的是可阅读、可复现、可验证的轻量资料；远端 RTX 4090 运行产生的原始视频、HDF5、日志和输出目录保留在本地工作区，暂未直接进入普通 Git 历史。

## GitHub 已提交内容

- 主学习 notebook：`RoboLab_4090_repro_learning_record.ipynb`
- 已执行 notebook：`RoboLab_4090_repro_learning_record.executed.ipynb`
- 精讲 0-16、精讲 13/14 深挖补充、问题来源索引
- 复现摘要：`COMPLETE_REPRO_pi05_banana_20260620.md`
- 复杂任务抽样摘要：`COMPLEX_TASKS_pi05_20260620.md`
- 复现实验摘要图表和 JSON/CSV：`robolab_repro_artifacts/`
- 远端中文源码阅读资料：`remote_docs/`
- 辅助脚本：`scripts/`、`tools/`

## 本地存在但未提交的原始证据

这些路径被 `.gitignore` 明确排除：

- `remote_outputs/`
- `remote_logs/`
- `RoboLab_4090_repro_learning_record.executed.html`

原因不是复现没有完成，而是这些目录包含视频、HDF5、压缩证据包、安装日志和运行输出。普通 Git 提交会让仓库变重；更合理的方式是把它们作为 Git LFS 对象或 GitHub Release artifact 管理。

## 本地证据目录概览

| 本地路径 | 文件数 | 大小 | 内容 |
|---|---:|---:|---|
| `remote_outputs/pi05_banana_full_20260620_015206/` | 7 | 5.96 MB | Pi05 / `BananaInBowlTask` 完整闭环，含视频、viewport 视频、HDF5、JSONL、event log、配置。 |
| `remote_outputs/pi05_complex_assets_ok_20260620_020721/` | 19 | 60.42 MB | 三个复杂任务抽样：`ReorientAllMugsTask`、`Stack3RubiksCubeTask`、`RedItemsInBinTask`，含每个任务的视频、viewport 视频、HDF5、日志和配置。 |
| `remote_logs/` | 54 | 2.13 MB | 远端 4090 安装、依赖、LFS 下载、no-policy smoke、subset smoke、Pi05 server/client 和证据包日志。 |
| `RoboLab_4090_repro_learning_record.executed.html` | 1 | 2.09 MB | notebook 的 HTML 渲染版，便于浏览器离线查看。 |

## 已完成的实测复现边界

- 已完成真实 Pi05 policy 单任务 smoke：`BananaInBowlTask`，记录中成功率为单条 episode 成功，不代表 RoboLab-120 全量成绩。
- 已完成一条更完整的 Pi05 / `BananaInBowlTask` 闭环：包含视频、viewport 视频、HDF5、event log 和 `episode_results.jsonl`。
- 已完成三个复杂任务抽样：`ReorientAllMugsTask` 失败、`Stack3RubiksCubeTask` 成功、`RedItemsInBinTask` 失败。
- 已完成 21 个 no-policy 初始化 smoke，用于验证环境、资产和任务初始化路径。
- 完整 RoboLab-120 仍未执行；这需要更多资产、更多 GPU 时间，以及更系统的结果归档。

## 后续如果要把“完整原始证据”也放上 GitHub

建议用下面三种方式之一，不建议直接把 `remote_outputs/` 和 `remote_logs/` 普通提交到 `main`：

1. GitHub Release artifact：适合视频、HDF5、tar.gz 证据包，仓库历史保持干净。
2. Git LFS：适合希望版本化保存视频/HDF5，但会占用 LFS 配额。
3. 精选证据提交：只挑选小体积 JSON、CSV、截图和关键日志进入 Git，视频和 HDF5 仍走 Release。

当前仓库先采用“轻量资料 + 证据清单”的方式，保证 GitHub 页面可读，同时不把大文件塞进普通 Git 历史。
