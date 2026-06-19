# 精讲 5：SPARC 轨迹平滑度指标，代码怎么实现

> [!NOTE]
> **颜色标识**：绿色表示核心结论，蓝色表示源码/输入输出路径，橙色表示边界、风险和容易误解的点。

## 先说结论

SPARC 全称是 **Spectral Arc Length**，论文把它放在 `III-C Metrics for Evaluation -> Trajectory Metrics`。它不是任务成功率，也不是 subtask score，而是一个连续轨迹质量指标，用来衡量末端执行器运动是否平滑。

> [!TIP]
> **核心结论**：RoboLab 用 SPARC 看“策略动作是不是顺”。成功率回答“有没有完成”，score 回答“完成到哪一步”，SPARC 回答“运动过程是不是平滑、有无抖动”。论文里说：越平滑的运动，SPARC 越接近 0；越抖、频率成分越复杂，SPARC 越负。

在 RoboLab 里，SPARC 的代码链路是：

```text
run_*.hdf5
  -> ee_pose/position 或 ee_pose/linear_velocity
  -> speed = ||velocity||
  -> FFT 得到归一化速度频谱
  -> 只保留 adaptive cutoff 以内的频率
  -> 计算频谱曲线弧长
  -> SPARC = - arc_length
  -> episode_metrics.json 里的 ee_sparc / joint_sparc_mean
```

## 1. SPARC 在论文里解决什么问题

RoboLab 不是只看二值 success，因为两个策略都成功时，动作质量可能差很多：

| 现象 | success 能看出来吗 | SPARC 能提供什么 |
|---|---|---|
| 一路顺滑抓取并放下 | 能看到成功 | SPARC 接近 0，表示频谱简单、运动平滑 |
| 抖动、来回试探，最后也成功 | 只能看到成功 | SPARC 更负，说明运动频谱更复杂 |
| 没完成，但中间动作很稳定 | success 只给失败 | SPARC 可单独反映运动质量 |
| 原地不动或几乎不动 | success 失败 | SPARC 应该谨慎处理，源码用 motion gate 返回 NaN |

论文原意是：success rate 很重要，但不能解释策略的运动效率、平滑度和最优性。SPARC、end-effector speed、path length 这些轨迹指标一起补上了“怎么动”的信息。

## 2. 公式说人话

论文描述的是：先取末端执行器速度曲线，再看这条速度曲线在频域里的形状。

```text
位置 p(t)
  -> 速度 v(t)
  -> 速率 s(t) = ||v(t)||
  -> Fourier magnitude spectrum V(ω)
  -> normalize V(ω)
  -> 在 cutoff 频率内计算频谱曲线弧长
  -> SPARC = -弧长
```

为什么频谱能衡量平滑？

- 平滑运动的速度曲线通常变化慢，频谱集中在低频，频谱曲线比较短。
- 抖动运动会引入高频成分，频谱曲线更曲折、更长。
- RoboLab 返回负弧长，所以弧长越大，SPARC 越负。

> [!WARNING]
> **方向不要读反**：RoboLab 论文文本说“smoother motions yield values closer to zero, jerkier trajectories produce more negative values”。当前 checkout 的 `compute_sparc()` docstring 前半段有一句“More negative values indicate smoother movements”容易误导；实际代码 `sparc = -arc_length`、函数后半段注释和论文一致：越接近 0 越平滑，越负越不平滑。

## 3. 源码入口

> [!NOTE]
> **源码入口**：SPARC 核心计算在 `robolab/core/metrics/trajectory_metrics.py::compute_sparc`；从 HDF5 读轨迹并写入 episode metrics 的入口在 `robolab/core/metrics/compute_metrics.py::compute_episode_metrics` 和 `compute_experiment_metrics`。

核心函数：

```python
def compute_sparc(
    speed,
    dt,
    padlevel=4,
    fc=10.0,
    amplitude_threshold=0.05,
    min_speed=1e-6,
):
    if len(speed) < 2 or np.max(np.abs(speed)) < min_speed:
        return float("nan")

    nfft = int(2 ** np.ceil(np.log2(N)) * padlevel)
    speed_fft = np.fft.rfft(speed, n=nfft)
    freq = np.fft.rfftfreq(nfft, d=dt)

    magnitude = np.abs(speed_fft)
    magnitude = magnitude / magnitude.max()

    above_threshold = magnitude >= amplitude_threshold
    fc_adaptive = min(freq[last_idx], fc)

    freq_mask = freq <= fc_adaptive
    d_magnitude = np.diff(magnitude_sel)
    d_freq = np.diff(freq_sel)
    arc_length = np.sum(np.sqrt((d_freq / fc_adaptive) ** 2 + d_magnitude**2))

    sparc = -arc_length
```

关键参数：

| 参数 | 默认值 | 作用 |
|---|---:|---|
| `dt` | 由 `env_cfg.json` 或默认 `1/15` | 采样时间间隔 |
| `padlevel` | `4` | FFT 零填充，提高频谱采样密度 |
| `fc` | `10.0 Hz` | 最大 cutoff 频率 |
| `amplitude_threshold` | `0.05` | adaptive cutoff 阈值，只保留有意义频段 |
| `min_speed` | `1e-6` | motion gate，几乎不动时返回 NaN |

## 4. 从 HDF5 到 `ee_sparc`

`compute_metrics.py` 负责把实验输出变成轨迹指标：

```python
data = load_demo_data(run_0.hdf5, demo_key)
ee_position = data["ee_position"]
ee_velocity = data.get("ee_linear_velocity")

if has_ee_velocity:
    metrics["ee_sparc"] = compute_ee_sparc_from_velocity(ee_velocity, dt)
else:
    metrics["ee_sparc"] = compute_ee_sparc_from_position(ee_position, dt)
```

HDF5 输入字段：

| 字段 | 用途 |
|---|---|
| `actions` | 计算 joint tracking RMSE |
| `states/articulation/robot/joint_position` | 关节状态 |
| `states/articulation/robot/joint_velocity` | joint SPARC / joint ISJ |
| `ee_pose/position` | 末端执行器位置、path length、位置差分速度 |
| `ee_pose/linear_velocity` | 如果存在，优先用于 EE SPARC 和 EE ISJ |

输出字段：

```text
ee_sparc
joint_sparc_mean
ee_isj
joint_isj
ee_path_length
joint_rmse_mean
ee_speed_max
ee_speed_mean
```

## 5. SPARC 和其他指标的区别

| 指标 | 看什么 | 什么时候有用 |
|---|---|---|
| success | 是否达成最终目标 | 最基础任务完成率 |
| normalized score | subtask 进度 | 失败但有部分进展时 |
| SPARC | 速度频谱平滑度 | 比较动作是否抖动、是否顺滑 |
| ISJ | jerk 的积分平方 | 对加速度变化更敏感 |
| path length | 末端路径长度 | 是否绕远、是否效率低 |
| speed mean/max | 动作快慢 | 评估是否过快、停滞或动作激进 |

SPARC 不应该单独解释策略好坏。一个策略可能 SPARC 很好但没完成任务，也可能成功但动作很抖。因此 RoboLab 把它和 success、score、path length、speed 一起看。

## 6. 为什么用 adaptive cutoff

频谱尾部可能有噪声。如果固定看很高频，噪声会把 arc length 拉大，导致 SPARC 过度惩罚。因此源码会：

1. 计算速度频谱幅值。
2. 归一化到最大幅值为 1。
3. 找到幅值仍高于 `amplitude_threshold=0.05` 的最高频率。
4. 用 `min(这个频率, fc)` 作为实际 cutoff。

说人话：只计算“频谱里真的有能量”的那段曲线，忽略后面几乎全是噪声的长尾。

## 7. 实际结果里怎么读

在论文表格中，SPARC 和 success/score 一起出现。读法建议：

1. 先看 success：任务是否完成。
2. 再看 score：失败时是否有部分 subtask 进展。
3. 再看 SPARC：动作是否平滑。
4. 再看 path length / speed：动作是否绕远或异常快慢。

> [!TIP]
> **一句话记忆**：success 看结果，score 看进度，SPARC 看动作质量。SPARC 越接近 0 越平滑，越负说明速度频谱越复杂、动作越抖。

## 8. 和我们复现结果的关系

我们已经有完整复现输出：

```text
run_0.hdf5
episode_results.jsonl
event log
sensor / viewport mp4
```

理论上可以对 `run_0.hdf5` 再跑：

```python
from robolab.core.metrics import compute_experiment_metrics

compute_experiment_metrics(output_dir, overwrite=True)
```

然后读取 `episode_metrics.json` 中的 `ee_sparc`。这一步不改变仿真结果，只是离线分析轨迹质量。

> [!WARNING]
> **注意边界**：SPARC 依赖采样率 `dt`、速度是否真实记录、轨迹是否足够长、是否几乎静止。源码里对静止轨迹返回 `NaN`，后续汇总时应过滤，而不是把 NaN 当成 0 或成功平滑。
