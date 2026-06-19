# RoboLab 单任务完整复现记录：Pi0.5 / BananaInBowlTask

## 结论

本次在 4090 远程主机上完成一条可交付的 RoboLab 复现闭环：使用 OpenPI `pi05_droid_jointpos` 策略，在 Isaac Sim / RoboLab 中运行 `BananaInBowlTask`，任务成功，并产出视频、HDF5 轨迹、事件日志和汇总结果。

## 运行环境

- 远程主机：`y12`
- GPU：NVIDIA GeForce RTX 4090，24GB VRAM
- 系统：Ubuntu 22.04.4
- RoboLab 仓库：`/home/yjl/codex_robolab_4090_20260619/RoboLab`
- OpenPI checkpoint：`/home/yjl/codex_robolab_4090_20260619/openpi_cache/openpi-assets-simeval/pi05_droid_jointpos`
- OpenPI server：`localhost:8000`

## 运行命令

```bash
cd /home/yjl/codex_robolab_4090_20260619/RoboLab

/home/yjl/.local/bin/uv run python policies/pi0_family/run.py \
  --policy pi05 \
  --remote-host localhost \
  --remote-port 8000 \
  --task BananaInBowlTask \
  --num-envs 1 \
  --num-runs 1 \
  --video-mode all \
  --output-folder-name pi05_banana_full_20260620_015206 \
  --headless \
  --device cuda:0
```

## 输出位置

远程输出目录：

```text
/home/yjl/codex_robolab_4090_20260619/RoboLab/output/pi05_banana_full_20260620_015206
```

本地同步目录：

```text
C:\Users\robot\Documents\成长学习库\robolab_2604_09860_repro_jupyter\remote_outputs\pi05_banana_full_20260620_015206
```

关键文件：

| 类型 | 文件 |
|---|---|
| 汇总结果 | `episode_results.jsonl` |
| 每环境事件日志 | `log_0_env0.json` |
| 轨迹数据 | `run_0.hdf5` |
| 策略相机视频 | `Pick_up_the_banana_and_place_it_in_the_bowl_0.mp4` |
| 第三人称 viewport 视频 | `Pick_up_the_banana_and_place_it_in_the_bowl_0_viewport.mp4` |
| 视频截图 | `viewport_mid.png` |

## 任务结果

| 指标 | 数值 |
|---|---:|
| 任务 | `BananaInBowlTask` |
| 指令 | `Pick up the banana and place it in the bowl` |
| 策略 | `pi05` |
| 成功 | `true` |
| episode step | `198` |
| 仿真时长 | `13.2 s` |
| wall time | `46.086 s` |
| policy inference avg | `13.6 ms` |
| env step avg | `214.2 ms` |
| video write avg | `4.9 ms` |
| FPS | `15` |

## 视频验证

策略相机视频：

- 分辨率：`1280x360`
- 帧数：`197`
- 时长：`13.134 s`
- 编码：`h264`
- 大小：`4,302,288 bytes`

第三人称 viewport 视频：

- 分辨率：`864x480`
- 帧数：`197`
- 时长：`13.134 s`
- 编码：`h264`
- 大小：`881,359 bytes`

## HDF5 轨迹内容

`run_0.hdf5` 包含：

- `actions`: `(198, 8)`，机器人动作序列
- `states/articulation/robot`: 机器人关节位置、速度、根位姿、根速度
- `states/rigid_object/banana`: 香蕉位姿和速度
- `states/rigid_object/bowl`: 碗位姿和速度
- `bbox`: 香蕉、碗、桌子的 3D bbox 和中心点
- `ee_pose`: 末端位置、姿态、线速度、角速度
- `initial_state`: 初始机器人、物体、相机状态

## 复现状态

这条复现已经完成：

- 策略服务可用
- Isaac Sim 环境成功启动
- RoboLab task 成功注册
- Pi0.5 策略完成推理闭环
- 任务成功
- 视频可读且非空白
- HDF5 轨迹和日志已保存

下一步对比实验建议以这条记录为模板，分别跑：

- RoboLab-120 全任务或分批任务
- RoboChallenge Pi baseline 的适配 smoke
- ReKep 方法的可行 smoke

