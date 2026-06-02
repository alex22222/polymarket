from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from polymtrade.data.derivatives import fetch_deribit_option_summaries, select_atm_iv
from polymtrade.data.crypto_prices import (
    fetch_best_spot,
    fetch_okx_funding_rate,
    fetch_okx_intraday,
    fetch_okx_open_interest,
)
from polymtrade.data.macro_events import macro_context, macro_risk_for_market
from polymtrade.data.polymarket_api import fetch_order_book
from polymtrade.storage.db import connect, data_quality_report
from polymtrade.superpowers.barrier import (
    BarrierInput,
    edge_for_yes,
    ewma_volatility,
    monte_carlo_touch_probability,
    realized_volatility,
)


SOURCE_PRIORITY = {
    "binance": 0,
    "binance-data-api": 1,
    "okx": 2,
    "coinbase": 3,
}


def float_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def stable_seed(*parts: object) -> int:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:8], 16)


def preferred_price_source(conn, asset: str) -> str | None:
    try:
        recommended = (data_quality_report(conn).get("recommendations") or {}).get(asset.upper()) or {}
        if recommended.get("source") and recommended.get("status") != "error":
            return str(recommended["source"])
    except Exception:
        pass
    rows = conn.execute(
        """
        select source, count(*) as candles
        from crypto_candles
        where asset = ? and interval = '1d'
        group by source
        """,
        (asset,),
    ).fetchall()
    if not rows:
        return None
    best = sorted(rows, key=lambda row: (SOURCE_PRIORITY.get(row["source"], 5), -row["candles"]))[0]
    return best["source"]


def latest_observed_market_state(conn, asset: str) -> dict[str, Any] | None:
    rows = conn.execute(
        """
        select contexts_json
        from scanner_observation_runs
        order by id desc
        limit 25
        """
    ).fetchall()
    for row in rows:
        try:
            contexts = json.loads(row["contexts_json"] or "{}")
        except json.JSONDecodeError:
            continue
        state = ((contexts.get(asset.upper()) or {}).get("market_state") or {})
        if state:
            return state
    return None


def funding_oi_tags(
    funding: dict[str, Any],
    open_interest: dict[str, Any],
    short_term: dict[str, Any],
) -> list[str]:
    tags: list[str] = []
    funding_rate = funding.get("funding_rate")
    oi_change = open_interest.get("open_interest_change")
    momentum_1h = short_term.get("momentum_1h")
    if isinstance(funding_rate, (int, float)):
        if funding_rate <= -0.0003:
            tags.append("funding 极负")
        elif funding_rate >= 0.0003:
            tags.append("funding 极正")
    if isinstance(oi_change, (int, float)):
        if oi_change <= -0.05:
            tags.append("OI 被清洗")
        elif oi_change >= 0.05:
            tags.append("OI 堆积")
    if "funding 极负" in tags and "OI 被清洗" in tags:
        tags.append("空头拥挤后去杠杆")
    elif "funding 极负" in tags and "OI 堆积" in tags:
        tags.append("空头拥挤但未清洗")
    if isinstance(momentum_1h, (int, float)):
        if momentum_1h > 0 and "funding 极负" in tags:
            tags.append("反弹确认观察")
        elif momentum_1h < 0 and "funding 极正" in tags:
            tags.append("回落确认观察")
    return tags


def _intraday_snapshot(
    asset: str,
    bar: str,
    limit: int,
    periods_per_hour: int,
    periods_per_year: float,
    timeout: int,
) -> dict[str, Any]:
    candles = fetch_okx_intraday(asset, bar=bar, limit=limit, timeout=timeout)
    closes = [item.close for item in candles]
    volumes = [item.volume for item in candles]
    latest = closes[-1] if closes else None

    def momentum(periods: int) -> float | None:
        if latest is None or len(closes) <= periods or closes[-(periods + 1)] <= 0:
            return None
        return latest / closes[-(periods + 1)] - 1.0

    recent_volume = sum(volumes[-periods_per_hour:]) if len(volumes) >= periods_per_hour else None
    previous_volume = (
        sum(volumes[-(periods_per_hour * 4) : -periods_per_hour])
        if len(volumes) >= periods_per_hour * 4
        else None
    )
    volume_ratio = (
        (recent_volume / periods_per_hour) / (previous_volume / (periods_per_hour * 3))
        if recent_volume is not None and previous_volume and previous_volume > 0
        else None
    )
    return {
        "source": "okx",
        "bar": bar,
        "candles": len(candles),
        "last_ts": candles[-1].ts if candles else None,
        "last_close": latest,
        "last_move": momentum(1),
        "momentum_1h": momentum(periods_per_hour),
        "momentum_4h": momentum(periods_per_hour * 4),
        "rv": realized_volatility(closes, periods_per_year=periods_per_year),
        "volume_1h": recent_volume,
        "volume_ratio_1h_vs_prev": volume_ratio,
        "error": None,
    }


def market_state(asset: str, timeout: int = 4, previous: dict[str, Any] | None = None) -> dict[str, Any]:
    state: dict[str, Any] = {
        "short_term": {},
        "funding": {},
        "open_interest": {},
        "regime": {"etf_flow": "not_configured", "onchain_accumulation": "deferred"},
        "signals": [],
        "errors": [],
    }
    try:
        state["short_term"]["5m"] = _intraday_snapshot(
            asset,
            bar="5m",
            limit=72,
            periods_per_hour=12,
            periods_per_year=365.0 * 24.0 * 12.0,
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001 - scanner should degrade when intraday data is unavailable
        state["short_term"]["5m"] = {"source": "okx", "bar": "5m", "error": str(exc)}
        state["errors"].append(f"okx-5m: {exc}")
    try:
        state["short_term"]["15m"] = _intraday_snapshot(
            asset,
            bar="15m",
            limit=32,
            periods_per_hour=4,
            periods_per_year=365.0 * 24.0 * 4.0,
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001 - scanner should degrade when intraday data is unavailable
        state["short_term"]["15m"] = {"source": "okx", "bar": "15m", "error": str(exc)}
        state["errors"].append(f"okx-15m: {exc}")
    try:
        state["funding"] = fetch_okx_funding_rate(asset, timeout=timeout)
        state["funding"]["error"] = None
    except Exception as exc:  # noqa: BLE001 - funding is an attribution factor, not a scanner blocker
        state["funding"] = {"source": "okx-funding", "error": str(exc)}
        state["errors"].append(f"okx-funding: {exc}")
    try:
        open_interest = fetch_okx_open_interest(asset, timeout=timeout)
        previous_oi = ((previous or {}).get("open_interest") or {}).get("open_interest_usd")
        current_oi = open_interest.get("open_interest_usd")
        if isinstance(previous_oi, (int, float)) and previous_oi > 0 and isinstance(current_oi, (int, float)):
            open_interest["previous_open_interest_usd"] = previous_oi
            open_interest["open_interest_change"] = current_oi / previous_oi - 1.0
        else:
            open_interest["previous_open_interest_usd"] = previous_oi
            open_interest["open_interest_change"] = None
        open_interest["error"] = None
        state["open_interest"] = open_interest
    except Exception as exc:  # noqa: BLE001 - open interest is an attribution factor, not a scanner blocker
        state["open_interest"] = {"source": "okx-open-interest", "error": str(exc)}
        state["errors"].append(f"okx-open-interest: {exc}")
    state["signals"] = funding_oi_tags(
        state.get("funding") or {},
        state.get("open_interest") or {},
        (state.get("short_term") or {}).get("5m") or {},
    )
    return state


def price_context(
    conn,
    asset: str,
    max_window: int = 180,
    realtime_spot: bool = True,
    spot_timeout: int = 4,
) -> dict[str, Any] | None:
    source = preferred_price_source(conn, asset)
    if not source:
        return None
    rows = conn.execute(
        """
        select ts, close
        from crypto_candles
        where asset = ? and source = ? and interval = '1d'
        order by ts desc
        limit ?
        """,
        (asset, source, max_window + 1),
    ).fetchall()
    ordered = list(reversed(rows))
    closes = [float(row["close"]) for row in ordered]
    if not closes:
        return None
    spot = closes[-1]
    spot_source = f"{source}:daily-close"
    spot_fetched_at = ordered[-1]["ts"]
    spot_is_realtime = False
    spot_errors: list[str] = []
    if realtime_spot:
        quote, spot_errors = fetch_best_spot(asset, timeout=spot_timeout)
        if quote:
            spot = quote.price
            spot_source = quote.source
            spot_fetched_at = quote.fetched_at
            spot_is_realtime = True
    vols = {}
    for window in (30, 90, 180):
        prices = closes[-(window + 1) :]
        vols[f"{window}d"] = realized_volatility(prices)
    ewma = ewma_volatility(closes)
    factors = market_state(asset, timeout=spot_timeout, previous=latest_observed_market_state(conn, asset))
    return {
        "asset": asset,
        "source": spot_source,
        "candle_source": source,
        "spot": spot,
        "daily_close": closes[-1],
        "spot_fetched_at": spot_fetched_at,
        "spot_is_realtime": spot_is_realtime,
        "spot_errors": spot_errors,
        "last_ts": ordered[-1]["ts"],
        "candles": len(ordered),
        "volatility": vols,
        "ewma_volatility": ewma,
        "market_state": factors,
    }


def fetch_iv_surfaces(assets: tuple[str, ...], timeout: int = 3) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    surfaces: dict[str, list[dict[str, Any]]] = {}
    errors: dict[str, str] = {}
    for asset in assets:
        try:
            surfaces[asset] = fetch_deribit_option_summaries(asset, timeout=timeout)
        except Exception as exc:  # noqa: BLE001 - scanner must degrade when Deribit is unavailable
            surfaces[asset] = []
            errors[asset] = str(exc)
    return surfaces, errors


def blended_annual_vol(
    context: dict[str, Any],
    vol_window: str,
    iv_quote: Any | None,
    vol_model: str,
) -> tuple[float, dict[str, Any]]:
    rv = float(context["volatility"].get(vol_window) or context["volatility"]["90d"])
    ewma = float(context.get("ewma_volatility") or rv)
    if vol_model == "rv":
        return rv, {
            "source": f"rv-{vol_window}",
            "rv": rv,
            "ewma": ewma,
            "iv": None,
            "weights": {"rv": 1.0, "ewma": 0.0, "iv": 0.0},
        }
    if iv_quote:
        iv = float(iv_quote.annual_vol)
        vol = 0.60 * iv + 0.25 * ewma + 0.15 * rv
        return vol, {
            "source": "iv-ewma-rv",
            "rv": rv,
            "ewma": ewma,
            "iv": iv,
            "weights": {"rv": 0.15, "ewma": 0.25, "iv": 0.60},
            "iv_instrument": iv_quote.instrument_name,
            "iv_expiry": iv_quote.expiry,
            "iv_strike": iv_quote.strike,
        }
    vol = 0.70 * ewma + 0.30 * rv
    return vol, {
        "source": "ewma-rv",
        "rv": rv,
        "ewma": ewma,
        "iv": None,
        "weights": {"rv": 0.30, "ewma": 0.70, "iv": 0.0},
    }


def scanner_markets(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select *
        from barrier_markets
        where asset in ('BTC', 'ETH')
          and coalesce(active, 1) = 1
          and coalesce(closed, 0) = 0
          and end_date is not null
          and yes_price is not null
        order by end_date asc, liquidity desc, volume desc
        """
    ).fetchall()
    return [dict(row) for row in rows]


def normalized_direction(market: dict[str, Any]) -> str:
    question = str(market.get("question") or "").lower()
    if (
        "dip" in question
        or "below" in question
        or "under" in question
        or "drop" in question
        or "less than" in question
        or "lower than" in question
    ):
        return "hit_below"
    return str(market.get("direction") or "hit_above")


def is_simple_touch_market(market: dict[str, Any]) -> bool:
    question = str(market.get("question") or "").lower()
    if " first" in question and " or " in question:
        return False
    return any(token in question for token in ("hit", "reach", "dip", "drop"))


def parse_book_levels(levels: Any, reverse: bool = False) -> list[dict[str, float]]:
    parsed: list[dict[str, float]] = []
    if not isinstance(levels, list):
        return parsed
    for level in levels:
        price = float_or_none(level.get("price") if isinstance(level, dict) else None)
        size = float_or_none(level.get("size") if isinstance(level, dict) else None)
        if price is None or size is None:
            continue
        if price <= 0 or size <= 0:
            continue
        parsed.append({"price": price, "size": size})
    return sorted(parsed, key=lambda item: item["price"], reverse=reverse)


def fill_buy_notional(asks: list[dict[str, float]], max_notional: float) -> dict[str, float | bool | None]:
    remaining = max(0.0, max_notional)
    spent = 0.0
    shares = 0.0
    for level in asks:
        if remaining <= 0:
            break
        level_cost = level["price"] * level["size"]
        spend = min(remaining, level_cost)
        spent += spend
        shares += spend / level["price"]
        remaining -= spend
    avg_price = spent / shares if shares > 0 else None
    return {
        "requested_notional": max_notional,
        "executable_notional": spent,
        "executable_shares": shares,
        "avg_price": avg_price,
        "complete_fill": remaining <= 0.000001,
    }


def parse_orderbook_timestamp(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return parse_datetime(str(value))
    if numeric > 10_000_000_000:
        numeric /= 1000
    try:
        return datetime.fromtimestamp(numeric, timezone.utc)
    except (OSError, OverflowError, ValueError):
        return None


def order_book_metrics(
    token_id: str | None,
    max_notional: float,
    source: str = "polymtrade",
    timeout: int = 4,
    max_age_seconds: int = 120,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    if not token_id:
        return {"orderbook_source": "missing-token", "orderbook_error": "missing yes_token_id"}
    try:
        book = fetch_order_book(token_id, source=source, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - scanner should degrade to cached price
        return {"orderbook_source": source, "orderbook_error": str(exc)}

    bids = parse_book_levels(book.get("bids"), reverse=True)
    asks = parse_book_levels(book.get("asks"), reverse=False)
    best_bid = bids[0]["price"] if bids else None
    best_ask = asks[0]["price"] if asks else None
    fill = fill_buy_notional(asks, max_notional) if asks else {}
    avg_price = fill.get("avg_price")
    book_at = parse_orderbook_timestamp(book.get("timestamp"))
    book_age = (now - book_at).total_seconds() if book_at else None
    if book_age is not None:
        book_age = max(0.0, book_age)
    return {
        "orderbook_source": source,
        "orderbook_timestamp": book.get("timestamp"),
        "orderbook_at": book_at.isoformat() if book_at else None,
        "orderbook_age_seconds": book_age,
        "orderbook_is_fresh": book_age is not None and book_age <= max_age_seconds,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": (best_ask - best_bid) if best_bid is not None and best_ask is not None else None,
        "last_trade_price": float_or_none(book.get("last_trade_price")),
        "tick_size": float_or_none(book.get("tick_size")),
        "min_order_size": float_or_none(book.get("min_order_size")),
        "executable_price": avg_price,
        "executable_notional": fill.get("executable_notional"),
        "executable_shares": fill.get("executable_shares"),
        "complete_fill": fill.get("complete_fill"),
        "orderbook_error": None,
    }


def add_review(
    row: dict[str, Any],
    edge_threshold: float,
    orderbook_enabled: bool,
    require_realtime_spot: bool,
    max_book_age_seconds: int,
    max_spread: float,
) -> None:
    checks: list[dict[str, str]] = []
    blockers: list[str] = []

    def check(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})
        if status == "fail":
            blockers.append(detail)

    if row.get("already_touched"):
        check("touch", "verify", "现货已触及目标，需要人工核验")
    else:
        check("touch", "pass", "尚未触及目标")

    if require_realtime_spot:
        if row.get("spot_is_realtime"):
            check("spot", "pass", f"实时现货来自 {row.get('spot_source')}")
        else:
            check("spot", "fail", "现货退回日线收盘价")
    elif row.get("spot_is_realtime"):
        check("spot", "pass", f"实时现货来自 {row.get('spot_source')}")
    else:
        check("spot", "warn", "使用最新日线收盘价")

    vol_source = str(row.get("annual_vol_source") or "")
    if "iv" in vol_source:
        check("vol", "pass", f"波动率使用 {vol_source}")
    elif vol_source:
        check("vol", "warn", f"波动率使用 {vol_source}")

    if orderbook_enabled:
        if row.get("pricing_source") != "orderbook":
            if row.get("pricing_source") == "cached-orderbook-not-sampled":
                check("book", "warn", row.get("orderbook_error") or "未进入本次盘口抽样范围")
            else:
                check("book", "fail", row.get("orderbook_error") or "实时盘口不可用")
        else:
            age = row.get("orderbook_age_seconds")
            if row.get("orderbook_is_fresh"):
                check("book", "pass", f"盘口 age {age:.0f}s" if isinstance(age, (int, float)) else "盘口时间戳新鲜")
            else:
                check("book", "fail", f"盘口超过 {max_book_age_seconds}s 未更新")

            if row.get("executable_price") is None:
                check("fill", "fail", "没有可买入 ask 深度")
            elif row.get("complete_fill"):
                check("fill", "pass", "测试金额可完整成交")
            else:
                check("fill", "fail", "测试金额只能部分成交")

            spread = row.get("spread")
            if spread is None:
                check("spread", "warn", "价差不可用")
            elif float(spread) <= max_spread:
                check("spread", "pass", f"价差 {float(spread):.3f}")
            else:
                check("spread", "fail", f"价差 {float(spread):.3f} 高于 {max_spread:.3f}")

    if row.get("net_edge") is None:
        check("edge", "fail", "净 edge 不可用")
    elif float(row["net_edge"]) >= edge_threshold:
        check("edge", "pass", "净 edge 达标")
    elif float(row["net_edge"]) <= -edge_threshold:
        check("edge", "fail", "净 edge 显著为负")
    else:
        check("edge", "warn", "净 edge 未达阈值")

    row["review_checks"] = checks
    row["review_blockers"] = blockers
    if row.get("already_touched"):
        row["action"] = "verify"
        row["review_status"] = "verify"
    elif blockers:
        row["action"] = "avoid" if row.get("net_edge") is not None and float(row["net_edge"]) <= -edge_threshold else "watch"
        row["review_status"] = "blocked"
    elif (
        row.get("net_edge") is not None
        and float(row["net_edge"]) >= edge_threshold
        and (not orderbook_enabled or row.get("pricing_source") == "orderbook")
    ):
        row["action"] = "candidate"
        row["review_status"] = "passed"
    else:
        row["action"] = "watch"
        row["review_status"] = "watch"
    assign_opportunity_tier(row, edge_threshold=edge_threshold)


def assign_opportunity_tier(row: dict[str, Any], edge_threshold: float) -> None:
    edge = float_or_none(row.get("net_edge"))
    blockers = row.get("review_blockers") or []
    if row.get("action") == "candidate":
        row["opportunity_tier"] = "candidate"
        row["opportunity_tier_label"] = "候选"
        row["opportunity_tier_reason"] = "净 edge 达标且盘口复核通过"
    elif edge is not None and edge >= max(0.01, edge_threshold * 0.5):
        row["opportunity_tier"] = "near"
        row["opportunity_tier_label"] = "准候选"
        row["opportunity_tier_reason"] = "edge 接近阈值" if not blockers else f"edge 接近阈值；{blockers[0]}"
    elif edge is not None and edge >= 0:
        row["opportunity_tier"] = "research"
        row["opportunity_tier_label"] = "研究机会"
        row["opportunity_tier_reason"] = "模型概率高于市场但安全边际不足" if not blockers else blockers[0]
    elif blockers:
        row["opportunity_tier"] = "blocked"
        row["opportunity_tier_label"] = "阻断"
        row["opportunity_tier_reason"] = blockers[0]
    else:
        row["opportunity_tier"] = "ignore"
        row["opportunity_tier_label"] = "忽略"
        row["opportunity_tier_reason"] = "模型概率未高于市场"


def opportunity_sort_key(row: dict[str, Any]) -> tuple[int, int, float, float]:
    tier_priority = {"candidate": 5, "near": 4, "research": 3, "blocked": 2, "ignore": 1}.get(
        str(row.get("opportunity_tier")),
        0,
    )
    priority = {"candidate": 3, "watch": 2, "verify": 1, "avoid": 0}.get(str(row.get("action")), 0)
    return (tier_priority, priority, float(row.get("net_edge") or 0.0), float(row.get("liquidity") or 0.0))


def scan_opportunities(
    conn,
    limit: int = 50,
    edge_threshold: float = 0.02,
    fee_rate: float = 0.04,
    slippage_bps: float = 50.0,
    min_liquidity: float = 500.0,
    min_yes_price: float = 0.001,
    max_yes_price: float = 0.995,
    simulations: int = 1_500,
    vol_window: str = "90d",
    vol_model: str = "factor",
    iv_timeout: int = 3,
    orderbook: bool = False,
    book_limit: int = 30,
    executable_notional: float = 100.0,
    book_source: str = "polymtrade",
    book_timeout: int = 4,
    max_book_age_seconds: int = 120,
    max_spread: float = 0.04,
    realtime_spot: bool = True,
    require_realtime_spot: bool = True,
    spot_timeout: int = 4,
    min_expiry_minutes: int = 30,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    macro = macro_context(now=now, horizon_hours=168)
    contexts = {
        asset: price_context(conn, asset, realtime_spot=realtime_spot, spot_timeout=spot_timeout)
        for asset in ("BTC", "ETH")
    }
    for context in contexts.values():
        if context:
            context["macro"] = macro
    iv_surfaces, iv_errors = fetch_iv_surfaces(("BTC", "ETH"), timeout=iv_timeout) if vol_model == "factor" else ({}, {})
    for asset, context in contexts.items():
        if context:
            context["iv_source"] = "deribit-atm-iv" if iv_surfaces.get(asset) else None
            context["iv_error"] = iv_errors.get(asset)
            context["vol_model"] = vol_model
    opportunities: list[dict[str, Any]] = []
    skipped = 0
    expired_skipped = 0
    near_expiry_skipped = 0
    scanned = 0
    min_expiry_days = max(0, min_expiry_minutes) / 1_440.0

    for market in scanner_markets(conn):
        if not is_simple_touch_market(market):
            skipped += 1
            continue
        context = contexts.get(market["asset"])
        if not context:
            skipped += 1
            continue
        end_at = parse_datetime(market.get("end_date"))
        if not end_at:
            skipped += 1
            continue
        days_to_expiry = (end_at - now).total_seconds() / 86_400.0
        if days_to_expiry <= 0:
            skipped += 1
            expired_skipped += 1
            continue
        if min_expiry_days and days_to_expiry < min_expiry_days:
            skipped += 1
            near_expiry_skipped += 1
            continue
        yes_price = float_or_none(market.get("yes_price"))
        barrier = float_or_none(market.get("barrier"))
        spot = float_or_none(context.get("spot"))
        if yes_price is None or barrier is None or spot is None:
            skipped += 1
            continue
        if yes_price < min_yes_price or yes_price > max_yes_price:
            skipped += 1
            continue
        liquidity = float_or_none(market.get("liquidity")) or 0.0
        if liquidity < min_liquidity:
            skipped += 1
            continue

        scanned += 1
        direction = normalized_direction(market)
        already_touched = (
            spot >= barrier
            if direction == "hit_above"
            else spot <= barrier
        )
        iv_quote = None
        if vol_model == "factor":
            iv_quote = select_atm_iv(
                market["asset"],
                iv_surfaces.get(market["asset"], []),
                spot=spot,
                days_to_expiry=days_to_expiry,
                now=now,
            )
        vol, vol_components = blended_annual_vol(context, vol_window, iv_quote, vol_model)
        state = context.get("market_state") or {}
        five_minute = ((state.get("short_term") or {}).get("5m") or {})
        fifteen_minute = ((state.get("short_term") or {}).get("15m") or {})
        funding = state.get("funding") or {}
        open_interest = state.get("open_interest") or {}
        macro_risk = macro_risk_for_market(now, end_at)
        result = monte_carlo_touch_probability(
            BarrierInput(
                spot=spot,
                barrier=barrier,
                days_to_expiry=days_to_expiry,
                annual_vol=vol,
                direction=direction,
            ),
            simulations=simulations,
            steps_per_day=4,
            seed=stable_seed(market["market_id"], context["spot"], market["barrier"], days_to_expiry, direction),
        )
        costs = edge_for_yes(result.adjusted_probability, yes_price, fee_rate, slippage_bps)
        simple_annualized_roi = costs["roi"] * (365.0 / days_to_expiry) if days_to_expiry > 0 else 0.0
        opportunities.append(
            {
                "market_id": market["market_id"],
                "asset": market["asset"],
                "question": market["question"],
                "direction": direction,
                "spot": spot,
                "barrier": barrier,
                "days_to_expiry": days_to_expiry,
                "minutes_to_expiry": days_to_expiry * 1_440.0,
                "end_date": market["end_date"],
                "market_yes_price": yes_price,
                "market_no_price": market.get("no_price"),
                "yes_token_id": market.get("yes_token_id"),
                "model_probability": result.adjusted_probability,
                "gross_edge": result.adjusted_probability - yes_price,
                "net_edge": costs["net_ev"],
                "roi": costs["roi"],
                "annualized_roi": simple_annualized_roi,
                "taker_fee": costs["taker_fee"],
                "slippage": costs["slippage"],
                "annual_vol": vol,
                "annual_vol_source": vol_components["source"],
                "vol_components": vol_components,
                "already_touched": already_touched,
                "volume": market.get("volume"),
                "liquidity": liquidity,
                "source": market.get("source"),
                "spot_source": context["source"],
                "spot_fetched_at": context.get("spot_fetched_at"),
                "spot_is_realtime": context.get("spot_is_realtime"),
                "daily_close": context.get("daily_close"),
                "market_state": state,
                "short_momentum_1h": five_minute.get("momentum_1h"),
                "short_momentum_4h": five_minute.get("momentum_4h"),
                "short_rv_5m": five_minute.get("rv"),
                "last_5m_move": five_minute.get("last_move"),
                "momentum_15m_1h": fifteen_minute.get("momentum_1h"),
                "funding_rate": funding.get("funding_rate"),
                "next_funding_rate": funding.get("next_funding_rate"),
                "open_interest_usd": open_interest.get("open_interest_usd"),
                "open_interest_change": open_interest.get("open_interest_change"),
                "factor_signals": state.get("signals") or [],
                "macro_risk": macro_risk,
                "macro_risk_level": macro_risk.get("risk_level"),
                "macro_event_labels": macro_risk.get("labels") or [],
                "action": "watch",
                "review_status": "unreviewed",
                "pricing_source": "cached",
            }
        )

    for row in opportunities:
        add_review(
            row,
            edge_threshold=edge_threshold,
            orderbook_enabled=False,
            require_realtime_spot=require_realtime_spot,
            max_book_age_seconds=max_book_age_seconds,
            max_spread=max_spread,
        )
    opportunities.sort(key=opportunity_sort_key, reverse=True)
    if orderbook:
        for row in opportunities[:book_limit]:
            book = order_book_metrics(
                row.get("yes_token_id"),
                executable_notional,
                source=book_source,
                timeout=book_timeout,
                max_age_seconds=max_book_age_seconds,
                now=now,
            )
            row.update(book)
            executable_price = row.get("executable_price") or row.get("best_ask")
            if executable_price is None:
                row["pricing_source"] = "cached-orderbook-unavailable"
            else:
                executable_costs = edge_for_yes(row["model_probability"], float(executable_price), fee_rate, slippage_bps)
                row["market_yes_price"] = float(executable_price)
                row["gross_edge"] = row["model_probability"] - float(executable_price)
                row["net_edge"] = executable_costs["net_ev"]
                row["roi"] = executable_costs["roi"]
                row["annualized_roi"] = (
                    executable_costs["roi"] * (365.0 / row["days_to_expiry"]) if row["days_to_expiry"] > 0 else 0.0
                )
                row["taker_fee"] = executable_costs["taker_fee"]
                row["slippage"] = executable_costs["slippage"]
                row["pricing_source"] = "orderbook"
        for row in opportunities:
            if row.get("pricing_source") == "cached" and row.get("orderbook_error") is None:
                row["pricing_source"] = "cached-orderbook-not-sampled"
                row["orderbook_error"] = "未进入本次盘口抽样范围"
            add_review(
                row,
                edge_threshold=edge_threshold,
                orderbook_enabled=True,
                require_realtime_spot=require_realtime_spot,
                max_book_age_seconds=max_book_age_seconds,
                max_spread=max_spread,
            )
        opportunities.sort(key=opportunity_sort_key, reverse=True)
    top = opportunities[:limit]
    candidates = [row for row in opportunities if row["action"] == "candidate"]
    near_candidates = [row for row in opportunities if row.get("opportunity_tier") == "near"]
    research_opportunities = [row for row in opportunities if row.get("opportunity_tier") == "research"]
    return {
        "generated_at": now.isoformat(),
        "assumptions": {
            "edge_threshold": edge_threshold,
            "fee_rate": fee_rate,
            "slippage_bps": slippage_bps,
            "min_liquidity": min_liquidity,
            "min_yes_price": min_yes_price,
            "max_yes_price": max_yes_price,
            "simulations": simulations,
            "vol_window": vol_window,
            "vol_model": vol_model,
            "iv_timeout": iv_timeout,
            "iv_source": "deribit-atm-iv",
            "orderbook": orderbook,
            "book_limit": book_limit,
            "book_source": book_source,
            "executable_notional": executable_notional,
            "book_timeout": book_timeout,
            "max_book_age_seconds": max_book_age_seconds,
            "max_spread": max_spread,
            "realtime_spot": realtime_spot,
            "require_realtime_spot": require_realtime_spot,
            "spot_timeout": spot_timeout,
            "min_expiry_minutes": min_expiry_minutes,
        },
        "contexts": {asset: context for asset, context in contexts.items() if context},
        "summary": {
            "markets_total": len(scanner_markets(conn)),
            "markets_scanned": scanned,
            "markets_skipped": skipped,
            "expired_skipped": expired_skipped,
            "near_expiry_skipped": near_expiry_skipped,
            "opportunities": len(opportunities),
            "candidates": len(candidates),
            "near_candidates": len(near_candidates),
            "research_opportunities": len(research_opportunities),
            "best_net_edge": top[0]["net_edge"] if top else None,
            "best_roi": top[0]["roi"] if top else None,
            "orderbook_priced": sum(1 for row in opportunities if row.get("pricing_source") == "orderbook"),
            "stale_orderbooks": sum(1 for row in opportunities if row.get("pricing_source") == "orderbook" and not row.get("orderbook_is_fresh")),
            "partial_fills": sum(1 for row in opportunities if row.get("pricing_source") == "orderbook" and row.get("complete_fill") is False),
            "wide_spreads": sum(1 for row in opportunities if row.get("spread") is not None and float(row["spread"]) > max_spread),
            "live_spot_assets": sum(1 for context in contexts.values() if context and context.get("spot_is_realtime")),
            "iv_assets": sum(1 for context in contexts.values() if context and context.get("iv_source")),
            "short_term_assets": sum(
                1
                for context in contexts.values()
                if context and (((context.get("market_state") or {}).get("short_term") or {}).get("5m") or {}).get("error") is None
            ),
            "funding_assets": sum(
                1
                for context in contexts.values()
                if context and ((context.get("market_state") or {}).get("funding") or {}).get("error") is None
            ),
            "open_interest_assets": sum(
                1
                for context in contexts.values()
                if context and ((context.get("market_state") or {}).get("open_interest") or {}).get("error") is None
            ),
            "factor_signal_assets": sum(
                1 for context in contexts.values() if context and ((context.get("market_state") or {}).get("signals") or [])
            ),
            "macro_active_events": macro.get("active_count"),
            "macro_upcoming_events": macro.get("upcoming_count"),
            "macro_risk_rows": sum(1 for row in opportunities if row.get("macro_risk_level") in {"high", "medium"}),
        },
        "opportunities": top,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan BTC/ETH barrier markets for model-vs-market edge")
    parser.add_argument("--db", default="polymtrade.sqlite")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--edge-threshold", type=float, default=0.02)
    parser.add_argument("--min-liquidity", type=float, default=500.0)
    parser.add_argument("--simulations", type=int, default=1_500)
    parser.add_argument("--vol-window", choices=("30d", "90d", "180d"), default="90d")
    parser.add_argument("--vol-model", choices=("factor", "rv"), default="factor")
    parser.add_argument("--iv-timeout", type=int, default=3)
    parser.add_argument("--orderbook", action="store_true", help="Price top results from live YES order books")
    parser.add_argument("--book-limit", type=int, default=30)
    parser.add_argument("--executable-notional", type=float, default=100.0)
    parser.add_argument("--book-timeout", type=int, default=4)
    parser.add_argument("--max-book-age-seconds", type=int, default=120)
    parser.add_argument("--max-spread", type=float, default=0.04)
    parser.add_argument("--daily-spot", action="store_true", help="Use latest daily close instead of live spot ticker")
    parser.add_argument("--allow-daily-spot", action="store_true", help="Do not block candidates when live spot is unavailable")
    parser.add_argument("--min-expiry-minutes", type=int, default=30, help="Skip markets expiring sooner than this threshold")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with connect(args.db) as conn:
        payload = scan_opportunities(
            conn,
            limit=args.limit,
            edge_threshold=args.edge_threshold,
            min_liquidity=args.min_liquidity,
            simulations=args.simulations,
            vol_window=args.vol_window,
            vol_model=args.vol_model,
            iv_timeout=args.iv_timeout,
            orderbook=args.orderbook,
            book_limit=args.book_limit,
            executable_notional=args.executable_notional,
            book_timeout=args.book_timeout,
            max_book_age_seconds=args.max_book_age_seconds,
            max_spread=args.max_spread,
            realtime_spot=not args.daily_spot,
            require_realtime_spot=not args.allow_daily_spot,
            min_expiry_minutes=args.min_expiry_minutes,
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
