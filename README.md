# roboplay

这个仓库先用于沉淀 RoboLab / 机器人仿真复现与学习记录。

## 当前内容

- [RoboLab 4090 复现与学习记录](./robolab_2604_09860_repro_jupyter/README.md)
- [RoboLab 主 Jupyter Notebook](./robolab_2604_09860_repro_jupyter/RoboLab_4090_repro_learning_record.ipynb)
- [RoboLab 精讲 0-16](./robolab_2604_09860_repro_jupyter/)
- [RoboLab 远端实测证据清单](./robolab_2604_09860_repro_jupyter/REMOTE_EVIDENCE_MANIFEST.md)
- [实验拓展：相机/腕部相机/机器人消融](./robolab_2604_09860_repro_jupyter/EXPERIMENT_17_camera_robot_ablation.md)
- [实验拓展：Pi05 能力轴 5×任务矩阵与扰动路线](./robolab_2604_09860_repro_jupyter/EXPERIMENT_18_pi05_axis5_then_perturb_compare.md)
- [实验拓展：Pi05、PaliGemma、GR00T、Cosmos、阿里模型等多模型对照](./robolab_2604_09860_repro_jupyter/EXPERIMENT_19_policy_baseline_models.md)

## 提交策略

第一版只提交可阅读、可复现、可验证的轻量资料：

- Markdown 精讲
- Jupyter notebook
- 来源清单和验证 JSON
- 复现摘要与小规模结果

暂不提交远端原始视频、大体积日志、缓存目录和运行输出目录；这些后续可以按需用 Git LFS 或 release artifact 管理。

如果你在 GitHub 页面上没有看到 `remote_outputs/`、`remote_logs/` 或 HTML 渲染版，这不是 push 失败，而是当前提交策略主动排除了原始运行输出。已提交的证据边界见 [RoboLab 远端实测证据清单](./robolab_2604_09860_repro_jupyter/REMOTE_EVIDENCE_MANIFEST.md)。
