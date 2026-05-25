# Polymtrade 界面诊断报告

> 审查对象：`http://127.0.0.1:8765/`（本地 Dashboard）  
> 审查时间：2026-05-24  
> 审查方式：代码审查（`web/index.html` + `web/app.js` + `web/styles.css` + `app.py`）+ 实际 API 测试  
> 审查人：Kimi Code CLI Agent

---

## 一句话定性

> **一个"看起来能扫描"但实际上扫不了的漂亮壳子。前端画好了所有功能，后端只实现了一半。**

---

## 界面功能概览

```
┌─────────────────────────────────────────┐
│  Polymtrade              [刷新] [Scanner] │  ← 顶部操作栏
├─────────────────────────────────────────┤
│ 候选 │ 最佳Edge │ 最佳ROI │ 扫描市场 │ 价格源 │  ← 5 个指标卡片
├────────────────────────┬────────────────┤
│                        │                │
│   价格序列（Canvas）    │   策略栈        │  ← 左：折线图；右：静态说明
│   [BTC] [ETH]          │   数据→模型→成本→执行 │
│                        │                │
├────────────────────────┴────────────────┤
│ 数据覆盖                                │
│ [抓取真实价格] [抓取真实市场]            │
│ BTC binance-data-api 3203 根 ...        │
├─────────────────────────────────────────┤
│ Scanner                                 │
│ 波动率 -- │ 路径 -- │ 过滤 -- │ 状态 -- │  ← Scanner 摘要
├─────────────────────────────────────────┤
│ 动作 │ 资产 │ 市场 │ 方向 │ 现价 │ 目标 │ 到期 │ 市场 │ 模型 │ 净Edge │ ROI │ 流动性 │
│                    （表格永远为空）       │  ← Scanner 结果表格
└─────────────────────────────────────────┘
```

---

## 正面评价

| 方面 | 评价 |
|------|------|
| **视觉设计** | 干净、现代、有专业感。配色（绿/红/蓝/金）克制，不是典型的"程序员审美" |
| **信息架构** | 5 个指标卡片 → 价格图表 + 策略栈 → 数据覆盖 → Scanner 表格，层级清晰，信息密度适中 |
| **响应式布局** | 有 `@media` 查询适配移动端，虽然量化研究场景很少在手机上使用 |
| **前端纯手写** | 无 React/Vue 依赖，原生 JS + Canvas，页面加载极快 |
| **数据覆盖展示** | 能直观看到已抓取了 3203 条 BTC/ETH 真实 K 线，来源和区间一目了然 |

---

## 致命问题

### 问题 1：Scanner 功能是"画皮"——后端根本没实现

**证据链：**

前端 `web/app.js` 第 246 行：
```javascript
const response = await fetch(
  "/api/scanner?limit=50&edge=0.02&min_liquidity=500&simulations=1500&vol_window=90d"
);
```

后端 `polymtrade/app.py` 中已实现的端点：
- `/api/health` ✅
- `/api/dashboard` ✅
- `/api/data-summary` ✅
- `/api/candles` ✅
- `/api/fetch-crypto-prices` ✅
- `/api/fetch-real-markets` ✅
- `/api/run-demo-backtest` ✅
- **`/api/scanner`** ❌ **不存在**

**后果：**
界面上最醒目的"运行 Scanner"按钮，点击后会返回 HTTP 404。用户看到的是一个**永远空的 Scanner 表格**。

这是整个界面最大的"欺诈"——**核心功能只存在于前端想象中**。

---

### 问题 2：Demo 数据和真实数据混杂

**实际 API 返回（`/api/data-summary`）：**

```json
{
  "candles": [
    {
      "asset": "BTC",
      "source": "binance-data-api",
      "candles": 3203,
      "latest_close": 76471.83
    },
    {
      "asset": "BTC",
      "source": "demo",
      "candles": 365,
      "latest_close": 151188.25
    },
    {
      "asset": "ETH",
      "source": "binance-data-api",
      "candles": 3203,
      "latest_close": 2095.94
    }
  ]
}
```

**问题：**
- BTC demo 数据显示收盘价 **$151,188**——这是随机生成的假数据
- 真实 BTC 价格是 **$76,471**
- 前端渲染时没有区分来源标识，用户可能分不清哪个是真的

---

### 问题 3：价格图表过于简陋

当前只是一个**收盘价折线图**，缺失：

| 缺失元素 | 对策略研究的价值 |
|---------|----------------|
| 成交量柱状图 | 识别放量突破/缩量回调 |
| 均线（MA20/MA60） | 判断趋势方向和支撑阻力 |
| 波动率区间（Bollinger Bands）| 直观看到价格偏离程度 |
| **Barrier 水平线** | **最关键：当前价格距离目标价多远** |
| 历史 touch 事件标记 | 验证模型回测结果 |

对于 barrier 策略研究，**"spot 价格 vs barrier 水平的距离"是最关键的可视化**，但图表完全没有体现这一点。

---

### 问题 4：策略栈是静态展示

```html
<div class="stack-list">
  <div><span>数据</span><strong>BTC / ETH + 宏观扩展预留</strong></div>
  <div><span>模型</span><strong>Monte Carlo Touch Probability</strong></div>
  <div><span>成本</span><strong>Taker Fee + Slippage</strong></div>
  <div><span>执行</span><strong>只读 / Paper Trading</strong></div>
</div>
```

这只是**写死的 HTML 文字**，没有任何实时参数。应该显示：
- 当前使用的波动率窗口（如 "90d realized vol = 42.3%"）
- 当前蒙特卡洛路径数（如 "10,000 paths"）
- 当前 fee 假设（如 "2% taker + 50bps slippage"）
- 当前 edge threshold（如 "min edge = 5%"）

---

### 问题 5：缺少最关键的交易信号可视化

策略核心逻辑是：**模型概率 vs 市场隐含概率的偏差**。

但界面上**没有任何地方直观展示这个偏差**。

理想情况下应该有一个**散点图**：
- **X 轴**：市场隐含概率（Polymarket Yes 价格）
- **Y 轴**：模型概率（蒙特卡洛计算结果）
- **对角线**：公平定价线（模型 = 市场）
- **偏离对角线的点**：交易机会
  - 上方 = 模型 > 市场 → **绿色 = 买入 Yes**
  - 下方 = 模型 < 市场 → **红色 = 买入 No**

这种可视化能让用户在 1 秒内识别所有交易机会。

---

## 期望满足度评估

基于项目 README 和对话中表达的期望：

| 期望 | 是否满足 | 差距说明 |
|------|---------|---------|
| 看到 BTC/ETH 历史价格走势 | ⚠️ 部分满足 | 有折线图，但太简单，没有 barrier 标记和技术指标 |
| 发现模型概率 vs 市场概率的偏差 | ❌ **不满足** | Scanner API 不存在，表格永远为空 |
| 判断是否应该买入 Yes/No | ❌ **不满足** | 没有信号生成逻辑和可视化 |
| 监控数据覆盖情况 | ✅ 满足 | 能显示已抓取多少 K 线、多少市场 |
| 运行回测看历史表现 | ⚠️ 部分满足 | 有 `/api/run-demo-backtest`，但用的是 demo 数据 |
| 策略参数实时调整 | ❌ 不满足 | 参数硬编码，界面无配置入口 |

**满足度：约 30%**。界面"看起来像那么回事"，但核心功能未接通。

---

## 资源分配失衡

```
当前代码量分布：
┌──────────────────────────────────────────┐
│ CSS (样式)        436 行  ████████████████ 35% │
│ JS (前端逻辑)     276 行  ██████████ 22%       │
│ HTML (结构)       134 行  █████ 11%           │
│ Python 后端       ~200 行 ████████ 16%        │
│ Scanner API        0 行   ░░░░░░░░ 0%         │
│ 策略模型核心       ~200 行 ████████ 16%       │
└──────────────────────────────────────────┘
```

对于一个量化研究系统，合理的资源分配应该是：
- 数据管道：40%
- 模型/回测：40%
- 可视化：20%

当前完全反过来：
- 可视化：60%
- 数据：20%
- 模型：20%（且 Scanner 未跑通）

---

## 改造优先级清单

### 🔴 立即修复（30 分钟内）

1. **删除或隔离 demo 数据**
   ```bash
   sqlite3 polymtrade.sqlite "DELETE FROM crypto_candles WHERE source = 'demo';"
   ```

2. **实现 `/api/scanner` 后端端点**
   ```python
   # 在 app.py 中添加：
   if path == "/api/scanner":
       # 1. 读取所有 active barrier markets
       # 2. 对每个市场获取 spot, barrier, days, market_ask
       # 3. 调用 barrier.py 的 monte_carlo_touch_probability
       # 4. 计算 net_edge = model_p - market_ask - fee - slippage
       # 5. 过滤出 candidates（net_edge > threshold）
       # 6. 返回 JSON
   ```

3. **在价格图表上画 barrier 水平线**
   ```javascript
   // 在 drawPriceChart() 中增加：
   const barrierY = yFor(barrierPrice);
   ctx.strokeStyle = "#b4233a";
   ctx.setLineDash([6, 4]);
   ctx.beginPath();
   ctx.moveTo(pad, barrierY);
   ctx.lineTo(width - pad, barrierY);
   ctx.stroke();
   ctx.fillStyle = "#b4233a";
   ctx.fillText("Barrier: " + money(barrierPrice), width - pad - 120, barrierY - 6);
   ```

### 🟡 短期增强（2-4 小时）

4. **添加散点图：模型概率 vs 市场概率**
   - 新建一个 Canvas 或复用现有图表区域
   - 每个 market 是一个点
   - 颜色编码：绿色 = 买入 Yes，红色 = 买入 No

5. **策略栈改为动态显示当前参数**
   - 从后端 API 获取当前 vol_window、simulations、fee_rate
   - 实时渲染到界面

6. **Scanner 表格添加"模拟下单"按钮**
   - 仅记录到本地 SQLite（paper trading）
   - 不连接真实钱包

### 🟢 中期优化（1-2 天）

7. **添加回测结果可视化**
   - 权益曲线（equity curve）
   - 最大回撤标记
   - 胜率/盈亏比统计卡片

8. **参数调优面板**
   - 滑块调整 vol_window、edge_threshold、simulations
   - 实时重新运行 scanner

---

## 一句话建议

> **先别管界面好不好看，把 `/api/scanner` 后端逻辑接通，让表格里能出现第一条真实的"候选/回避"信号。在那之前，这个界面只是一个漂亮的空壳。**

---

## 附录：已测试的 API 端点状态

| 端点 | HTTP 状态 | 实际功能 |
|------|----------|---------|
| `GET /` | 200 | 返回 index.html |
| `GET /api/health` | 200 | 返回 `{"ok": true, "mode": "offline-first"}` |
| `GET /api/data-summary` | 200 | 返回 candles + markets + priceHistory 摘要 |
| `GET /api/candles?asset=BTC` | 200 | 返回 3203 条日线数据 |
| `GET /api/fetch-crypto-prices` | 200 | 从 Binance 抓取真实价格 |
| `GET /api/fetch-real-markets` | 200/502 | 从 Polymarket 抓取市场（网络受限时失败） |
| `GET /api/run-demo-backtest` | 200 | 运行 demo 回测 |
| **`GET /api/scanner`** | **404** | **未实现** |
| `GET /api/dashboard` | 200 | 返回 runs + trades（空表） |

---

*本文档基于代码审查和实际 API 测试生成，所有结论可复现。*
