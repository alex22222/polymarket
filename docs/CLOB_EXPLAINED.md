# Polymarket CLOB 订单簿模式详解

> 本文解释 Polymarket 的中央限价订单簿（CLOB）机制，以及它与传统 AMM 预测市场的根本差异。  
> 理解 CLOB 对 barrier 策略至关重要——它直接决定了你的**可成交价格**和**实际滑点**。

---

## 1. 什么是 CLOB（Central Limit Order Book）

### 1.1 核心概念

**CLOB = 中央限价订单簿**，是所有传统金融交易所（纽交所、纳斯达克、芝加哥商品交易所）使用的核心交易机制。

想象一个公开的电子白板：

```
┌─────────────────────────────────────┐
│         买单（Bids）                 │
│  价格 $0.62  |  数量 5000  shares   │  ← 买家愿意以 $0.62 买入
│  价格 $0.61  |  数量 12000 shares   │
│  价格 $0.60  |  数量 8000  shares   │
├─────────────────────────────────────┤
│         卖单（Asks）                 │
│  价格 $0.65  |  数量 3000  shares   │  ← 卖家愿意以 $0.65 卖出
│  价格 $0.66  |  数量 7000  shares   │
│  价格 $0.67  |  数量 15000 shares   │
└─────────────────────────────────────┘

Spread = $0.65 - $0.62 = $0.03 (4.6%)
Mid Price = ($0.62 + $0.65) / 2 = $0.635
```

**关键特征**：
- **买方（Bids）**从高到低排列——价格越高越靠前
- **卖方（Asks）**从低到高排列——价格越低越靠前
- **最优买价（Best Bid）**= 最高的买单价格
- **最优卖价（Best Ask）**= 最低的卖单价格
- **Spread（价差）**= Best Ask - Best Bid
- **撮合引擎**自动匹配价格交叉的买卖单

### 1.2 与 AMM 的根本区别

| 维度 | CLOB（Polymarket） | AMM（如 Uniswap、Catnip） |
|---|---|---|
| **定价机制** | 买卖双方自由挂单，价格由市场共识形成 | 算法自动定价（恒定乘积公式 `x*y=k`） |
| **流动性来源** | 专业做市商 + 散户限价单 | 流动性提供者（LP）存入资金池 |
| **滑点** | 取决于订单簿深度，大额订单会"吃穿"多档价格 | 固定公式计算，大额交易滑点巨大 |
| **手续费** | 对 taker 收费（Polymarket 约 2%） | 对每笔交易收费（通常 0.3%） |
| **价格精度** | 离散 tick size（如 $0.01） | 连续价格 |
| **预测准确度** | 通常更高（做市商竞争压缩 spread） | 受 LP 规模和套利效率限制 |
| **透明度** | **完全透明**，所有人可见完整订单簿 | 只能看到资金池余额 |

> **核心洞察**：CLOB 模式下，"市场价格"不是一个数字，而是一个**区间** `[best_bid, best_ask]`。真正的可成交价格取决于你的订单方向和大小。

---

## 2. Polymarket 的 CLOB 具体实现

### 2.1 二元结果代币（Binary Outcome Tokens）

Polymarket 的每个市场发行两种代币：

- **YES Token**：事件发生时价值 $1，否则 $0
- **NO Token**：事件不发生时价值 $1，否则 $0

```
YES 价格 + NO 价格 = $1  （无套利约束）

例："BTC 会在 6 月底前突破 $100k 吗？"
  YES 价格 = $0.62  → 市场认为概率 62%
  NO 价格  = $0.38  → 市场认为概率 38%
```

每个代币都在 CLOB 上独立交易，有独立的订单簿。

### 2.2 订单簿结构（真实 API 响应示例）

Polymarket 的 CLOB API（`clob.polymarket.com/book`）返回如下结构：

```json
{
  "market": "0xabc...123",
  "asset_id": "0xdef...456",
  "bids": [
    { "price": "0.62", "size": "5000" },
    { "price": "0.61", "size": "12000" },
    { "price": "0.60", "size": "8000" }
  ],
  "asks": [
    { "price": "0.65", "size": "3000" },
    { "price": "0.66", "size": "7000" },
    { "price": "0.67", "size": "15000" }
  ],
  "timestamp": "2026-05-25T12:00:00Z",
  "last_trade_price": "0.63"
}
```

### 2.3 交易方向与成本

#### 买入 YES（看多）

你想赌事件会发生，需要**买入 YES Token**：

```
你想买入 $100 的 YES Token

订单簿 Asks（卖方挂单）：
  $0.65 × 3000 shares = $1950 可用
  $0.66 × 7000 shares = $4620 可用

你的 $100 订单：
  - 先吃掉 $0.65 档的 153 shares（$99.45）
  - 还需 $0.55，吃掉 $0.66 档的 0.83 shares（$0.55）

实际成交均价 = $100 / 153.83 = $0.6501
即你以略高于 best_ask 的价格成交
```

#### 买入 NO（看空）

你想赌事件不会发生，需要**买入 NO Token**：

```
NO Token 订单簿：
  Bids: $0.35 × 5000, $0.34 × 8000
  Asks: $0.38 × 3000, $0.39 × 6000

买入 NO 相当于 "看空"，你支付 $0.38/张
隐含 YES 概率 = 1 - 0.38 = 0.62
```

> **注意**：在 Polymarket 上，买 YES 和买 NO 是对称的，但订单簿深度可能完全不同。一个方向的流动性可能很深，另一个方向可能很浅。

### 2.4 Polymarket 的手续费结构

| 费用类型 | 费率 | 说明 |
|---|---|---|
| **Taker Fee** | 2% | 吃单者（市价/限价 crossing）支付 |
| **Maker Fee** | 0% | 挂单者（提供流动性）免费 |
| **Settlement Fee** | 0% | 结算时无额外费用 |
| **Gas Fee** | ~$0.01–0.05 | Polygon 链上转账费用 |

**实际成本示例**：

```
你想买入 YES，best_ask = $0.65

名义成本：$0.65 × 100 shares = $65
Taker Fee：$65 × 2% = $1.30
实际支付：$66.30

如果事件成真，你获得：$100
净利润：$100 - $66.30 = $33.70
实际 ROI：33.70 / 66.30 = 50.8%
```

> **重要**：Polymarket 的 taker fee 不是按名义金额收，而是按 `price × (1 - price)` 计算，即对高确定性事件收费更低。但 scanner 中简化为固定 2% fee rate。

---

## 3. 为什么 CLOB 对 Barrier 策略至关重要

### 3.1 模型概率 vs 市场概率的差距

```
Scanner 计算出的模型概率：      72%
Polymarket CLOB 上的 YES 价格：  62%

直观判断：有 10% 的 edge，应该买入！
```

但等等——**这个价格是 best_ask 还是 last_trade？**

### 3.2 CLOB 上的真实可成交价格

```python
# 缓存价格（Gamma API 提供的）
cached_yes_price = 0.62  # 可能是 last_trade 或 midpoint

# CLOB 上的真实价格
best_ask = 0.65   # 你实际能买到的最低价格
best_bid = 0.60   # 你卖出时能拿到的最高价格
spread = 0.05     # 8.1% 的 spread！

# 你的真实买入成本
executable_price = 0.65      # 如果订单小
executable_price = 0.652     # 如果订单大（吃穿多档）

# 扣除费用后的净 edge
net_edge = model_probability - executable_price - taker_fee - slippage
net_edge = 0.72 - 0.65 - 0.02 - 0.005 = 0.045  # 4.5% 净 edge
```

**如果没有 CLOB 数据**：
- 你会用 cached price $0.62 计算 edge = 10%
- 实际可成交价格 $0.65，真实 edge 只有 4.5%
- **高估 edge 一倍以上！**

### 3.3 订单簿深度决定仓位上限

```
你想下注 $10,000

订单簿 Asks：
  $0.65 × 3000 shares = $1,950
  $0.66 × 7000 shares = $4,620
  $0.67 × 15000 shares = $10,050

你的 $10,000 订单会吃穿：
  - 全部 $0.65 档（$1,950）
  - 全部 $0.66 档（$4,620）
  - $0.67 档的 5,120 shares（$3,430）

实际成交均价 = $10,000 / 15,120 = $0.6614
比 best_ask 贵了 $0.0114（1.75% 额外滑点）

如果订单簿深度只有 $500：
  你的 $10,000 订单会导致 20% 以上的滑点！
  此时即使模型 edge 很大，实际也是亏损交易。
```

### 3.4 订单簿时效性

```python
# CLOB 数据是实时变化的
orderbook_age = 30  # 秒

if orderbook_age > 120:
    # 订单簿超过 2 分钟未更新
    # 价格可能已大幅变动
    flag = "stale_orderbook"
```

在高波动事件中，订单簿可能在**几秒钟内**完全重构。缓存的 CLOB 数据价值随时间指数衰减。

---

## 4. Polymarket CLOB 的技术细节

### 4.1 API 端点

```python
# 获取实时订单簿
GET https://clob.polymarket.com/book?token_id=<YES_TOKEN_ID>

# 获取历史成交
GET https://clob.polymarket.com/trades?token_id=<YES_TOKEN_ID>

# 获取市场元数据
GET https://gamma-api.polymarket.com/markets?limit=100
```

### 4.2 Tick Size（最小价格单位）

Polymarket 的 tick size 是 **$0.01**（1 cent）。这意味着：

- 价格只能是 0.01, 0.02, ..., 0.99, 1.00
- Spread 最小为 $0.01
- 在接近 0 或 1 的极端概率下，相对 spread 会非常大：
  - YES = $0.02, NO = $0.98 → spread = $0.01，但相对 spread = 50%！

### 4.3 最小订单量

- **最小订单**：约 $1（取决于具体市场）
- **整数 shares**：必须整手交易，不能买 0.5 share

### 4.4 链上结算

Polymarket 运行在 **Polygon** 上：

```
交易流程：
1. 用户在 CLOB 上提交订单（off-chain 撮合）
2. 撮合引擎匹配买卖方（off-chain）
3. 成交后，链上转移代币（Polygon，gas ~$0.01）
4. 事件结算时，UMA Oracle 提供结果
5. 获胜方按 $1/share 赎回 USDC
```

**关键**：CLOB 撮合本身是**链下**的（速度和成本优势），但**结算**是**链上**的（去中心化信任）。

---

## 5. CLOB vs AMM：对策略设计的启示

### 5.1 为什么 Polymarket 选择 CLOB

1. **更高的价格效率**：专业做市商竞争压缩 spread，价格更贴近真实概率
2. **更低的长期滑点**：大额交易在深度足够的 CLOB 上比 AMM 便宜
3. **更好的市场操纵抵抗力**：需要同时攻击 bids 和 asks 两侧
4. **更适合机构投资者**：熟悉的交易界面和风控模型

### 5.2 为什么这增加了我们的复杂度

在 AMM 模式下：
```python
# AMM 定价简单直接
market_price = pool_yes / (pool_yes + pool_no)
slippage = calculate_amm_slippage(amount_in, pool_yes, pool_no)  # 公式确定
```

在 CLOB 模式下：
```python
# CLOB 定价复杂多维
best_ask = min(ask["price"] for ask in orderbook["asks"])
best_bid = max(bid["price"] for bid in orderbook["bids"])
executable_price = walk_orderbook(target_notional, orderbook["asks"])
slippage = executable_price - best_ask  # 取决于你的订单大小和深度
spread = best_ask - best_bid  # 市场流动性的即时指标

# 还要考虑：
- orderbook_age: 数据有多新鲜？
- depth_imbalance: 买方深度 vs 卖方深度？
- recent_trades: 最近成交价是否偏离订单簿？
```

### 5.3 Scanner 中的 CLOB 处理逻辑

```python
# 当前 scanner 的 CLOB 处理流程
for market in barrier_markets:
    # 1. 获取模型概率（Monte Carlo）
    model_p = monte_carlo_touch_probability(market)

    # 2. 获取 CLOB 订单簿（如果启用 orderbook=True）
    book = fetch_order_book(market.yes_token_id, timeout=4)

    # 3. 计算可成交价格
    if book["asks"]:
        fill = walk_orderbook(book["asks"], executable_notional=$100)
        executable_price = fill["avg_price"]
        complete_fill = fill["complete_fill"]
    else:
        executable_price = cached_yes_price  # fallback

    # 4. 计算费用和滑点
    taker_fee = 0.02 * executable_price * (1 - executable_price)
    slippage = executable_price - best_ask

    # 5. 净 edge
    net_edge = model_p - executable_price - taker_fee - slippage
```

---

## 6. 常见问题

### Q1: 为什么 CLOB 上的 YES 价格 + NO 价格 ≠ $1？

理论上 `YES + NO = $1` 是无套利约束。但由于：
- CLOB 是离散的（tick size $0.01）
- 两个代币的订单簿深度不同
- 手续费的存在

实际中会有微小偏离（通常 < $0.02），套利者会迅速消除。

### Q2: 我可以同时买 YES 和 NO 套利吗？

如果 `YES_ask + NO_ask < $1`，理论上可以：
- 买入 YES + 买入 NO
- 成本 < $1
- 结算时获得 $1
- 净利润 = $1 - 成本 - 2×fee

但 Polymarket 的 spread 通常不会让这种机会存在，且 taker fee 会吃掉利润。

### Q3: 为什么有些市场没有 CLOB 数据？

- **新市场**：刚创建，尚未有做市商挂单
- **低流动性市场**：交易量 < $1000，做市商不愿参与
- **即将到期**：最后几小时，做市商撤单避险
- **已关闭**：事件已发生，不再交易

### Q4: CLOB 数据延迟多久？

Polymarket CLOB API 的延迟：
- 美国服务器：< 100ms
- 欧洲服务器：200–400ms
- 中国大陆服务器：通常超时或 3–10s（如果可达）

---

## 7. 总结

| 要点 | 结论 |
|---|---|
| **CLOB 是什么** | 中央限价订单簿，买卖双方公开挂单、撮合引擎自动匹配 |
| **Polymarket 为什么用 CLOB** | 更高的价格效率、更低的长期滑点、更适合机构级预测市场 |
| **对策略的影响** | 必须用 **best_ask** 而非 **last_trade** 计算成本；订单大小受限于订单簿深度 |
| **核心风险** | 模型 edge ≠ 实际 edge，CLOB 深度和 spread 可能让"看起来有利可图"的交易变成亏损 |
| **技术要点** | YES/NO 分别交易、tick size $0.01、taker fee 2%、Polygon 链上结算 |

> **一句话记住**：在 CLOB 上，**你看到的价格不是你能成交的价格**。真正的交易发生在订单簿的 "asks" 一侧，且你的订单越大，实际价格越差。
