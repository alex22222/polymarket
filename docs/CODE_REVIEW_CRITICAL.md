# Polymtrade 项目代码审查：致命错误与系统性缺陷

> 审查日期：2026-05-25
> 审查范围：全栈代码（后端 / 数据层 / 定价模型 / 前端）
> 审查态度：**不留情面，只找问题**

---

## 0. 总评：一句话

> **这是一套"能跑起来"的科研原型，不是一套"能赚钱"的交易系统。** 致命逻辑错误分布在定价模型、回测框架、数据管道三个核心环节，任何一个都足以让实盘策略在不知情的情况下稳定亏损。

---

## 1. 定价模型：致命的数学错误

### 1.1 Monte Carlo 每天只检查 4 次价格 —— 严重低估触及概率

**文件**：`superpowers/barrier.py:60-93`

```python
steps_per_day = 4
steps = max(1, int(item.days_to_expiry * steps_per_day))
```

**问题**：模型假设价格在 4 个离散时间点检查 barrier，但真实 GBM 是连续路径。一个市场在上午 10:00 触及 barrier 后反弹，你的模型因为只在 00:00、06:00、12:00、18:00 检查，**完全错过了这个触及事件**。

**影响**：对于 14 天到期的市场，你只有 56 次检查。学术界对离散监控 barrier 的标准修正（continuity correction）是 `P_discrete ≈ P_continuous × exp(-β×σ×√(Δt))`，你的代码完全没有这个修正。

**后果**：模型概率被系统性低估，导致大量本应识别为"高概率触及"的机会被错误过滤掉。**你错过的是真正的 alpha。**

---

### 1.2 确定性种子 = 零模拟方差 —— "Monte Carlo" 名不副实

**文件**：`superpowers/barrier.py:74` 及 `scanner.py:726`

```python
seed = stable_seed(market["market_id"], context["spot"], ...)
rng = random.Random(seed)
```

**问题**：只要市场参数不变，每次运行产生**完全相同的随机序列**。这意味着：
- 你无法估计模拟误差（standard error）
- 你无法判断 1500 次模拟是否足够
- 对于 p≈0.5 的市场，1500 次模拟的标准误差约为 ±1.3%。如果你的 edge threshold 是 2%，这个误差**吞噬了 half 你的信号**

**正确做法**：每次运行用不同种子，跑多次模拟，报告均值 ± 标准误差。如果误差 > edge 的 50%，增加模拟次数或换用闭式解。

---

### 1.3 费用公式可能是错的

**文件**：`superpowers/barrier.py:96-106`

```python
taker_fee = fee_rate * ask_price * (1.0 - ask_price)
```

**问题**：这个公式把费用写成 `ask × (1-ask)`，在 ask=0.5 时费用最大，ask→1 时费用→0。这与直觉相反——为什么越确定的事件手续费越低？

Polymarket 的实际费用结构是：
- Taker fee = 2% of trade value（固定比例）

**如果你的费用模型是错的，所有 edge 计算都是错的。**

---

### 1.4 已触及市场被错误封顶

**文件**：`scanner.py:695-699`

```python
if already_touched:
    model_probability = min(touched / simulations, 0.995)
```

**问题**：当现货价已经触及 barrier 时，真实概率应该是 1.0（或非常接近），但代码硬编码封顶到 0.995。然后如果市场价格是 0.99，模型只报告 0.5% edge。**你低估了已触及市场的真实价值。**

---

## 2. 回测框架：用未来数据欺骗自己

### 2.1 Lookahead Bias：回测包含观察时刻之前的数据

**文件**：`research/paper.py:48-72`

```python
def _candles_after_observation(conn, market_id, observed_at, asset):
    start_key = observed_at.date().isoformat()
    # 查询从 start_key 开始的所有日线数据
```

**问题**：如果观察在 14:30 做出，start_key 是当天的日期（00:00）。**回测会包含当天 00:00–14:30 的数据**——也就是观察时刻之前的"未来信息"。

**后果**：一个在上午 10:00 已经触及 barrier 的市场，下午 14:30 的观察会把它标记为"已触及"。你的回测胜率被人为夸大，实盘时全部失效。

**这是量化回测中最致命的错误之一。**

---

### 2.2 current_only=False 重复计数，人为放大样本量

**文件**：`research/paper.py:462-476`

```python
if market_id and market_id in seen_markets:
    reasons.append("duplicate market; newer observation kept")
if reasons and current_only:
    excluded.append(...)
    continue
selected.append(row)  # 重复行仍然被加入！
```

**问题**：当 `current_only=False` 时，同一个市场的多条观察记录会被**同时纳入**，导致：
- 胜率被人为拉高（同一个赢/输被重复计算）
- P&L 被人为放大
- 校准曲线完全失真

**你的回测结果不可信。**

---

### 2.3 校准归因报告平均 edge 计算错误

**文件**：`research/paper.py:683-686, 759`

```python
if model_p is not None and market_p is not None:
    edge_sum += model_p - market_p
# ...
"avg_model_minus_market": edge_sum / len(rows)
```

**问题**：`edge_sum` 只对有有效数据的行累加，但分母是 **所有行数**。如果 500 行中只有 100 行有有效数据，平均值被除以 500，**真实平均 edge 被低估 5 倍**。

---

## 3. Scanner：方向解析错误会翻转策略

### 3.1 Naive 子串匹配可能翻转方向

**文件**：`research/scanner.py:369-380`

```python
def normalized_direction(question):
    if "dip" in question or "below" in question:
        return "hit_below"
    return "hit_above"
```

**问题**：一个市场叫 "Will BTC dip below $40k before reaching $50k?"，代码匹配到 "dip" 就返回 `hit_below`。但市场的实际结算条件可能是"先触及 $50k"（hit_above）。

**后果**：方向翻转 → 模型计算的是"下破概率"，但市场在赌"上破" → 你的 edge 是**反向的**。你以为有 +10% edge，实际是 -10%。

---

### 3.2 Orderbook 启用时任意阻塞非 Top N 候选

**文件**：`research/scanner.py:782-790, 818-829`

```python
# 第一次调用（orderbook_enabled=False）
add_review(row, ..., orderbook_enabled=False, ...)

# 第二次调用（orderbook_enabled=True），对 ALL rows
add_review(row, ..., orderbook_enabled=True, ...)
```

**问题**：当 `orderbook=True` 时，scanner 只对前 `book_limit` 行获取 orderbook，但**对所有行调用 review**。不在 book_limit 内的行被强制标记为 `pricing_source="cached-orderbook-not-sampled"`，然后在 review 中被 `check("book", "fail")` **自动阻断**。

**后果**：一个模型 edge = 15%、流动性充足的市场，仅仅因为它不在前 8 个排序里，就被强制降级为"avoid"。**你主动过滤掉了最好的机会。**

---

## 4. 数据管道：API 处理漏洞百出

### 4.1 SSL 证书验证无条件绕过 —— MITM 攻击面

**文件**：`data/crypto_prices.py:62-66`

```python
except (TimeoutError, urllib.error.URLError) as exc:
    if "CERTIFICATE_VERIFY_FAILED" in str(exc):
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, ..., context=context) as resp:
            return json.loads(resp.read().decode("utf-8"))
```

**问题**：任何人可以通过中间人攻击触发这个路径，然后拦截你的金融数据。**你在交易系统中内置了一个"关闭 SSL"的开关。**

---

### 4.2 _get_json 证书重试异常泄漏

**文件**：`data/crypto_prices.py:62-66`

**问题**：如果 SSL 绕过后的请求再次失败（超时、连接错误），异常**直接抛出**，外层 `for` 循环没有机会重试。**retries=1 形同虚设。**

---

### 4.3 derivatives.py 无法解析单日期权

**文件**：`data/derivatives.py:62-81`

```python
day = int(expiry_text[:2])
```

**问题**：Deribit 的单日期权格式是 `BTC-3JAN25`，`expiry_text[:2]` = `"3J"`，`int("3J")` 抛出 `ValueError`。**所有单日、单数月期权被系统性排除**，导致 IV 选择偏向月中到期，与 barrier 到期日不匹配。

---

### 4.4 _normalized_iv 摧毁合法高 IV 数据

**文件**：`data/derivatives.py:94-103`

```python
if vol > 3.0:
    vol /= 100.0
return max(0.05, min(2.5, vol))
```

**问题**：
- IV = 500%（vol = 5.0）→ 先除以 100 得 0.05 → 再 clamp 到 0.05。**500% IV 被压到 5%**
- IV = 3%（vol = 0.03）→ clamp 到 0.05。**3% IV 被抬到 5%**

**你在扭曲波动率输入。**

---

### 4.5 select_atm_iv 为每个市场重复计算

**文件**：`research/scanner.py:701-708`

```python
for market in markets:
    iv_quote = select_atm_iv(asset, iv_surfaces[asset], spot, days_to_expiry)
```

**问题**：IV surface 对每个资产是相同的，但 `select_atm_iv` 对每个市场都重新遍历整个 surface 选最优。**应该每个资产只计算一次。**

---

## 5. 后端：开发服务器直接上生产

### 5.1 ThreadingHTTPServer + SimpleHTTPRequestHandler 是玩具

**文件**：`app.py`

**问题**：
- 没有请求体大小限制 → 可被 DoS（发送 Content-Length: 10GB）
- 没有请求超时 → 慢客户端可占满线程池
- 没有限流 → 任何人可疯狂触发 scanner 做 CPU DoS
- 没有认证 → 任何人可清空日志、触发报告、保存观测
- `super().do_GET()` 可暴露 WEB_ROOT 下任意文件

**你在用 Python 标准库的开发演示服务器跑一个金融交易系统。**

---

### 5.2 Scanner 同步阻塞 HTTP 线程

**文件**：`app.py:339-368`

```python
if path == "/api/scanner":
    result = scan_opportunities(...)
```

**问题**：一次 scanner 运行可能 10–60 秒。`ThreadingHTTPServer` 会开新线程，但线程数无上限。并发请求会导致系统资源耗尽。**这是一个单点故障。**

---

### 5.3 每个请求都执行完整 schema

**文件**：`storage/db.py:178-183`

```python
def connect(path):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    ensure_schema(conn)
    return conn
```

**问题**：每次 HTTP 请求都重新解析并执行整个 SCHEMA 字符串。对于一个繁忙的 web 服务器，这是**巨大的磁盘 I/O 浪费**。

---

### 5.4 SQLite 没有 WAL 模式和 busy timeout

**文件**：`storage/db.py`

**问题**：默认 `journal_mode=DELETE`，`busy_timeout=0`。并发写入立即报错 `database is locked`。**ThreadingHTTPServer 多线程 + SQLite 默认配置 = 生产事故。**

---

## 6. 前端：XSS 和严重的可访问性问题

### 6.1 externalLink 不验证 URL scheme —— XSS 漏洞

**文件**：`web/app.js:898-902`

```javascript
function externalLink(url, text) {
  return `<a href="${url}" target="_blank" rel="noopener">${text}</a>`;
}
```

**问题**：`url` 来自 API 数据，如果后端返回 `javascript:alert(document.cookie)`，用户点击即执行。**一个被攻破的后端（或中间人）可以通过这个路径窃取用户凭证。**

---

### 6.2 CSS order 属性反转 DOM 顺序 —— 屏幕阅读器完全错乱

**文件**：`web/styles.css:43-90`

```css
.validation-section > *:nth-child(1) { order: 15; }
.validation-section > *:nth-child(2) { order: 14; }
/* ... 完全反转 */
```

**问题**：视觉顺序和 DOM 顺序完全相反。屏幕阅读器按 DOM 顺序朗读，键盘 Tab 导航也按 DOM 顺序。**这违反了 WCAG 1.3.2 和 2.4.3，是一个严重的可访问性缺陷。**

---

## 7. 自动化任务：Binance 被错误标记为降级

### 7.1 binance_spot_errors 逻辑反转

**文件**：`research/automation_job.py:230-245`

```python
binance_spot_errors = [
    f"{asset}: ..."
    for asset, context in contexts.items()
    if context.get("spot_errors") and not str(context.get("source") or "").startswith("binance")
]
```

**问题**：这个变量收集的是**非 Binance 来源**的 spot 错误（即 OKX 错误），但变量名叫 `binance_spot_errors`。然后：

```python
if binance_spot_assets:
    status = "healthy" if not binance_spot_errors else "degraded"
```

**Binance 成功了，但 OKX 失败了 → Binance 被标记为"降级"。** 你的监控仪表板在撒谎。

---

## 8. 系统性缺陷清单

### 8.1 没有测试覆盖

整个项目**零单元测试**。没有：
- barrier 模型的单元测试（验证闭式解 vs Monte Carlo）
- 数据管道测试（模拟 API 响应）
- 回测逻辑测试（验证无 lookahead bias）
- 前端组件测试

### 8.2 没有缓存层

`data_quality_report`、`candle_summary`、`market_state` 每次请求都重新计算。对于一个 dashboard 来说，这些应该是**秒级缓存**的。

### 8.3 没有断路器

外部 API（Deribit、Polymarket、Binance）失败时没有退避、没有熔断。自动化任务中 `retries=0` 意味着任何瞬断都会导致源级失败。

### 8.4 没有 schema 版本管理

`db.py` 的 schema 是一个大字符串，没有版本表。无法知道当前数据库是什么版本，无法做复杂迁移。

### 8.5 混合语言

错误消息、UI 标签、review 状态都是中文，代码和注释是英文。这对非中文维护者是巨大的障碍。

---

## 9. 优先级修复路线图

### P0（立即修复，否则策略不可信）

| # | 问题 | 文件 | 修复工作量 |
|---|---|---|---|
| 1 | 回测 lookahead bias | `paper.py` | 2 小时 |
| 2 | current_only=False 重复计数 | `paper.py` | 1 小时 |
| 3 | 校准归因平均 edge 计算错误 | `paper.py` | 30 分钟 |
| 4 | 方向解析子串匹配 | `scanner.py` | 2 小时 |
| 5 | Orderbook review 对非 Top N 错误阻塞 | `scanner.py` | 3 小时 |
| 6 | Monte Carlo 离散步骤修正 | `barrier.py` | 4 小时 |
| 7 | 费用公式验证 | `barrier.py` | 2 小时 |

### P1（本周修复，影响数据质量）

| # | 问题 | 文件 | 修复工作量 |
|---|---|---|---|
| 8 | SSL 验证绕过 | `crypto_prices.py` | 1 小时 |
| 9 | _get_json 异常泄漏 | `crypto_prices.py` | 1 小时 |
| 10 | _normalized_iv 摧毁高 IV | `derivatives.py` | 1 小时 |
| 11 | 单日期权解析失败 | `derivatives.py` | 1 小时 |
| 12 | SQLite WAL + busy timeout | `db.py` | 30 分钟 |
| 13 | 每次请求执行 schema | `db.py` | 1 小时 |

### P2（本月修复，影响工程可靠性）

| # | 问题 | 文件 | 修复工作量 |
|---|---|---|---|
| 14 | 后端换生产级服务器 | `app.py` | 1 天 |
| 15 | Scanner 异步化或队列化 | `app.py` | 2 天 |
| 16 | XSS URL scheme 验证 | `app.js` | 30 分钟 |
| 17 | CSS order 反转修复 | `styles.css` | 2 小时 |
| 18 | binance_spot_errors 逻辑修复 | `automation_job.py` | 30 分钟 |
| 19 | 添加单元测试框架 | 全局 | 2 天 |

---

## 10. 结论：该继续吗？

**当前状态下，这套代码不能直接上实盘。** 至少 7 个 P0 级错误会让回测结果和策略信号完全失真。

**但是**：
- 这些错误大多是**可修复的编码问题**，不是策略本身的根本缺陷
- 基础设施（数据采集、前端、自动化）已经搭好，修复成本可控
- 如果修复 P0 + P1 后，8 周 walk-forward 验证仍然有效，策略值得继续

**我的建议**：
1. **先修复 P0 错误**（2 周工作量）
2. **部署美国服务器**（已部署）
3. **跑 8 周 walk-forward**
4. 用修复后的代码和数据做最终判决

**不要在没有修复 P0 错误的情况下做任何资金决策。** 你现在的回测结果不可信，scanner 信号不可靠，费用计算可能错误。

---

*审查人：Polymtrade Research（自我审查）*
*审查方法：静态代码分析 + 逻辑推演 + 学术标准对比*
