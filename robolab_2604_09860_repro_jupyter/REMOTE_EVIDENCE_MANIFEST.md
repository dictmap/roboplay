# RoboLab 远端实测证据清单

<!-- FINAL-20260621-UPDATE:BEGIN -->
> [!IMPORTANT]
> 2026-06-21 更新：Pi05/OpenPI 的 RoboLab-120 clean run 已在 4090 上完成，并通过 120/120 任务产物完整性校验。最终任务成功率为 34/120 = 28.3%。旧文档中的“未跑 full-120”口径已经作废。
<!-- FINAL-20260621-UPDATE:END -->

这个文件用于解释为什么 GitHub 页面不是把所有原始运行目录完整塞进去：仓库提交的是可阅读、可复现、可验证的轻量资料；远端 RTX 4090 运行产生的完整视频、HDF5、日志和大体积输出目录继续保留在 4090 工作区。这样 GitHub 页面保持可读，原始证据也不丢。

## GitHub 已提交内容

- 主学习 notebook：`RoboLab_4090_repro_learning_record.ipynb`，已重新嵌入最终 120 任务结果页。
- 最终结果页：`FINAL_ROBOLAB120_RESULTS_20260621.md`。
- 当前状态页：`CURRENT_ROBOLAB120_STATUS.md`。
- 模型下载状态页：`MODEL_DOWNLOADS_STATUS.md`。
- 样例视频说明页：`SAMPLE_VIDEOS.md`。
- 精讲 0-16、精讲 13/14 深挖补充、问题来源索引，以及各实验说明页。
- 复现实验摘要表和机器可读结果：`robolab_repro_artifacts/` 中的 manifest、episode summary、policy compare、read_results 表、check_results 日志和状态 JSON。
- 少量可在 GitHub 直接浏览的样例视频：`sample_videos/`。
- 远端中文源码阅读资料：`remote_docs/`。
- 辅助脚本：`scripts/`、`tools/`。

## 4090 上保留的完整原始证据

完整 raw evidence 不直接进普通 Git 历史，主要因为视频和 HDF5 数量多、体积大，后续更适合放 GitHub Release、对象存储或 Git LFS。

| 证据类别 | 4090 路径/前缀 | 当前结论 |
|---|---|---|
| 最终 full-120 运行 | `robolab120_pi05_full_assetsfixed_20260620_170411` | 120/120 任务完成，`run_returncode=0`，`verify_returncode=0`。 |
| 逐任务结果 | `episode_results.jsonl` | 每个任务目录 1 份，共 120 份。 |
| HDF5 | `run_0.hdf5` | 每个任务目录 1 份，共 120 份。 |
| 视频 | 主视频 + viewport 视频 | 共 240 个 MP4，其中 3 个样例已提交到 GitHub。 |
| 子任务日志 | `log_0_env0.json` | 每个任务目录 1 份，共 120 份。 |
| 聚合分析 | `robolab_repro_artifacts/*read_results*.csv` | 已按能力轴、难度、任务长度出表。 |

## 已完成的实测复现边界

- 已完成 Pi05/OpenPI 在 RoboLab-120 上的 clean full run：120 个任务全部执行并完成产物校验。
- 产物完整性：120 task folders、120 HDF5、240 MP4、120 `episode_results.jsonl`、120 `log_0_env0.json`。
- 最终任务成功率：34/120 = 28.3%。失败任务按策略/任务结果记录，不是资产缺失或运行中断。
- 按能力轴：PROCEDURAL 6/34 = 17.6%，RELATIONAL 15/42 = 35.7%，VISUAL 20/84 = 23.8%。
- 按难度：simple 21/64 = 32.8%，moderate 10/39 = 25.6%，complex 3/17 = 17.6%。
- 已完成早期 Pi05 单任务和复杂任务抽样，这些保留为过程证据；最终结论以 full-120 clean run 为准。
- RoboChallenge pi 和 ReKep 当前仍属于 adapter-pending 对照：已有实验入口和对照计划，但不能把 adapter 未完成误写成 0 分或完成评测。

## 后续如果要把完整原始证据也放上 GitHub

建议用下面三种方式之一，不建议直接把完整 `remote_outputs/` 和 full-run 输出目录普通提交到 `main`：

1. GitHub Release artifact：适合视频、HDF5、tar.gz 证据包，仓库历史保持干净。
2. Git LFS：适合希望版本化保存视频/HDF5，但会占用 LFS 配额。
3. 精选证据提交：只挑选小体积 JSON、CSV、截图和关键日志进入 Git，视频和 HDF5 仍走 Release 或对象存储。

当前仓库采用“轻量资料 + 聚合表 + 样例视频 + 远端完整证据保留”的方式，保证 GitHub 页面可读，同时保留后续归档全量 raw evidence 的空间。
