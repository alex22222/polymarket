from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from polymtrade.storage.db import connect
from polymtrade.superpowers.barrier import (
    BarrierInput,
    edge_for_yes,
    monte_carlo_touch_probability,
    realized_volatility,
)


SOURCE_PRIORITY = {
    "binance-data-api": 0,
    "binance": 1,
    "okx": 2,
    "coinbase": 3,
}


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


def price_context(conn, asset: str, max_window: int = 180) -> dict[str, Any] | None:
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
    vols = {}
    for window in (30, 90, 180):
        prices = closes[-(window + 1) :]
        vols[f"{window}d"] = realized_volatility(prices)
    return {
        "asset": asset,
        "source": source,
        "spot": closes[-1],
        "last_ts": ordered[-1]["ts"],
        "candles": len(ordered),
        "volatility": vols,
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
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    contexts = {asset: price_context(conn, asset) for asset in ("BTC", "ETH")}
    opportunities: list[dict[str, Any]] = []
    skipped = 0
    scanned = 0

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
            continue
        yes_price = float(market["yes_price"])
        if yes_price < min_yes_price or yes_price > max_yes_price:
            skipped += 1
            continue
        liquidity = float(market.get("liquidity") or 0.0)
        if liquidity < min_liquidity:
            skipped += 1
            continue

        scanned += 1
        direction = normalized_direction(market)
        already_touched = (
            float(context["spot"]) >= float(market["barrier"])
            if direction == "hit_above"
            else float(context["spot"]) <= float(market["barrier"])
        )
        vol = float(context["volatility"].get(vol_window) or context["volatility"]["90d"])
        result = monte_carlo_touch_probability(
            BarrierInput(
                spot=float(context["spot"]),
                barrier=float(market["barrier"]),
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
        action = "watch"
        if already_touched:
            action = "verify"
        elif costs["net_ev"] >= edge_threshold:
            action = "candidate"
        elif costs["net_ev"] <= -edge_threshold:
            action = "avoid"
        opportunities.append(
            {
                "market_id": market["market_id"],
                "asset": market["asset"],
                "question": market["question"],
                "direction": direction,
                "spot": context["spot"],
                "barrier": market["barrier"],
                "days_to_expiry": days_to_expiry,
                "end_date": market["end_date"],
                "market_yes_price": yes_price,
                "market_no_price": market.get("no_price"),
                "model_probability": result.adjusted_probability,
                "gross_edge": result.adjusted_probability - yes_price,
                "net_edge": costs["net_ev"],
                "roi": costs["roi"],
                "annualized_roi": simple_annualized_roi,
                "taker_fee": costs["taker_fee"],
                "slippage": costs["slippage"],
                "annual_vol": vol,
                "already_touched": already_touched,
                "volume": market.get("volume"),
                "liquidity": liquidity,
                "source": market.get("source"),
                "action": action,
            }
        )

    opportunities.sort(key=lambda row: (row["net_edge"], row["liquidity"]), reverse=True)
    top = opportunities[:limit]
    candidates = [row for row in opportunities if row["action"] == "candidate"]
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
        },
        "contexts": {asset: context for asset, context in contexts.items() if context},
        "summary": {
            "markets_total": len(scanner_markets(conn)),
            "markets_scanned": scanned,
            "markets_skipped": skipped,
            "opportunities": len(opportunities),
            "candidates": len(candidates),
            "best_net_edge": top[0]["net_edge"] if top else None,
            "best_roi": top[0]["roi"] if top else None,
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
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
