from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from polymtrade.research.scanner import order_book_metrics, parse_datetime, preferred_price_source

CURRENT_RULES_FROM = datetime(2026, 5, 26, tzinfo=timezone.utc)
DEFAULT_MAX_DAYS_TO_EXPIRY = 14.0
DEFAULT_MAX_SPREAD = 0.04
DEFAULT_MAX_BOOK_AGE_SECONDS = 120.0


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _observation_end_date(row: dict[str, Any]) -> datetime | None:
    try:
        raw = json.loads(row.get("raw_json") or "{}")
    except json.JSONDecodeError:
        raw = {}
    return parse_datetime(raw.get("end_date"))


def _candidate_rows(conn, limit: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select *
        from scanner_observations
        where action = 'candidate'
        order by id desc
        limit ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def _candles_after_observation(
    conn,
    asset: str,
    observed_at: datetime,
    end_at: datetime,
) -> list[dict[str, Any]]:
    source = preferred_price_source(conn, asset)
    if not source:
        return []
    start_key = observed_at.date().isoformat()
    end_key = f"{end_at.date().isoformat()}T23:59:59+00:00"
    rows = conn.execute(
        """
        select ts, high, low, close
        from crypto_candles
        where asset = ?
          and source = ?
          and interval = '1d'
          and ts >= ?
          and ts <= ?
        order by ts asc
        """,
        (asset, source, start_key, end_key),
    ).fetchall()
    return [dict(row) for row in rows]


def _hit_barrier(row: dict[str, Any], candles: list[dict[str, Any]]) -> bool:
    barrier = float(row["barrier"])
    direction = str(row.get("direction") or "hit_above")
    if direction == "hit_below":
        return any(float(candle["low"]) <= barrier for candle in candles)
    return any(float(candle["high"]) >= barrier for candle in candles)


def _risk_level(required_move_pct: float | None, days_remaining: float | None, safety_margin: float | None) -> str:
    score = 0
    if required_move_pct is None:
        score += 2
    else:
        move = abs(required_move_pct)
        if move >= 0.08:
            score += 3
        elif move >= 0.05:
            score += 2
        elif move >= 0.03:
            score += 1
    if days_remaining is None:
        score += 2
    elif days_remaining < 2:
        score += 3
    elif days_remaining < 5:
        score += 2
    elif days_remaining < 10:
        score += 1
    if safety_margin is None:
        score += 1
    elif safety_margin < 0.02:
        score += 2
    elif safety_margin < 0.05:
        score += 1
    if score >= 6:
        return "extreme"
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _risk_label(level: str) -> str:
    return {
        "low": "低风险",
        "medium": "中风险",
        "high": "高风险",
        "extreme": "极高风险",
    }.get(level, "未知风险")


def _risk_panel(row: dict[str, Any], now: datetime, stake: float, price: float, end_at: datetime | None) -> dict[str, Any]:
    spot = _float_or_none(row.get("spot"))
    barrier = _float_or_none(row.get("barrier"))
    model_probability = _float_or_none(row.get("model_probability"))
    spread = _float_or_none(row.get("spread"))
    orderbook_age_seconds = _float_or_none(row.get("orderbook_age_seconds"))
    required_move_pct = None
    if spot and barrier:
        required_move_pct = (barrier - spot) / spot
        if str(row.get("direction") or "") == "hit_below":
            required_move_pct = -abs(required_move_pct)
    days_remaining = None
    if end_at:
        days_remaining = max((end_at - now).total_seconds() / 86400, 0.0)
    breakeven_probability = price if price > 0 else None
    safety_margin = None
    if model_probability is not None and breakeven_probability is not None:
        safety_margin = model_probability - breakeven_probability
    profit_if_win = stake / price - stake if price > 0 else None
    loss_if_lose = -stake
    level = _risk_level(required_move_pct, days_remaining, safety_margin)
    notes = [
        "二元合约若未触及目标，投入本金全部亏损。",
        "触及概率不是收盘概率，短期大幅波动样本对模型误差很敏感。",
    ]
    if safety_margin is not None and safety_margin < 0.05:
        notes.append("安全边际偏薄，盘口轻微变化就可能吞掉 edge。")
    if spread is None:
        notes.append("缺少 spread 数据，盘口风险需要人工复核。")
    elif spread > DEFAULT_MAX_SPREAD:
        notes.append("盘口价差偏宽，真实成交 ROI 可能明显下降。")
    return {
        "required_move_pct": required_move_pct,
        "days_remaining": days_remaining,
        "breakeven_probability": breakeven_probability,
        "model_probability": model_probability,
        "safety_margin": safety_margin,
        "max_loss_pct": 1.0,
        "profit_if_win": profit_if_win,
        "loss_if_lose": loss_if_lose,
        "risk_level": level,
        "risk_label": _risk_label(level),
        "spread": spread,
        "orderbook_age_seconds": orderbook_age_seconds,
        "notes": notes,
    }


def _position_recommendation(trade: dict[str, Any], metrics: dict[str, Any]) -> tuple[str, str, list[str]]:
    risk = trade.get("risk") or {}
    notes: list[str] = []
    spread = _float_or_none(metrics.get("spread"))
    best_ask = _float_or_none(metrics.get("best_ask"))
    model_probability = _float_or_none(trade.get("model_probability"))
    unrealized_return = _float_or_none(trade.get("unrealized_return"))
    days_remaining = _float_or_none(risk.get("days_remaining"))
    required_move_pct = _float_or_none(risk.get("required_move_pct"))

    if metrics.get("orderbook_error"):
        return "review", "盘口不可用，人工复核", [str(metrics.get("orderbook_error"))]
    if not metrics.get("orderbook_is_fresh"):
        notes.append("盘口时间戳不新鲜")
    if spread is None:
        notes.append("缺少当前 spread")
    elif spread > DEFAULT_MAX_SPREAD:
        notes.append("当前 spread 偏宽")
    if best_ask is not None and model_probability is not None:
        edge_to_current_ask = model_probability - best_ask
        if edge_to_current_ask < -0.02:
            return "exit", "edge 已转负，建议退出观察", [f"模型概率低于当前 ask {abs(edge_to_current_ask):.1%}"]
        if edge_to_current_ask < 0.01:
            notes.append("安全边际接近消失")
    if days_remaining is not None and days_remaining < 1:
        notes.append("距离到期不足 1 天")
    if required_move_pct is not None and days_remaining is not None and days_remaining < 3 and abs(required_move_pct) > 0.04:
        notes.append("短时间内仍需较大价格变动")
    if unrealized_return is not None and unrealized_return > 0.25:
        notes.append("已有可观浮盈，可观察是否锁定")
    if any("安全边际" in item or "spread" in item or "到期" in item or "较大价格变动" in item or "浮盈" in item for item in notes):
        return "review", "观察退出", notes
    return "hold", "继续持有观察", notes or ["原始 edge 尚未被当前盘口明显否定"]


def position_management_report(
    conn,
    limit: int = 100,
    stake: float = 100.0,
    now: datetime | None = None,
    book_timeout: int = 4,
    max_book_age_seconds: int = int(DEFAULT_MAX_BOOK_AGE_SECONDS),
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    paper = paper_trading_report(conn, limit=limit, stake=stake, now=now)
    trades = [item for item in paper.get("trades", []) if item.get("status") == "open"]
    positions: list[dict[str, Any]] = []
    for trade in trades:
        row = conn.execute(
            "select raw_json from scanner_observations where id = ?",
            (trade.get("observation_id"),),
        ).fetchone()
        raw = {}
        if row:
            try:
                raw = json.loads(row["raw_json"] or "{}")
            except json.JSONDecodeError:
                raw = {}
        token_id = raw.get("yes_token_id")
        metrics = order_book_metrics(
            str(token_id) if token_id else None,
            max_notional=stake,
            timeout=book_timeout,
            max_age_seconds=max_book_age_seconds,
            now=now,
        )
        entry_price = _float_or_none(trade.get("market_yes_price")) or 0.0
        best_bid = _float_or_none(metrics.get("best_bid"))
        shares = stake / entry_price if entry_price > 0 else None
        exit_value = shares * best_bid if shares is not None and best_bid is not None else None
        unrealized_pnl = exit_value - stake if exit_value is not None else None
        unrealized_return = unrealized_pnl / stake if unrealized_pnl is not None and stake else None
        trade["unrealized_return"] = unrealized_return
        action, label, notes = _position_recommendation(trade, metrics)
        positions.append(
            {
                "observation_id": trade.get("observation_id"),
                "market_id": trade.get("market_id"),
                "asset": trade.get("asset"),
                "question": trade.get("question"),
                "direction": trade.get("direction"),
                "spot": trade.get("spot"),
                "barrier": trade.get("barrier"),
                "end_date": trade.get("end_date"),
                "entry_price": entry_price,
                "stake": stake,
                "shares": shares,
                "current_best_bid": best_bid,
                "current_best_ask": _float_or_none(metrics.get("best_ask")),
                "spread": _float_or_none(metrics.get("spread")),
                "orderbook_age_seconds": _float_or_none(metrics.get("orderbook_age_seconds")),
                "orderbook_is_fresh": metrics.get("orderbook_is_fresh"),
                "exit_value": exit_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_return": unrealized_return,
                "model_probability": trade.get("model_probability"),
                "risk": trade.get("risk"),
                "recommendation": action,
                "recommendation_label": label,
                "notes": notes,
            }
        )
    counts = {"hold": 0, "review": 0, "exit": 0}
    for item in positions:
        key = str(item.get("recommendation"))
        if key in counts:
            counts[key] += 1
    return {
        "generated_at": now.isoformat(),
        "assumptions": {
            "mode": "read-only paper position management",
            "exit_price": "YES best bid; this is the executable side for selling YES",
            "book_timeout": book_timeout,
            "max_book_age_seconds": max_book_age_seconds,
        },
        "summary": {
            "positions": len(positions),
            "hold": counts["hold"],
            "review": counts["review"],
            "exit": counts["exit"],
            "unrealized_pnl": sum(float(item["unrealized_pnl"] or 0.0) for item in positions),
            "exit_value": sum(float(item["exit_value"] or 0.0) for item in positions),
        },
        "positions": positions,
    }


def _paper_trade(conn, row: dict[str, Any], now: datetime, default_stake: float) -> dict[str, Any]:
    observed_at = parse_datetime(row.get("created_at")) or now
    end_at = _observation_end_date(row)
    price = float(row.get("market_yes_price") or 0.0)
    stake = float(row.get("executable_notional") or default_stake)
    result = {
        "observation_id": row["id"],
        "run_id": row["run_id"],
        "created_at": row["created_at"],
        "market_id": row["market_id"],
        "asset": row["asset"],
        "question": row["question"],
        "direction": row["direction"],
        "spot": row["spot"],
        "barrier": row["barrier"],
        "end_date": end_at.isoformat() if end_at else None,
        "market_yes_price": price,
        "model_probability": row["model_probability"],
        "net_edge": row["net_edge"],
        "roi": row["roi"],
        "stake": stake,
        "status": "unresolved",
        "hit": None,
        "pnl": 0.0,
        "return_pct": 0.0,
        "evidence": "waiting for end_date",
        "risk": _risk_panel(row, now, stake, price, end_at),
    }
    if not end_at:
        result["status"] = "unknown"
        result["evidence"] = "missing end_date"
        return result
    if price <= 0:
        result["status"] = "unknown"
        result["evidence"] = "missing market yes price"
        return result

    cutoff = min(now, end_at)
    candles = _candles_after_observation(conn, str(row["asset"]), observed_at, cutoff)
    hit = _hit_barrier(row, candles)
    result["hit"] = hit
    result["evidence"] = f"{len(candles)} daily candles checked"
    if hit:
        payout = stake / price
        pnl = payout - stake
        result["status"] = "won"
        result["pnl"] = pnl
        result["return_pct"] = pnl / stake if stake else 0.0
    elif end_at <= now:
        result["status"] = "lost"
        result["pnl"] = -stake
        result["return_pct"] = -1.0
    else:
        result["status"] = "open"
        result["pnl"] = 0.0
        result["return_pct"] = 0.0
    return result


def _truthy(value: Any) -> bool:
    return value in {True, 1, "1", "true", "True", "yes"}


def _paper_row_reject_reasons(
    row: dict[str, Any],
    now: datetime,
    *,
    max_days_to_expiry: float,
    max_spread: float,
    max_book_age_seconds: float,
    current_rules_from: datetime,
) -> list[str]:
    reasons: list[str] = []
    observed_at = parse_datetime(row.get("created_at"))
    end_at = _observation_end_date(row)
    if not observed_at:
        reasons.append("missing observation time")
    elif observed_at < current_rules_from:
        reasons.append(f"legacy rules before {current_rules_from.date().isoformat()}")
    if not end_at:
        reasons.append("missing end date")
    elif end_at <= now:
        reasons.append("already expired")
    try:
        days_to_expiry = float(row.get("days_to_expiry"))
        if days_to_expiry > max_days_to_expiry:
            reasons.append(f"horizon > {max_days_to_expiry:g}d")
        if days_to_expiry <= 0:
            reasons.append("expired at observation")
    except (TypeError, ValueError):
        reasons.append("missing days to expiry")
    if row.get("pricing_source") != "orderbook":
        reasons.append("not orderbook priced")
    if not _truthy(row.get("complete_fill")):
        reasons.append("incomplete executable fill")
    try:
        spread = row.get("spread")
        if spread is None:
            reasons.append("missing spread")
        elif float(spread) > max_spread:
            reasons.append(f"spread > {max_spread:.0%}")
    except (TypeError, ValueError):
        reasons.append("invalid spread")
    try:
        age = row.get("orderbook_age_seconds")
        if age is None:
            reasons.append("missing orderbook age")
        elif float(age) > max_book_age_seconds:
            reasons.append(f"orderbook age > {max_book_age_seconds:g}s")
    except (TypeError, ValueError):
        reasons.append("invalid orderbook age")
    return reasons


def _select_paper_rows(
    rows: list[dict[str, Any]],
    now: datetime,
    *,
    current_only: bool,
    max_days_to_expiry: float,
    max_spread: float,
    max_book_age_seconds: float,
    current_rules_from: datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    seen_markets: set[str] = set()
    for row in rows:
        reasons = _paper_row_reject_reasons(
            row,
            now,
            max_days_to_expiry=max_days_to_expiry,
            max_spread=max_spread,
            max_book_age_seconds=max_book_age_seconds,
            current_rules_from=current_rules_from,
        )
        market_id = str(row.get("market_id") or "")
        if market_id and market_id in seen_markets:
            reasons.append("duplicate market; newer observation kept")
        if reasons and current_only:
            excluded.append(
                {
                    "observation_id": row.get("id"),
                    "market_id": row.get("market_id"),
                    "asset": row.get("asset"),
                    "question": row.get("question"),
                    "created_at": row.get("created_at"),
                    "reasons": reasons,
                }
            )
            continue
        selected.append(row)
        if market_id:
            seen_markets.add(market_id)
    return selected, excluded


def paper_trading_report(
    conn,
    limit: int = 100,
    stake: float = 100.0,
    now: datetime | None = None,
    current_only: bool = True,
    max_days_to_expiry: float = DEFAULT_MAX_DAYS_TO_EXPIRY,
    max_spread: float = DEFAULT_MAX_SPREAD,
    max_book_age_seconds: float = DEFAULT_MAX_BOOK_AGE_SECONDS,
    current_rules_from: datetime = CURRENT_RULES_FROM,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    raw_rows = _candidate_rows(conn, limit)
    rows, excluded = _select_paper_rows(
        raw_rows,
        now,
        current_only=current_only,
        max_days_to_expiry=max_days_to_expiry,
        max_spread=max_spread,
        max_book_age_seconds=max_book_age_seconds,
        current_rules_from=current_rules_from,
    )
    trades = []
    for row in rows:
        trades.append(_paper_trade(conn, row, now=now, default_stake=stake))
    resolved = [trade for trade in trades if trade["status"] in {"won", "lost"}]
    open_trades = [trade for trade in trades if trade["status"] == "open"]
    pnl = sum(float(trade["pnl"]) for trade in resolved)
    stake_resolved = sum(float(trade["stake"]) for trade in resolved)
    wins = sum(1 for trade in resolved if trade["status"] == "won")
    losses = sum(1 for trade in resolved if trade["status"] == "lost")
    return {
        "generated_at": now.isoformat(),
        "assumptions": {
            "stake": stake,
            "current_only": current_only,
            "current_rules_from": current_rules_from.isoformat(),
            "max_days_to_expiry": max_days_to_expiry,
            "max_spread": max_spread,
            "max_book_age_seconds": max_book_age_seconds,
            "resolution": "daily OHLC high/low after observation; intraday order within a candle is unknown",
        },
        "summary": {
            "tracked": len(trades),
            "raw_candidates": len(raw_rows),
            "excluded_legacy": len(excluded),
            "resolved": len(resolved),
            "open": len(open_trades),
            "won": wins,
            "lost": losses,
            "win_rate": wins / len(resolved) if resolved else None,
            "pnl": pnl,
            "roi": pnl / stake_resolved if stake_resolved else None,
            "open_exposure": sum(float(trade["stake"]) for trade in open_trades),
        },
        "trades": trades,
        "excluded": excluded[:20],
    }


def _edge_bucket(value: Any) -> str:
    try:
        edge = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if edge < 0.02:
        return "<2%"
    if edge < 0.05:
        return "2-5%"
    if edge < 0.10:
        return "5-10%"
    return "10%+"


def _book_quality(raw: dict[str, Any]) -> str:
    if raw.get("pricing_source") != "orderbook":
        return "not-orderbook"
    if raw.get("orderbook_is_fresh") is False:
        return "stale"
    if raw.get("complete_fill") is False:
        return "partial-fill"
    spread = raw.get("spread")
    try:
        if spread is not None and float(spread) > 0.04:
            return "wide-spread"
    except (TypeError, ValueError):
        pass
    return "fresh-fill"


def _raw_json(row: dict[str, Any]) -> dict[str, Any]:
    try:
        raw = json.loads(row.get("raw_json") or "{}")
    except json.JSONDecodeError:
        return {}
    return raw if isinstance(raw, dict) else {}


def _empty_group(name: str, kind: str) -> dict[str, Any]:
    return {
        "name": name,
        "kind": kind,
        "tracked": 0,
        "resolved": 0,
        "open": 0,
        "won": 0,
        "lost": 0,
        "pnl": 0.0,
        "stake": 0.0,
        "stake_resolved": 0.0,
        "avg_edge": 0.0,
        "avg_spread": None,
        "win_rate": None,
        "roi": None,
    }


def _add_to_group(group: dict[str, Any], trade: dict[str, Any], row: dict[str, Any], raw: dict[str, Any]) -> None:
    group["tracked"] += 1
    group["pnl"] += float(trade.get("pnl") or 0.0)
    group["stake"] += float(trade.get("stake") or 0.0)
    group.setdefault("_edge_sum", 0.0)
    group["_edge_sum"] += float(row.get("net_edge") or 0.0)
    spread = raw.get("spread")
    if spread is not None:
        try:
            group.setdefault("_spread_sum", 0.0)
            group.setdefault("_spread_count", 0)
            group["_spread_sum"] += float(spread)
            group["_spread_count"] += 1
        except (TypeError, ValueError):
            pass
    status = str(trade.get("status"))
    if status == "open":
        group["open"] += 1
    elif status in {"won", "lost"}:
        group["resolved"] += 1
        group[status] += 1
        group["stake_resolved"] += float(trade.get("stake") or 0.0)


def _finalize_group(group: dict[str, Any]) -> dict[str, Any]:
    tracked = int(group["tracked"])
    resolved = int(group["resolved"])
    stake = float(group["stake_resolved"])
    group["avg_edge"] = group.pop("_edge_sum", 0.0) / tracked if tracked else 0.0
    spread_count = group.pop("_spread_count", 0)
    spread_sum = group.pop("_spread_sum", 0.0)
    group["avg_spread"] = spread_sum / spread_count if spread_count else None
    group["win_rate"] = group["won"] / resolved if resolved else None
    group["roi"] = group["pnl"] / stake if stake else None
    return group


def candidate_quality_report(
    conn,
    limit: int = 500,
    stake: float = 100.0,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    rows = _candidate_rows(conn, limit)
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    recent: list[dict[str, Any]] = []
    for row in rows:
        raw = _raw_json(row)
        trade = _paper_trade(conn, row, now=now, default_stake=stake)
        keys = [
            ("asset", str(row.get("asset") or "unknown")),
            ("edge", _edge_bucket(row.get("net_edge"))),
            ("vol", str(raw.get("annual_vol_source") or "unknown")),
            ("book", _book_quality(raw)),
        ]
        for kind, name in keys:
            key = (kind, name)
            if key not in groups:
                groups[key] = _empty_group(name, kind)
            _add_to_group(groups[key], trade, row, raw)
        recent.append(
            {
                "observation_id": row["id"],
                "asset": row["asset"],
                "question": row["question"],
                "created_at": row["created_at"],
                "status": trade["status"],
                "net_edge": row["net_edge"],
                "roi": row["roi"],
                "pnl": trade["pnl"],
                "vol_source": raw.get("annual_vol_source") or "unknown",
                "book_quality": _book_quality(raw),
                "pricing_source": row.get("pricing_source"),
            }
        )
    grouped = [_finalize_group(group) for group in groups.values()]
    grouped.sort(key=lambda item: (item["kind"], -item["tracked"], item["name"]))
    resolved = [item for item in recent if item["status"] in {"won", "lost"}]
    return {
        "generated_at": now.isoformat(),
        "summary": {
            "tracked_candidates": len(rows),
            "resolved": len(resolved),
            "open": sum(1 for item in recent if item["status"] == "open"),
            "won": sum(1 for item in recent if item["status"] == "won"),
            "lost": sum(1 for item in recent if item["status"] == "lost"),
            "groups": len(grouped),
        },
        "groups": grouped,
        "recent": recent[:20],
    }


def candidate_review_report(
    conn,
    limit: int = 100,
    stake: float = 100.0,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    rows = _candidate_rows(conn, limit)
    reviewed: list[dict[str, Any]] = []
    for row in rows:
        raw = _raw_json(row)
        trade = _paper_trade(conn, row, now=now, default_stake=stake)
        reviewed.append(
            {
                "observation_id": row["id"],
                "run_id": row["run_id"],
                "created_at": row["created_at"],
                "asset": row["asset"],
                "question": row["question"],
                "status": trade["status"],
                "hit": trade["hit"],
                "evidence": trade["evidence"],
                "pnl": trade["pnl"],
                "return_pct": trade["return_pct"],
                "stake": trade["stake"],
                "spot": row["spot"],
                "barrier": row["barrier"],
                "direction": row["direction"],
                "end_date": trade["end_date"],
                "market_yes_price": row["market_yes_price"],
                "model_probability": row["model_probability"],
                "net_edge": row["net_edge"],
                "roi": row["roi"],
                "pricing_source": row["pricing_source"],
                "spread": row["spread"],
                "orderbook_age_seconds": row["orderbook_age_seconds"],
                "complete_fill": row["complete_fill"],
                "liquidity": row["liquidity"],
                "vol_source": raw.get("annual_vol_source") or "unknown",
                "book_quality": _book_quality(raw),
            }
        )

    resolved = [row for row in reviewed if row["status"] in {"won", "lost"}]
    open_rows = [row for row in reviewed if row["status"] == "open"]
    won = sum(1 for row in resolved if row["status"] == "won")
    pnl = sum(float(row["pnl"] or 0.0) for row in resolved)
    stake_resolved = sum(float(row["stake"] or 0.0) for row in resolved)
    return {
        "generated_at": now.isoformat(),
        "summary": {
            "tracked": len(reviewed),
            "resolved": len(resolved),
            "open": len(open_rows),
            "won": won,
            "lost": len(resolved) - won,
            "win_rate": won / len(resolved) if resolved else None,
            "pnl": pnl,
            "roi": pnl / stake_resolved if stake_resolved else None,
        },
        "candidates": reviewed,
    }
