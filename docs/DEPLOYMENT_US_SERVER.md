# 美国服务器部署指南

> 目标：在美国 VPS 上部署 Polymtrade，解决中国大陆网络环境下 Polymarket / Deribit / Coinbase / OKX 等 API 不可达的问题。  
> 预估成本：$5–12/月  
> 预估部署时间：30–60 分钟

---

## 1. 为什么需要美国服务器

### 1.1 当前网络限制

在中国大陆网络环境下，以下核心数据源**完全不可达**或**严重不稳定**：

| API | 当前状态 | 影响 |
|---|---|---|
| `gamma-api.polymarket.com` | DNS 解析失败 / 连接超时 | **无法获取 barrier 市场列表** |
| `clob.polymarket.com` (CLOB 盘口) | 连接超时 | **无法获取实时 orderbook 定价** |
| `polym.trade` | 间歇性可用 | 搜索 API 时好时坏 |
| `www.deribit.com` | 连接超时 | **无法获取隐含波动率 IV** |
| `api.exchange.coinbase.com` | 连接超时 | 价格 fallback 不可用 |
| `www.okx.com` | Host is down | 价格 fallback 不可用 |
| `api.binance.com` | 被阻断 | 已用 `data-api.binance.vision` 替代 |

**核心矛盾**：Polymarket 本身就是美国预测市场，其 Gamma API 和 CLOB 服务器位于美国（AWS us-east-1）。在中国大陆网络下，这些 API 的连通性完全取决于网络波动，导致 scanner 大部分时间只能依赖本地缓存的过期数据，严重削弱策略有效性。

### 1.2 美国服务器能解决什么

部署到美国（特别是美东，如纽约、弗吉尼亚、新泽西）后：

- ✅ **Polymarket Gamma/CLOB**：同区域低延迟访问（<50ms）
- ✅ **Deribit**：正常访问，获取 BTC/ETH ATM IV
- ✅ **Coinbase**：完全可用，作为 Binance 的 fallback
- ✅ **Binance data-api**：继续可用（公开数据归档，全球无限制）
- ⚠️ **OKX**：可能仍受限（OKX 对美国部分州有合规限制），但影响极小

---

## 2. 服务商选择与对比

### 2.1 推荐方案（按优先级排序）

#### 方案 A：Vultr（最推荐，适合中国用户）

| 项目 | 详情 |
|---|---|
| **价格** | $5/月（1 vCPU / 1GB RAM / 25GB SSD） |
| **地区** | 纽约（New Jersey）、洛杉矶、硅谷 |
| **计费** | 按小时计费，随时销毁，无长期合约 |
| **支付** | ✅ **支持支付宝**、PayPal、信用卡、加密货币 |
| **网络** | 1Gbps 共享带宽，1TB/月流量 |
| **特点** | 一键部署，控制面板极简，适合个人项目 |

**推荐机房**：`New Jersey` 或 `New York`（离 Polymarket 服务器最近）。

**注册地址**：https://www.vultr.com （使用推荐码首次充值 $10 送 $100，但实际到账可能有门槛，建议直接充值 $10）

#### 方案 B：DigitalOcean（开发者友好）

| 项目 | 详情 |
|---|---|
| **价格** | $6/月（1 vCPU / 512MB RAM / 10GB SSD）或 $12/月（1GB RAM） |
| **地区** | 纽约（NYC1/NYC3）、旧金山 |
| **计费** | 按小时计费 |
| **支付** | PayPal、信用卡（**不支持支付宝/微信**） |
| **特点** | 文档极全，社区活跃，有 Managed Database 等扩展 |

**注意**：DigitalOcean 需要信用卡或 PayPal，对没有外币卡的中国用户不太友好。

#### 方案 C：AWS Lightsail（大厂背书，有免费 tier）

| 项目 | 详情 |
|---|---|
| **价格** | $5/月（512MB RAM）/ $10/月（1GB RAM） |
| **免费 tier** | 新用户首年每月 750 小时免费（足够跑 1 台） |
| **地区** | 弗吉尼亚（us-east-1）、俄亥俄 |
| **支付** | 信用卡（**不支持支付宝/微信**） |
| **特点** | 与 AWS 生态无缝集成，适合未来扩展 |

**注意**：AWS 免费 tier 需要绑定信用卡，到期后会自动扣费，务必设置 billing alert。

#### 方案 D：Linode (Akamai)

| 项目 | 详情 |
|---|---|
| **价格** | $5/月（1GB RAM / 1 vCPU / 25GB SSD） |
| **地区** | 纽瓦克（Newark，离 NYC 最近） |
| **支付** | ✅ **支持支付宝**、PayPal、信用卡 |
| **特点** | 老牌厂商，网络质量稳定 |

---

### 2.2 方案决策树

```
有支付宝，不想绑信用卡？
  └─ 是 → Vultr（$5/月，New Jersey）
  └─ 否 →
       有 PayPal / 双币信用卡？
         └─ 是 → DigitalOcean（$6/月，NYC）
         └─ 否 →
              想免费试用一年？
                └─ 是 → AWS Lightsail（需信用卡，首年免费）
                └─ 否 → 找朋友代付 / 购买虚拟信用卡
```

---

## 3. 详细部署步骤（以 Vultr + Ubuntu 22.04 为例）

### 3.1 购买服务器

1. 访问 https://my.vultr.com/，注册账号
2. 点击 **Deploy** → **Deploy New Server**
3. 选择 **Cloud Compute**（Shared CPU）
4. 选择 **Location**：`New Jersey` 或 `New York`
5. 选择 **Server Image**：`Ubuntu 22.04 LTS x64`
6. 选择 **Plan**：`Cloud Compute - Regular`，选 `$5/月` 或 `$6/月`（1GB RAM 更稳妥）
7. **Auto Backups**：建议关闭（节省 $1/月）
8. **SSH Keys**：点击 `Add New` 上传你的公钥（`~/.ssh/id_rsa.pub`）
   ```bash
   # 在本地终端生成 SSH 密钥（如果没有）
   ssh-keygen -t ed25519 -C "your_email@example.com"
   cat ~/.ssh/id_ed25519.pub
   ```
9. **Server Hostname & Label**：`polymtrade-us`
10. 点击 **Deploy Now**
11. 等待 2–3 分钟，服务器状态变为 `Running`，记下 **IP Address**

### 3.2 连接服务器

```bash
ssh root@<你的服务器IP>
```

首次连接会提示确认指纹，输入 `yes`。

### 3.3 系统初始化

```bash
# 更新系统
apt update && apt upgrade -y

# 安装必要工具
apt install -y git python3 python3-pip python3-venv sqlite3 curl htop tmux

# 创建项目用户（不要用 root 跑服务）
useradd -m -s /bin/bash polymtrade
usermod -aG sudo polymtrade

# 切换到项目用户
su - polymtrade
```

### 3.4 部署项目

```bash
# 克隆仓库（假设你已有 GitHub 仓库）
cd ~
git clone https://github.com/alex22222/polymarket.git
cd polymarket

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖（项目目前没有 requirements.txt，需手动安装）
pip install --upgrade pip
pip install requests urllib3

# 验证 Python 版本
python3 --version  # 应 >= 3.10
```

> **注意**：如果项目后续添加了 `requirements.txt`，改为 `pip install -r requirements.txt`。

### 3.5 数据迁移（从本地到服务器）

如果你希望保留本地已有的历史数据（BTC/ETH 3203 天 K 线、已有市场记录等），将本地 SQLite 数据库上传到服务器：

**在本地终端执行**：

```bash
# 压缩数据库
scp polymtrade.sqlite root@<你的服务器IP>:/home/polymtrade/polymarket/

# 或者使用 rsync（支持断点续传）
rsync -avz --progress polymtrade.sqlite root@<你的服务器IP>:/home/polymtrade/polymarket/
```

**在服务器上执行**：

```bash
chown polymtrade:polymtrade /home/polymtrade/polymarket/polymtrade.sqlite
```

如果不迁移数据，服务器上首次运行时会自动创建空数据库，需要重新抓取历史数据（Binance data-api 约 10–20 分钟即可完成）。

### 3.6 验证 API 连通性

```bash
cd ~/polymarket
source .venv/bin/activate

# 验证 Polymarket Gamma
python3 -c "
from polymtrade.data.polymarket_api import fetch_gamma_markets
try:
    r = fetch_gamma_markets(limit=5, timeout=5)
    print(f'✅ Gamma OK: {len(r)} markets')
except Exception as e:
    print(f'❌ Gamma FAIL: {e}')
"

# 验证 Deribit IV
python3 -c "
from polymtrade.data.derivatives import fetch_deribit_option_summaries
try:
    r = fetch_deribit_option_summaries('BTC', timeout=5)
    print(f'✅ Deribit OK: {len(r)} summaries')
except Exception as e:
    print(f'❌ Deribit FAIL: {e}')
"

# 验证 Coinbase
python3 -c "
from polymtrade.data.crypto_prices import fetch_coinbase_daily
try:
    r = fetch_coinbase_daily('BTC', limit=3)
    print(f'✅ Coinbase OK: {len(r)} candles')
except Exception as e:
    print(f'❌ Coinbase FAIL: {e}')
"

# 验证 OKX
python3 -c "
from polymtrade.data.crypto_prices import fetch_okx_daily
try:
    r = fetch_okx_daily('BTC', limit=3)
    print(f'✅ OKX OK: {len(r)} candles')
except Exception as e:
    print(f'❌ OKX FAIL: {e}')
"
```

**预期输出**（美国服务器）：

```
✅ Gamma OK: 5 markets
✅ Deribit OK: 12 summaries
✅ Coinbase OK: 3 candles
❌ OKX FAIL: <urlopen error ...>  # OKX 在美国部分州仍受限，可忽略
```

### 3.7 启动 Web 服务

```bash
cd ~/polymarket
source .venv/bin/activate

# 前台测试启动
python3 -m polymtrade.app
```

如果启动成功，你会看到：

```
Polymtrade dashboard: http://127.0.0.1:8765
```

但此时服务只监听 `127.0.0.1`，无法从外部访问。需要修改配置或使用 SSH 隧道。

#### 方案 1：SSH 隧道（快速测试，无需改配置）

在**本地终端**执行：

```bash
ssh -N -L 8765:127.0.0.1:8765 root@<你的服务器IP>
```

然后在本机浏览器访问 `http://localhost:8765`。

#### 方案 2：绑定公网 IP（正式使用）

修改 `polymtrade/app.py` 中的服务器绑定地址：

```python
# 原代码
server = ThreadingHTTPServer(("127.0.0.1", 8765), AppHandler)

# 改为监听所有接口（或指定公网 IP）
server = ThreadingHTTPServer(("0.0.0.0", 8765), AppHandler)
```

然后重启服务，即可通过 `http://<服务器IP>:8765` 访问。

> **安全提醒**：`0.0.0.0` 会暴露到公网，建议配合防火墙（UFW）限制访问 IP：
> ```bash
> sudo ufw allow from <你的本地IP> to any port 8765
> sudo ufw enable
> ```

---

## 4. 持续运行与自动化

### 4.1 使用 systemd 管理后台服务

创建 systemd 服务文件：

```bash
sudo tee /etc/systemd/system/polymtrade.service << 'EOF'
[Unit]
Description=Polymtrade Research Dashboard
After=network.target

[Service]
Type=simple
User=polymtrade
WorkingDirectory=/home/polymtrade/polymarket
Environment=PYTHONPATH=/home/polymtrade/polymarket
ExecStart=/home/polymtrade/polymarket/.venv/bin/python3 -m polymtrade.app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable polymtrade
sudo systemctl start polymtrade

# 查看状态
sudo systemctl status polymtrade
# 查看日志
sudo journalctl -u polymtrade -f
```

### 4.2 配置自动化任务（cron）

```bash
# 编辑 crontab
crontab -e
```

添加以下内容（每 6 小时自动刷新数据并保存观测）：

```cron
# 每 6 小时运行一次自动化任务
0 */6 * * * cd /home/polymtrade/polymarket && /home/polymtrade/polymarket/.venv/bin/python3 -m polymtrade.research.automation_job --days 10 --save-observation >> /home/polymtrade/polymarket/automation.log 2>&1

# 每日凌晨清理 7 天前的日志
0 3 * * * cd /home/polymtrade/polymarket && sqlite3 polymtrade.sqlite "DELETE FROM system_logs WHERE created_at < datetime('now', '-7 days');"
```

### 4.3 使用 tmux 保持会话（临时方案）

如果你不想用 systemd，可以用 tmux：

```bash
ssh root@<你的服务器IP>
su - polymtrade
tmux new -s polymtrade
cd ~/polymarket && source .venv/bin/activate && python3 -m polymtrade.app

# 按 Ctrl+B，然后按 D 分离会话
# 之后随时重新连接：
# tmux attach -t polymtrade
```

---

## 5. 性能监控与维护

### 5.1 基础监控脚本

```bash
# 创建监控脚本
cat > /home/polymtrade/polymarket/monitor.sh << 'EOF'
#!/bin/bash
# 检查服务是否运行
if ! pgrep -f "polymtrade.app" > /dev/null; then
    echo "$(date): Polymtrade not running, restarting..." >> /home/polymtrade/polymarket/monitor.log
    cd /home/polymtrade/polymarket && /home/polymtrade/polymarket/.venv/bin/python3 -m polymtrade.app >> /home/polymtrade/polymarket/server.log 2>&1 &
fi

# 检查磁盘空间
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "$(date): Disk usage ${DISK_USAGE}%, cleaning old logs..." >> /home/polymtrade/polymarket/monitor.log
    find /home/polymtrade/polymarket -name "*.log" -mtime +7 -delete
fi
EOF
chmod +x /home/polymtrade/polymarket/monitor.sh

# 每 5 分钟检查一次
crontab -l | { cat; echo "*/5 * * * * /home/polymtrade/polymarket/monitor.sh"; } | crontab -
```

### 5.2 数据库备份

```bash
# 每日备份 SQLite 到 /backup 目录
mkdir -p /home/polymtrade/backup
crontab -l | { cat; echo "0 2 * * * cp /home/polymtrade/polymarket/polymtrade.sqlite /home/polymtrade/backup/polymtrade_$(date +\%Y\%m\%d).sqlite && find /home/polymtrade/backup -name '*.sqlite' -mtime +14 -delete"; } | crontab -
```

---

## 6. 成本估算

| 项目 | Vultr $5/月 | Vultr $6/月 | DigitalOcean $6/月 | AWS Lightsail $5/月 |
|---|---|---|---|---|
| **vCPU** | 1 | 1 | 1 | 1 |
| **RAM** | 768MB | 1GB | 512MB | 512MB |
| **SSD** | 25GB | 25GB | 10GB | 20GB |
| **流量** | 1TB | 1TB | 500GB | 1TB |
| **适合** | 最小可行 | **推荐** | 开发测试 | 免费 tier |
| **年付** | $60 | $72 | $72 | $60（首年可能免费） |

**额外成本**：
- 域名（可选）：$10–15/年
- 备份存储（可选）：$1–2/月

---

## 7. 常见问题排查

### Q1: SSH 连接被拒绝
```bash
# 检查防火墙
sudo ufw status
# 如果启用了 UFW 但没允许 SSH
sudo ufw allow ssh
```

### Q2: Python 版本过低（< 3.10）
```bash
# Ubuntu 22.04 自带 Python 3.10，如果用的是 20.04
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv
python3.12 -m venv .venv
```

### Q3: 服务启动后无法从外部访问
```bash
# 检查是否绑定到 0.0.0.0
netstat -tlnp | grep 8765
# 应显示 0.0.0.0:8765 而不是 127.0.0.1:8765

# 检查 Vultr 防火墙（控制面板中）
# 确保入站规则允许 8765 端口
```

### Q4: SQLite 数据库越来越大
```bash
# SQLite 不会自动释放空间，需要 VACUUM
sqlite3 polymtrade.sqlite "VACUUM;"
```

### Q5: OKX 在美国服务器上仍不可用
这是预期行为，OKX 对美国 IP 做了限制。**无需修复**，Binance + Coinbase + Deribit 已足够。

---

## 8. 安全加固（生产环境建议）

```bash
# 1. 禁用 root SSH 登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 2. 启用自动安全更新
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# 3. 安装 fail2ban（防暴力破解）
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 4. 限制 dashboard 访问（仅允许你的 IP）
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow from <你的本地公网IP> to any port 8765
sudo ufw enable
```

---

## 9. 下一步

部署完成后，你将获得：

1. ✅ **实时 Polymarket 市场数据**（barrier 列表、到期日、流动性）
2. ✅ **实时 CLOB 盘口定价**（可成交价格、spread、 executable notional）
3. ✅ **Deribit ATM IV**（替代历史波动率，提升模型准确度）
4. ✅ **Coinbase fallback**（价格冗余）
5. ✅ **自动化数据刷新**（cron 每 6 小时运行）
6. ✅ **walk-forward 观测记录**（保存到 SQLite，用于策略回测验证）

**建议优先验证**：

```bash
# 1. 运行 scanner 验证所有 API
python3 -m polymtrade.research.automation_job --days 10 --save-observation

# 2. 检查 dashboard
# 在本地浏览器打开 http://<服务器IP>:8765
# 确认 analysis 标签页中所有数据源状态为 正常/网络受限（无红色 失败）
```

---

*文档版本：v1.0  
最后更新：2026-05-25*
