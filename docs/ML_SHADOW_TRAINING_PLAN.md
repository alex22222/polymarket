# ML Shadow Training Plan

> 目标：让 Polymtrade 往机器学习方向演进，但不让未验证模型直接影响交易信号。

## 核心原则

- 先做 shadow model，不替换生产 scanner。
- 只能用真实历史价格、真实结算、真实盘口作为标签或验证依据。
- 不能用系统自己的预测当标签训练自己。
- 任何模型切换都必须通过 `docs/SPEC.md` 的决策门槛。

## 自动执行路线

### Phase 1：历史 barrier 样本生成

每天从 BTC/ETH 历史日线生成 synthetic barrier 样本：

- horizon：1d / 3d / 7d / 14d
- barrier distance：1% / 2% / 5% / 10%
- direction：hit_above / hit_below
- label：未来窗口内 high/low 是否触及 barrier

用途：快速评估触及概率模型是否系统性高估或低估。

### Phase 2：影子校准模型

训练一个轻量 logistic calibration model：

- 输入：GBM 概率、方向、到期、距离、RV、EWMA、momentum
- 输出：shadow probability
- 评估：GBM vs shadow 的 Brier / logloss

用途：判断是否存在稳定校准收益。

### Phase 3：每日报告

每日自动输出：

- 训练样本数
- 验证样本数
- GBM Brier / shadow Brier
- GBM logloss / shadow logloss
- shadow 是否持续优于 GBM

### Phase 4：候选复盘对照

只有当历史 shadow model 连续稳定优于 GBM，才进入真实候选复盘对照：

- 不参与交易
- 只记录“如果用 shadow probability，候选排序是否改善”
- 等真实 resolved 样本足够后再判断

## 当前实现

命令：

```bash
python3 -m polymtrade.research.shadow_training \
  --db polymtrade.sqlite \
  --lookback 1200 \
  --save \
  --output reports/shadow_training/latest.json
```

日报会读取最近一次 shadow training，并展示：

- samples
- validation samples
- GBM Brier
- shadow Brier
- Brier delta

## 安全边界

当前 shadow model 的 `decision` 固定为：

```text
observe_only
```

它不会进入 scanner，不会改变 candidate，不会改变交易控制台。
