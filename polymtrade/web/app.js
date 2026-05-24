const els = {
  topScanBtn: document.getElementById("topScanBtn"),
  refreshBtn: document.getElementById("refreshBtn"),
  statusText: document.getElementById("statusText"),
  priceChart: document.getElementById("priceChart"),
  edgeChart: document.getElementById("edgeChart"),
  fetchPricesBtn: document.getElementById("fetchPricesBtn"),
  fetchMarketsBtn: document.getElementById("fetchMarketsBtn"),
  coverageRows: document.getElementById("coverageRows"),
  scanBtn: document.getElementById("scanBtn"),
  scannerRows: document.getElementById("scannerRows"),
  scannerMeta: document.getElementById("scannerMeta"),
  scannerCandidates: document.getElementById("scannerCandidates"),
  scannerBestEdge: document.getElementById("scannerBestEdge"),
  scannerBestRoi: document.getElementById("scannerBestRoi"),
  scannerScanned: document.getElementById("scannerScanned"),
  scannerVol: document.getElementById("scannerVol"),
  scannerPaths: document.getElementById("scannerPaths"),
  scannerSkipped: document.getElementById("scannerSkipped"),
  scannerStatus: document.getElementById("scannerStatus"),
  priceSource: document.getElementById("priceSource"),
  stackData: document.getElementById("stackData"),
  stackModel: document.getElementById("stackModel"),
  stackCost: document.getElementById("stackCost"),
  stackExecution: document.getElementById("stackExecution"),
};

let selectedAsset = "BTC";
let lastPrices = [];
let lastScanner = null;

function percent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `${(Number(value) * 100).toFixed(2)}%`;
}

function money(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function signedPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  const cls = Number(value) >= 0 ? "positive" : "negative";
  return `<span class="${cls}">${percent(value)}</span>`;
}

function number(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return Number(value).toFixed(digits);
}

function actionLabel(action) {
  if (action === "candidate") return `<span class="pill positive-pill">候选</span>`;
  if (action === "avoid") return `<span class="pill negative-pill">回避</span>`;
  if (action === "verify") return `<span class="pill warning-pill">核验</span>`;
  return `<span class="pill neutral-pill">观察</span>`;
}

function priceCell(row) {
  const main = percent(row.market_yes_price);
  if (row.pricing_source !== "orderbook") return `${main}<small>cached</small>`;
  const spread = Number.isFinite(Number(row.spread)) ? `spread ${percent(row.spread)}` : "spread --";
  const ask = Number.isFinite(Number(row.best_ask)) ? `ask ${percent(row.best_ask)}` : "ask --";
  return `${main}<small>${ask} · ${spread}</small>`;
}

function fillCell(row) {
  if (row.pricing_source !== "orderbook") return "--";
  const fill = row.complete_fill ? "full" : "partial";
  return `${money(row.executable_notional)}<small>${fill}</small>`;
}

function scannerRowsForAsset(asset) {
  return (lastScanner?.opportunities || []).filter((row) => row.asset === asset);
}

function contextSourceLabel(contexts = {}) {
  const items = Object.values(contexts);
  if (!items.length) return "--";
  const sources = [...new Set(items.map((item) => item.source))];
  const assets = items.map((item) => item.asset).join("/");
  if (sources.length === 1) return `${assets} ${sources[0]}`;
  return items.map((item) => `${item.asset}:${item.source}`).join(" / ");
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
  let barrierRows = scannerRowsForAsset(selectedAsset).filter((row) => ["candidate", "verify"].includes(row.action));
  if (!barrierRows.length) {
    barrierRows = scannerRowsForAsset(selectedAsset).filter((row) => row.action === "watch").slice(0, 3);
  }
  barrierRows = barrierRows.slice(0, 5);
  const barrierValues = barrierRows.map((row) => Number(row.barrier)).filter((item) => Number.isFinite(item));
  if (!values.length) {
    ctx.fillStyle = "#65736d";
    ctx.font = "14px system-ui";
    ctx.fillText("暂无价格数据", pad, height / 2);
    return;
  }
  const min = Math.min(...values, ...barrierValues) * 0.98;
  const max = Math.max(...values, ...barrierValues) * 1.02;
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

  const labelSlots = [];
  barrierRows.forEach((row) => {
    const barrier = Number(row.barrier);
    if (!Number.isFinite(barrier)) return;
    const y = yFor(barrier);
    if (y < pad || y > height - pad) return;
    ctx.save();
    ctx.strokeStyle = row.action === "candidate" ? "#0f7a55" : row.action === "verify" ? "#8a5a00" : "#b4233a";
    ctx.lineWidth = row.action === "candidate" ? 1.8 : 1.2;
    ctx.setLineDash(row.action === "candidate" ? [8, 4] : [4, 4]);
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(width - pad, y);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = ctx.strokeStyle;
    ctx.font = "11px system-ui";
    const label = `${row.direction === "hit_below" ? "Below" : "Above"} ${money(barrier)} · ${row.action}`;
    let labelY = Math.max(pad + 12, Math.min(height - pad - 6, y - 6));
    while (labelSlots.some((slot) => Math.abs(slot - labelY) < 14)) labelY += 14;
    labelY = Math.min(height - pad - 6, labelY);
    labelSlots.push(labelY);
    ctx.fillText(label, pad + 8, labelY);
    ctx.restore();
  });

  ctx.fillStyle = "#17201c";
  ctx.font = "12px system-ui";
  ctx.fillText(`${selectedAsset} ${money(values[values.length - 1])}`, pad, pad - 10);
  ctx.fillStyle = "#65736d";
  ctx.fillText(`${values.length} daily candles`, width - pad - 112, height - 10);
}

function drawEdgeChart(rows) {
  const canvas = els.edgeChart;
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.max(600, Math.floor(rect.width * dpr));
  canvas.height = Math.max(250, Math.floor(rect.height * dpr));
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const width = canvas.width / dpr;
  const height = canvas.height / dpr;
  const pad = 42;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#fbfcfa";
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "#dce2de";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) {
    const p = i / 4;
    const x = pad + (width - pad * 2) * p;
    const y = height - pad - (height - pad * 2) * p;
    ctx.beginPath();
    ctx.moveTo(x, pad);
    ctx.lineTo(x, height - pad);
    ctx.moveTo(pad, y);
    ctx.lineTo(width - pad, y);
    ctx.stroke();
  }

  const xFor = (value) => pad + (width - pad * 2) * Math.max(0, Math.min(1, value));
  const yFor = (value) => height - pad - (height - pad * 2) * Math.max(0, Math.min(1, value));

  ctx.strokeStyle = "#65736d";
  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  ctx.moveTo(xFor(0), yFor(0));
  ctx.lineTo(xFor(1), yFor(1));
  ctx.stroke();
  ctx.setLineDash([]);

  const validRows = rows.filter((row) => Number.isFinite(Number(row.market_yes_price)) && Number.isFinite(Number(row.model_probability)));
  if (!validRows.length) {
    ctx.fillStyle = "#65736d";
    ctx.font = "14px system-ui";
    ctx.fillText("暂无 scanner 点位", pad, height / 2);
  }

  validRows.forEach((row) => {
    const x = xFor(Number(row.market_yes_price));
    const y = yFor(Number(row.model_probability));
    const radius = row.action === "candidate" ? 6 : row.action === "verify" ? 5 : 4;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = row.action === "candidate" ? "#0f7a55" : row.action === "verify" ? "#8a5a00" : row.net_edge < 0 ? "#b4233a" : "#2757a7";
    ctx.globalAlpha = row.action === "avoid" ? 0.35 : 0.82;
    ctx.fill();
    ctx.globalAlpha = 1;
  });

  ctx.fillStyle = "#17201c";
  ctx.font = "12px system-ui";
  ctx.fillText("Market implied probability", pad, height - 12);
  ctx.save();
  ctx.translate(14, height - pad);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("Model probability", 0, 0);
  ctx.restore();
  ctx.fillStyle = "#65736d";
  ctx.fillText("0%", pad - 8, height - pad + 18);
  ctx.fillText("100%", width - pad - 24, height - pad + 18);
  ctx.fillText("100%", pad - 36, pad + 4);
}

function renderCoverage(candleRows, marketRows = [], priceHistoryRows = []) {
  if (!candleRows.length && !marketRows.length && !priceHistoryRows.length) {
    els.coverageRows.innerHTML = `<div class="coverage-row"><strong>暂无真实数据</strong><span>请抓取真实价格或真实市场。</span></div>`;
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
          <span>scanner 候选池</span>
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

function renderScanner(data) {
  lastScanner = data;
  const summary = data.summary || {};
  const assumptions = data.assumptions || {};
  const rows = data.opportunities || [];
  els.scannerCandidates.textContent = summary.candidates ?? "--";
  els.scannerBestEdge.innerHTML = signedPercent(summary.best_net_edge);
  els.scannerBestRoi.innerHTML = signedPercent(summary.best_roi);
  els.scannerScanned.textContent = summary.markets_scanned ?? "--";
  els.scannerVol.textContent = assumptions.vol_window || "--";
  els.scannerPaths.textContent = assumptions.simulations ?? "--";
  els.scannerSkipped.textContent = summary.markets_skipped ?? "--";
  els.scannerStatus.textContent = summary.candidates > 0 ? "有候选" : "观察";
  els.scannerMeta.textContent = `${assumptions.vol_window || "90d"} vol · ${assumptions.simulations || 0} paths`;
  const contextSources = contextSourceLabel(data.contexts || {});
  els.priceSource.textContent = contextSources || "--";
  const selectedContext = data.contexts?.[selectedAsset];
  const selectedVol = selectedContext?.volatility?.[assumptions.vol_window];
  els.stackData.textContent = contextSources || "无真实价格源";
  els.stackModel.textContent = `${assumptions.vol_window || "90d"} realized vol${selectedVol ? ` · ${percent(selectedVol)}` : ""} · ${assumptions.simulations || 0} paths`;
  els.stackCost.textContent = `fee ${percent(assumptions.fee_rate)} · slippage ${Number(assumptions.slippage_bps || 0).toFixed(0)} bps · min edge ${percent(assumptions.edge_threshold)}`;
  els.stackExecution.textContent = assumptions.orderbook
    ? `order book ${summary.orderbook_priced ?? 0}/${assumptions.book_limit} · ${money(assumptions.executable_notional)} test size · ${summary.candidates ?? 0} candidates`
    : `cached price · min liquidity ${money(assumptions.min_liquidity)} · ${summary.candidates ?? 0} candidates`;
  drawEdgeChart(rows);
  drawPriceChart(lastPrices);
  if (!rows.length) {
    els.scannerRows.innerHTML = `<tr><td colspan="13">暂无可扫描市场</td></tr>`;
    return;
  }
  els.scannerRows.innerHTML = rows
    .map(
      (row) => `
        <tr>
          <td>${actionLabel(row.action)}</td>
          <td>${row.asset}</td>
          <td class="question">${row.question}</td>
          <td>${row.direction === "hit_below" ? "下破" : "上破"}</td>
          <td>${money(row.spot)}</td>
          <td>${money(row.barrier)}</td>
          <td>${number(row.days_to_expiry, 1)}d</td>
          <td>${priceCell(row)}</td>
          <td>${percent(row.model_probability)}</td>
          <td>${signedPercent(row.net_edge)}</td>
          <td>${signedPercent(row.roi)}</td>
          <td>${fillCell(row)}</td>
          <td>${money(row.liquidity)}</td>
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

async function loadScanner() {
  els.topScanBtn.disabled = true;
  els.scanBtn.disabled = true;
  els.scannerMeta.textContent = "运行中";
  els.scannerRows.innerHTML = `<tr><td colspan="13">Scanner 正在计算盘口与模型概率...</td></tr>`;
  try {
    const response = await fetch("/api/scanner?limit=50&edge=0.02&min_liquidity=500&simulations=800&vol_window=90d&orderbook=1&book_limit=8&executable_notional=100&book_timeout=4");
    if (!response.ok) {
      throw new Error(`scanner api ${response.status}`);
    }
    const data = await response.json();
    renderScanner(data);
    els.statusText.textContent = `Scanner 已更新：${data.summary?.candidates ?? 0} 个候选`;
  } catch (error) {
    els.scannerMeta.textContent = "失败";
    els.scannerRows.innerHTML = `<tr><td colspan="13">Scanner API 请求失败：${error.message}</td></tr>`;
    els.statusText.textContent = `Scanner 失败：${error.message}`;
  } finally {
    els.topScanBtn.disabled = false;
    els.scanBtn.disabled = false;
  }
}

async function loadDashboard() {
  els.statusText.textContent = "读取本地数据库";
  await Promise.all([loadDataSummary(), loadCandles(), loadScanner()]);
}

els.refreshBtn.addEventListener("click", loadDashboard);
els.fetchPricesBtn.addEventListener("click", fetchRealPrices);
els.fetchMarketsBtn.addEventListener("click", fetchRealMarkets);
els.scanBtn.addEventListener("click", loadScanner);
els.topScanBtn.addEventListener("click", loadScanner);
document.querySelectorAll(".asset-toggle").forEach((button) => {
  button.addEventListener("click", async () => {
    selectedAsset = button.dataset.asset;
    document.querySelectorAll(".asset-toggle").forEach((item) => item.classList.toggle("active", item === button));
    await loadCandles();
    if (lastScanner) renderScanner(lastScanner);
  });
});
window.addEventListener("resize", () => {
  drawPriceChart(lastPrices);
  drawEdgeChart(lastScanner?.opportunities || []);
});
loadDashboard();
