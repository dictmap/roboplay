# 实验 21：Pi05 跑 RoboLab-120 前 5 个任务的真实 smoke 结果

## 核心结论

这次不是完整 RoboLab-120，而是一次 `TASK_LIMIT=5` 的端到端 smoke：在 4090 机器 `y12` 上固定 Pi05 policy server，按官方 `task_metadata.json` 的前 5 个任务逐个启动，保存 manifest、artifact check、episode 汇总和日志诊断。

最重要的结论是：

> 5 个任务都被 runner 调起；只有 `BananaInBowlTask` 完整产出了 `episode_results.jsonl`、HDF5、视频和 event log，并且 `success=True / score=1.0`。另外 4 个任务没有完整 episode 证据，失败发生在环境初始化/资产/contact sensor 层，不能直接算成 Pi05 策略失败。

所以当前数字应该读作：

| 口径 | 结果 |
|---|---:|
| 调起的任务数 | 5 |
| 完整产出评分 episode 的任务数 | 1 |
| 已评分 episode 数 | 1 |
| 已评分 episode 成功数 | 1 |
| 已评分 episode success rate | 1.0 |
| 不能进入策略成功率统计的任务数 | 4 |

这个边界非常关键：如果把 4 个没有产出 episode 的任务粗暴当作失败，会把“资产/仿真环境未就绪”误读成“策略能力失败”。

## 本轮运行配置

| 项 | 值 |
|---|---|
| 远端机器 | `light-47022` / host `y12` |
| GPU | RTX 4090 24GB |
| RoboLab 路径 | `/home/yjl/codex_robolab_4090_20260619/RoboLab` |
| roboplay 路径 | `/home/yjl/roboplay` |
| roboplay commit | `127c502` |
| policy | `pi05` |
| policy server | `localhost:8000` |
| num_envs | `1` |
| num_runs | `1` |
| video_mode | `all` |
| task_limit | `5` |
| run_prefix | `robolab120_pi05_smoke5_20260620_085451` |

启动器：

```bash
cd /home/yjl/roboplay/robolab_2604_09860_repro_jupyter
bash scripts/remote_start_pi05_robolab120_smoke5_4090.sh
```

远端日志：

```text
/home/yjl/codex_robolab_4090_20260619/robolab120_pi05_smoke5_20260620_085451.log
/home/yjl/codex_robolab_4090_20260619/robolab120_pi05_smoke5_20260620_085451.status
/home/yjl/codex_robolab_4090_20260619/robolab120_pi05_smoke5_20260620_085451_runner.sh
```

本地同步日志：

```text
remote_logs/robolab120_pi05_smoke5_20260620_085451.log
remote_logs/robolab120_pi05_smoke5_20260620_085451.status
remote_logs/robolab120_pi05_smoke5_20260620_085451_runner.sh
```

## 逐任务结果

| 任务 | run_returncode | verify_returncode | artifact check | 诊断 |
|---|---:|---:|---|---|
| `AnimalsInBinTask` | 0 | 1 | fail | 环境初始化/contact sensor 失败；无 episode/HDF5/video |
| `AppleAndYogurtInBowlTask` | 0 | 1 | fail | 环境初始化/contact sensor 失败；无 episode/HDF5/video |
| `BagelsOnPlateTask` | 0 | 1 | fail | `bagel_00` contact reporter API 缺失；无 episode/HDF5/video |
| `BananaInBowlTask` | 0 | 0 | pass | 完整评分 episode，成功 |
| `BananaOnPlateTask` | 0 | 1 | fail | 环境初始化/contact sensor 失败；无 episode/HDF5/video |

这里还暴露出一个工程细节：manifest 里的 `run_returncode=0` 不能单独作为任务成功依据，因为 Isaac/Kit 里可能打印 traceback 但外层进程仍然返回 0。后续必须同时看：

1. `verify_returncode`
2. `*_artifact_check.json`
3. `episode_results.jsonl`
4. HDF5、视频、event log 是否都存在且非空
5. failure diagnosis 里的 traceback/contact sensor/missing asset 信号

## 成功 episode 指标

来自 `robolab120_pi05_smoke5_20260620_085451_merged/episode_results.jsonl`：

| 指标 | 值 |
|---|---:|
| task | `BananaInBowlTask` |
| instruction | `Pick up the banana and place it in the bowl` |
| success | `true` |
| score | `1.0` |
| episode_step | `177` |
| duration | `11.8 s` |
| policy_inference_avg_ms | `76.1 ms` |
| env_step_avg_ms | `194.7 ms` |
| ee_path_length | `0.8278` |
| ee_sparc | `-3.4517` |
| event | `TARGET_OBJECT_DROPPED: 1` |

解释一下这个 event：`TARGET_OBJECT_DROPPED=1` 表示过程中目标物体发生过一次掉落/接触异常事件，但最终仍然完成了 pick-and-place 子任务，所以 `success=True / score=1.0`。这正是 RoboLab event log 的价值：它不仅告诉我们成功/失败，还告诉我们成功过程是否稳定。

## 视频与本地证据文件

本地可直接打开的视频：

- `remote_outputs/robolab120_pi05_smoke5_20260620_085451_BananaInBowlTask/Pick_up_the_banana_and_place_it_in_the_bowl_0.mp4`
- `remote_outputs/robolab120_pi05_smoke5_20260620_085451_BananaInBowlTask/Pick_up_the_banana_and_place_it_in_the_bowl_0_viewport.mp4`

本地完整证据：

| 文件 | 作用 |
|---|---|
| `remote_outputs/robolab120_pi05_smoke5_20260620_085451_BananaInBowlTask/run_0.hdf5` | 轨迹、状态和动作数据 |
| `remote_outputs/robolab120_pi05_smoke5_20260620_085451_BananaInBowlTask/log_0_env0.json` | 子任务/event 日志 |
| `remote_outputs/robolab120_pi05_smoke5_20260620_085451_BananaInBowlTask/env_cfg.json` | 环境配置 |
| `robolab_repro_artifacts/robolab120_pi05_smoke5_20260620_085451_episode_summary.json` | episode 聚合结果 |
| `robolab_repro_artifacts/robolab120_pi05_smoke5_20260620_085451_policy_compare.json` | 按任务/能力轴/难度聚合 |
| `robolab_repro_artifacts/robolab120_pi05_smoke5_20260620_085451_failure_diagnosis.json` | 失败任务诊断 |
| `robolab_repro_artifacts/robolab120_pi05_smoke5_20260620_085451_task_run_manifest.jsonl` | 每个任务的运行 manifest |

远端原始证据仍保留在：

```text
/home/yjl/codex_robolab_4090_20260619/RoboLab/output/robolab120_pi05_smoke5_20260620_085451_BananaInBowlTask/BananaInBowlTask/
```

## failure diagnosis 结果

新增脚本：

```bash
python scripts/diagnose_robolab120_smoke_log.py \
  --log remote_logs/robolab120_pi05_smoke5_20260620_085451.log \
  --manifest robolab_repro_artifacts/robolab120_pi05_smoke5_20260620_085451_task_run_manifest.jsonl \
  --artifact-check-glob "robolab_repro_artifacts/robolab120_pi05_smoke5_20260620_085451_*Task_artifact_check.json" \
  --out robolab_repro_artifacts/robolab120_pi05_smoke5_20260620_085451_failure_diagnosis.json
```

诊断摘要：

| 项 | 值 |
|---|---:|
| observed tasks | 5 |
| complete scored episode | 1 |
| env init/contact sensor failed | 4 |
| missing asset references | 1055 |
| unique missing assets | 108 |

最典型的报错：

```text
RuntimeError: Sensor at path '/World/envs/env_.*/scene/bagel_00' could not find any bodies with contact reporter API.
HINT: Make sure to enable 'activate_contact_sensors' in the corresponding asset spawn configuration.
```

同时日志里有大量类似下面的资产缺失：

```text
Could not open asset @.../RoboLab/assets/objects/objaverse/bagel_00.usd@
Could not open asset @.../RoboLab/assets/objects/vomp/plate_large/plate_large.usd@
Could not open asset @.../RoboLab/assets/objects/hot3d/glasses.usd@
```

这说明当前继续直接跑 120 个任务会得到大量“无 episode 证据”的失败行，实验质量不够。下一步应该先做资产/contact sensor preflight，再扩大任务矩阵。

## 对下一步实验的影响

原计划是：

1. 固定 Pi05，扩到每个能力轴至少 5 个任务。
2. 每个任务保存 `episode_results.jsonl`、HDF5、视频和子任务日志。
3. 用 `analysis/read_results.py` 按能力轴、难度、任务长度出表。
4. 再选成功率中等任务做光照/背景/物体位置扰动。
5. 最后换 RoboChallenge pi、ReKep、GR00T、PaliGemma/Cosmos/阿里模型做对照。

这次 smoke 说明第 1 步前必须补一个 gate：

> 先跑 asset/contact preflight，生成“可完整初始化且能产出证据”的任务白名单，再在白名单里按能力轴选任务。

建议下一轮推进顺序：

1. 扫描 120 个任务对应场景和对象引用，找出当前远端缺失的 USD/纹理/物理配置。
2. 优先补齐或避开会触发 contact sensor 初始化失败的对象，比如 `bagel_00`、`lizard_figurine`、`glasses`。
3. 先构造一个 asset-ready axis subset，而不是直接跑官方前 15 或全 120。
4. 对 asset-ready subset 跑 Pi05，要求每个任务都必须有 episode JSONL、HDF5、视频、event log。
5. 只有当 subset 的 artifact 完整率接近 100% 后，再扩大到 RoboLab-120。

## 这轮实验的真实边界

可以确认：

- 4090 能连通，Pi05 server 能启动并响应。
- RoboLab policy runner 能在 4090 上真实调用 Pi05。
- `BananaInBowlTask` 形成了一条完整复现闭环：视频、HDF5、event log、episode result、summary table 都齐了。
- full-120 runner 的“失败不中断”机制能工作。
- 结果聚合脚本能从多任务输出中汇总 scored episode。

还不能确认：

- 不能说完成了 RoboLab-120。
- 不能说 Pi05 在 5 个任务上成功率是 20%。
- 不能说 RoboChallenge pi 或 ReKep 已经进入同口径对照。
- 不能把缺资产/contact sensor 失败当作策略失败。

这轮的价值是把 full-120 前的主要阻塞点从“感觉没跑完”定位成了具体工程问题：资产完整性、contact sensor 配置和 artifact gate。
