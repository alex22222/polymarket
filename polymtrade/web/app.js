const els = {
  topScanBtn: document.getElementById("topScanBtn"),
  refreshBtn: document.getElementById("refreshBtn"),
  statusText: document.getElementById("statusText"),
  versionBadge: document.getElementById("versionBadge"),
  priceChart: document.getElementById("priceChart"),
  edgeChart: document.getElementById("edgeChart"),
  fetchPricesBtn: document.getElementById("fetchPricesBtn"),
  fetchMarketsBtn: document.getElementById("fetchMarketsBtn"),
  sendReportBtn: document.getElementById("sendReportBtn"),
  dataQualityRows: document.getElementById("dataQualityRows"),
  candleAnomalyRows: document.getElementById("candleAnomalyRows"),
  coverageRows: document.getElementById("coverageRows"),
  automationMeta: document.getElementById("automationMeta"),
  automationStatus: document.getElementById("automationStatus"),
  automationAge: document.getElementById("automationAge"),
  automationRuns: document.getElementById("automationRuns"),
  automationCandidates: document.getElementById("automationCandidates"),
  automationDetail: document.getElementById("automationDetail"),
  sourceHealthRows: document.getElementById("sourceHealthRows"),
  refreshHealthBtn: document.getElementById("refreshHealthBtn"),
  observationSummary: document.getElementById("observationSummary"),
  observationRows: document.getElementById("observationRows"),
  saveObservationBtn: document.getElementById("saveObservationBtn"),
  qualityMeta: document.getElementById("qualityMeta"),
  qualityTracked: document.getElementById("qualityTracked"),
  qualityResolved: document.getElementById("qualityResolved"),
  qualityOpen: document.getElementById("qualityOpen"),
  qualityGroups: document.getElementById("qualityGroups"),
  qualityRows: document.getElementById("qualityRows"),
  refreshQualityBtn: document.getElementById("refreshQualityBtn"),
  paperMeta: document.getElementById("paperMeta"),
  paperTracked: document.getElementById("paperTracked"),
  paperResolved: document.getElementById("paperResolved"),
  paperWinRate: document.getElementById("paperWinRate"),
  paperPnl: document.getElementById("paperPnl"),
  paperExposure: document.getElementById("paperExposure"),
  paperRows: document.getElementById("paperRows"),
  refreshPaperBtn: document.getElementById("refreshPaperBtn"),
  positionMeta: document.getElementById("positionMeta"),
  positionCount: document.getElementById("positionCount"),
  positionHold: document.getElementById("positionHold"),
  positionReview: document.getElementById("positionReview"),
  positionExit: document.getElementById("positionExit"),
  positionPnl: document.getElementById("positionPnl"),
  positionRows: document.getElementById("positionRows"),
  refreshPositionsBtn: document.getElementById("refreshPositionsBtn"),
  candidateReviewMeta: document.getElementById("candidateReviewMeta"),
  candidateReviewTracked: document.getElementById("candidateReviewTracked"),
  candidateReviewResolved: document.getElementById("candidateReviewResolved"),
  candidateReviewWinRate: document.getElementById("candidateReviewWinRate"),
  candidateReviewPnl: document.getElementById("candidateReviewPnl"),
  candidateReviewRoi: document.getElementById("candidateReviewRoi"),
  candidateReviewRows: document.getElementById("candidateReviewRows"),
  refreshCandidateReviewBtn: document.getElementById("refreshCandidateReviewBtn"),
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
  logList: document.getElementById("logList"),
  logMeta: document.getElementById("logMeta"),
  logLevelFilter: document.getElementById("logLevelFilter"),
  logModuleFilter: document.getElementById("logModuleFilter"),
  refreshLogsBtn: document.getElementById("refreshLogsBtn"),
  clearLogsBtn: document.getElementById("clearLogsBtn"),
  logBtn: document.getElementById("logBtn"),
  logBadge: document.getElementById("logBadge"),
  logPanel: document.getElementById("logPanel"),
  logPanelClose: document.getElementById("logPanelClose"),
};

let selectedAsset = "BTC";
let lastPrices = [];
let lastScanner = null;
let scannerSort = { field: null, dir: "asc" };
let activeView = "overview";

function percent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `${(Number(value) * 100).toFixed(2)}%`;
}

function money(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

async function apiJson(url, options) {
  const response = await fetch(url, options);
  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    if (response.ok) return {};
    throw new Error(`api ${response.status}`);
  }
  if (!response.ok) {
    throw new Error(data?.error || `api ${response.status}`);
  }
  return data;
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

function compactAge(minutes) {
  if (minutes === null || minutes === undefined || Number.isNaN(Number(minutes))) return "--";
  const value = Number(minutes);
  if (value < 60) return `${value.toFixed(0)}m`;
  if (value < 60 * 24) return `${(value / 60).toFixed(1)}h`;
  return `${(value / 1440).toFixed(1)}d`;
}

function expiryCell(row) {
  const minutes = Number(row.minutes_to_expiry ?? Number(row.days_to_expiry) * 1440);
  const end = row.end_date ? new Date(row.end_date).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "--";
  if (!Number.isFinite(minutes)) return `--<small>${escapeHtml(end)}</small>`;
  if (minutes <= 0) return `<span class="negative">已到期</span><small>等待结算 · ${escapeHtml(end)}</small>`;
  if (minutes < 60) return `<span class="warning-text">${minutes.toFixed(0)}m</span><small>临近到期 · ${escapeHtml(end)}</small>`;
  if (minutes < 1440) return `${(minutes / 60).toFixed(1)}h<small>${escapeHtml(end)}</small>`;
  return `${(minutes / 1440).toFixed(1)}d<small>${escapeHtml(end)}</small>`;
}

function actionLabel(action) {
  if (action === "candidate") return `<span class="pill positive-pill">候选</span>`;
  if (action === "avoid") return `<span class="pill negative-pill">回避</span>`;
  if (action === "verify") return `<span class="pill warning-pill">核验</span>`;
  return `<span class="pill neutral-pill">观察</span>`;
}

function reviewCell(row) {
  const statusMap = {
    passed: ["通过", "positive"],
    blocked: ["阻断", "negative"],
    verify: ["需核验", "warning"],
    watch: ["观察", "neutral"],
  };
  const [label, cls] = statusMap[row.review_status] || ["未复核", "neutral"];
  const blockers = row.review_blockers || [];
  const checks = row.review_checks || [];
  const notes = blockers.length
    ? blockers.slice(0, 2)
    : checks.filter((item) => item.status !== "pass").map((item) => item.detail).slice(0, 2);
  return `
    <span class="review-status ${cls}">${label}</span>
    <small>${notes.length ? notes.map(escapeHtml).join(" · ") : "盘口/现货/edge 均通过"}</small>
  `;
}

function priceCell(row) {
  const main = percent(row.market_yes_price);
  if (row.pricing_source !== "orderbook") return `${main}<small>cached</small>`;
  const spread = Number.isFinite(Number(row.spread)) ? `spread ${percent(row.spread)}` : "spread --";
  const ask = Number.isFinite(Number(row.best_ask)) ? `ask ${percent(row.best_ask)}` : "ask --";
  const age = Number.isFinite(Number(row.orderbook_age_seconds)) ? `age ${Number(row.orderbook_age_seconds).toFixed(0)}s` : "age --";
  return `${main}<small>${ask} · ${spread} · ${age}</small>`;
}

function fillCell(row) {
  if (row.pricing_source !== "orderbook") return "--";
  const fill = row.complete_fill ? "full" : "partial";
  return `${money(row.executable_notional)}<small>${fill}</small>`;
}

function modelCell(row) {
  const source = row.annual_vol_source || "rv";
  const vol = Number.isFinite(Number(row.annual_vol)) ? percent(row.annual_vol) : "--";
  const iv = row.vol_components?.iv ? ` · IV ${percent(row.vol_components.iv)}` : "";
  return `${percent(row.model_probability)}<small>${escapeHtml(source)} · vol ${vol}${iv}</small>`;
}

function scannerRowsForAsset(asset) {
  return (lastScanner?.opportunities || []).filter((row) => row.asset === asset);
}

function contextSourceLabel(contexts = {}) {
  const items = Object.values(contexts);
  if (!items.length) return "--";
  const sources = [...new Set(items.map((item) => item.source))];
  const assets = items.map((item) => item.asset).join("/");
  const live = items.every((item) => item.spot_is_realtime) ? "live spot" : "daily fallback";
  if (sources.length === 1) return `${assets} ${sources[0]} · ${live}`;
  return `${items.map((item) => `${item.asset}:${item.source}`).join(" / ")} · ${live}`;
}

function setActiveView(view) {
  const allowed = new Set(["overview", "analysis", "research", "scanner"]);
  activeView = allowed.has(view) ? view : "overview";
  document.querySelectorAll(".view-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.viewTab === activeView);
  });
  document.querySelectorAll(".view-section").forEach((section) => {
    section.classList.toggle("hidden", section.dataset.view !== activeView);
  });
  window.location.hash = activeView;
  if (activeView === "overview") {
    drawPriceChart(lastPrices);
  }
  if (activeView === "scanner") {
    drawEdgeChart(lastScanner?.opportunities || []);
  }
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
          <strong><span>${escapeHtml(row.asset)} / ${escapeHtml(row.source)}</span><span>${row.candles} 根</span></strong>
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
          <strong><span>${escapeHtml(row.asset)} markets</span><span>${row.markets} 个</span></strong>
          <span>${escapeHtml(row.direction)} · ${escapeHtml(row.source)}</span>
          <span>scanner 候选池</span>
        </div>
      `,
    )
    .join("");
  const history = priceHistoryRows
    .map(
      (row) => `
        <div class="coverage-row">
          <strong><span>${escapeHtml(row.outcome)} price history</span><span>${row.prices} 点</span></strong>
          <span>${escapeHtml(row.source)}</span>
          <span>${new Date(row.first_ts * 1000).toLocaleDateString()} 至 ${new Date(row.last_ts * 1000).toLocaleDateString()}</span>
        </div>
      `,
    )
    .join("");
  els.coverageRows.innerHTML = candles + markets + history;
}

function dataQualityStatusLabel(status) {
  if (status === "healthy") return `<span class="source-status source-ok">可靠</span>`;
  if (status === "degraded") return `<span class="source-status source-warn">需复核</span>`;
  if (status === "stale") return `<span class="source-status source-warn">过期</span>`;
  return `<span class="source-status source-bad">不可用</span>`;
}

function renderDataQuality(data = {}) {
  if (!els.dataQualityRows) return;
  const sources = data.sources || [];
  if (!sources.length) {
    els.dataQualityRows.innerHTML = `<div class="data-quality-row"><strong>暂无 K 线质量数据</strong><span>需要先导入 BTC / ETH 历史价格。</span></div>`;
    return;
  }
  const recommendations = data.recommendations || {};
  const recommendedRows = Object.values(recommendations)
    .map((row) => `
      <div class="data-quality-row canonical">
        <strong>
          <span>${escapeHtml(row.asset)} canonical</span>
          ${dataQualityStatusLabel(row.status)}
        </strong>
        <span>${escapeHtml(row.source || "--")} · score ${number(row.score, 1)} · coverage ${percent(row.coverage)}</span>
        <span>${escapeHtml(row.reason || "")}</span>
      </div>
    `)
    .join("");
  const sourceRows = sources
    .map((row) => `
      <div class="data-quality-row">
        <strong>
          <span>${escapeHtml(row.asset)} / ${escapeHtml(row.source)}</span>
          ${dataQualityStatusLabel(row.status)}
        </strong>
        <span>${row.candles} 根 · ${new Date(row.first_ts).toLocaleDateString()} 至 ${new Date(row.last_ts).toLocaleDateString()}</span>
        <span>coverage ${percent(row.coverage)} · 缺口 ${row.missing_days} · 跳变 ${row.anomalies} · OHLC ${row.ohlc_errors}</span>
        <span>latest ${money(row.latest_close)} · stale ${row.stale_days ?? "--"}d · score ${number(row.score, 1)}</span>
      </div>
    `)
    .join("");
  els.dataQualityRows.innerHTML = recommendedRows + sourceRows;
}

function anomalyReviewLabel(row) {
  if (row.review_status === "reviewed") {
    return `<span class="source-status source-ok">已复核</span>`;
  }
  if (row.review_status === "excluded") {
    return `<span class="source-status source-bad">剔除</span>`;
  }
  return `<span class="source-status source-warn">待复核</span>`;
}

function renderCandleAnomalies(data = {}) {
  if (!els.candleAnomalyRows) return;
  const rows = data.anomalies || [];
  if (!rows.length) {
    els.candleAnomalyRows.innerHTML = `<div class="anomaly-row clean"><strong>异常 K 线</strong><span>当前阈值下没有发现异常跳变。</span></div>`;
    return;
  }
  els.candleAnomalyRows.innerHTML = rows
    .slice(0, 8)
    .map((row) => `
      <div class="anomaly-row">
        <strong>
          <span>${escapeHtml(row.asset)} / ${escapeHtml(row.source)}</span>
          ${anomalyReviewLabel(row)}
        </strong>
        <span>${signedPercent(row.move)} · ${escapeHtml(row.review_decision || "未决策")}</span>
        <span>${new Date(row.previous_ts).toLocaleDateString()} ${money(row.previous_close)} → ${new Date(row.ts).toLocaleDateString()} ${money(row.close)}</span>
        <span>OHLC ${money(row.open)} / ${money(row.high)} / ${money(row.low)} / ${money(row.close)}</span>
        <span>${escapeHtml(row.review_note || "")}</span>
      </div>
    `)
    .join("");
}

function renderObservationSummary(summary = {}) {
  if (!els.observationSummary) return;
  const latest = summary.latest_at ? new Date(summary.latest_at).toLocaleString("zh-CN") : "无";
  els.observationSummary.textContent = `${summary.runs || 0} 次 · ${summary.rows || 0} 条 · 候选 ${summary.candidates || 0} · 最新 ${latest}`;
}

function renderObservations(data = {}) {
  renderObservationSummary(data.summary || {});
  if (!els.observationRows) return;
  const rows = data.observations || [];
  if (!rows.length) {
    els.observationRows.innerHTML = `<div class="coverage-row"><strong>尚无观测</strong><span>运行 scanner 后保存本次观测。</span></div>`;
    return;
  }
  els.observationRows.innerHTML = rows
    .slice(0, 8)
    .map((row) => {
      const dt = new Date(row.created_at).toLocaleString("zh-CN");
      return `
        <div class="observation-row">
          <strong>
            <span>${actionLabel(row.action)} ${escapeHtml(row.asset)}</span>
            <span>${signedPercent(row.net_edge)}</span>
          </strong>
          <span>${escapeHtml(row.question)}</span>
          <span>${dt} · ${escapeHtml(row.review_status)} · ${escapeHtml(row.pricing_source || "cached")} · 模型 ${percent(row.model_probability)} / 市场 ${percent(row.market_yes_price)}</span>
        </div>
      `;
    })
    .join("");
}

function healthStatusLabel(status) {
  if (status === "healthy") return `<span class="pill positive-pill">正常</span>`;
  if (status === "error") return `<span class="pill negative-pill">失败</span>`;
  if (status === "stale") return `<span class="pill warning-pill">过期</span>`;
  return `<span class="pill neutral-pill">未知</span>`;
}

function sourceStatusLabel(status) {
  if (status === "healthy") return `<span class="source-status source-ok">正常</span>`;
  if (status === "degraded") return `<span class="source-status source-warn">降级</span>`;
  if (status === "network_unavailable") return `<span class="source-status source-net">网络受限</span>`;
  if (status === "error") return `<span class="source-status source-bad">失败</span>`;
  return `<span class="source-status source-muted">跳过</span>`;
}

function renderAutomationHealth(data = {}) {
  const latest = data.latest || {};
  const counts = data.counts || {};
  if (els.automationMeta) els.automationMeta.textContent = latest.created_at ? new Date(latest.created_at).toLocaleString("zh-CN") : "尚无自动任务日志";
  if (els.automationStatus) els.automationStatus.innerHTML = healthStatusLabel(data.status);
  if (els.automationAge) els.automationAge.textContent = compactAge(data.age_minutes);
  if (els.automationRuns) els.automationRuns.textContent = counts.observation_runs ?? "--";
  if (els.automationCandidates) els.automationCandidates.textContent = counts.candidates ?? "--";
  if (!els.automationDetail) return;
  const detail = latest.detail_json || {};
  const prices = detail.prices ? `价格 ${detail.prices.inserted ?? 0}` : "价格 --";
  const markets = detail.markets ? `市场 ${detail.markets.inserted ?? 0} / errors ${(detail.markets.errors || []).length}` : "市场 --";
  const scanner = detail.scanner?.payload?.summary ? `候选 ${detail.scanner.payload.summary.candidates ?? 0}` : "候选 --";
  const runId = detail.scanner?.observation_run_id ? `run #${detail.scanner.observation_run_id}` : "run --";
  els.automationDetail.textContent = `${latest.level || "--"} · ${latest.message || "暂无自动任务"} · ${prices} · ${markets} · ${scanner} · ${runId}`;
  if (!els.sourceHealthRows) return;
  const sources = data.sources || [];
  const sourceSummary = new Map((data.source_summary || []).map((row) => [`${row.source}::${row.component}`, row]));
  if (!sources.length) {
    els.sourceHealthRows.innerHTML = `<div class="source-health-row"><strong>等待源级别健康数据</strong><span>下一次自动任务会写入 Gamma / Polymtrade / Deribit / Binance 状态。</span></div>`;
    return;
  }
  els.sourceHealthRows.innerHTML = sources
    .map((row) => {
      const summary = sourceSummary.get(`${row.source}::${row.component}`) || {};
      const history = summary.checks
        ? `近 ${summary.checks} 次 OK ${percent(summary.success_rate)} · 失败 ${summary.error || 0} · 降级 ${summary.degraded || 0}`
        : "暂无历史聚合";
      return `
        <div class="source-health-row">
          <strong>
            <span>${escapeHtml(row.source)} · ${escapeHtml(row.component)}</span>
            ${sourceStatusLabel(row.status)}
          </strong>
          <span>${escapeHtml(row.message || "")}</span>
          <span>records ${row.records ?? "--"} · errors ${row.errors ?? 0}</span>
          <span class="source-history">${escapeHtml(history)}</span>
        </div>
      `;
    })
    .join("");
}

function renderQualityAnalysis(data = {}) {
  const summary = data.summary || {};
  if (els.qualityMeta) els.qualityMeta.textContent = `生成 ${data.generated_at ? new Date(data.generated_at).toLocaleString("zh-CN") : "--"}`;
  if (els.qualityTracked) els.qualityTracked.textContent = summary.tracked_candidates ?? "--";
  if (els.qualityResolved) els.qualityResolved.textContent = summary.resolved ?? "--";
  if (els.qualityOpen) els.qualityOpen.textContent = summary.open ?? "--";
  if (els.qualityGroups) els.qualityGroups.textContent = summary.groups ?? "--";
  if (!els.qualityRows) return;
  const rows = data.groups || [];
  if (!rows.length) {
    els.qualityRows.innerHTML = `<tr><td colspan="8">暂无 candidate 样本</td></tr>`;
    return;
  }
  const kindLabel = { asset: "资产", edge: "Edge", vol: "波动率", book: "盘口" };
  els.qualityRows.innerHTML = rows
    .map((row) => `
      <tr>
        <td>${kindLabel[row.kind] || escapeHtml(row.kind)}</td>
        <td>${escapeHtml(row.name)}</td>
        <td>${row.tracked}</td>
        <td>${row.resolved}<small>open ${row.open}</small></td>
        <td>${percent(row.win_rate)}</td>
        <td>${signedPercent(row.roi)}</td>
        <td>${signedPercent(row.avg_edge)}</td>
        <td>${percent(row.avg_spread)}</td>
      </tr>
    `)
    .join("");
}

function paperStatusLabel(status) {
  if (status === "won") return `<span class="pill positive-pill">赢</span>`;
  if (status === "lost") return `<span class="pill negative-pill">亏</span>`;
  if (status === "open") return `<span class="pill neutral-pill">未结</span>`;
  return `<span class="pill warning-pill">未知</span>`;
}

function riskClass(level) {
  if (level === "low") return "risk-low";
  if (level === "medium") return "risk-medium";
  if (level === "high") return "risk-high";
  if (level === "extreme") return "risk-extreme";
  return "risk-unknown";
}

function renderRiskPanel(risk = {}) {
  const notes = Array.isArray(risk.notes) ? risk.notes.slice(0, 2) : [];
  return `
    <div class="risk-panel ${riskClass(risk.risk_level)}">
      <div class="risk-panel-head">
        <span>${escapeHtml(risk.risk_label || "未知风险")}</span>
        <strong>最大亏损 ${percent(risk.max_loss_pct)}</strong>
      </div>
      <div class="risk-metrics">
        <span>需要变动 <strong>${signedPercent(risk.required_move_pct)}</strong></span>
        <span>剩余 <strong>${risk.days_remaining === null || risk.days_remaining === undefined ? "--" : `${Number(risk.days_remaining).toFixed(1)}d`}</strong></span>
        <span>模型概率 <strong>${percent(risk.model_probability)}</strong></span>
        <span>盈亏平衡 <strong>${percent(risk.breakeven_probability)}</strong></span>
        <span>安全边际 <strong>${signedPercent(risk.safety_margin)}</strong></span>
        <span>赢/输 <strong>${money(risk.profit_if_win)} / ${money(risk.loss_if_lose)}</strong></span>
      </div>
      ${notes.length ? `<p>${notes.map((item) => escapeHtml(item)).join(" ")}</p>` : ""}
    </div>
  `;
}

function renderPaperTrading(data = {}) {
  const summary = data.summary || {};
  const excluded = data.excluded || [];
  if (els.paperMeta) {
    const generated = data.generated_at ? new Date(data.generated_at).toLocaleString("zh-CN") : "--";
    els.paperMeta.textContent = `当前有效 ${summary.tracked ?? 0} 条 · 旧样本 ${summary.excluded_legacy ?? 0}/${summary.raw_candidates ?? 0} · 生成 ${generated}`;
  }
  if (els.paperTracked) els.paperTracked.textContent = summary.tracked ?? "--";
  if (els.paperResolved) els.paperResolved.textContent = summary.resolved ?? "--";
  if (els.paperWinRate) els.paperWinRate.textContent = percent(summary.win_rate);
  if (els.paperPnl) els.paperPnl.innerHTML = summary.pnl === null || summary.pnl === undefined ? "--" : `<span class="${Number(summary.pnl) >= 0 ? "positive" : "negative"}">${money(summary.pnl)}</span>`;
  if (els.paperExposure) els.paperExposure.textContent = money(summary.open_exposure);
  if (!els.paperRows) return;
  const rows = data.trades || [];
  if (!rows.length) {
    const legacyText = excluded.length
      ? `已隔离 ${summary.excluded_legacy ?? excluded.length} 条旧规则/不可执行样本，最新原因：${escapeHtml(excluded[0].reasons?.join("；") || "legacy sample")}`
      : "保存当前规则通过的 candidate 后，这里会跟踪是否触及 barrier。";
    els.paperRows.innerHTML = `<div class="coverage-row"><strong>暂无当前有效 Paper Trade</strong><span>${legacyText}</span></div>`;
    return;
  }
  els.paperRows.innerHTML = rows
    .slice(0, 10)
    .map((row) => `
      <div class="paper-row">
        <strong>
          <span>${paperStatusLabel(row.status)} ${escapeHtml(row.asset)}</span>
          <span>${signedPercent(row.return_pct)}</span>
        </strong>
        <span>${escapeHtml(row.question)}</span>
        <span>${money(row.spot)} → ${money(row.barrier)} · ${row.direction === "hit_below" ? "下破" : "上破"} · 到期 ${row.end_date ? new Date(row.end_date).toLocaleDateString() : "--"}</span>
        ${renderRiskPanel(row.risk || {})}
        <span>stake ${money(row.stake)} · PnL ${money(row.pnl)} · ${escapeHtml(row.evidence || "")}</span>
      </div>
    `)
    .join("");
}

function recommendationPill(action, label) {
  if (action === "hold") return `<span class="pill positive-pill">${escapeHtml(label || "继续持有")}</span>`;
  if (action === "exit") return `<span class="pill negative-pill">${escapeHtml(label || "应退出")}</span>`;
  return `<span class="pill warning-pill">${escapeHtml(label || "观察退出")}</span>`;
}

function renderPositions(data = {}) {
  const summary = data.summary || {};
  if (els.positionMeta) {
    const generated = data.generated_at ? new Date(data.generated_at).toLocaleString("zh-CN") : "--";
    els.positionMeta.textContent = `只读退出观察 · 生成 ${generated}`;
  }
  if (els.positionCount) els.positionCount.textContent = summary.positions ?? "--";
  if (els.positionHold) els.positionHold.textContent = summary.hold ?? "--";
  if (els.positionReview) els.positionReview.textContent = summary.review ?? "--";
  if (els.positionExit) els.positionExit.textContent = summary.exit ?? "--";
  if (els.positionPnl) els.positionPnl.innerHTML = summary.unrealized_pnl === null || summary.unrealized_pnl === undefined ? "--" : `<span class="${Number(summary.unrealized_pnl) >= 0 ? "positive" : "negative"}">${money(summary.unrealized_pnl)}</span>`;
  if (!els.positionRows) return;
  const rows = data.positions || [];
  if (!rows.length) {
    els.positionRows.innerHTML = `<div class="coverage-row"><strong>暂无开放持仓</strong><span>当前有效 Paper Trade 出现后，这里会复核退出机会。</span></div>`;
    return;
  }
  els.positionRows.innerHTML = rows
    .map((row) => `
      <div class="position-row">
        <strong>
          <span>${recommendationPill(row.recommendation, row.recommendation_label)} ${escapeHtml(row.asset)}</span>
          <span>${signedPercent(row.unrealized_return)}</span>
        </strong>
        <span>${escapeHtml(row.question)}</span>
        <div class="position-metrics">
          <span>入场 <strong>${percent(row.entry_price)}</strong></span>
          <span>卖出 bid <strong>${percent(row.current_best_bid)}</strong></span>
          <span>买入 ask <strong>${percent(row.current_best_ask)}</strong></span>
          <span>spread <strong>${percent(row.spread)}</strong></span>
          <span>退出价值 <strong>${money(row.exit_value)}</strong></span>
          <span>未实现 PnL <strong>${money(row.unrealized_pnl)}</strong></span>
        </div>
        <span>${escapeHtml((row.notes || []).join("；"))}</span>
      </div>
    `)
    .join("");
}

function renderCandidateReview(data = {}) {
  const summary = data.summary || {};
  if (els.candidateReviewMeta) els.candidateReviewMeta.textContent = `生成 ${data.generated_at ? new Date(data.generated_at).toLocaleString("zh-CN") : "--"}`;
  if (els.candidateReviewTracked) els.candidateReviewTracked.textContent = summary.tracked ?? "--";
  if (els.candidateReviewResolved) els.candidateReviewResolved.textContent = summary.resolved ?? "--";
  if (els.candidateReviewWinRate) els.candidateReviewWinRate.textContent = percent(summary.win_rate);
  if (els.candidateReviewPnl) els.candidateReviewPnl.innerHTML = summary.pnl === null || summary.pnl === undefined ? "--" : `<span class="${Number(summary.pnl) >= 0 ? "positive" : "negative"}">${money(summary.pnl)}</span>`;
  if (els.candidateReviewRoi) els.candidateReviewRoi.innerHTML = signedPercent(summary.roi);
  if (!els.candidateReviewRows) return;
  const rows = data.candidates || [];
  if (!rows.length) {
    els.candidateReviewRows.innerHTML = `<tr><td colspan="7">暂无 candidate 样本</td></tr>`;
    return;
  }
  els.candidateReviewRows.innerHTML = rows
    .slice(0, 30)
    .map((row) => `
      <tr>
        <td>${paperStatusLabel(row.status)}<small>${new Date(row.created_at).toLocaleDateString()}</small></td>
        <td>${escapeHtml(row.asset)}</td>
        <td class="question">${escapeHtml(row.question)}</td>
        <td>${percent(row.model_probability)}<small>market ${percent(row.market_yes_price)}</small></td>
        <td>${signedPercent(row.net_edge)}<small>ROI ${signedPercent(row.roi)}</small></td>
        <td>${escapeHtml(row.book_quality)}<small>${escapeHtml(row.pricing_source || "--")} · spread ${percent(row.spread)}</small></td>
        <td>${money(row.pnl)}<small>${escapeHtml(row.evidence || "")}</small></td>
      </tr>
    `)
    .join("");
}

function sortValue(row, field) {
  if (field === "action") {
    const order = { candidate: 0, verify: 1, watch: 2, avoid: 3 };
    return order[row.action] ?? 99;
  }
  if (field === "review_status") {
    const order = { passed: 0, verify: 1, watch: 2, blocked: 3 };
    return order[row.review_status] ?? 99;
  }
  if (field === "ask_price") {
    return Number.isFinite(Number(row.best_ask)) ? Number(row.best_ask) : Number(row.market_yes_price);
  }
  const v = row[field];
  if (typeof v === "number") return v;
  if (typeof v === "string") return v.toLowerCase();
  return 0;
}

function applySort(rows) {
  if (!scannerSort.field) return rows;
  const { field, dir } = scannerSort;
  const mult = dir === "desc" ? -1 : 1;
  return [...rows].sort((a, b) => {
    const av = sortValue(a, field);
    const bv = sortValue(b, field);
    if (av < bv) return -1 * mult;
    if (av > bv) return 1 * mult;
    return 0;
  });
}

function updateSortIndicators() {
  document.querySelectorAll(".scanner-table th.sortable").forEach((th) => {
    const field = th.dataset.sort;
    th.classList.remove("sort-asc", "sort-desc");
    if (field === scannerSort.field) th.classList.add(scannerSort.dir === "asc" ? "sort-asc" : "sort-desc");
  });
}

function renderScanner(data) {
  lastScanner = data;
  const summary = data.summary || {};
  const assumptions = data.assumptions || {};
  const rows = applySort(data.opportunities || []);
  if (els.saveObservationBtn) els.saveObservationBtn.disabled = !rows.length;
  els.scannerCandidates.textContent = summary.candidates ?? "--";
  els.scannerBestEdge.innerHTML = signedPercent(summary.best_net_edge);
  els.scannerBestRoi.innerHTML = signedPercent(summary.best_roi);
  els.scannerScanned.textContent = summary.markets_scanned ?? "--";
  els.scannerVol.textContent = assumptions.vol_window || "--";
  els.scannerPaths.textContent = assumptions.simulations ?? "--";
  els.scannerSkipped.textContent = summary.markets_skipped ?? "--";
  els.scannerStatus.textContent = summary.candidates > 0 ? "有候选" : "观察";
  els.scannerMeta.textContent = `${assumptions.vol_window || "90d"} vol · ${assumptions.simulations || 0} paths · 最小到期 ${assumptions.min_expiry_minutes ?? 30}m`;
  const contextSources = contextSourceLabel(data.contexts || {});
  els.priceSource.textContent = contextSources || "--";
  const selectedContext = data.contexts?.[selectedAsset];
  const selectedVol = selectedContext?.volatility?.[assumptions.vol_window];
  els.stackData.textContent = contextSources || "无真实价格源";
  const ewmaVol = selectedContext?.ewma_volatility;
  const ivState = selectedContext?.iv_source ? "Deribit IV on" : selectedContext?.iv_error ? "Deribit IV unavailable" : "IV off";
  els.stackModel.textContent = `${assumptions.vol_model || "factor"} vol · RV ${assumptions.vol_window || "90d"}${selectedVol ? ` ${percent(selectedVol)}` : ""}${ewmaVol ? ` · EWMA ${percent(ewmaVol)}` : ""} · ${ivState} · ${assumptions.simulations || 0} paths`;
  els.stackCost.textContent = `fee ${percent(assumptions.fee_rate)} · slippage ${Number(assumptions.slippage_bps || 0).toFixed(0)} bps · min edge ${percent(assumptions.edge_threshold)}`;
  els.stackExecution.textContent = assumptions.orderbook
    ? `盘口 ${summary.orderbook_priced ?? 0}/${assumptions.book_limit} · 过期 ${summary.stale_orderbooks ?? 0} · 部分 ${summary.partial_fills ?? 0} · 候选 ${summary.candidates ?? 0}`
    : `cached price · min liquidity ${money(assumptions.min_liquidity)} · ${summary.candidates ?? 0} candidates`;
  drawEdgeChart(rows);
  drawPriceChart(lastPrices);
  if (!rows.length) {
    els.scannerRows.innerHTML = `<tr><td colspan="14">暂无可扫描市场</td></tr>`;
    return;
  }
  els.scannerRows.innerHTML = rows
    .map(
      (row) => `
        <tr>
          <td>${actionLabel(row.action)}</td>
          <td class="review-cell">${reviewCell(row)}</td>
          <td>${escapeHtml(row.asset)}</td>
          <td class="question">${escapeHtml(row.question)}</td>
          <td>${row.direction === "hit_below" ? "下破" : "上破"}</td>
          <td>${money(row.spot)}</td>
          <td>${money(row.barrier)}</td>
          <td>${expiryCell(row)}</td>
          <td>${priceCell(row)}</td>
          <td>${modelCell(row)}</td>
          <td>${signedPercent(row.net_edge)}</td>
          <td>${signedPercent(row.roi)}</td>
          <td>${fillCell(row)}</td>
          <td>${money(row.liquidity)}</td>
        </tr>
      `,
    )
    .join("");
  updateSortIndicators();
}

async function loadDataSummary() {
  const [data, quality, anomalies] = await Promise.all([
    apiJson("/api/data-summary"),
    apiJson("/api/data-quality"),
    apiJson("/api/candle-anomalies?threshold=0.25"),
  ]);
  renderDataQuality(quality);
  renderCandleAnomalies(anomalies);
  renderCoverage(data.candles || [], data.markets || [], data.priceHistory || []);
  renderObservationSummary(data.observations || {});
}

async function loadVersion() {
  if (!els.versionBadge) return;
  try {
    const data = await apiJson("/api/version");
    const version = data.version || data.sha || "--";
    const source = data.source === "deploy" ? "deploy" : "local";
    const deployed = data.deployed_at ? new Date(data.deployed_at).toLocaleString("zh-CN") : "";
    els.versionBadge.textContent = `${source} ${version}`;
    els.versionBadge.title = deployed ? `部署时间 ${deployed}` : "本地版本";
  } catch (error) {
    els.versionBadge.textContent = "version --";
    els.versionBadge.title = `版本信息读取失败：${error.message}`;
  }
}

async function loadObservations() {
  if (!els.observationRows) return;
  const data = await apiJson("/api/scanner-observations?limit=25");
  renderObservations(data);
}

async function loadAutomationHealth() {
  if (!els.automationStatus) return;
  const data = await apiJson("/api/automation-health?max_age_minutes=150");
  renderAutomationHealth(data);
}

async function loadQualityAnalysis() {
  if (!els.qualityRows) return;
  const data = await apiJson("/api/quality-analysis?limit=500&stake=100");
  renderQualityAnalysis(data);
}

async function loadPaperTrading() {
  if (!els.paperRows) return;
  if (els.refreshPaperBtn) {
    els.refreshPaperBtn.disabled = true;
    els.refreshPaperBtn.textContent = "刷新中...";
  }
  if (els.paperMeta) els.paperMeta.textContent = "正在刷新 paper trading";
  els.statusText.textContent = "正在刷新 Paper Trading 结果";
  try {
    const data = await apiJson("/api/paper-trading?limit=100&stake=100&current_only=1&max_days=14&max_spread=0.04&max_book_age_seconds=120");
    renderPaperTrading(data);
    const summary = data.summary || {};
    els.statusText.textContent = `Paper Trading 已刷新：当前有效 ${summary.tracked ?? 0} 条，旧样本 ${summary.excluded_legacy ?? 0} 条`;
  } catch (error) {
    if (els.paperMeta) els.paperMeta.textContent = "刷新失败";
    els.statusText.textContent = `Paper Trading 刷新失败：${error.message}`;
    throw error;
  } finally {
    if (els.refreshPaperBtn) {
      els.refreshPaperBtn.disabled = false;
      els.refreshPaperBtn.textContent = "刷新结果";
    }
  }
}

async function loadPositions() {
  if (!els.positionRows) return;
  if (els.refreshPositionsBtn) {
    els.refreshPositionsBtn.disabled = true;
    els.refreshPositionsBtn.textContent = "刷新中...";
  }
  if (els.positionMeta) els.positionMeta.textContent = "正在刷新持仓";
  try {
    const data = await apiJson("/api/position-management?limit=100&stake=100&book_timeout=4&max_book_age_seconds=120");
    renderPositions(data);
    const summary = data.summary || {};
    els.statusText.textContent = `持仓管理已刷新：开放 ${summary.positions ?? 0} 条，观察退出 ${summary.review ?? 0} 条`;
  } catch (error) {
    if (els.positionMeta) els.positionMeta.textContent = "刷新失败";
    els.statusText.textContent = `持仓管理刷新失败：${error.message}`;
    throw error;
  } finally {
    if (els.refreshPositionsBtn) {
      els.refreshPositionsBtn.disabled = false;
      els.refreshPositionsBtn.textContent = "刷新持仓";
    }
  }
}

async function loadCandidateReview() {
  if (!els.candidateReviewRows) return;
  const data = await apiJson("/api/candidate-review?limit=150&stake=100");
  renderCandidateReview(data);
}

async function loadCandles() {
  const data = await apiJson(`/api/candles?asset=${selectedAsset}&limit=365`);
  lastPrices = data.candles || [];
  drawPriceChart(lastPrices);
}

async function fetchRealPrices() {
  els.fetchPricesBtn.disabled = true;
  els.statusText.textContent = "正在抓取真实价格";
  try {
    const data = await apiJson("/api/fetch-crypto-prices");
    await loadDataSummary();
    await loadCandles();
    els.statusText.textContent = data.ok
      ? data.partial
        ? `已更新 ${data.candles} 根真实 K 线，部分源失败`
        : `已抓取 ${data.candles} 根真实 K 线`
      : `真实价格抓取失败，已保留本地缓存`;
  } catch (error) {
    els.statusText.textContent = `真实价格抓取失败，已保留本地缓存：${error.message}`;
  } finally {
    els.fetchPricesBtn.disabled = false;
  }
}

async function fetchRealMarkets() {
  els.fetchMarketsBtn.disabled = true;
  els.statusText.textContent = "正在抓取真实 Polymarket 市场";
  try {
    const data = await apiJson("/api/fetch-real-markets");
    await loadDataSummary();
    els.statusText.textContent = data.ok
      ? `已抓取 ${data.markets} 个真实 barrier 市场`
      : `真实市场抓取失败：${(data.errors || []).join("; ") || "无可用数据"}`;
  } catch (error) {
    els.statusText.textContent = `真实市场抓取失败：${error.message}`;
  } finally {
    els.fetchMarketsBtn.disabled = false;
  }
}

async function loadScanner() {
  els.topScanBtn.disabled = true;
  els.scanBtn.disabled = true;
  els.scannerMeta.textContent = "运行中";
  els.scannerRows.innerHTML = `<tr><td colspan="14">Scanner 正在计算盘口与模型概率...</td></tr>`;
  try {
    const data = await apiJson("/api/scanner?limit=50&edge=0.02&min_liquidity=500&simulations=800&vol_window=90d&vol_model=factor&iv_timeout=3&orderbook=1&book_limit=8&executable_notional=100&book_timeout=4&max_book_age_seconds=120&max_spread=0.04&spot=realtime&require_realtime_spot=1&spot_timeout=4&min_expiry_minutes=30");
    renderScanner(data);
    els.statusText.textContent = `Scanner 已更新：${data.summary?.candidates ?? 0} 个候选`;
  } catch (error) {
    els.scannerMeta.textContent = "失败";
    els.scannerRows.innerHTML = `<tr><td colspan="14">Scanner API 请求失败：${escapeHtml(error.message)}</td></tr>`;
    els.statusText.textContent = `Scanner 失败：${error.message}`;
  } finally {
    els.topScanBtn.disabled = false;
    els.scanBtn.disabled = false;
  }
}

async function saveObservation() {
  if (!lastScanner?.opportunities?.length) {
    els.statusText.textContent = "先运行 Scanner，再保存观测";
    return;
  }
  els.saveObservationBtn.disabled = true;
  els.statusText.textContent = "正在保存本次 scanner 观测";
  try {
    const data = await apiJson("/api/scanner-observations", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(lastScanner),
    });
    if (!data.ok) throw new Error(data.error || "save api failed");
    await Promise.all([loadObservations(), loadQualityAnalysis(), loadPaperTrading(), loadPositions(), loadCandidateReview(), loadAutomationHealth(), loadLogs()]);
    els.statusText.textContent = `已保存观测 run #${data.run_id}`;
  } catch (error) {
    els.statusText.textContent = `保存观测失败：${error.message}`;
  } finally {
    els.saveObservationBtn.disabled = false;
  }
}

async function sendReport() {
  if (!els.sendReportBtn) return;
  els.sendReportBtn.disabled = true;
  els.statusText.textContent = "正在发送飞书报告";
  try {
    const data = await apiJson("/api/send-report", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ channel: "feishu" }),
    });
    els.statusText.textContent = data.ok ? "飞书报告已发送" : "飞书报告发送失败";
    await loadLogs();
  } catch (error) {
    els.statusText.textContent = `飞书报告发送失败：${error.message}`;
    await loadLogs();
  } finally {
    els.sendReportBtn.disabled = false;
  }
}

async function loadLogs() {
  const level = els.logLevelFilter?.value || "";
  const module = els.logModuleFilter?.value || "";
  let url = "/api/logs?limit=100";
  if (level) url += `&level=${encodeURIComponent(level)}`;
  if (module) url += `&module=${encodeURIComponent(module)}`;
  try {
    const data = await apiJson(url);
    renderLogs(data.logs || [], data.total || 0);
  } catch (error) {
    if (els.logList) els.logList.innerHTML = `<div class="log-empty">日志加载失败：${escapeHtml(error.message)}</div>`;
  }
}

function renderLogs(logs, total) {
  if (!els.logList || !els.logMeta) return;
  if (els.logBadge) els.logBadge.textContent = total;
  els.logMeta.textContent = `共 ${total} 条日志` + (logs.length < total ? `，显示最新 ${logs.length} 条` : "");
  if (!logs.length) {
    els.logList.innerHTML = `<div class="log-empty">暂无日志</div>`;
    return;
  }
  const levelClass = (lvl) => {
    if (lvl === "ERROR") return "log-error";
    if (lvl === "WARN") return "log-warn";
    if (lvl === "INFO") return "log-info";
    return "log-debug";
  };
  const levelLabel = (lvl) => {
    if (lvl === "ERROR") return "ERROR";
    if (lvl === "WARN") return "WARN";
    if (lvl === "INFO") return "INFO";
    return escapeHtml(lvl || "DEBUG");
  };
  els.logList.innerHTML = logs.map((log) => {
    const dt = new Date(log.created_at).toLocaleString("zh-CN");
    return `
      <div class="log-row ${levelClass(log.level)}">
        <span class="log-time">${dt}</span>
        <span class="log-level">${levelLabel(log.level)}</span>
        <span class="log-module">[${escapeHtml(log.module)}]</span>
        <span class="log-message">${escapeHtml(log.message)}</span>
      </div>
    `;
  }).join("");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function toggleLogPanel(show) {
  if (!els.logPanel) return;
  const want = show === undefined ? !els.logPanel.classList.contains("hidden") : !show;
  els.logPanel.classList.toggle("hidden", want);
  if (!want) loadLogs();
}

async function clearLogs() {
  if (!confirm("确定要清空系统日志吗？清空后会保留一条清理记录。")) return;
  if (els.clearLogsBtn) {
    els.clearLogsBtn.disabled = true;
    els.clearLogsBtn.textContent = "清空中...";
  }
  try {
    const data = await apiJson("/api/logs/clear", { method: "POST" });
    els.statusText.textContent = data.ok ? `已清空 ${data.deleted} 条日志，当前剩余 ${data.remaining} 条` : "清理失败";
    await loadLogs();
  } catch (error) {
    els.statusText.textContent = `清理日志失败：${error.message}`;
  } finally {
    if (els.clearLogsBtn) {
      els.clearLogsBtn.disabled = false;
      els.clearLogsBtn.textContent = "清空";
    }
  }
}

async function loadDashboard() {
  els.statusText.textContent = "读取本地数据库";
  const results = await Promise.allSettled([
    loadDataSummary(),
    loadCandles(),
    loadScanner(),
    loadObservations(),
    loadAutomationHealth(),
    loadQualityAnalysis(),
    loadPaperTrading(),
    loadPositions(),
    loadCandidateReview(),
    loadLogs(),
    loadVersion(),
  ]);
  const failed = results.filter((result) => result.status === "rejected");
  if (failed.length) {
    els.statusText.textContent = `刷新完成，${failed.length} 个模块失败`;
  }
}

els.refreshBtn.addEventListener("click", loadDashboard);
els.fetchPricesBtn.addEventListener("click", fetchRealPrices);
els.fetchMarketsBtn.addEventListener("click", fetchRealMarkets);
els.scanBtn.addEventListener("click", loadScanner);
els.topScanBtn.addEventListener("click", () => {
  setActiveView("scanner");
  loadScanner();
});
if (els.saveObservationBtn) els.saveObservationBtn.addEventListener("click", saveObservation);
if (els.refreshHealthBtn) els.refreshHealthBtn.addEventListener("click", loadAutomationHealth);
if (els.refreshQualityBtn) els.refreshQualityBtn.addEventListener("click", loadQualityAnalysis);
if (els.refreshPaperBtn) els.refreshPaperBtn.addEventListener("click", loadPaperTrading);
if (els.refreshPositionsBtn) els.refreshPositionsBtn.addEventListener("click", loadPositions);
if (els.refreshCandidateReviewBtn) els.refreshCandidateReviewBtn.addEventListener("click", loadCandidateReview);
if (els.sendReportBtn) els.sendReportBtn.addEventListener("click", sendReport);
if (els.logBtn) els.logBtn.addEventListener("click", () => toggleLogPanel(true));
if (els.logPanelClose) els.logPanelClose.addEventListener("click", () => toggleLogPanel(false));
if (els.logPanel) els.logPanel.addEventListener("click", (e) => { if (e.target === els.logPanel) toggleLogPanel(false); });
if (els.refreshLogsBtn) els.refreshLogsBtn.addEventListener("click", loadLogs);
if (els.clearLogsBtn) els.clearLogsBtn.addEventListener("click", clearLogs);
if (els.logLevelFilter) els.logLevelFilter.addEventListener("change", loadLogs);
if (els.logModuleFilter) els.logModuleFilter.addEventListener("change", loadLogs);
document.querySelectorAll(".scanner-table th.sortable").forEach((th) => {
  th.addEventListener("click", () => {
    const field = th.dataset.sort;
    if (!field) return;
    if (scannerSort.field === field) {
      scannerSort.dir = scannerSort.dir === "asc" ? "desc" : "asc";
    } else {
      scannerSort = { field, dir: "asc" };
    }
    if (lastScanner) renderScanner(lastScanner);
  });
});

document.querySelectorAll(".view-tab").forEach((button) => {
  button.addEventListener("click", () => setActiveView(button.dataset.viewTab));
});

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
setActiveView((window.location.hash || "#overview").replace("#", ""));
loadDashboard();
