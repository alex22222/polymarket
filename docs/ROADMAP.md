# Polymtrade 系统发展建议

> 生成时间：2026-05-24  
> 基于对系统代码、界面、数据管道的全面审查

---

## 第一性原理

这个系统的核心假设：

> **"我的模型算出的概率，比 Polymarket 市场的隐含概率更准确。"**

如果这个假设成立，你就能赚钱。如果它不成立，你就是在掷骰子。

**所有建议都围绕一个目标：用最快、最便宜的方式，证明或证伪这个假设。**

---

## 短期（1-2 周）：让系统从"玩具"变"工具"

### 1. 用真实波动率替换硬编码

**现状：**
```python
vol = 0.72 if market.asset == "BTC" else 0.86
```

**问题：** 72% 是 2022 年熊市波动率，不是常态。用固定值会让模型系统性高估/低估 barrier touch 概率。

**做法：**
```python
from polymtrade.superpowers.barrier import realized_volatility

def get_rolling_vol(asset, lookback_days=60):
    candles = fetch_recent_candles(asset, limit=lookback_days)
    prices = [c["close"] for c in candles]
    return realized_volatility(prices, periods_per_year=365)
```

**影响：** ⭐⭐⭐⭐⭐ 最大单一改进，消除模型最大的偏差源。

---

### 2. 把 barrier touch 概率从蒙特卡洛换成解析解

**现状：** 跑 5000-10000 次蒙特卡洛模拟。

**问题：** Barrier option 的 touch probability 有**闭式解**：
```
P(hit_above) = N(d1) + (B/S)^(2μ/σ²-1) * N(d2)
```

**做法：** 用 `py_vollib` 或自己实现 Black-Scholes barrier 公式。

**好处：**
- 从 500ms → 0.1ms（快 5000 倍）
- 没有随机噪声（蒙特卡洛每次结果略有不同）
- 可以求导数（做 Greeks 分析）

**影响：** ⭐⭐⭐⭐⭐ 性能 + 精确度双提升。

---

### 3. 建立 Polymarket 价格跟踪表

**现状：** 你有真实 K 线，但没有 Polymarket 市场的历史价格。

**问题：** 没有市场价格历史 = 无法回测。

**最现实的方案：**

每天手动记录（或写个定时脚本）几个活跃 barrier 市场的：
- 市场 question
- 当前 spot 价格
- barrier 价格
- 到期天数
- Yes 价格（市场隐含概率）
- 当时计算的模型概率

```python
# 每天运行一次
python3 -c "
import datetime
from polymtrade.research.scanner import scan_markets

results = scan_markets()
for r in results[:10]:
    print(f'{datetime.datetime.now()},{r.question},{r.spot},{r.barrier},{r.days},{r.market_yes_price},{r.model_probability}')
" >> data/raw/market_price_log.csv
```

**积累 1-2 个月后**，你就有足够的数据做**真实回测**了。

**影响：** ⭐⭐⭐⭐⭐ 没有这一步，整个系统无法验证。

---

### 4. 删除所有 demo 数据相关代码

**现状：** `make_demo_markets()`、`DemoMarket`、`demo_data.py` 还在代码库里（虽然文件已删，但可能有残留引用）。

**问题：** Demo 数据会污染你的思维——让你误以为策略有效。

**做法：** 全局搜索 `demo`、`Demo`、`fake`、`mock`，全部清理。

**影响：** ⭐⭐⭐⭐ 避免自欺欺人。

---

## 中期（1 个月）：建立可验证的研究流程

### 5. Walk-Forward Backtest（滚动前向回测）

**现状：** 之前的回测是"开天眼"——用已知 outcome 验证模型。

**正确的回测：**
```
假设今天是 2024-06-01
用 2024-03-01 ~ 2024-06-01 的价格算波动率
用蒙特卡洛/解析解算 P(touch by 2024-07-01)
对比 2024-06-01 的市场价格
如果 EV > threshold，记录"虚拟买入"
等到 2024-07-01，看实际是否触及 barrier
记录盈亏
```

然后滚动窗口：
```
2024-06-02 ~ 2024-09-02
2024-06-03 ~ 2024-09-03
...
```

**这是唯一能证明策略有效的方法。**

**影响：** ⭐⭐⭐⭐⭐ 没有 walk-forward，所有回测都是垃圾。

---

### 6. 接入 Option 隐含波动率（IV）作为基准

**现状：** 你用历史 realized vol 算模型概率。

**问题：** 市场参与者（尤其是机构）用的是 **option implied vol**，不是 realized vol。

**做法：** 从 Deribit 或 CME 获取 BTC option 的 ATM IV：
```python
# Deribit API（免费，无需认证）
https://www.deribit.com/api/v2/public/get_instruments?currency=BTC&kind=option
```

比较：
- 你的模型概率（基于 realized vol）
- 市场隐含概率（Polymarket Yes 价格）
- Option IV 隐含概率（基于 option 市场）

**如果 option IV 和 Polymarket 价格一致，但你的模型偏离** → 可能是你的波动率假设错了。  
**如果 option IV 和你的模型一致，但 Polymarket 偏离** → 可能是 Polymarket 的市场无效性，有机会。

**影响：** ⭐⭐⭐⭐ 提供独立的验证基准。

---

### 7. 添加参数敏感性分析

**现状：** edge_threshold、vol_window、simulations 都是硬编码。

**问题：** 你不知道策略表现是否依赖特定参数。

**做法：** 跑参数网格搜索：
```python
for vol_window in [30, 60, 90, 120]:
    for edge_threshold in [0.02, 0.03, 0.05, 0.10]:
        for fee_rate in [0.02, 0.04]:
            result = run_backtest(vol_window, edge_threshold, fee_rate)
            print(f"{vol_window}d / {edge_threshold} edge / {fee_rate} fee → PnL: {result.pnl}")
```

**影响：** ⭐⭐⭐⭐ 防止过拟合。

---

### 8. 添加风险管理模块

**现状：** 没有止损、没有仓位控制。

**问题：** 即使 EV 为正，单笔重仓 + 连续亏损也会爆仓。

**最小可行风控：**
- **单笔限额**：不超过总资金的 2%
- **日止损**：单日亏损超过 5% 停止交易
- **相关性控制**：同时持仓不超过 3 个相关市场（比如不能同时押注 BTC 80K、BTC 90K、BTC 100K）
- **Kelly Criterion**：根据胜率和赔率动态调整仓位

```python
def kelly_fraction(win_rate, avg_win, avg_loss):
    return (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
```

**影响：** ⭐⭐⭐⭐ 防止"正确但破产"。

---

## 长期（1-3 个月）：从研究到实盘

### 9. Paper Trading（模拟交易）

**不要真钱。**

用 $100 虚拟资金，每天根据 Scanner 信号"下单"，记录：
- 买入价格
- 预期 EV
- 实际结果
- 盈亏

跑 100 笔交易后，统计：
- 胜率
- 平均盈亏
- 最大回撤
- Sharpe ratio

**如果 paper trading 不赚钱，不要上真钱。**

**影响：** ⭐⭐⭐⭐⭐ 唯一的真理标准。

---

### 10. 数据管道自动化

**现状：** 手动运行脚本抓取数据。

**自动化：**
```bash
# crontab -e

# 每天 00:05 UTC 拉取最新 K 线
5 0 * * * cd /path/to/polymarket && python3 scripts/fetch_crypto_history.py --symbol BTCUSDT --interval 1d --start $(date -v-1d +%Y-%m-%d) --out data/raw

# 每小时扫描一次市场
0 * * * * cd /path/to/polymarket && python3 -m polymtrade.research.scanner >> logs/scanner-$(date +\%Y\%m\%d).log
```

**影响：** ⭐⭐⭐ 解放双手。

---

### 11. 多资产扩展

**现状：** 只覆盖 BTC/ETH。

**扩展：**
- **SOL**、**XRP**、**DOGE** 也有 Polymarket barrier 市场
- 宏观事件（美联储决议、CPI、非农）也有二元市场
- 体育、政治事件（你的信息优势可能在这里）

**但不要急于扩展。** 先在 BTC/ETH 上证明模型有效，再复制到其他资产。

**影响：** ⭐⭐⭐ 放大容量，但前提是核心模型有效。

---

### 12. 建立"失败日志"

**大多数人只记录赢的交易。你应该记录输的交易。**

每次模型预测错误时，记录：
- 模型概率 vs 实际结果
- 当时的波动率假设
- 是否有突发事件（新闻、监管、大户操纵）
- 市场流动性是否充足

**定期复盘失败日志，比复盘成功日志更有价值。**

**影响：** ⭐⭐⭐ 持续改进的燃料。

---

## 优先级矩阵

| # | 建议 | 实施难度 | 影响 | 优先级 |
|---|------|---------|------|--------|
| 1 | 真实波动率替换硬编码 | 低 | 极高 | 🔴 P0 |
| 2 | 解析解替换蒙特卡洛 | 低 | 极高 | 🔴 P0 |
| 3 | 建立价格跟踪表 | 低 | 极高 | 🔴 P0 |
| 4 | 删除 demo 数据 | 低 | 高 | 🔴 P0 |
| 5 | Walk-Forward 回测 | 中 | 极高 | 🟡 P1 |
| 6 | 接入 Option IV | 中 | 高 | 🟡 P1 |
| 7 | 参数敏感性分析 | 中 | 高 | 🟡 P1 |
| 8 | 风险管理模块 | 中 | 高 | 🟡 P1 |
| 9 | Paper Trading | 低 | 极高 | 🟢 P2 |
| 10 | 数据管道自动化 | 低 | 中 | 🟢 P2 |
| 11 | 多资产扩展 | 中 | 中 | 🟢 P2 |
| 12 | 失败日志 | 低 | 中 | 🟢 P2 |

---

## 一句话总结

> **不要优化界面，不要加新功能，不要扩展资产。接下来两周只做一件事：用真实波动率 + 解析解 + 手动价格跟踪，跑 30 天的 walk-forward paper trading。如果这 30 天是赚钱的，你手里拿的就是印钞机。如果亏钱，说明核心假设是错的，再漂亮的界面也救不了。**
