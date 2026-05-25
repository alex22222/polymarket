from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from polymtrade.research.scanner import parse_datetime, preferred_price_source


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


def paper_trading_report(
    conn,
    limit: int = 100,
    stake: float = 100.0,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    rows = _candidate_rows(conn, limit)
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
            "resolution": "daily OHLC high/low after observation; intraday order within a candle is unknown",
        },
        "summary": {
            "tracked": len(trades),
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
