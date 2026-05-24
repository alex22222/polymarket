#!/usr/bin/env python3
"""Read-only Polymarket binary arbitrage scanner.

This script fetches active binary markets, reads both YES/NO order books, and
reports fee-adjusted buy-combo opportunities where YES ask + NO ask < 1.
It does not place orders or require a wallet.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"
CLOB_BOOK_URL = "https://clob.polymarket.com/book"


# Official taker fee categories vary by market. Gamma metadata is not always
# normalized enough to infer the exact category, so the scanner defaults to a
# conservative fee rate that can be overridden on the command line.
DEFAULT_TAKER_FEE_RATE = 0.04


@dataclass
class BookTop:
    bid: float | None
    bid_size: float
    ask: float | None
    ask_size: float


@dataclass
class Opportunity:
    ts: str
    market_id: str
    question: str
    slug: str
    yes_token_id: str
    no_token_id: str
    yes_ask: float
    no_ask: float
    yes_size: float
    no_size: float
    gross_edge: float
    taker_fees: float
    slippage_buffer: float
    net_edge: float
    roi: float
    max_shares: float
    capital_required: float
    expected_profit: float
    url: str


def get_json(
    url: str,
    params: dict[str, Any] | None = None,
    timeout: int = 30,
    retries: int = 2,
) -> Any:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    req = urllib.request.Request(
        url,
        headers={
            "accept": "application/json",
            "user-agent": "polymtrade-readonly-scanner/0.1",
        },
    )
    last_error: BaseException | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.0 + attempt)
                continue
            raise
    raise RuntimeError(f"request failed: {url}") from last_error


def parse_jsonish(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def fetch_markets(limit: int, offset: int = 0) -> list[dict[str, Any]]:
    params = {
        "active": "true",
        "closed": "false",
        "archived": "false",
        "limit": limit,
        "offset": offset,
        "order": "volume",
        "ascending": "false",
    }
    data = get_json(GAMMA_MARKETS_URL, params)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("markets", "data", "results"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def binary_token_ids(market: dict[str, Any]) -> tuple[str, str] | None:
    token_ids = parse_jsonish(market.get("clobTokenIds"))
    outcomes = parse_jsonish(market.get("outcomes"))
    if not isinstance(token_ids, list) or len(token_ids) != 2:
        return None
    if isinstance(outcomes, list) and len(outcomes) == 2:
        labels = [str(x).strip().lower() for x in outcomes]
        if "yes" in labels and "no" in labels:
            yes_idx = labels.index("yes")
            no_idx = labels.index("no")
            return str(token_ids[yes_idx]), str(token_ids[no_idx])
    return str(token_ids[0]), str(token_ids[1])


def best_price(levels: list[dict[str, Any]], side: str) -> tuple[float | None, float]:
    parsed: list[tuple[float, float]] = []
    for level in levels:
        try:
            parsed.append((float(level["price"]), float(level.get("size", 0))))
        except (KeyError, TypeError, ValueError):
            continue
    if not parsed:
        return None, 0.0
    price, size = min(parsed) if side == "ask" else max(parsed)
    return price, size


def fetch_book_top(token_id: str) -> BookTop:
    book = get_json(CLOB_BOOK_URL, {"token_id": token_id})
    bids = book.get("bids") if isinstance(book, dict) else []
    asks = book.get("asks") if isinstance(book, dict) else []
    bid, bid_size = best_price(bids or [], "bid")
    ask, ask_size = best_price(asks or [], "ask")
    return BookTop(bid=bid, bid_size=bid_size, ask=ask, ask_size=ask_size)


def taker_fee_per_share(price: float, fee_rate: float) -> float:
    return fee_rate * price * (1.0 - price)


def scan_once(
    market_limit: int,
    fee_rate: float,
    slippage_bps: float,
    min_roi: float,
    min_profit: float,
    sleep_between_books: float,
) -> tuple[list[Opportunity], dict[str, int]]:
    markets = fetch_markets(market_limit)
    stats = {
        "markets_seen": len(markets),
        "binary_markets": 0,
        "books_read": 0,
        "missing_books": 0,
        "opportunities": 0,
    }
    opportunities: list[Opportunity] = []
    ts = datetime.now(timezone.utc).isoformat()

    for market in markets:
        pair = binary_token_ids(market)
        if not pair:
            continue
        stats["binary_markets"] += 1
        yes_token_id, no_token_id = pair

        try:
            yes = fetch_book_top(yes_token_id)
            if sleep_between_books:
                time.sleep(sleep_between_books)
            no = fetch_book_top(no_token_id)
            stats["books_read"] += 2
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            stats["missing_books"] += 1
            continue

        if yes.ask is None or no.ask is None:
            stats["missing_books"] += 1
            continue

        max_shares = min(yes.ask_size, no.ask_size)
        cost = yes.ask + no.ask
        gross_edge = 1.0 - cost
        taker_fees = taker_fee_per_share(yes.ask, fee_rate) + taker_fee_per_share(no.ask, fee_rate)
        slippage_buffer = cost * (slippage_bps / 10_000.0)
        net_edge = gross_edge - taker_fees - slippage_buffer
        roi = net_edge / cost if cost > 0 else 0.0
        capital_required = cost * max_shares
        expected_profit = net_edge * max_shares

        if roi < min_roi or expected_profit < min_profit or net_edge <= 0:
            continue

        stats["opportunities"] += 1
        market_id = str(market.get("id") or market.get("conditionId") or "")
        slug = str(market.get("slug") or "")
        opportunities.append(
            Opportunity(
                ts=ts,
                market_id=market_id,
                question=str(market.get("question") or market.get("title") or ""),
                slug=slug,
                yes_token_id=yes_token_id,
                no_token_id=no_token_id,
                yes_ask=yes.ask,
                no_ask=no.ask,
                yes_size=yes.ask_size,
                no_size=no.ask_size,
                gross_edge=gross_edge,
                taker_fees=taker_fees,
                slippage_buffer=slippage_buffer,
                net_edge=net_edge,
                roi=roi,
                max_shares=max_shares,
                capital_required=capital_required,
                expected_profit=expected_profit,
                url=f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com",
            )
        )

    opportunities.sort(key=lambda item: item.expected_profit, reverse=True)
    return opportunities, stats


def init_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        create table if not exists opportunities (
          ts text,
          market_id text,
          question text,
          slug text,
          yes_token_id text,
          no_token_id text,
          yes_ask real,
          no_ask real,
          yes_size real,
          no_size real,
          gross_edge real,
          taker_fees real,
          slippage_buffer real,
          net_edge real,
          roi real,
          max_shares real,
          capital_required real,
          expected_profit real,
          url text
        )
        """
    )
    return conn


def store(conn: sqlite3.Connection, opportunities: list[Opportunity]) -> None:
    if not opportunities:
        return
    cols = list(asdict(opportunities[0]).keys())
    placeholders = ", ".join(["?"] * len(cols))
    conn.executemany(
        f"insert into opportunities ({', '.join(cols)}) values ({placeholders})",
        [tuple(asdict(item).values()) for item in opportunities],
    )
    conn.commit()


def print_report(opportunities: list[Opportunity], stats: dict[str, int], top: int) -> None:
    print(
        "stats "
        + " ".join(f"{key}={value}" for key, value in stats.items()),
        flush=True,
    )
    if not opportunities:
        print("no positive fee-adjusted opportunities found", flush=True)
        return

    for op in opportunities[:top]:
        print(
            "\n"
            f"{op.expected_profit:,.2f} expected profit | "
            f"{op.roi * 100:.3f}% ROI | "
            f"{op.net_edge * 100:.3f}c net edge/share\n"
            f"  {op.question}\n"
            f"  YES ask={op.yes_ask:.4f} size={op.yes_size:,.2f} | "
            f"NO ask={op.no_ask:.4f} size={op.no_size:,.2f}\n"
            f"  gross={op.gross_edge * 100:.3f}c "
            f"fees={op.taker_fees * 100:.3f}c "
            f"slip={op.slippage_buffer * 100:.3f}c "
            f"capital=${op.capital_required:,.2f}\n"
            f"  {op.url}",
            flush=True,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only Polymarket binary arbitrage scanner")
    parser.add_argument("--market-limit", type=int, default=100)
    parser.add_argument("--fee-rate", type=float, default=DEFAULT_TAKER_FEE_RATE)
    parser.add_argument("--slippage-bps", type=float, default=10.0)
    parser.add_argument("--min-roi", type=float, default=0.0, help="Decimal ROI, e.g. 0.003 for 0.3%%")
    parser.add_argument("--min-profit", type=float, default=0.0)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--interval", type=float, default=0.0, help="Repeat interval in seconds; 0 runs once")
    parser.add_argument("--db", default="scanner_results.sqlite")
    parser.add_argument("--sleep-between-books", type=float, default=0.03)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    conn = init_db(args.db)
    try:
        while True:
            try:
                opportunities, stats = scan_once(
                    market_limit=args.market_limit,
                    fee_rate=args.fee_rate,
                    slippage_bps=args.slippage_bps,
                    min_roi=args.min_roi,
                    min_profit=args.min_profit,
                    sleep_between_books=args.sleep_between_books,
                )
            except (urllib.error.URLError, TimeoutError) as exc:
                print(
                    "network error while reading Polymarket APIs: "
                    f"{exc}\n"
                    "Try again from a network that can reach "
                    "gamma-api.polymarket.com and clob.polymarket.com.",
                    file=sys.stderr,
                )
                return 2
            store(conn, opportunities)
            print_report(opportunities, stats, args.top)
            if args.interval <= 0:
                break
            time.sleep(args.interval)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("stopped", file=sys.stderr)
        raise SystemExit(130)
