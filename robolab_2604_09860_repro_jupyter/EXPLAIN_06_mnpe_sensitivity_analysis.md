# 精讲 6：MNPE 敏感性分析，代码怎么实现

> [!NOTE]
> **颜色标识**：绿色表示核心结论，蓝色表示源码/输入输出路径，橙色表示边界、风险和容易误解的点。

## 先说结论

MNPE 全称是 **Mixed Neural Posterior Estimation**。论文把它放在 `III-D Sensitivity Analysis` 和 `Appendix B Details of MNPE Sensitivity Analysis`。它不是机器人策略，也不是新的任务成功率，而是 rollout 之后的一种诊断工具：用已经采集到的仿真评测数据，反过来估计“什么环境参数最可能对应成功/失败”。

> [!TIP]
> **核心结论**：普通评测问的是“给定相机、光照、物体位置，策略能不能成功”；MNPE 问的是反向问题：“如果我只看到了成功或失败，哪些相机偏移、光照、桌面材质、物体初始位姿最可能导致这个结果”。所以它适合找策略脆弱点，而不是替代 policy rollout。

在 RoboLab 里，MNPE 的代码链路可以理解成：

```text
扰动评测脚本
  -> 运行同一任务在多组 camera/background/table/object pose 变化下的 episodes
  -> 汇总成 CSV，每行包含参数 theta 与观测 x
  -> posterior_inference.py 读取 CSV
  -> prepare_data_for_mnpe() 整理参数列和观测列
  -> 有离散参数时用 MNPE，只有连续参数时退回 NPE
  -> append_simulations(theta, x).train()
  -> build_posterior()
  -> 给定 x_o = success=1 或 success=0 采样 p(theta | x_o)
  -> 输出均值、95% credible interval、类别概率和图
```

## 1. MNPE 在论文里解决什么问题

RoboLab 已经能输出 success、score、SPARC、path length 等指标，但这些指标回答的是“结果怎么样”。敏感性分析想继续追问：

| 问题 | 普通 success 表能回答吗 | MNPE 能补什么 |
|---|---|---|
| 相机轻微移动会不会让策略崩 | 只能看到某些设置下成功/失败 | 估计成功样本对应的相机偏移分布 |
| 失败是否集中在某类光照/桌面材质 | 需要人工分组对比 | 输出每个离散类别在 posterior 里的概率 |
| 物体初始位姿离参考位置多远时更容易失败 | 需要自己画分箱曲线 | 输出连续参数的均值和 95% credible interval |
| 策略到底是对某个参数敏感，还是整体都不稳 | 单个均值难判断 | 看 posterior 是窄而集中，还是宽而接近 prior |

论文里的判断逻辑很直接：如果 `p(theta | success=1)` 紧紧集中在参考配置附近，说明策略只有在参数接近默认值时才容易成功，也就是对这个参数敏感；如果 posterior 很宽，说明成功不依赖某个很窄的参数范围，鲁棒性更强。

> [!WARNING]
> **不要把 MNPE 读成因果证明**：它给的是“在已有实验分布下，参数和结果的后验关联”。如果采样数据太少、任务太少、或者某些参数组合根本没跑过，MNPE 只能反映已有数据，不会自动证明真实世界因果。

## 2. 输入输出说清楚

MNPE 的输入有两类：

| 名称 | 符号 | 在代码里是什么 | 例子 |
|---|---|---|---|
| 参数 | `theta` | `param_columns` 整理出的张量 | `external_cam_initial_pose_distance`、`wrist_cam_initial_pose_distance`、`lighting_intensity`、`table_material` |
| 观测 | `x` | `obs_columns` 整理出的张量 | `success`、`success_rate`、`task_duration`、`score` |

输出是 posterior：

```text
p(theta | x_o)
```

这里的 `x_o` 是查询条件，例如：

```text
x_o = [success=1.0]  -> 什么参数最可能对应成功
x_o = [success=0.0]  -> 什么参数最可能对应失败
x_o = [success=1.0, duration=30.0] -> 什么参数最可能对应成功且耗时约 30 秒
```

RoboLab 脚本最终会输出：

| 输出 | 含义 |
|---|---|
| continuous mean | 连续参数在 posterior 里的平均值 |
| 95% credible interval | 连续参数的后验可信区间 |
| categorical probabilities | 离散类别在 posterior 样本里的占比 |
| pairplot / histogram / bar plot | 帮人看参数间的联合关系和边缘分布 |
| ESS | importance sampling 后的有效样本量，太低说明纠偏不稳 |

> [!NOTE]
> **源码入口**：核心脚本是 `analysis/sensitivity_analysis/posterior_inference.py`；使用说明在 `analysis/sensitivity_analysis/README_posterior_inference.md`；产生扰动数据的入口包括 `policies/pi0_family/run_camera_pose_variation.py`、`run_background_variation.py`、`run_table_variation.py`，底层扰动配置在 `robolab/variations/camera.py`、`backgrounds.py`、`lighting.py`。

## 3. 扰动数据从哪里来

MNPE 不能凭空分析，必须先有一批带扰动参数的 rollout 数据。RoboLab 里常见来源有三类：

```text
run_camera_pose_variation.py
  -> 对 external camera / wrist camera 做 reset-time pose perturbation
  -> 输出每个 task + camera variation 的 episode result

run_background_variation.py
  -> 把同一任务注册成多个 background variation env
  -> 输出不同 HDR/EXR 背景下的 episode result

run_table_variation.py
  -> 运行不同 table material
  -> episode_results.jsonl 里额外记录 table_material
```

这些脚本的共同点是：它们不是只跑一个默认环境，而是系统化扫一组环境变化。后处理时再把结果汇总成 CSV，让每一行长得像这样：

```text
policy, env_name, experiment_name,
external_cam_initial_pose, wrist_cam_initial_pose,
lighting_intensity, table_material,
success, score, task_duration
```

然后 `posterior_inference.py --use-real-data --csv-file ...` 才能把这些列变成 MNPE 的训练数据。

## 4. `prepare_data_for_mnpe()` 做了什么

这一步是整条链路最容易低估的部分。MNPE 本身只认识数值张量，真实 CSV 里却混着字符串、布尔值、类别和位姿字符串，所以脚本先做数据清洗。

源码等价逻辑：

```python
df = read_csv(csv_file)
df = filter_by_policy_task_experiment(df)

theta_columns = continuous_columns + categorical_columns
theta_df = df[theta_columns]
obs_df = df[obs_columns]

theta_df = encode_categories(theta_df)
theta_df = normalize_continuous_to_0_1(theta_df)
obs_df = convert_success_bool_to_0_1(obs_df)

theta = torch.tensor(theta_df.values)
x = torch.tensor(obs_df.values)
prior = create_uniform_prior(...)
```

重点有四个：

1. **过滤实验范围**：可以只看某个 policy、某个 task、某个 experiment，避免把不同问题混在一起。
2. **连续参数放前面，离散参数放后面**：这是脚本对 MNPE 的约束，方便区分 normalizing flow 和 categorical distribution。
3. **连续参数归一化到 `[0, 1]`**：相机距离、物体位姿距离、角度等量纲不同，先归一化能让神经网络更容易训练。
4. **离散参数编码成整数**：例如桌面材质、光照强度档位、背景类别，最终变成 `0, 1, 2...`。

> [!TIP]
> **怎么记**：`theta` 是“我动了哪些旋钮”，`x` 是“策略最后表现如何”。MNPE 学的是“看到表现以后，哪些旋钮位置最可能”。

## 5. 位姿参数怎么变成一个数

论文里把 camera pose / object pose 当成 SE(3) 位姿。位姿本来是 7 维：位置 `x,y,z` 加四元数 `qw,qx,qy,qz`。为了做敏感性分析，代码会把位姿转成“离参考位姿多远”的连续参数。

说人话：

```text
pose_distance =
  平移距离
  + beta * 旋转 geodesic distance
```

其中：

- 平移距离看相机或物体位置偏了多少米。
- 旋转距离看四元数方向偏了多少弧度。
- `beta` 控制“旋转偏差”在总距离里占多大权重。

README 里给了两个典型相机列：

```text
external_cam_initial_pose -> external_cam_initial_pose_distance
wrist_cam_initial_pose    -> wrist_cam_initial_pose_distance
```

如果只分析物体初始位置，脚本也支持把类似 `banana_initial_pose`、`bowl_initial_pose` 的字符串解析成到原点的欧氏距离。

> [!WARNING]
> **距离是压缩表示**：把 7DoF 位姿压成一个距离，便于训练和可视化，但会丢掉“往左偏”和“往右偏”的方向信息。如果要分析方向性，应该把位姿拆成多个参数，而不是只用距离。

## 6. 训练和推理的核心代码

RoboLab 脚本的核心训练逻辑可以压缩成下面几步：

```python
if num_categorical > 0:
    inference = MNPE(device=device)
else:
    inference = NPE(device=device)

inference.append_simulations(theta, x)
density_estimator = inference.train(max_num_epochs=max_epochs)
posterior = inference.build_posterior(density_estimator, prior=target_prior)
samples = posterior.sample((num_samples,), x=x_o)
```

这里有一个容易误解的点：

> [!WARNING]
> **论文叫 MNPE，但代码不总是调用 MNPE**：当参数里有桌面材质、光照档位、背景类别这类离散列时，脚本用 `sbi.inference.MNPE`。如果只有相机距离、物体距离这类连续参数，脚本会用 `NPE`。这不是绕开论文，而是同一类 posterior estimation 在纯连续场景下的合适实现。

训练目标是让神经网络学习 `p(theta | x)`。训练完成后，我们不再问“这个 theta 会不会成功”，而是给一个观测 `x_o`：

```text
success = 1.0
```

再从 posterior 里采样很多组 `theta`。这些样本就是“在模型看来，最能解释成功的环境参数分布”。

## 7. Importance sampling 为什么存在

论文强调使用 uniform prior，是为了让分析不要先验偏向某个参数区域。但真实评测数据经常不是均匀采样的：比如 70% 都在默认光照，只有少量极暗光照；或者某个背景跑得很多，另一个背景跑得少。

代码里的 correction 思路是：

```text
目标：想要 uniform prior 下的 posterior
现实：训练数据来自不均匀 empirical proposal
做法：给 posterior samples 乘 importance weight
权重：target prior probability / empirical proposal probability
```

输出里的 ESS，也就是 Effective Sample Size，用来提醒这个纠偏是否可靠：

| ESS 状态 | 解读 |
|---|---|
| 高 | 数据覆盖和目标 prior 比较匹配，重加权较稳 |
| 中 | 可以看趋势，但别过度解释细节 |
| 很低 | 说明你跑的数据太偏，应该补采样，而不是相信漂亮图 |

> [!WARNING]
> **低 ESS 是数据问题，不是画图问题**：如果某些参数区域没有 rollout，后验纠偏只能靠很少的样本硬撑，结论会很脆。

## 8. 结果怎么读

假设我们查询：

```text
obs_columns = ["success"]
obs_values = [1.0]
```

看到下面几种结果时应该这样理解：

| posterior 形状 | 说人话解释 |
|---|---|
| `external_cam_distance` 均值很小，95% CI 很窄 | 成功大多发生在相机接近默认位置时，策略对外部相机偏移敏感 |
| `wrist_cam_distance` CI 很宽 | 腕部相机偏移对成功影响没那么集中，可能更鲁棒 |
| `table_material=wood` 概率远高于其他材质 | 成功更常和某个桌面材质关联，可能有纹理/反光/对比度影响 |
| success=0 的 posterior 集中在极暗光照 | 失败更可能来自照明不足 |
| success=1 和 success=0 的 posterior 差不多 | 这个参数可能不是主要失败因素，或者数据量不足 |

## 9. 和本次 4090 复现的关系

我们目前已经完成：

- 一条 `Pi05 + BananaInBowlTask` 完整成功闭环。
- 三个复杂任务抽样，其中 1 个成功、2 个失败。
- 视频、HDF5、event log、episode_results.jsonl 已同步。

这还不够支撑正式 MNPE 敏感性分析。原因是 MNPE 需要同一任务/同一策略在很多扰动参数组合下的结果，至少要形成可训练的 `theta, x` 数据表。当前几条复现更适合作为“rollout 链路通了”的证据，而不是 posterior inference 的统计证据。

下一步如果要真的跑 MNPE，正确顺序是：

```text
1. 选一个任务，例如 BananaInBowlTask
2. 固定一个策略，例如 pi05_droid_jointpos
3. 跑 camera pose variation / lighting variation / table variation
4. 汇总每个 episode 的参数列和 success/score/duration
5. 用 posterior_inference.py 查询 success=1 和 success=0
6. 比较 posterior 是否集中在某些参数区域
```

> [!TIP]
> **最小可行实验**：先不要上 RoboLab-120。先用一个任务、一个策略、两类扰动，每类 20-50 个 episode，确认 CSV 和 posterior 图能跑通，再扩展到多任务。

## 10. 额外示例：一个轻量 MNPE 思维实验

为了让 notebook 不依赖 `sbi` 也能验证 MNPE 的直觉，我们可以用一个轻量贝叶斯重加权测试：

```text
先均匀采样 camera_offset in [0, 1]
再设定 success probability 随 camera_offset 增大而下降
然后只观察 success=1
最后看 posterior 里的 camera_offset 是否比 prior 更靠近 0
```

如果测试结果显示：

```text
prior camera mean      ≈ 0.50
posterior success mean < 0.50
posterior success CI   更偏向小偏移
good_lighting posterior probability > prior probability
```

这说明“成功”确实把参数分布往更友好的区域拉了过去，也就是 MNPE 在论文里要表达的核心直觉。

如果我们把 success probability 设成和 camera_offset 无关，posterior 应该接近 prior。这对应“策略对这个参数不敏感，或者数据没有显示出这个参数的影响”。

## 11. 本节最重要的边界

- MNPE 是离线分析，不在每一步机器人控制循环里运行。
- MNPE 依赖扰动评测数据，不能用 3-5 条 episode 就下结论。
- posterior 集中说明“成功样本关联到某个参数区域”，不等价于严格因果。
- 论文里的 MNPE 框架支持混合连续/离散参数；RoboLab 代码在纯连续参数时会自动退回 NPE。
- 如果实验数据的采样分布很偏，必须关注 importance sampling 和 ESS。
- 对 4090 来说，MNPE 本身通常不是显存瓶颈；真正耗时耗显存的是前面的 Isaac Sim + VLA rollout 数据采集。

## 12. 一句话总结

> [!TIP]
> **核心结论**：RoboLab 的 MNPE 敏感性分析，是把“跑完很多带扰动的 episode”之后得到的表格数据，变成 `p(环境参数 | 成功或失败)`。它的价值是定位策略对相机、光照、材质、物体位姿等因素的脆弱性，而不是再给一个简单平均分。

