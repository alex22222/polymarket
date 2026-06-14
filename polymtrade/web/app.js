const els = {
  topScanBtn: document.getElementById("topScanBtn"),
  refreshBtn: document.getElementById("refreshBtn"),
  metricsPanel: document.getElementById("metricsPanel"),
  statusText: document.getElementById("statusText"),
  versionBadge: document.getElementById("versionBadge"),
  dataTrustBadge: document.getElementById("dataTrustBadge"),
  btcTickerPrice: document.getElementById("btcTickerPrice"),
  btcTickerChange: document.getElementById("btcTickerChange"),
  btcTickerSparkline: document.getElementById("btcTickerSparkline"),
  ethTickerPrice: document.getElementById("ethTickerPrice"),
  ethTickerChange: document.getElementById("ethTickerChange"),
  ethTickerSparkline: document.getElementById("ethTickerSparkline"),
  priceChart: document.getElementById("priceChart"),
  edgeChart: document.getElementById("edgeChart"),
  edgeOutliers: document.getElementById("edgeOutliers"),
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
  macroMeta: document.getElementById("macroMeta"),
  macroActive: document.getElementById("macroActive"),
  macroUpcoming: document.getElementById("macroUpcoming"),
  macroHighImpact: document.getElementById("macroHighImpact"),
  macroSource: document.getElementById("macroSource"),
  macroRows: document.getElementById("macroRows"),
  refreshMacroBtn: document.getElementById("refreshMacroBtn"),
  reflectionMeta: document.getElementById("reflectionMeta"),
  reflectionRuns: document.getElementById("reflectionRuns"),
  reflectionTodos: document.getElementById("reflectionTodos"),
  reflectionOpen: document.getElementById("reflectionOpen"),
  reflectionDone: document.getElementById("reflectionDone"),
  reflectionRows: document.getElementById("reflectionRows"),
  refreshReflectionBtn: document.getElementById("refreshReflectionBtn"),
  shadowMeta: document.getElementById("shadowMeta"),
  shadowSamples: document.getElementById("shadowSamples"),
  shadowValidation: document.getElementById("shadowValidation"),
  shadowBrierDelta: document.getElementById("shadowBrierDelta"),
  shadowDecision: document.getElementById("shadowDecision"),
  shadowBuckets: document.getElementById("shadowBuckets"),
  shadowRuns: document.getElementById("shadowRuns"),
  shadowInsight: document.getElementById("shadowInsight"),
  refreshShadowBtn: document.getElementById("refreshShadowBtn"),
  calibrationMeta: document.getElementById("calibrationMeta"),
  calibrationSamples: document.getElementById("calibrationSamples"),
  calibrationResolved: document.getElementById("calibrationResolved"),
  calibrationModelBrier: document.getElementById("calibrationModelBrier"),
  calibrationMarketBrier: document.getElementById("calibrationMarketBrier"),
  calibrationRows: document.getElementById("calibrationRows"),
  attributionRows: document.getElementById("attributionRows"),
  calibrationRecentRows: document.getElementById("calibrationRecentRows"),
  refreshCalibrationBtn: document.getElementById("refreshCalibrationBtn"),
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
  realPositionMeta: document.getElementById("realPositionMeta"),
  realPositionRows: document.getElementById("realPositionRows"),
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
  tradeMeta: document.getElementById("tradeMeta"),
  tradeModeStatus: document.getElementById("tradeModeStatus"),
  tradeDraftCount: document.getElementById("tradeDraftCount"),
  tradeDraftRows: document.getElementById("tradeDraftRows"),
  tradeMasterSwitch: document.getElementById("tradeMasterSwitch"),
  refreshTradeDraftsBtn: document.getElementById("refreshTradeDraftsBtn"),
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
  scannerNear: document.getElementById("scannerNear"),
  scannerResearch: document.getElementById("scannerResearch"),
  scannerStatus: document.getElementById("scannerStatus"),
  scannerTierBoard: document.getElementById("scannerTierBoard"),
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
let lastPositionData = null;
let lastRealPositionData = null;
let lastTickers = [];
let edgeChartPoints = [];
let edgeChartHoverId = null;
let scannerSort = { field: null, dir: "asc" };
let activeView = "overview";
let activeValidationPanel = "positions";
let tradingEnabled = localStorage.getItem("polymtradeTradingEnabled") === "1";

function percent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `${(Number(value) * 100).toFixed(2)}%`;
}

function money(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  const amount = Number(value);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: Math.abs(amount) < 10 ? 2 : 0,
  }).format(amount);
}

function compactMoney(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  const amount = Number(value);
  if (Math.abs(amount) >= 1_000_000_000) return `$${(amount / 1_000_000_000).toFixed(2)}B`;
  if (Math.abs(amount) >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
  if (Math.abs(amount) >= 1_000) return `$${(amount / 1_000).toFixed(1)}K`;
  return money(amount);
}

function marketMoney(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  const amount = Number(value);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: amount >= 1000 ? 0 : 2,
  }).format(amount);
}

function edgeDislocation(row) {
  const model = Number(row.model_probability);
  const market = Number(row.market_yes_price);
  if (!Number.isFinite(model) || !Number.isFinite(market)) return 0;
  return Math.abs(model - market);
}

function shortQuestion(text, max = 72) {
  const value = String(text || "");
  return value.length > max ? `${value.slice(0, max - 1)}…` : value;
}

function edgeRowId(row) {
  return String(row?.market_id || row?.question || "");
}

function roundedRect(ctx, x, y, width, height, radius) {
  if (typeof ctx.roundRect === "function") {
    ctx.roundRect(x, y, width, height, radius);
    return;
  }
  const r = Math.min(radius, width / 2, height / 2);
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + width - r, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + r);
  ctx.lineTo(x + width, y + height - r);
  ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
  ctx.lineTo(x + r, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
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

function renderRealPositionsError(error) {
  if (els.realPositionMeta) els.realPositionMeta.textContent = "真实持仓刷新失败";
  if (!els.realPositionRows) return;
  els.realPositionRows.innerHTML = `
    <div class="coverage-row">
      <strong>真实持仓暂不可用</strong>
      <span>${escapeHtml(error?.message || "请求失败，请稍后重试。")}</span>
    </div>
  `;
}

function signedPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  const cls = Number(value) >= 0 ? "positive" : "negative";
  return `<span class="${cls}">${percent(value)}</span>`;
}

function signedPercentText(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `${Number(value) >= 0 ? "+" : ""}${percent(value)}`;
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

function tierCell(row) {
  const tier = row.opportunity_tier || "ignore";
  const label = row.opportunity_tier_label || tier;
  const cls = {
    candidate: "positive-pill",
    near: "warning-pill",
    research: "neutral-pill",
    blocked: "negative-pill",
  }[tier] || "neutral-pill";
  return `<span class="pill ${cls}">${escapeHtml(label)}</span><small>${escapeHtml(row.opportunity_tier_reason || "")}</small>`;
}

function opportunityBucket(row) {
  const tier = row.opportunity_tier || "";
  const passed = row.review_status === "passed";
  if (tier === "candidate" && row.action === "candidate" && passed) {
    return "candidate";
  }
  if (tier === "near" || row.action === "verify" || row.review_status === "verify") {
    return "near";
  }
  if (tier === "research" || row.action === "watch") {
    return "research";
  }
  return "blocked";
}

function opportunityBucketLabel(bucket) {
  return {
    candidate: "候选",
    near: "准候选",
    research: "研究机会",
    blocked: "阻断",
  }[bucket] || "其他";
}

function opportunityBucketHint(bucket) {
  return {
    candidate: "可以进入 Paper Trading / 交易控制台；仍需人工确认盘口和限价。",
    near: "有接近机会，但 edge 或盘口条件未完全达标；观察，不交易。",
    research: "模型和市场有分歧，但执行条件不过；用于复盘训练。",
    blocked: "到期、盘口、流动性或复核条件不通过；不交易。",
  }[bucket] || "";
}

function renderScannerTierBoard(rows) {
  if (!els.scannerTierBoard) return;
  const counts = { candidate: 0, near: 0, research: 0 };
  rows.forEach((row) => {
    const bucket = opportunityBucket(row);
    if (counts[bucket] !== undefined) counts[bucket] += 1;
  });
  const cards = [
    ["candidate", "候选", "净 edge ≥ 2% 且盘口通过，可进入 Paper / 半自动草稿。"],
    ["near", "准候选", "净 edge 1%-2% 或盘口小问题，只观察不交易。"],
    ["research", "研究机会", "模型和市场有分歧，但执行条件不过，用于复盘。"],
  ];
  els.scannerTierBoard.innerHTML = cards
    .map(([bucket, label, hint]) => `
      <article class="tier-card tier-card-${bucket}">
        <span>${label}</span>
        <strong>${counts[bucket] || 0}</strong>
        <small>${hint}</small>
      </article>
    `)
    .join("");
}

function tradeDirectionCell(row) {
  const label = row.direction_label || (row.direction === "hit_below" ? "下破" : "上破");
  const recommendation = row.trade_recommendation || `买 YES ${label}`;
  const cls = row.action === "candidate" ? "positive-pill" : row.opportunity_tier === "near" ? "warning-pill" : "neutral-pill";
  const relation = row.direction === "hit_below"
    ? `YES = ${money(row.spot)} 跌到/跌破 ${money(row.barrier)}`
    : `YES = ${money(row.spot)} 涨到/涨破 ${money(row.barrier)}`;
  const noMeaning = row.direction === "hit_below" ? "NO = 不下破" : "NO = 不上破";
  return `<span class="pill ${cls}">${escapeHtml(recommendation)}</span><small>${escapeHtml(relation)}</small><small>${escapeHtml(noMeaning)}</small>`;
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
  const macroMultiplier = Number(row.vol_components?.macro_multiplier || 1);
  const macroVol = Number.isFinite(macroMultiplier) && macroMultiplier > 1 ? ` · macro×${macroMultiplier.toFixed(2)}` : "";
  const ciLow = Number(row.model_probability_ci_low);
  const ciHigh = Number(row.model_probability_ci_high);
  const edgeCiLow = Number(row.net_edge_ci_low);
  const edgeCiHigh = Number(row.net_edge_ci_high);
  const probabilityCi = Number.isFinite(ciLow) && Number.isFinite(ciHigh) && Math.abs(ciHigh - ciLow) > 0.000001
    ? `CI ${percent(ciLow)}-${percent(ciHigh)}`
    : "";
  const mcProbability = Number(row.mc_probability);
  const mcDiff = Number(row.mc_probability_diff);
  const mcText = Number.isFinite(mcProbability)
    ? `MC ${percent(mcProbability)}${Number.isFinite(mcDiff) ? ` Δ${signedPercentText(mcDiff)}` : ""}`
    : "";
  const drift = Number(row.drift);
  const driftText = Number.isFinite(drift) && Math.abs(drift) > 0.001 ? `drift ${signedPercentText(drift)}` : "";
  const edgeCi = Number.isFinite(edgeCiLow) && Number.isFinite(edgeCiHigh)
    ? `edgeCI ${signedPercentText(edgeCiLow)}-${signedPercentText(edgeCiHigh)}`
    : "";
  const state = row.market_state || {};
  const short = state.short_term?.["5m"] || {};
  const funding = state.funding || {};
  const oi = state.open_interest || {};
  const tags = (row.factor_signals || state.signals || []).slice(0, 2).join(" / ");
  const macro = row.macro_risk || {};
  const macroLabels = (row.macro_event_labels || macro.labels || []).slice(0, 2).join(" / ");
  const factors = [
    `1h ${signedPercentText(short.momentum_1h)}`,
    `4h ${signedPercentText(short.momentum_4h)}`,
    `RV5m ${percent(short.rv)}`,
    `fund ${signedPercentText(funding.funding_rate)}`,
    `OI ${signedPercentText(oi.open_interest_change)}`,
  ].join(" · ");
  const macroText = macro.risk_level && macro.risk_level !== "normal" ? `macro ${macro.risk_level}${macroLabels ? ` · ${macroLabels}` : ""}` : "";
  return `${percent(row.model_probability)}<small>${escapeHtml(row.model_probability_method || "model")} · ${escapeHtml(source)} · vol ${vol}${iv}${macroVol}</small>${probabilityCi || edgeCi ? `<small>${escapeHtml([probabilityCi, edgeCi].filter(Boolean).join(" · "))}</small>` : ""}${mcText || driftText ? `<small>${escapeHtml([mcText, driftText].filter(Boolean).join(" · "))}</small>` : ""}<small>${escapeHtml(factors)}</small>${tags ? `<small>${escapeHtml(tags)}</small>` : ""}${macroText ? `<small>${escapeHtml(macroText)}</small>` : ""}`;
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

function compactContextSourceLabel(contexts = {}) {
  const items = Object.values(contexts);
  if (!items.length) return "--";
  const assets = items.map((item) => item.asset).join("/");
  const live = items.every((item) => item.spot_is_realtime) ? "live" : "daily";
  const sources = [...new Set(items.map((item) => String(item.source || "").toLowerCase()))];
  let source = sources.length === 1 ? sources[0] : "mixed";
  if (source.includes("binance")) source = "Binance";
  else if (source.includes("okx")) source = "OKX";
  else if (source === "mixed") source = "mixed";
  else source = source.replace(/-ticker$/, "") || "source";
  return `${assets} · ${source} · ${live}`;
}

function contextFactorLabel(context) {
  if (!context) return "--";
  const state = context.market_state || {};
  const short = state.short_term?.["5m"] || {};
  const funding = state.funding || {};
  const oi = state.open_interest || {};
  const macro = context.macro || {};
  const shortLabel = short.error
    ? "1h -- · RV --"
    : `1h ${signedPercentText(short.momentum_1h)} · RV ${percent(short.rv)}`;
  const fundingLabel = funding.error ? "fund --" : `fund ${signedPercentText(funding.funding_rate)}`;
  const oiLabel = oi.error ? "OI --" : `OI ${signedPercentText(oi.open_interest_change)}`;
  const signals = (state.signals || []).slice(0, 2).join(" / ");
  const activeMacro = macro.active_count ? `macro ${macro.active_count}` : macro.upcoming_count ? `macro ${macro.upcoming_count}` : "macro 0";
  return `${shortLabel} · ${fundingLabel} · ${oiLabel} · ${activeMacro}${signals ? ` · ${signals}` : ""}`;
}

function renderValidationPanel() {
  const allowedPanels = new Set(["positions", "paper", "review", "calibration", "shadow", "quality", "reflection", "observations"]);
  if (!allowedPanels.has(activeValidationPanel)) activeValidationPanel = "positions";
  document.querySelectorAll("[data-validation-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.validationTab === activeValidationPanel);
  });
  document.querySelectorAll("[data-validation-panel]").forEach((section) => {
    const isVisible = activeView === "validation" && section.dataset.validationPanel === activeValidationPanel;
    section.classList.toggle("hidden", !isVisible);
  });
}

function setActiveView(view) {
  const legacyViews = { analysis: "validation", research: "validation" };
  view = legacyViews[view] || view;
  const allowed = new Set(["overview", "scanner", "trading", "validation", "system"]);
  activeView = allowed.has(view) ? view : "overview";
  document.querySelectorAll(".view-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.viewTab === activeView);
  });
  document.querySelectorAll(".view-section").forEach((section) => {
    if (section.dataset.validationPanel) return;
    section.classList.toggle("hidden", section.dataset.view !== activeView);
  });
  if (els.metricsPanel) {
    els.metricsPanel.classList.toggle("hidden", activeView === "overview" || activeView === "system");
  }
  renderValidationPanel();
  window.location.hash = activeView === "validation" ? `validation:${activeValidationPanel}` : activeView;
  if (activeView === "overview") {
    drawPriceChart(lastPrices);
  }
  if (activeView === "scanner") {
    drawEdgeChart(lastScanner?.opportunities || []);
  }
  if (activeView === "trading") {
    renderTradeConsole();
  }
}

function setActiveValidationPanel(panel) {
  activeValidationPanel = panel;
  if (activeView !== "validation") {
    setActiveView("validation");
    return;
  }
  renderValidationPanel();
  window.location.hash = `validation:${activeValidationPanel}`;
}

function initialViewFromHash() {
  const raw = (window.location.hash || "#overview").replace("#", "");
  const [view, panel] = raw.split(":");
  if (panel) activeValidationPanel = panel;
  return view;
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

function drawSparkline(canvas, candles = [], price = null, tone = "neutral") {
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(120, Math.floor((rect.width || 180) * dpr));
  const height = Math.max(42, Math.floor((rect.height || 54) * dpr));
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  const w = width / dpr;
  const h = height / dpr;
  ctx.clearRect(0, 0, w, h);
  const values = candles.map((item) => Number(item.close)).filter(Number.isFinite).slice(-48);
  const live = Number(price);
  if (Number.isFinite(live)) {
    if (values.length) values[values.length - 1] = live;
    else values.push(live);
  }
  if (values.length < 2) {
    ctx.fillStyle = "#65736d";
    ctx.font = "12px system-ui";
    ctx.fillText("暂无走势", 10, h / 2 + 4);
    return;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(1, max - min);
  const pad = 5;
  const xFor = (index) => pad + ((w - pad * 2) * index) / Math.max(1, values.length - 1);
  const yFor = (value) => h - pad - ((h - pad * 2) * (value - min)) / range;
  const color = tone === "up" ? "#0f7a55" : tone === "down" ? "#b4233a" : "#2757a7";
  const gradient = ctx.createLinearGradient(0, 0, 0, h);
  gradient.addColorStop(0, tone === "down" ? "rgba(180,35,58,0.18)" : "rgba(15,122,85,0.18)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  ctx.beginPath();
  values.forEach((value, index) => {
    const x = xFor(index);
    const y = yFor(value);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.lineTo(xFor(values.length - 1), h - pad);
  ctx.lineTo(xFor(0), h - pad);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();
  ctx.beginPath();
  values.forEach((value, index) => {
    const x = xFor(index);
    const y = yFor(value);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.stroke();
}

function renderTicker(ticker) {
  const asset = String(ticker.asset || "").toUpperCase();
  const priceEl = asset === "BTC" ? els.btcTickerPrice : els.ethTickerPrice;
  const changeEl = asset === "BTC" ? els.btcTickerChange : els.ethTickerChange;
  const canvas = asset === "BTC" ? els.btcTickerSparkline : els.ethTickerSparkline;
  const card = document.querySelector(`[data-ticker-card="${asset}"]`);
  if (!priceEl || !changeEl) return;
  const changePct = Number(ticker.change_pct);
  const tone = Number.isFinite(changePct) && changePct > 0 ? "up" : Number.isFinite(changePct) && changePct < 0 ? "down" : "neutral";
  priceEl.textContent = marketMoney(ticker.price);
  changeEl.textContent = Number.isFinite(changePct)
    ? `${signedPercentText(changePct)} · ${ticker.is_realtime ? "实时" : "缓存"} · ${ticker.source || "--"}`
    : `${ticker.is_realtime ? "实时" : "缓存"} · ${ticker.source || "--"}`;
  changeEl.className = tone === "up" ? "positive" : tone === "down" ? "negative" : "";
  if (card) {
    card.classList.toggle("market-up", tone === "up");
    card.classList.toggle("market-down", tone === "down");
  }
  drawSparkline(canvas, ticker.candles || [], ticker.price, tone);
}

async function loadMarketTickers() {
  const data = await apiJson("/api/crypto-tickers?assets=BTC,ETH&limit=60&timeout=3");
  lastTickers = data.tickers || [];
  lastTickers.forEach(renderTicker);
}

function renderDataTrust(data = {}) {
  if (!els.dataTrustBadge) return;
  const status = data.status || "unknown";
  const label = status === "healthy" ? "数据正常" : status === "degraded" ? "数据降级" : status === "blocked" ? "数据阻断" : "数据未知";
  const components = data.components || [];
  const summary = components.map((item) => `${item.label}:${item.summary}`).join(" · ");
  const detail = components.map((item) => `${item.label} ${item.status} - ${item.detail || item.summary}`).join("\n");
  els.dataTrustBadge.textContent = summary ? `${label} · ${summary}` : label;
  els.dataTrustBadge.title = detail || "暂无数据可信状态";
  els.dataTrustBadge.classList.toggle("healthy", status === "healthy");
  els.dataTrustBadge.classList.toggle("degraded", status === "degraded");
  els.dataTrustBadge.classList.toggle("blocked", status === "blocked");
}

async function loadDataTrust() {
  const data = await apiJson("/api/data-trust");
  renderDataTrust(data);
}

function drawEdgeChart(rows) {
  const canvas = els.edgeChart;
  edgeChartPoints = [];
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

  const outliers = [...validRows].sort((a, b) => edgeDislocation(b) - edgeDislocation(a)).slice(0, 5);
  const outlierIds = new Map(outliers.map((row, index) => [edgeRowId(row), index + 1]));

  validRows.forEach((row) => {
    const x = xFor(Number(row.market_yes_price));
    const y = yFor(Number(row.model_probability));
    const pointId = edgeRowId(row);
    const outlierRank = outlierIds.get(pointId);
    const radius = row.action === "candidate" ? 6 : row.action === "verify" ? 5 : 4;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = row.action === "candidate" ? "#0f7a55" : row.action === "verify" ? "#8a5a00" : row.net_edge < 0 ? "#b4233a" : "#2757a7";
    ctx.globalAlpha = row.action === "avoid" ? 0.35 : 0.82;
    ctx.fill();
    ctx.globalAlpha = 1;
    if (outlierRank) {
      ctx.fillStyle = "#17201c";
      ctx.font = "bold 11px system-ui";
      ctx.fillText(String(outlierRank), x + radius + 3, y - radius - 2);
    }
    edgeChartPoints.push({ x, y, radius: Math.max(radius + 6, 12), row, outlierRank });
  });

  const hovered = edgeChartHoverId
    ? edgeChartPoints.find((point) => edgeRowId(point.row) === edgeChartHoverId)
    : null;
  if (hovered) {
    const row = hovered.row;
    ctx.beginPath();
    ctx.arc(hovered.x, hovered.y, hovered.radius - 2, 0, Math.PI * 2);
    ctx.strokeStyle = "#17201c";
    ctx.lineWidth = 2;
    ctx.stroke();
    const detail = [
      `${row.trade_recommendation || (row.direction === "hit_below" ? "买 YES 下破" : "买 YES 上破")} · ${row.asset}`,
      `市场 ${percent(row.market_yes_price)} / 模型 ${percent(row.model_probability)} / 差异 ${signedPercentText(row.model_probability - row.market_yes_price)}`,
      shortQuestion(row.question, 54),
    ];
    const boxWidth = Math.min(430, width - pad * 2);
    const boxHeight = 74;
    const boxX = Math.min(width - pad - boxWidth, Math.max(pad, hovered.x + 14));
    const boxY = Math.min(height - pad - boxHeight, Math.max(pad, hovered.y - boxHeight - 14));
    ctx.fillStyle = "rgba(255, 255, 255, 0.96)";
    ctx.strokeStyle = "#d6dfda";
    ctx.lineWidth = 1;
    ctx.beginPath();
    roundedRect(ctx, boxX, boxY, boxWidth, boxHeight, 8);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#17201c";
    ctx.font = "bold 12px system-ui";
    ctx.fillText(detail[0], boxX + 10, boxY + 20);
    ctx.font = "12px system-ui";
    ctx.fillText(detail[1], boxX + 10, boxY + 42);
    ctx.fillStyle = "#65736d";
    ctx.fillText(detail[2], boxX + 10, boxY + 62);
  }

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
  renderEdgeOutliers(outliers);
}

function renderEdgeOutliers(rows) {
  if (!els.edgeOutliers) return;
  if (!rows.length) {
    els.edgeOutliers.innerHTML = `<div class="edge-outlier-empty">暂无模型与市场分歧点</div>`;
    return;
  }
  els.edgeOutliers.innerHTML = rows
    .map((row, index) => {
      const id = escapeHtml(edgeRowId(row));
      const gap = Number(row.model_probability) - Number(row.market_yes_price);
      const active = edgeChartHoverId === edgeRowId(row) ? " active" : "";
      const explanation = edgeOutlierExplanation(row, gap);
      return `
        <button class="edge-outlier${active}" data-edge-id="${id}">
          <span class="edge-rank">图 ${index + 1}</span>
          <strong>${escapeHtml(row.trade_recommendation || (row.direction === "hit_below" ? "买 YES 下破" : "买 YES 上破"))}</strong>
          <span>${escapeHtml(row.asset)} · 市场 ${percent(row.market_yes_price)} · 模型 ${percent(row.model_probability)} · 差异 ${signedPercentText(gap)}</span>
          <small>${escapeHtml(shortQuestion(row.question, 92))}</small>
          <span class="edge-explain">${escapeHtml(explanation)}</span>
        </button>
      `;
    })
    .join("");
}

function edgeOutlierExplanation(row, gap) {
  const recommendation = row.trade_recommendation || (row.direction === "hit_below" ? "买 YES 下破" : "买 YES 上破");
  const absGap = Math.abs(Number(gap) || 0);
  const edgeText = gap >= 0
    ? `模型比市场高 ${percent(absGap)}，意思是系统认为这边价格可能被低估。`
    : `模型比市场低 ${percent(absGap)}，意思是系统认为市场可能太乐观。`;
  const actionText = String(row.action || row.opportunity_tier || "").toLowerCase();
  const discipline = actionText === "candidate"
    ? "执行条件相对干净，可以优先复核盘口和滑点。"
    : actionText === "verify" || actionText === "near"
      ? "还没到直接交易级别，更适合继续观察。"
      : "这更像研究样本，不应只因为偏离大就交易。";
  const drift = Number(row.drift);
  const driftText = Number.isFinite(drift) && Math.abs(drift) > 0.02
    ? drift > 0
      ? "趋势项偏顺风。"
      : "趋势项偏逆风。"
    : "趋势项没有给出很强方向。";
  const state = row.market_state || {};
  const short = state.short_term?.["5m"] || {};
  const momentum1h = Number(short.momentum_1h);
  const momentum4h = Number(short.momentum_4h);
  const momentumText = Number.isFinite(momentum1h) || Number.isFinite(momentum4h)
    ? `短线动能：1h ${signedPercentText(momentum1h)}，4h ${signedPercentText(momentum4h)}。`
    : "";
  const macro = row.macro_risk || {};
  const labels = (row.macro_event_labels || macro.labels || []).slice(0, 2).join(" / ");
  const macroText = macro.risk_level && macro.risk_level !== "normal"
    ? `宏观风险偏高${labels ? `，附近有 ${labels}` : ""}。`
    : "宏观事件压力不明显。";
  return `${edgeText} 建议方向是“${recommendation}”。${discipline} ${driftText} ${momentumText} ${macroText}`;
}

function edgePointAtEvent(event) {
  const rect = els.edgeChart.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  return edgeChartPoints.find((point) => Math.hypot(point.x - x, point.y - y) <= point.radius);
}

function scrollToScannerRow(edgeId) {
  if (!edgeId || !els.scannerRows) return;
  const row = [...els.scannerRows.querySelectorAll("[data-edge-id]")].find((item) => item.dataset.edgeId === edgeId);
  if (!row) return;
  row.scrollIntoView({ behavior: "smooth", block: "center" });
  row.classList.remove("scanner-row-highlight");
  window.requestAnimationFrame(() => {
    row.classList.add("scanner-row-highlight");
    window.setTimeout(() => row.classList.remove("scanner-row-highlight"), 1800);
  });
}

function renderCoverage(candleRows, marketRows = [], priceHistoryRows = []) {
  if (!candleRows.length && !marketRows.length && !priceHistoryRows.length) {
    els.coverageRows.innerHTML = `<div class="coverage-row"><strong>暂无真实数据</strong><span>请抓取真实价格或真实市场。</span></div>`;
    return;
  }
  const candles = candleRows
    .map(
      (row) => {
        const status = row.selected ? "推荐源" : row.status === "stale" ? "过期源" : "备用源";
        const statusClass = row.selected ? "source-ok" : row.status === "stale" ? "source-warn" : "source-muted";
        const stale = row.stale_days === null || row.stale_days === undefined ? "--" : `${row.stale_days}d`;
        return `
        <div class="coverage-row">
          <strong><span>${escapeHtml(row.asset)} / ${escapeHtml(row.source)}</span><span class="source-status ${statusClass}">${status}</span></strong>
          <span>${new Date(row.first_ts).toLocaleDateString()} 至 ${new Date(row.last_ts).toLocaleDateString()}</span>
          <span>${row.candles} 根 · latest ${money(row.latest_close)} · stale ${stale} · ${row.interval}</span>
        </div>
      `;
      },
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

function impactPill(impact) {
  if (impact === "high") return `<span class="pill negative-pill">高影响</span>`;
  if (impact === "medium") return `<span class="pill warning-pill">中影响</span>`;
  return `<span class="pill neutral-pill">低影响</span>`;
}

const macroTypeLabels = {
  cpi: "通胀",
  fomc: "美联储",
  employment: "就业",
  gdp: "GDP",
  macro: "宏观",
};

const macroTitleTranslations = {
  "US Employment Situation": "美国就业报告",
  "US CPI": "美国 CPI 通胀数据",
  "FOMC Statement": "美联储 FOMC 利率声明",
  "FOMC Press Conference": "美联储主席新闻发布会",
  "US GDP": "美国 GDP 数据",
};

const macroNoteTranslations = {
  "Monthly nonfarm payrolls and unemployment rate.": "月度非农就业和失业率数据，通常会影响美元、利率预期和风险资产。",
  "Monthly CPI release; can raise short-term jump risk.": "月度通胀数据，可能改变降息预期，并提高 BTC / ETH 短时跳变风险。",
  "Policy statement and rate decision.": "利率决议和政策声明，直接影响美元流动性、收益率和风险偏好。",
  "Chair press conference; can move rates, USD, equities, and crypto.": "主席问答可能引发利率、美元、美股和加密资产的二次波动。",
  "GDP release; lower immediate crypto impact than CPI/FOMC/NFP.": "经济增长数据，通常短线冲击低于 CPI、FOMC 和非农，但会影响宏观叙事。",
};

function macroTitle(event) {
  return event.title_zh || macroTitleTranslations[event.title] || event.title || "--";
}

function macroNotes(event) {
  return event.notes_zh || macroNoteTranslations[event.notes] || event.notes || "";
}

function macroTypeLabel(type) {
  return macroTypeLabels[type] || type || "宏观";
}

function formatMacroDistance(hoursUntil) {
  const value = Number(hoursUntil);
  if (!Number.isFinite(value)) return "--";
  const days = value / 24;
  if (Math.abs(days) < 0.05) return value >= 0 ? "今天" : "刚过去";
  if (days < 0) return `已过 ${Math.abs(days).toFixed(1)} 天`;
  return `${days.toFixed(1)} 天`;
}

function compactMacroSourceLabel(source) {
  const value = String(source || "").trim();
  if (!value) return "--";
  if (value.includes("macro_events")) return "本地事件表";
  if (/^https?:\/\//i.test(value)) {
    try {
      return new URL(value).hostname.replace(/^www\./, "");
    } catch (error) {
      return "外部事件源";
    }
  }
  const filename = value.split(/[\\/]/).filter(Boolean).pop();
  return filename || value;
}

function renderMacroEvents(data = {}) {
  const events = data.upcoming || [];
  const active = data.active || [];
  const highImpact = [...events, ...active].filter((event) => event.impact === "high").length;
  if (els.macroMeta) {
    const generated = data.generated_at ? new Date(data.generated_at).toLocaleString("zh-CN") : "--";
    els.macroMeta.textContent = `未来 ${(Number(data.horizon_hours || 0) / 24).toFixed(0)} 天 · 生成 ${generated}`;
  }
  if (els.macroActive) els.macroActive.textContent = active.length;
  if (els.macroUpcoming) els.macroUpcoming.textContent = events.length;
  if (els.macroHighImpact) els.macroHighImpact.textContent = highImpact;
  if (els.macroSource) {
    els.macroSource.textContent = compactMacroSourceLabel(data.source);
    els.macroSource.title = data.source || "";
  }
  if (!els.macroRows) return;
  if (!events.length && !active.length) {
    els.macroRows.innerHTML = `<div class="coverage-row"><strong>暂无宏观事件</strong><span>当前窗口内没有配置的 CPI / FOMC / 非农 / GDP。</span></div>`;
    return;
  }
  const rowMap = new Map();
  [...events.map((event) => ({ ...event, active: false })), ...active.map((event) => ({ ...event, active: true }))].forEach((event) => {
    rowMap.set(event.id || `${event.title}-${event.scheduled_at}`, event);
  });
  const rows = Array.from(rowMap.values()).sort((a, b) => {
    if (a.active !== b.active) return a.active ? -1 : 1;
    return Number(a.hours_until || 0) - Number(b.hours_until || 0);
  });
  els.macroRows.innerHTML = rows
    .map((event) => {
      const at = event.scheduled_at ? new Date(event.scheduled_at).toLocaleString("zh-CN") : "--";
      const distance = formatMacroDistance(event.hours_until);
      const title = macroTitle(event);
      const notes = macroNotes(event);
      const sourceSummary = event.source_summary_zh || "";
      const sourceLabel = event.source ? `来源：${event.source}` : "来源：manual";
      return `
        <div class="macro-row">
          <strong>
            <span>${escapeHtml(title)}</span>
            ${impactPill(event.impact)}
          </strong>
          <span>${event.active ? "活跃窗口" : "未来事件"} · ${escapeHtml(macroTypeLabel(event.type))} · 距离 ${escapeHtml(distance)}</span>
          <span>${escapeHtml(at)} · ${escapeHtml(sourceLabel)} ${externalLink(event.source_url, "官方链接")}</span>
          <span>${escapeHtml(notes)}</span>
          ${sourceSummary ? `<span>${escapeHtml(sourceSummary)}</span>` : ""}
        </div>
      `;
    })
    .join("");
}

function reflectionStatusLabel(status) {
  const labels = {
    open: "待处理",
    adopted: "已采纳",
    doing: "执行中",
    done: "已完成",
    dismissed: "已忽略",
  };
  return labels[status] || status || "--";
}

function reflectionStatusClass(status) {
  if (status === "done") return "done";
  if (status === "dismissed") return "dismissed";
  if (status === "doing") return "doing";
  if (status === "adopted") return "adopted";
  return "open";
}

function renderReflectionTodos(data = {}) {
  if (!els.reflectionRows) return;
  const summary = data.summary || {};
  const byStatus = Object.fromEntries((summary.by_status || []).map((row) => [row.status, row.count]));
  const openCount = (byStatus.open || 0) + (byStatus.adopted || 0) + (byStatus.doing || 0);
  if (els.reflectionRuns) els.reflectionRuns.textContent = summary.reflections ?? 0;
  if (els.reflectionTodos) els.reflectionTodos.textContent = summary.todos ?? 0;
  if (els.reflectionOpen) els.reflectionOpen.textContent = openCount;
  if (els.reflectionDone) els.reflectionDone.textContent = byStatus.done || 0;
  const latest = (data.reflections || [])[0];
  if (els.reflectionMeta) {
    const dt = latest?.generated_at ? new Date(latest.generated_at).toLocaleString("zh-CN") : "--";
    els.reflectionMeta.textContent = latest ? `最新日报 ${latest.reflection_date} · ${dt}` : "暂无日报";
  }
  const rows = data.todos || [];
  if (!rows.length) {
    els.reflectionRows.innerHTML = `<div class="coverage-row"><strong>暂无 TODO</strong><span>下一次每日反思后会自动生成。</span></div>`;
    return;
  }
  els.reflectionRows.innerHTML = rows.map((row) => {
    const dt = row.updated_at ? new Date(row.updated_at).toLocaleString("zh-CN") : "--";
    const active = row.status !== "done" && row.status !== "dismissed";
    return `
      <article class="reflection-row ${reflectionStatusClass(row.status)}">
        <div class="reflection-main">
          <div class="reflection-title">
            <span class="priority-pill">${escapeHtml(row.priority || "P2")}</span>
            <strong>${escapeHtml(row.title)}</strong>
            <span class="status-pill ${reflectionStatusClass(row.status)}">${escapeHtml(reflectionStatusLabel(row.status))}</span>
          </div>
          <p>${escapeHtml(row.why || "")}</p>
          <small>${escapeHtml(row.action || "")}</small>
          ${row.note ? `<em>${escapeHtml(row.note)}</em>` : ""}
        </div>
        <div class="reflection-side">
          <span>${escapeHtml(row.reflection_date || "--")} · 更新 ${dt}</span>
          <div class="actions compact">
            ${active ? `<button class="secondary-btn" data-reflection-action="adopted" data-todo-id="${row.id}">采纳</button>` : ""}
            ${active ? `<button class="secondary-btn" data-reflection-action="doing" data-todo-id="${row.id}">执行中</button>` : ""}
            ${active ? `<button class="secondary-btn" data-reflection-action="done" data-todo-id="${row.id}">完成</button>` : ""}
            ${row.status !== "dismissed" ? `<button class="secondary-btn" data-reflection-action="dismissed" data-todo-id="${row.id}">忽略</button>` : ""}
          </div>
        </div>
      </article>
    `;
  }).join("");
}

function shadowDecisionLabel(decision) {
  if (decision === "observe_only") return "观察";
  if (decision === "promote_candidate") return "可候选";
  if (decision === "disabled") return "关闭";
  return decision || "观察";
}

function shadowDeltaClass(value) {
  const delta = Number(value);
  if (!Number.isFinite(delta)) return "";
  if (delta > 0) return "positive";
  if (delta < 0) return "negative";
  return "";
}

function renderShadowTraining(data = {}) {
  if (!els.shadowBuckets) return;
  const latest = data.latest || {};
  const summary = latest.summary || {};
  const metrics = summary.metrics || {};
  const improvement = summary.improvement || {};
  const created = latest.created_at ? new Date(latest.created_at).toLocaleString("zh-CN") : "--";
  const delta = improvement.brier_delta ?? (
    latest.base_brier !== null && latest.shadow_brier !== null
      ? Number(latest.base_brier) - Number(latest.shadow_brier)
      : null
  );
  const deltaClass = shadowDeltaClass(delta);

  if (els.shadowMeta) {
    const mode = latest.mode || summary.mode || "shadow-logistic";
    els.shadowMeta.textContent = latest.id ? `最近训练 #${latest.id} · ${created} · ${mode}` : "暂无训练结果";
  }
  if (els.shadowSamples) els.shadowSamples.textContent = latest.samples ?? summary.samples ?? "--";
  if (els.shadowValidation) els.shadowValidation.textContent = latest.validation_samples ?? summary.validation_samples ?? "--";
  if (els.shadowBrierDelta) {
    els.shadowBrierDelta.innerHTML = delta === null || delta === undefined || Number.isNaN(Number(delta))
      ? "--"
      : `<span class="${deltaClass}">${Number(delta) >= 0 ? "+" : ""}${number(delta, 5)}</span>`;
  }
  if (els.shadowDecision) els.shadowDecision.textContent = shadowDecisionLabel(summary.decision);

  const baseBrier = metrics.base_brier ?? latest.base_brier;
  const shadowBrier = metrics.shadow_brier ?? latest.shadow_brier;
  const baseLogloss = metrics.base_logloss ?? latest.base_logloss;
  const shadowLogloss = metrics.shadow_logloss ?? latest.shadow_logloss;
  if (els.shadowInsight) {
    const verdict = Number(delta) > 0
      ? "本次影子模型略优于 GBM，但仍只做观察，需连续多日稳定胜出。"
      : Number(delta) < 0
        ? "本次影子模型弱于 GBM，说明暂时不能升级到交易决策。"
        : "样本不足或改善不明显，继续观察。";
    els.shadowInsight.textContent = `${verdict} GBM Brier ${number(baseBrier, 5)} / Shadow Brier ${number(shadowBrier, 5)} · GBM logloss ${number(baseLogloss, 5)} / Shadow logloss ${number(shadowLogloss, 5)}`;
  }

  const buckets = summary.calibration_buckets || [];
  if (!buckets.length) {
    els.shadowBuckets.innerHTML = `<div class="coverage-row"><strong>暂无分桶</strong><span>下一次训练完成后会显示预测概率和真实命中率。</span></div>`;
  } else {
    els.shadowBuckets.innerHTML = buckets.map((bucket) => {
      const actual = Number(bucket.actual_rate);
      const shadow = Number(bucket.avg_shadow_probability);
      const gbm = Number(bucket.avg_gbm_probability);
      const width = Number.isFinite(actual) ? Math.max(2, Math.min(100, actual * 100)) : 2;
      return `
        <div class="shadow-bucket-row">
          <div class="shadow-bucket-label">
            <strong>${escapeHtml(bucket.bucket || "--")}</strong>
            <span>${bucket.samples ?? 0} 样本</span>
          </div>
          <div class="shadow-bar-track" title="真实命中率 ${percent(actual)}">
            <span style="width:${width}%"></span>
          </div>
          <div class="shadow-bucket-values">
            <span>实际 ${percent(actual)}</span>
            <span>Shadow ${percent(shadow)}</span>
            <span>GBM ${percent(gbm)}</span>
          </div>
        </div>
      `;
    }).join("");
  }

  const runs = data.runs || [];
  if (!runs.length) {
    els.shadowRuns.innerHTML = `<div class="coverage-row"><strong>暂无历史</strong><span>每天训练一次后，这里会形成趋势。</span></div>`;
    return;
  }
  els.shadowRuns.innerHTML = runs.map((run) => {
    const runSummary = run.summary || {};
    const runDelta = runSummary.improvement?.brier_delta ?? (
      run.base_brier !== null && run.shadow_brier !== null ? Number(run.base_brier) - Number(run.shadow_brier) : null
    );
    const runCreated = run.created_at ? new Date(run.created_at).toLocaleString("zh-CN") : "--";
    const cls = shadowDeltaClass(runDelta);
    return `
      <div class="shadow-run-row">
        <strong>#${run.id} · ${escapeHtml(runCreated)}</strong>
        <span>样本 ${run.samples ?? "--"} / 验证 ${run.validation_samples ?? "--"}</span>
        <span>GBM ${number(run.base_brier, 5)} · Shadow ${number(run.shadow_brier, 5)} · <b class="${cls}">Δ ${runDelta === null || runDelta === undefined || Number.isNaN(Number(runDelta)) ? "--" : `${Number(runDelta) >= 0 ? "+" : ""}${number(runDelta, 5)}`}</b></span>
      </div>
    `;
  }).join("");
}

function renderCalibration(data = {}) {
  const summary = data.summary || {};
  if (els.calibrationMeta) {
    const generated = data.generated_at ? new Date(data.generated_at).toLocaleString("zh-CN") : "--";
    const better = summary.better_calibration === "model" ? "模型较准" : summary.better_calibration === "market" ? "市场较准" : "样本不足";
    els.calibrationMeta.textContent = `${better} · open ${summary.open ?? 0} · 生成 ${generated}`;
  }
  if (els.calibrationSamples) els.calibrationSamples.textContent = summary.samples ?? "--";
  if (els.calibrationResolved) els.calibrationResolved.textContent = summary.resolved ?? "--";
  if (els.calibrationModelBrier) els.calibrationModelBrier.textContent = number(summary.model_brier, 4);
  if (els.calibrationMarketBrier) els.calibrationMarketBrier.textContent = number(summary.market_brier, 4);

  const buckets = data.buckets || [];
  if (els.calibrationRows) {
    if (!buckets.length) {
      els.calibrationRows.innerHTML = `<tr><td colspan="8">暂无校准样本</td></tr>`;
    } else {
      els.calibrationRows.innerHTML = buckets
        .map((row) => `
          <tr>
            <td>${escapeHtml(row.bucket)}</td>
            <td>${row.samples}<small>open ${row.open}</small></td>
            <td>${row.resolved}</td>
            <td>${percent(row.avg_model_probability)}</td>
            <td>${percent(row.avg_market_probability)}</td>
            <td>${percent(row.actual_rate)}</td>
            <td>${signedPercent(row.model_error)}</td>
            <td>${signedPercent(row.market_error)}</td>
          </tr>
        `)
        .join("");
    }
  }

  const attributions = data.attribution || [];
  if (els.attributionRows) {
    if (!attributions.length) {
      els.attributionRows.innerHTML = `<div class="coverage-row"><strong>暂无归因</strong><span>需要 candidate 样本。</span></div>`;
    } else {
      els.attributionRows.innerHTML = attributions
        .slice(0, 8)
        .map((row) => `
          <div class="attribution-row">
            <strong>${escapeHtml(row.label)}</strong>
            <span>${row.count} 条候选</span>
          </div>
        `)
        .join("");
    }
  }

  const recent = data.recent || [];
  if (els.calibrationRecentRows) {
    if (!recent.length) {
      els.calibrationRecentRows.innerHTML = `<tr><td colspan="5">暂无候选样本</td></tr>`;
    } else {
      els.calibrationRecentRows.innerHTML = recent
        .slice(0, 20)
        .map((row) => `
          <tr>
            <td>${paperStatusLabel(row.status)}<small>${new Date(row.created_at).toLocaleDateString()}</small></td>
            <td class="question">${escapeHtml(row.question)}</td>
            <td>${percent(row.model_probability)}<small>market ${percent(row.market_probability)}</small></td>
            <td>${percent(row.latest_bid)}<small>${signedPercent(row.bid_change)}</small></td>
            <td>${(row.attributions || []).map((item) => `<span class="mini-tag">${escapeHtml(item)}</span>`).join("")}</td>
          </tr>
        `)
        .join("");
    }
  }
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

function externalLink(url, label) {
  if (!url) return "";
  let parsed = null;
  try {
    parsed = new URL(url, window.location.origin);
  } catch (error) {
    return "";
  }
  if (!["http:", "https:"].includes(parsed.protocol)) return "";
  const safeUrl = escapeHtml(parsed.href);
  return `<a class="external-link" href="${safeUrl}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
}

function renderPositions(data = {}) {
  lastPositionData = data;
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
    renderTradeConsole();
    return;
  }
  els.positionRows.innerHTML = rows
    .map((row) => `
      <div class="position-row">
        <strong>
          <span>${recommendationPill(row.recommendation, row.recommendation_label)} ${escapeHtml(row.asset)}</span>
          <span>${signedPercent(row.unrealized_return)}</span>
        </strong>
        <span>${escapeHtml(row.question)} ${externalLink(row.market_url, "打开 Polymtrade")}</span>
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
  renderTradeConsole();
}

function realPositionStatus(row) {
  if (row.status === "spot_unavailable") return `<span class="pill negative-pill">无行情</span>`;
  if ((row.triggered_rules || []).some((item) => String(item).includes("not_sent_non_realtime"))) return `<span class="pill warning-pill">旧价触发</span>`;
  if ((row.triggered_rules || []).length) return `<span class="pill negative-pill">已触发</span>`;
  return `<span class="pill positive-pill">监控中</span>`;
}

function renderRealPositions(data = {}) {
  lastRealPositionData = data;
  if (!els.realPositionRows) return;
  const rows = data.positions || [];
  const generated = data.generated_at ? new Date(data.generated_at).toLocaleString("zh-CN") : "--";
  const alertCount = (data.alerts || []).length;
  const positionSource = data.position_source || {};
  const wallet = positionSource.wallet ? `${String(positionSource.wallet).slice(0, 6)}...${String(positionSource.wallet).slice(-4)}` : "--";
  const sourceLabel = positionSource.mode === "wallet_api"
    ? `钱包 API · ${escapeHtml(wallet)} · ${escapeHtml(positionSource.source || "source unavailable")}`
    : "手工配置";
  if (els.realPositionMeta) {
    els.realPositionMeta.textContent = `生成 ${generated} · ${sourceLabel} · 触发 ${alertCount} 条`;
  }
  if (!rows.length) {
    const errors = (positionSource.errors || []).join("；");
    els.realPositionRows.innerHTML = `<div class="coverage-row"><strong>暂无真实持仓</strong><span>${escapeHtml(errors || "未从钱包 API 获取到持仓。")}</span></div>`;
    renderTradeConsole();
    return;
  }
  els.realPositionRows.innerHTML = rows
    .map((row) => {
      const source = row.spot_source || "--";
      const fetched = row.spot_fetched_at ? new Date(row.spot_fetched_at).toLocaleString("zh-CN") : "--";
      const realtime = row.spot_is_realtime ? "实时" : row.spot_source ? "非实时" : "--";
      const rules = (row.exit_rules || []).map((rule) => `${rule.severity || "review"}: ${rule.message || rule.id}`).join("；");
      const triggered = (row.triggered_rules || []).length ? `触发 ${row.triggered_rules.join(", ")}` : "未触发";
      return `
        <div class="position-row real-position-row">
          <strong>
            <span>${realPositionStatus(row)} ${escapeHtml(row.asset)} ${escapeHtml(row.side || "")}</span>
            <span>${escapeHtml(triggered)}</span>
          </strong>
          <span>${escapeHtml(row.question)} ${externalLink(row.portfolio_url, "打开真实持仓")}</span>
          <div class="position-metrics">
            <span>份数 <strong>${escapeHtml(row.shares ?? "--")}</strong></span>
            <span>成本 <strong>${money(row.initial_value)}</strong></span>
            <span>当前价值 <strong>${money(row.current_value)}</strong></span>
            <span>PnL <strong>${money(row.cash_pnl)} / ${percent(row.percent_pnl)}</strong></span>
            <span>均价 <strong>${percent(row.avg_price)}</strong></span>
            <span>当前合约价 <strong>${percent(row.current_price)}</strong></span>
            <span>现货 <strong>${money(row.spot)}</strong></span>
            <span>目标 <strong>${money(row.barrier)}</strong></span>
            <span>距离 <strong>${percent(row.distance_to_barrier)}</strong></span>
          </div>
          <span>持仓源 ${escapeHtml(row.position_source || "--")} · 行情 ${escapeHtml(realtime)} · ${escapeHtml(source)} · ${escapeHtml(fetched)}</span>
          <span>${escapeHtml(rules || "暂无触发规则")}</span>
        </div>
      `;
    })
    .join("");
  renderTradeConsole();
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

function questionCell(row) {
  const tradeLink = row.market_url ? externalLink(row.market_url, "打开 Polymtrade") : "";
  const sourceNote = row.market_url_source === "category" ? `<small>未找到事件参数，打开 crypto 列表</small>` : "";
  return `${escapeHtml(row.question)}${tradeLink}${sourceNote}`;
}

function tradeDraftRows() {
  const rows = lastScanner?.opportunities || [];
  return rows
    .filter((row) => row.action === "candidate" && row.review_status === "passed" && row.opportunity_tier === "candidate")
    .filter((row) => Number(row.minutes_to_expiry ?? 1) > 0)
    .sort((a, b) => Number(b.net_edge || 0) - Number(a.net_edge || 0))
    .slice(0, 8);
}

function tradeReviewRows() {
  const rows = lastScanner?.opportunities || [];
  return rows
    .filter((row) => row.review_status !== "passed")
    .filter((row) => ["near", "research", "blocked"].includes(row.opportunity_tier || "") || ["verify", "watch"].includes(row.action || ""))
    .filter((row) => Number(row.minutes_to_expiry ?? 1) > 0)
    .sort((a, b) => Number(b.net_edge || 0) - Number(a.net_edge || 0))
    .slice(0, 6);
}

function exitDraftRows() {
  const paperRows = (lastPositionData?.positions || [])
    .filter((row) => ["exit", "review"].includes(row.recommendation) || Number(row.unrealized_return) >= 0.2)
    .map((row) => ({ type: "paper", row }));
  const realRows = (lastRealPositionData?.positions || [])
    .filter((row) => (row.triggered_rules || []).length || Number(row.cash_pnl) > 0 || Number(row.percent_pnl) >= 0.2)
    .map((row) => ({ type: "real", row }));
  return [...paperRows, ...realRows]
    .sort((a, b) => exitDraftPriority(b) - exitDraftPriority(a))
    .slice(0, 8);
}

function exitDraftPriority(item) {
  const row = item.row || {};
  if (item.type === "paper") {
    if (row.recommendation === "exit") return 100 + Number(row.unrealized_return || 0);
    if (row.recommendation === "review") return 60 + Number(row.unrealized_return || 0);
    return Number(row.unrealized_return || 0);
  }
  const triggered = (row.triggered_rules || []).length ? 80 : 0;
  return triggered + Number(row.percent_pnl || 0);
}

function tradeDraftRisk(row) {
  const checks = [];
  const tier = row.opportunity_tier || "";
  const fresh = row.pricing_source === "orderbook" && row.orderbook_is_fresh;
  const completeFill = row.complete_fill !== false;
  const edge = Number(row.net_edge);
  const ask = tradeDraftPrice(row);
  checks.push(fresh ? "盘口新鲜" : "盘口需复核");
  checks.push(completeFill ? "可完整成交" : "可能部分成交");
  checks.push(Number.isFinite(edge) && edge >= 0.02 ? "edge 达标" : "edge 偏低");
  checks.push(Number.isFinite(ask) ? "限价可估" : "缺少限价");
  const blocked = !fresh || !completeFill || !Number.isFinite(ask);
  if (blocked) return { label: "需人工复核", cls: "warning-pill", checks };
  if (tier === "candidate" || row.action === "candidate") return { label: "可半自动", cls: "positive-pill", checks };
  return { label: "观察草稿", cls: "neutral-pill", checks };
}

function exitDraftRisk(item) {
  const row = item.row || {};
  if (item.type === "paper") {
    if (row.recommendation === "exit") return { label: "应平仓", cls: "negative-pill", detail: (row.notes || []).join("；") || "退出条件触发" };
    if (row.recommendation === "review") return { label: "复核止盈", cls: "warning-pill", detail: (row.notes || []).join("；") || "收益/盘口需要复核" };
    return { label: "止盈观察", cls: "positive-pill", detail: "浮盈达到观察阈值" };
  }
  if ((row.triggered_rules || []).length) {
    return { label: "规则触发", cls: "negative-pill", detail: row.triggered_rules.join("；") };
  }
  return { label: "止盈观察", cls: "positive-pill", detail: "真实持仓当前为正收益" };
}

function tradeDraftPrice(row) {
  const values = [row.ask_price, row.executable_avg_price, row.best_ask, row.market_yes_price];
  for (const value of values) {
    const price = Number(value);
    if (Number.isFinite(price) && price > 0) return price;
  }
  return NaN;
}

function exitDraftText(item) {
  const row = item.row || {};
  const risk = exitDraftRisk(item);
  if (item.type === "paper") {
    return [
      "Polymtrade 半自动平仓草稿",
      "类型: Paper 持仓",
      `市场: ${row.question || "--"}`,
      `资产: ${row.asset || "--"}`,
      `建议: ${row.recommendation_label || risk.label}`,
      `卖出参考: ${percent(row.current_best_bid)}`,
      `入场: ${percent(row.entry_price)}`,
      `未实现收益: ${signedPercentText(row.unrealized_return)}`,
      `未实现 PnL: ${money(row.unrealized_pnl)}`,
      `退出价值: ${money(row.exit_value)}`,
      `理由: ${risk.detail || "--"}`,
      `链接: ${row.market_url || "未找到具体市场链接"}`,
    ].join("\n");
  }
  return [
    "Polymtrade 半自动平仓草稿",
    "类型: 真实持仓",
    `市场: ${row.question || "--"}`,
    `资产/方向: ${row.asset || "--"} ${row.side || ""}`,
    `建议: ${risk.label}`,
    `份数: ${row.shares ?? "--"}`,
    `成本: ${money(row.initial_value)}`,
    `当前价值: ${money(row.current_value)}`,
    `PnL: ${money(row.cash_pnl)} / ${percent(row.percent_pnl)}`,
    `当前合约价: ${percent(row.current_price)}`,
    `现货/目标: ${money(row.spot)} / ${money(row.barrier)}`,
    `理由: ${risk.detail || "--"}`,
    `链接: ${row.portfolio_url || "未找到真实持仓链接"}`,
  ].join("\n");
}

function tradeDraftText(row) {
  const price = tradeDraftPrice(row);
  const recommendation = row.trade_recommendation || (row.direction === "hit_below" ? "买 YES 下破" : "买 YES 上破");
  return [
    "Polymtrade 半自动订单草稿",
    `市场: ${row.question || "--"}`,
    `资产: ${row.asset || "--"}`,
    `方向: ${recommendation}`,
    `限价参考: ${Number.isFinite(price) ? percent(price) : "--"}`,
    `建议最大单笔: $5`,
    `模型概率: ${percent(row.model_probability)}`,
    `市场价格: ${percent(row.market_yes_price)}`,
    `净 Edge: ${signedPercentText(row.net_edge)}`,
    `ROI: ${signedPercentText(row.roi)}`,
    `现价/目标: ${money(row.spot)} / ${money(row.barrier)}`,
    `到期: ${row.end_date || "--"}`,
    `链接: ${row.market_url || "未找到具体市场链接"}`,
  ].join("\n");
}

function updateTradingMode() {
  if (els.tradeMasterSwitch) els.tradeMasterSwitch.checked = tradingEnabled;
  if (els.tradeModeStatus) {
    els.tradeModeStatus.textContent = tradingEnabled ? "半自动开启" : "关闭";
    els.tradeModeStatus.className = tradingEnabled ? "positive" : "negative";
  }
  document.querySelectorAll("[data-trade-action]").forEach((button) => {
    button.disabled = !tradingEnabled;
    button.setAttribute("aria-disabled", tradingEnabled ? "false" : "true");
    button.classList.toggle("disabled", !tradingEnabled);
  });
}

function renderTradeConsole() {
  const openRows = tradeDraftRows();
  const reviewRows = tradeReviewRows();
  const exitRows = exitDraftRows();
  if (els.tradeDraftCount) els.tradeDraftCount.textContent = openRows.length + exitRows.length;
  if (els.tradeMeta) {
    const generated = lastScanner?.generated_at ? new Date(lastScanner.generated_at).toLocaleString("zh-CN") : "--";
    els.tradeMeta.textContent = lastScanner ? `Scanner ${generated} · 可交易 ${openRows.length} / 复核 ${reviewRows.length} / 平仓 ${exitRows.length}` : `等待 Scanner · 平仓 ${exitRows.length}`;
  }
  if (!els.tradeDraftRows) return;
  if (!lastScanner && !exitRows.length) {
    els.tradeDraftRows.innerHTML = `<div class="coverage-row"><strong>等待 Scanner / 持仓</strong><span>运行 Scanner 生成开仓草稿；刷新持仓后生成止盈/平仓草稿。</span></div>`;
    updateTradingMode();
    return;
  }
  const openHtml = openRows.length ? openRows
    .map((row, index) => {
      const risk = tradeDraftRisk(row);
      const recommendation = row.trade_recommendation || (row.direction === "hit_below" ? "买 YES 下破" : "买 YES 上破");
      const price = tradeDraftPrice(row);
      const url = row.market_url || "https://polym.trade/?category=crypto";
      return `
        <article class="trade-draft-card">
          <div class="trade-draft-head">
            <span class="edge-rank">单 ${index + 1}</span>
            <strong>${escapeHtml(recommendation)} · ${escapeHtml(row.asset || "--")}</strong>
            <span class="pill ${risk.cls}">${escapeHtml(risk.label)}</span>
          </div>
          <p>${escapeHtml(shortQuestion(row.question, 120))}</p>
          <div class="trade-draft-grid">
            <span>限价 <strong>${Number.isFinite(price) ? percent(price) : "--"}</strong></span>
            <span>净 Edge <strong>${signedPercentText(row.net_edge)}</strong></span>
            <span>ROI <strong>${signedPercentText(row.roi)}</strong></span>
            <span>可成交 <strong>${money(row.executable_notional)}</strong></span>
            <span>到期 <strong>${compactAge(row.minutes_to_expiry)}</strong></span>
            <span>单笔上限 <strong>$5</strong></span>
          </div>
          <small>${escapeHtml(risk.checks.join(" · "))}</small>
          <div class="trade-draft-actions">
            <button class="secondary-btn" data-trade-action="copy" data-draft-type="open" data-draft-index="${index}">复制订单</button>
            <a class="secondary-btn" data-trade-action="open" data-draft-type="open" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">打开市场</a>
          </div>
        </article>
      `;
    })
    .join("") : `<div class="coverage-row"><strong>暂无可交易开仓草稿</strong><span>只有机会扫描里“候选 + 复核通过”的记录才会进入这里。</span></div>`;
  const reviewHtml = reviewRows.length ? reviewRows
    .map((row, index) => {
      const blockers = row.review_blockers || [];
      const reason = blockers[0] || row.opportunity_tier_reason || "未通过交易控制台开仓规则";
      const bucket = opportunityBucket(row);
      return `
        <article class="trade-draft-card review-draft-card">
          <div class="trade-draft-head">
            <span class="edge-rank">核 ${index + 1}</span>
            <strong>${escapeHtml(row.trade_recommendation || "--")} · ${escapeHtml(row.asset || "--")}</strong>
            <span class="pill ${row.review_status === "blocked" ? "negative-pill" : "warning-pill"}">${escapeHtml(row.review_status === "blocked" ? "阻断" : "需复核")}</span>
          </div>
          <p>${escapeHtml(shortQuestion(row.question, 120))}</p>
          <div class="trade-draft-grid">
            <span>分层 <strong>${escapeHtml(opportunityBucketLabel(bucket))}</strong></span>
            <span>复核 <strong>${escapeHtml(row.review_status || "--")}</strong></span>
            <span>净 Edge <strong>${signedPercentText(row.net_edge)}</strong></span>
            <span>ROI <strong>${signedPercentText(row.roi)}</strong></span>
            <span>盘口 <strong>${escapeHtml(row.pricing_source || "--")}</strong></span>
            <span>到期 <strong>${compactAge(row.minutes_to_expiry)}</strong></span>
          </div>
          <small>${escapeHtml(`${opportunityBucketHint(bucket)} ${reason}`.trim())}</small>
        </article>
      `;
    })
    .join("") : `<div class="coverage-row"><strong>暂无复核记录</strong><span>阻断和需复核记录不会生成交易动作。</span></div>`;
  const exitHtml = exitRows.length ? exitRows
    .map((item, index) => {
      const row = item.row || {};
      const risk = exitDraftRisk(item);
      const url = item.type === "paper" ? row.market_url : row.portfolio_url;
      const title = item.type === "paper"
        ? `${row.asset || "--"} · ${row.recommendation_label || risk.label}`
        : `${row.asset || "--"} ${row.side || ""} · ${risk.label}`;
      const primaryMetric = item.type === "paper"
        ? `未实现 ${signedPercentText(row.unrealized_return)} / ${money(row.unrealized_pnl)}`
        : `PnL ${money(row.cash_pnl)} / ${percent(row.percent_pnl)}`;
      return `
        <article class="trade-draft-card exit-draft-card">
          <div class="trade-draft-head">
            <span class="edge-rank">平 ${index + 1}</span>
            <strong>${escapeHtml(title)}</strong>
            <span class="pill ${risk.cls}">${escapeHtml(risk.label)}</span>
          </div>
          <p>${escapeHtml(shortQuestion(row.question, 120))}</p>
          <div class="trade-draft-grid">
            <span>收益 <strong>${primaryMetric}</strong></span>
            <span>卖出参考 <strong>${item.type === "paper" ? percent(row.current_best_bid) : percent(row.current_price)}</strong></span>
            <span>成本 <strong>${item.type === "paper" ? percent(row.entry_price) : money(row.initial_value)}</strong></span>
            <span>当前价值 <strong>${money(row.current_value ?? row.exit_value)}</strong></span>
            <span>份数 <strong>${escapeHtml(row.shares ?? "--")}</strong></span>
            <span>来源 <strong>${item.type === "paper" ? "Paper" : "真实"}</strong></span>
          </div>
          <small>${escapeHtml(risk.detail || "等待复核")}</small>
          <div class="trade-draft-actions">
            <button class="secondary-btn" data-trade-action="copy" data-draft-type="exit" data-draft-index="${index}">复制平仓</button>
            <a class="secondary-btn" data-trade-action="open" data-draft-type="exit" href="${escapeHtml(url || "https://polym.trade/portfolio")}" target="_blank" rel="noopener noreferrer">打开持仓</a>
          </div>
        </article>
      `;
    })
    .join("") : `<div class="coverage-row"><strong>暂无止盈/平仓草稿</strong><span>当前没有 Paper 或真实持仓触发止盈/退出观察。</span></div>`;
  els.tradeDraftRows.innerHTML = `
    <div class="trade-draft-group">
      <div class="trade-draft-group-head"><strong>可交易开仓草稿</strong><span>${openRows.length} 条</span></div>
      ${openHtml}
    </div>
    <div class="trade-draft-group">
      <div class="trade-draft-group-head"><strong>阻断 / 复核记录</strong><span>${reviewRows.length} 条</span></div>
      ${reviewHtml}
    </div>
    <div class="trade-draft-group">
      <div class="trade-draft-group-head"><strong>止盈 / 平仓草稿</strong><span>${exitRows.length} 条</span></div>
      ${exitHtml}
    </div>
  `;
  updateTradingMode();
}

async function refreshTradeConsole() {
  if (els.refreshTradeDraftsBtn) {
    els.refreshTradeDraftsBtn.disabled = true;
    els.refreshTradeDraftsBtn.textContent = "更新中...";
  }
  if (els.tradeMeta) els.tradeMeta.textContent = "正在刷新持仓与草稿";
  try {
    await loadPositions();
    renderTradeConsole();
    els.statusText.textContent = "交易草稿已更新";
  } catch (error) {
    renderTradeConsole();
    els.statusText.textContent = `交易草稿更新失败：${error.message}`;
  } finally {
    if (els.refreshTradeDraftsBtn) {
      els.refreshTradeDraftsBtn.disabled = false;
      els.refreshTradeDraftsBtn.textContent = "更新草稿";
    }
  }
}

function sortValue(row, field) {
  if (field === "action") {
    const order = { candidate: 0, verify: 1, watch: 2, avoid: 3 };
    return order[row.action] ?? 99;
  }
  if (field === "opportunity_tier") {
    const order = { candidate: 0, near: 1, research: 2, blocked: 3, ignore: 4 };
    return order[row.opportunity_tier] ?? 99;
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
  if (!scannerSort.field) {
    const order = { candidate: 0, near: 1, research: 2, blocked: 3 };
    return [...rows].sort((a, b) => {
      const av = order[opportunityBucket(a)] ?? 9;
      const bv = order[opportunityBucket(b)] ?? 9;
      if (av !== bv) return av - bv;
      return Number(b.net_edge || 0) - Number(a.net_edge || 0);
    });
  }
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
  renderScannerTierBoard(data.opportunities || []);
  if (els.saveObservationBtn) els.saveObservationBtn.disabled = !rows.length;
  els.scannerCandidates.textContent = summary.candidates ?? "--";
  els.scannerBestEdge.innerHTML = signedPercent(summary.best_net_edge);
  els.scannerBestRoi.innerHTML = signedPercent(summary.best_roi);
  els.scannerScanned.textContent = summary.markets_scanned ?? "--";
  const selectedContext = data.contexts?.[selectedAsset];
  els.scannerVol.textContent = contextFactorLabel(selectedContext);
  els.scannerPaths.textContent = assumptions.simulations ?? "--";
  els.scannerSkipped.textContent = summary.markets_skipped ?? "--";
  if (els.scannerNear) els.scannerNear.textContent = summary.near_candidates ?? "--";
  if (els.scannerResearch) els.scannerResearch.textContent = summary.research_opportunities ?? "--";
  els.scannerStatus.textContent = summary.candidates > 0 ? "有候选" : summary.near_candidates > 0 ? "有准候选" : summary.research_opportunities > 0 ? "有研究机会" : "观察";
  els.scannerMeta.textContent = `${assumptions.model_probability_method || "GBM closed-form"} · ${assumptions.vol_window || "90d"} vol · MC ${assumptions.mc_diagnostic_paths || assumptions.simulations || 0} paths · 最小到期 ${assumptions.min_expiry_minutes ?? 30}m`;
  const contextSources = contextSourceLabel(data.contexts || {});
  els.priceSource.textContent = compactContextSourceLabel(data.contexts || {});
  els.priceSource.title = contextSources || "";
  const selectedVol = selectedContext?.volatility?.[assumptions.vol_window];
  els.stackData.textContent = contextSources || "无真实价格源";
  const ewmaVol = selectedContext?.ewma_volatility;
  const drift = Number(selectedContext?.drift_90d);
  const driftLabel = Number.isFinite(drift) ? ` · drift90 ${signedPercentText(drift)}` : "";
  const ivState = selectedContext?.iv_source ? "Deribit IV on" : selectedContext?.iv_error ? "Deribit IV unavailable" : "IV off";
  els.stackModel.textContent = `GBM closed-form · ${assumptions.vol_model || "factor"} vol · RV ${assumptions.vol_window || "90d"}${selectedVol ? ` ${percent(selectedVol)}` : ""}${ewmaVol ? ` · EWMA ${percent(ewmaVol)}` : ""}${driftLabel} · ${ivState} · MC diag ${assumptions.simulations || 0}`;
  els.stackCost.textContent = `fee ${percent(assumptions.fee_rate)} · slippage ${Number(assumptions.slippage_bps || 0).toFixed(0)} bps · min edge ${percent(assumptions.edge_threshold)} · ${contextFactorLabel(selectedContext)}`;
  els.stackExecution.textContent = assumptions.orderbook
    ? `盘口 ${summary.orderbook_priced ?? 0}/${assumptions.book_limit} · 过期 ${summary.stale_orderbooks ?? 0} · 部分 ${summary.partial_fills ?? 0} · 不确定 ${summary.uncertain_edges ?? 0} · 候选 ${summary.candidates ?? 0}`
    : `cached price · min liquidity ${money(assumptions.min_liquidity)} · macro ${summary.macro_risk_rows ?? 0}/${summary.macro_vol_adjusted ?? 0} · 不确定 ${summary.uncertain_edges ?? 0}`;
  drawEdgeChart(rows);
  drawPriceChart(lastPrices);
  renderTradeConsole();
  if (!rows.length) {
    els.scannerRows.innerHTML = `<tr><td colspan="15">暂无可扫描市场</td></tr>`;
    return;
  }
  let lastBucket = null;
  els.scannerRows.innerHTML = rows
    .map(
      (row) => {
        const bucket = opportunityBucket(row);
        const section = scannerSort.field ? "" : bucket !== lastBucket
          ? `<tr class="scanner-group-row"><td colspan="15"><strong>${escapeHtml(opportunityBucketLabel(bucket))}</strong><span>${escapeHtml(opportunityBucketHint(bucket))}</span></td></tr>`
          : "";
        lastBucket = bucket;
        return `
        ${section}
        <tr data-edge-id="${escapeHtml(edgeRowId(row))}">
          <td>${actionLabel(row.action)}</td>
          <td class="review-cell">${tierCell(row)}</td>
          <td class="review-cell">${reviewCell(row)}</td>
          <td>${escapeHtml(row.asset)}</td>
          <td class="question">${questionCell(row)}</td>
          <td class="trade-cell">${tradeDirectionCell(row)}</td>
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
      `;
      },
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
    const environment = data.runtime_environment || (data.source === "deploy" ? "server" : "local");
    const label = environment === "server" ? "服务器" : "本地";
    const deployed = data.deployed_at ? new Date(data.deployed_at).toLocaleString("zh-CN") : "";
    els.versionBadge.textContent = `${label} · ${version}`;
    els.versionBadge.classList.toggle("server", environment === "server");
    els.versionBadge.classList.toggle("local", environment !== "server");
    els.versionBadge.title = environment === "server"
      ? `服务器版本 · 部署时间 ${deployed || "--"}`
      : "本地版本";
  } catch (error) {
    els.versionBadge.textContent = "version --";
    els.versionBadge.classList.remove("server", "local");
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

async function loadMacroEvents() {
  if (!els.macroRows) return;
  const data = await apiJson("/api/macro-events?horizon_hours=720");
  renderMacroEvents(data);
}

async function loadReflectionTodos() {
  if (!els.reflectionRows) return;
  const data = await apiJson("/api/reflection-todos?limit=100");
  renderReflectionTodos(data);
}

async function loadShadowTraining() {
  if (!els.shadowBuckets) return;
  if (els.refreshShadowBtn) {
    els.refreshShadowBtn.disabled = true;
    els.refreshShadowBtn.textContent = "刷新中...";
  }
  if (els.shadowMeta) els.shadowMeta.textContent = "正在读取影子模型";
  try {
    const data = await apiJson("/api/shadow-training?limit=14");
    renderShadowTraining(data);
    const latest = data.latest || {};
    const delta = latest.summary?.improvement?.brier_delta;
    els.statusText.textContent = latest.id
      ? `影子模型已刷新：训练 #${latest.id}，Brier 改善 ${delta === null || delta === undefined ? "--" : number(delta, 5)}`
      : "影子模型暂无训练记录";
  } catch (error) {
    if (els.shadowMeta) els.shadowMeta.textContent = "刷新失败";
    els.statusText.textContent = `影子模型刷新失败：${error.message}`;
    throw error;
  } finally {
    if (els.refreshShadowBtn) {
      els.refreshShadowBtn.disabled = false;
      els.refreshShadowBtn.textContent = "刷新模型";
    }
  }
}

async function updateReflectionTodo(id, status) {
  const note = status === "dismissed" ? "人工忽略" : status === "done" ? "人工标记完成" : "";
  const data = await apiJson("/api/reflection-todos", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ id, status, note }),
  });
  if (!data.ok) throw new Error(data.error || "todo update failed");
  renderReflectionTodos(data.report);
  await loadLogs();
}

async function loadCalibration() {
  if (!els.calibrationRows) return;
  if (els.refreshCalibrationBtn) {
    els.refreshCalibrationBtn.disabled = true;
    els.refreshCalibrationBtn.textContent = "刷新中...";
  }
  if (els.calibrationMeta) els.calibrationMeta.textContent = "正在刷新校准";
  try {
    const data = await apiJson("/api/calibration-attribution?limit=500&stake=100");
    renderCalibration(data);
    const summary = data.summary || {};
    els.statusText.textContent = `模型校准已刷新：样本 ${summary.samples ?? 0}，已结算 ${summary.resolved ?? 0}`;
  } catch (error) {
    if (els.calibrationMeta) els.calibrationMeta.textContent = "刷新失败";
    els.statusText.textContent = `模型校准刷新失败：${error.message}`;
    throw error;
  } finally {
    if (els.refreshCalibrationBtn) {
      els.refreshCalibrationBtn.disabled = false;
      els.refreshCalibrationBtn.textContent = "刷新校准";
    }
  }
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
  if (!els.positionRows && !els.realPositionRows) return;
  if (els.refreshPositionsBtn) {
    els.refreshPositionsBtn.disabled = true;
    els.refreshPositionsBtn.textContent = "刷新中...";
  }
  if (els.realPositionMeta) els.realPositionMeta.textContent = "正在刷新真实持仓";
  if (els.positionMeta) els.positionMeta.textContent = "正在刷新持仓";
  try {
    const [realResult, positionResult] = await Promise.allSettled([
      apiJson("/api/real-positions?timeout=4&max_fallback_age_hours=36"),
      apiJson("/api/position-management?limit=100&stake=100&book_timeout=4&max_book_age_seconds=120"),
    ]);

    if (realResult.status === "fulfilled") {
      renderRealPositions(realResult.value);
    } else {
      renderRealPositionsError(realResult.reason);
    }

    if (positionResult.status !== "fulfilled") {
      throw positionResult.reason;
    }

    const data = positionResult.value;
    renderPositions(data);
    const summary = data.summary || {};
    const realAlerts = realResult.status === "fulfilled" ? (realResult.value.alerts || []).length : 0;
    els.statusText.textContent = `持仓管理已刷新：开放 ${summary.positions ?? 0} 条，观察退出 ${summary.review ?? 0} 条`;
    if (realAlerts) els.statusText.textContent += `，真实持仓触发 ${realAlerts} 条`;
    if (realResult.status === "rejected") els.statusText.textContent += "，真实持仓刷新失败";
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
    loadDataTrust().catch(() => {});
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
    await Promise.all([loadObservations(), loadQualityAnalysis(), loadCalibration(), loadShadowTraining(), loadPaperTrading(), loadPositions(), loadCandidateReview(), loadAutomationHealth(), loadLogs()]);
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
    loadReflectionTodos(),
    loadShadowTraining(),
    loadMacroEvents(),
    loadCalibration(),
    loadPaperTrading(),
    loadPositions(),
    loadCandidateReview(),
    loadLogs(),
    loadVersion(),
    loadMarketTickers(),
    loadDataTrust(),
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
if (els.refreshMacroBtn) els.refreshMacroBtn.addEventListener("click", loadMacroEvents);
if (els.refreshReflectionBtn) els.refreshReflectionBtn.addEventListener("click", loadReflectionTodos);
if (els.refreshShadowBtn) els.refreshShadowBtn.addEventListener("click", loadShadowTraining);
if (els.refreshCalibrationBtn) els.refreshCalibrationBtn.addEventListener("click", loadCalibration);
if (els.refreshPaperBtn) els.refreshPaperBtn.addEventListener("click", loadPaperTrading);
if (els.refreshPositionsBtn) els.refreshPositionsBtn.addEventListener("click", loadPositions);
if (els.refreshCandidateReviewBtn) els.refreshCandidateReviewBtn.addEventListener("click", loadCandidateReview);
if (els.refreshTradeDraftsBtn) els.refreshTradeDraftsBtn.addEventListener("click", refreshTradeConsole);
if (els.tradeMasterSwitch) {
  els.tradeMasterSwitch.addEventListener("change", () => {
    tradingEnabled = els.tradeMasterSwitch.checked;
    localStorage.setItem("polymtradeTradingEnabled", tradingEnabled ? "1" : "0");
    updateTradingMode();
    els.statusText.textContent = tradingEnabled ? "交易控制台已开启半自动模式" : "交易控制台已关闭";
  });
}
if (els.tradeDraftRows) {
  els.tradeDraftRows.addEventListener("click", async (event) => {
    const target = event.target.closest("[data-trade-action]");
    if (!target) return;
    if (!tradingEnabled) {
      event.preventDefault();
      els.statusText.textContent = "交易总开关关闭，未执行交易动作";
      return;
    }
    if (target.dataset.tradeAction !== "copy") return;
    const draftType = target.dataset.draftType || "open";
    const draftIndex = Number(target.dataset.draftIndex);
    const row = draftType === "exit" ? exitDraftRows()[draftIndex] : tradeDraftRows()[draftIndex];
    if (!row) return;
    event.preventDefault();
    try {
      await navigator.clipboard.writeText(draftType === "exit" ? exitDraftText(row) : tradeDraftText(row));
      els.statusText.textContent = draftType === "exit" ? "平仓草稿已复制" : "订单草稿已复制";
    } catch (error) {
      els.statusText.textContent = `订单草稿复制失败：${error.message}`;
    }
  });
}
if (els.reflectionRows) {
  els.reflectionRows.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-reflection-action]");
    if (!button) return;
    button.disabled = true;
    const status = button.dataset.reflectionAction;
    const id = Number(button.dataset.todoId);
    try {
      await updateReflectionTodo(id, status);
      els.statusText.textContent = `TODO 已更新为：${reflectionStatusLabel(status)}`;
    } catch (error) {
      els.statusText.textContent = `TODO 更新失败：${error.message}`;
      button.disabled = false;
    }
  });
}
if (els.sendReportBtn) els.sendReportBtn.addEventListener("click", sendReport);
if (els.logBtn) els.logBtn.addEventListener("click", () => toggleLogPanel(true));
if (els.logPanelClose) els.logPanelClose.addEventListener("click", () => toggleLogPanel(false));
if (els.logPanel) els.logPanel.addEventListener("click", (e) => { if (e.target === els.logPanel) toggleLogPanel(false); });
if (els.refreshLogsBtn) els.refreshLogsBtn.addEventListener("click", loadLogs);
if (els.clearLogsBtn) els.clearLogsBtn.addEventListener("click", clearLogs);
if (els.logLevelFilter) els.logLevelFilter.addEventListener("change", loadLogs);
if (els.logModuleFilter) els.logModuleFilter.addEventListener("change", loadLogs);
if (els.edgeChart) {
  els.edgeChart.addEventListener("mousemove", (event) => {
    const point = edgePointAtEvent(event);
    const nextId = point ? edgeRowId(point.row) : null;
    els.edgeChart.style.cursor = point ? "pointer" : "default";
    if (nextId !== edgeChartHoverId) {
      edgeChartHoverId = nextId;
      drawEdgeChart(lastScanner?.opportunities || []);
    }
  });
  els.edgeChart.addEventListener("mouseleave", () => {
    if (!edgeChartHoverId) return;
    edgeChartHoverId = null;
    els.edgeChart.style.cursor = "default";
    drawEdgeChart(lastScanner?.opportunities || []);
  });
  els.edgeChart.addEventListener("click", (event) => {
    const point = edgePointAtEvent(event);
    if (!point) return;
    scrollToScannerRow(edgeRowId(point.row));
  });
}
if (els.edgeOutliers) {
  els.edgeOutliers.addEventListener("mouseover", (event) => {
    const item = event.target.closest("[data-edge-id]");
    if (!item || item.dataset.edgeId === edgeChartHoverId) return;
    edgeChartHoverId = item.dataset.edgeId;
    drawEdgeChart(lastScanner?.opportunities || []);
  });
  els.edgeOutliers.addEventListener("mouseleave", () => {
    if (!edgeChartHoverId) return;
    edgeChartHoverId = null;
    drawEdgeChart(lastScanner?.opportunities || []);
  });
  els.edgeOutliers.addEventListener("click", (event) => {
    const item = event.target.closest("[data-edge-id]");
    if (!item) return;
    scrollToScannerRow(item.dataset.edgeId);
  });
}
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

document.querySelectorAll("[data-validation-tab]").forEach((button) => {
  button.addEventListener("click", () => setActiveValidationPanel(button.dataset.validationTab));
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
  lastTickers.forEach(renderTicker);
});
updateTradingMode();
setActiveView(initialViewFromHash());
loadDashboard();
