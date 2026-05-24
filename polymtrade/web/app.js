const els = {
  runBtn: document.getElementById("runBtn"),
  refreshBtn: document.getElementById("refreshBtn"),
  statusText: document.getElementById("statusText"),
  totalReturn: document.getElementById("totalReturn"),
  tradeCount: document.getElementById("tradeCount"),
  winRate: document.getElementById("winRate"),
  maxDrawdown: document.getElementById("maxDrawdown"),
  profitFactor: document.getElementById("profitFactor"),
  tradeRows: document.getElementById("tradeRows"),
  lastRun: document.getElementById("lastRun"),
  equityChart: document.getElementById("equityChart"),
  priceChart: document.getElementById("priceChart"),
  seedDemoBtn: document.getElementById("seedDemoBtn"),
  fetchPricesBtn: document.getElementById("fetchPricesBtn"),
  fetchMarketsBtn: document.getElementById("fetchMarketsBtn"),
  coverageRows: document.getElementById("coverageRows"),
};

let lastEquity = [10000];
let selectedAsset = "BTC";
let lastPrices = [];

function percent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `${(Number(value) * 100).toFixed(2)}%`;
}

function money(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function signedMoney(value) {
  const cls = Number(value) >= 0 ? "positive" : "negative";
  return `<span class="${cls}">${money(value)}</span>`;
}

function drawEquity(values) {
  const canvas = els.equityChart;
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.max(600, Math.floor(rect.width * dpr));
  canvas.height = Math.max(260, Math.floor(rect.height * dpr));
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const width = canvas.width / dpr;
  const height = canvas.height / dpr;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#fbfcfa";
  ctx.fillRect(0, 0, width, height);

  const pad = 34;
  const min = Math.min(...values) * 0.995;
  const max = Math.max(...values) * 1.005;
  const range = Math.max(1, max - min);

  ctx.strokeStyle = "#dce2de";
  ctx.lineWidth = 1;
  for (let i = 0; i < 5; i += 1) {
    const y = pad + ((height - pad * 2) * i) / 4;
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(width - pad, y);
    ctx.stroke();
  }

  const xFor = (index) => pad + ((width - pad * 2) * index) / Math.max(1, values.length - 1);
  const yFor = (value) => height - pad - ((height - pad * 2) * (value - min)) / range;

  ctx.strokeStyle = "#2757a7";
  ctx.lineWidth = 3;
  ctx.beginPath();
  values.forEach((value, index) => {
    const x = xFor(index);
    const y = yFor(value);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = "#17201c";
  ctx.font = "12px system-ui";
  ctx.fillText(money(values[0]), pad, height - 10);
  ctx.fillText(money(values[values.length - 1]), width - pad - 78, yFor(values[values.length - 1]) - 10);
}

function drawPriceChart(candles) {
  const canvas = els.priceChart;
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.max(600, Math.floor(rect.width * dpr));
  canvas.height = Math.max(250, Math.floor(rect.height * dpr));
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const width = canvas.width / dpr;
  const height = canvas.height / dpr;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#fbfcfa";
  ctx.fillRect(0, 0, width, height);

  const pad = 34;
  const values = candles.map((item) => Number(item.close)).filter((item) => Number.isFinite(item));
  if (!values.length) {
    ctx.fillStyle = "#65736d";
    ctx.font = "14px system-ui";
    ctx.fillText("暂无价格数据", pad, height / 2);
    return;
  }
  const min = Math.min(...values) * 0.98;
  const max = Math.max(...values) * 1.02;
  const range = Math.max(1, max - min);

  ctx.strokeStyle = "#dce2de";
  ctx.lineWidth = 1;
  for (let i = 0; i < 4; i += 1) {
    const y = pad + ((height - pad * 2) * i) / 3;
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(width - pad, y);
    ctx.stroke();
  }

  const xFor = (index) => pad + ((width - pad * 2) * index) / Math.max(1, values.length - 1);
  const yFor = (value) => height - pad - ((height - pad * 2) * (value - min)) / range;
  ctx.strokeStyle = selectedAsset === "BTC" ? "#b7791f" : "#2757a7";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  values.forEach((value, index) => {
    const x = xFor(index);
    const y = yFor(value);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = "#17201c";
  ctx.font = "12px system-ui";
  ctx.fillText(`${selectedAsset} ${money(values[values.length - 1])}`, pad, pad - 10);
  ctx.fillStyle = "#65736d";
  ctx.fillText(`${values.length} daily candles`, width - pad - 112, height - 10);
}

function renderCoverage(candleRows, marketRows = [], priceHistoryRows = []) {
  if (!candleRows.length && !marketRows.length && !priceHistoryRows.length) {
    els.coverageRows.innerHTML = `<div class="coverage-row"><strong>暂无数据</strong><span>先导入 Demo 价格，或尝试抓取真实价格。</span></div>`;
    return;
  }
  const candles = candleRows
    .map(
      (row) => `
        <div class="coverage-row">
          <strong><span>${row.asset} / ${row.source}</span><span>${row.candles} 根</span></strong>
          <span>${new Date(row.first_ts).toLocaleDateString()} 至 ${new Date(row.last_ts).toLocaleDateString()}</span>
          <span>latest close ${money(row.latest_close)} · ${row.interval}</span>
        </div>
      `,
    )
    .join("");
  const markets = marketRows
    .map(
      (row) => `
        <div class="coverage-row">
          <strong><span>${row.asset} markets</span><span>${row.markets} 个</span></strong>
          <span>${row.direction} · ${row.source}</span>
          <span>用于后续真实 barrier 回测样本池</span>
        </div>
      `,
    )
    .join("");
  const history = priceHistoryRows
    .map(
      (row) => `
        <div class="coverage-row">
          <strong><span>${row.outcome} price history</span><span>${row.prices} 点</span></strong>
          <span>${row.source}</span>
          <span>${new Date(row.first_ts * 1000).toLocaleDateString()} 至 ${new Date(row.last_ts * 1000).toLocaleDateString()}</span>
        </div>
      `,
    )
    .join("");
  els.coverageRows.innerHTML = candles + markets + history;
}

function renderRun(run, trades) {
  if (!run) {
    drawEquity(lastEquity);
    return;
  }
  els.totalReturn.textContent = percent(run.total_return);
  els.tradeCount.textContent = run.trades ?? "--";
  els.winRate.textContent = percent(run.win_rate);
  els.maxDrawdown.textContent = percent(run.max_drawdown);
  els.profitFactor.textContent = Number(run.profit_factor || 0).toFixed(2);
  els.lastRun.textContent = new Date(run.created_at).toLocaleString();
  if (run.equity_curve) lastEquity = run.equity_curve;
  else if (run.starting_capital && run.ending_capital) lastEquity = [run.starting_capital, run.ending_capital];
  drawEquity(lastEquity);

  els.tradeRows.innerHTML = trades
    .slice(0, 30)
    .map(
      (trade) => `
        <tr>
          <td>${trade.asset}</td>
          <td class="question">${trade.question}</td>
          <td>${Number(trade.market_ask).toFixed(3)}</td>
          <td>${percent(trade.model_probability)}</td>
          <td>${percent(trade.net_edge)}</td>
          <td>${percent(trade.roi)}</td>
          <td>${money(trade.stake)}</td>
          <td>${signedMoney(trade.pnl)}</td>
        </tr>
      `,
    )
    .join("");
}

async function loadDataSummary() {
  const response = await fetch("/api/data-summary");
  const data = await response.json();
  renderCoverage(data.candles || [], data.markets || [], data.priceHistory || []);
}

async function loadCandles() {
  const response = await fetch(`/api/candles?asset=${selectedAsset}&limit=365`);
  const data = await response.json();
  lastPrices = data.candles || [];
  drawPriceChart(lastPrices);
}

async function seedDemoPrices() {
  els.seedDemoBtn.disabled = true;
  els.statusText.textContent = "正在导入 demo 价格";
  try {
    const response = await fetch("/api/seed-demo-prices");
    const data = await response.json();
    await loadDataSummary();
    await loadCandles();
    els.statusText.textContent = `已导入 ${data.candles} 根 demo K 线`;
  } finally {
    els.seedDemoBtn.disabled = false;
  }
}

async function fetchRealPrices() {
  els.fetchPricesBtn.disabled = true;
  els.statusText.textContent = "正在抓取真实价格";
  try {
    const response = await fetch("/api/fetch-crypto-prices");
    const data = await response.json();
    await loadDataSummary();
    await loadCandles();
    els.statusText.textContent = data.ok
      ? `已抓取 ${data.candles} 根真实 K 线`
      : `真实价格抓取失败，已保留本地缓存`;
  } finally {
    els.fetchPricesBtn.disabled = false;
  }
}

async function fetchRealMarkets() {
  els.fetchMarketsBtn.disabled = true;
  els.statusText.textContent = "正在抓取真实 Polymarket 市场";
  try {
    const response = await fetch("/api/fetch-real-markets");
    const data = await response.json();
    await loadDataSummary();
    els.statusText.textContent = data.ok
      ? `已抓取 ${data.markets} 个真实 barrier 市场`
      : `真实市场抓取失败：${(data.errors || []).join("; ") || "无可用数据"}`;
  } finally {
    els.fetchMarketsBtn.disabled = false;
  }
}

async function loadDashboard() {
  els.statusText.textContent = "读取本地数据库";
  const [dashboardResponse] = await Promise.all([fetch("/api/dashboard"), loadDataSummary(), loadCandles()]);
  const data = await dashboardResponse.json();
  const run = data.runs?.[0];
  renderRun(run, data.trades || []);
  els.statusText.textContent = run ? "已加载最近一次回测" : "等待运行";
}

async function runDemoBacktest() {
  els.runBtn.disabled = true;
  els.statusText.textContent = "正在运行 demo 回测";
  try {
    const response = await fetch("/api/run-demo-backtest");
    const data = await response.json();
    renderRun(data.run, data.trades || []);
    els.statusText.textContent = `已保存 Run #${data.run_id}`;
  } finally {
    els.runBtn.disabled = false;
  }
}

els.runBtn.addEventListener("click", runDemoBacktest);
els.refreshBtn.addEventListener("click", loadDashboard);
els.seedDemoBtn.addEventListener("click", seedDemoPrices);
els.fetchPricesBtn.addEventListener("click", fetchRealPrices);
els.fetchMarketsBtn.addEventListener("click", fetchRealMarkets);
document.querySelectorAll(".asset-toggle").forEach((button) => {
  button.addEventListener("click", async () => {
    selectedAsset = button.dataset.asset;
    document.querySelectorAll(".asset-toggle").forEach((item) => item.classList.toggle("active", item === button));
    await loadCandles();
  });
});
window.addEventListener("resize", () => {
  drawEquity(lastEquity);
  drawPriceChart(lastPrices);
});
loadDashboard();
