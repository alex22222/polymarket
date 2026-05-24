from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from polymtrade.data.polymarket_api import fetch_order_book
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


def parse_book_levels(levels: Any, reverse: bool = False) -> list[dict[str, float]]:
    parsed: list[dict[str, float]] = []
    if not isinstance(levels, list):
        return parsed
    for level in levels:
        try:
            price = float(level["price"])
            size = float(level["size"])
        except (KeyError, TypeError, ValueError):
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


def order_book_metrics(
    token_id: str | None,
    max_notional: float,
    source: str = "polymtrade",
    timeout: int = 4,
) -> dict[str, Any]:
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
    return {
        "orderbook_source": source,
        "orderbook_timestamp": book.get("timestamp"),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": (best_ask - best_bid) if best_bid is not None and best_ask is not None else None,
        "last_trade_price": float(book["last_trade_price"]) if book.get("last_trade_price") is not None else None,
        "tick_size": float(book["tick_size"]) if book.get("tick_size") is not None else None,
        "min_order_size": float(book["min_order_size"]) if book.get("min_order_size") is not None else None,
        "executable_price": avg_price,
        "executable_notional": fill.get("executable_notional"),
        "executable_shares": fill.get("executable_shares"),
        "complete_fill": fill.get("complete_fill"),
        "orderbook_error": None,
    }


def opportunity_sort_key(row: dict[str, Any]) -> tuple[int, float, float]:
    priority = {"candidate": 3, "watch": 2, "verify": 1, "avoid": 0}.get(str(row.get("action")), 0)
    return (priority, float(row.get("net_edge") or 0.0), float(row.get("liquidity") or 0.0))


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
    orderbook: bool = False,
    book_limit: int = 30,
    executable_notional: float = 100.0,
    book_source: str = "polymtrade",
    book_timeout: int = 4,
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
                "yes_token_id": market.get("yes_token_id"),
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
                "pricing_source": "cached",
            }
        )

    opportunities.sort(key=opportunity_sort_key, reverse=True)
    if orderbook:
        for row in opportunities[:book_limit]:
            book = order_book_metrics(
                row.get("yes_token_id"),
                executable_notional,
                source=book_source,
                timeout=book_timeout,
            )
            row.update(book)
            executable_price = row.get("executable_price") or row.get("best_ask")
            if executable_price is None:
                row["pricing_source"] = "cached-orderbook-unavailable"
                continue
            executable_costs = edge_for_yes(row["model_probability"], float(executable_price), fee_rate, slippage_bps)
            row["market_yes_price"] = float(executable_price)
            row["gross_edge"] = row["model_probability"] - float(executable_price)
            row["net_edge"] = executable_costs["net_ev"]
            row["roi"] = executable_costs["roi"]
            row["annualized_roi"] = executable_costs["roi"] * (365.0 / row["days_to_expiry"]) if row["days_to_expiry"] > 0 else 0.0
            row["taker_fee"] = executable_costs["taker_fee"]
            row["slippage"] = executable_costs["slippage"]
            row["pricing_source"] = "orderbook"
            if row["already_touched"]:
                row["action"] = "verify"
            elif row["net_edge"] >= edge_threshold:
                row["action"] = "candidate"
            elif row["net_edge"] <= -edge_threshold:
                row["action"] = "avoid"
            else:
                row["action"] = "watch"
        opportunities.sort(key=opportunity_sort_key, reverse=True)
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
            "orderbook": orderbook,
            "book_limit": book_limit,
            "book_source": book_source,
            "executable_notional": executable_notional,
            "book_timeout": book_timeout,
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
            "orderbook_priced": sum(1 for row in opportunities if row.get("pricing_source") == "orderbook"),
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
    parser.add_argument("--orderbook", action="store_true", help="Price top results from live YES order books")
    parser.add_argument("--book-limit", type=int, default=30)
    parser.add_argument("--executable-notional", type=float, default=100.0)
    parser.add_argument("--book-timeout", type=int, default=4)
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
            orderbook=args.orderbook,
            book_limit=args.book_limit,
            executable_notional=args.executable_notional,
            book_timeout=args.book_timeout,
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
