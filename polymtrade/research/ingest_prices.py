from __future__ import annotations

import argparse
import sys

from polymtrade.data.crypto_prices import (
    fetch_best_daily,
    fetch_binance_daily,
    fetch_coinbase_daily,
    fetch_okx_daily,
    make_demo_daily,
)
from polymtrade.storage.db import candle_summary, connect, upsert_candles


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import BTC/ETH daily candles")
    parser.add_argument("--source", choices=("demo", "auto", "okx", "binance", "coinbase"), default="demo")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--db", default="polymtrade.sqlite")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candles = []
    errors: list[str] = []
    for asset in ("BTC", "ETH"):
        try:
            if args.source == "demo":
                candles.extend(make_demo_daily(asset, days=args.days))
            elif args.source == "auto":
                fetched, source_errors = fetch_best_daily(asset, limit=args.days)
                candles.extend(fetched)
                errors.extend(f"{asset} {item}" for item in source_errors)
            elif args.source == "coinbase":
                candles.extend(fetch_coinbase_daily(asset, limit=args.days))
            elif args.source == "okx":
                candles.extend(fetch_okx_daily(asset, limit=args.days))
            else:
                candles.extend(fetch_binance_daily(asset, limit=args.days))
        except Exception as exc:  # noqa: BLE001 - CLI should show source failures plainly
            errors.append(f"{asset}: {exc}")

    with connect(args.db) as conn:
        inserted = upsert_candles(conn, candles)
        print(f"inserted={inserted} source={args.source}")
        for row in candle_summary(conn):
            print(
                f"{row['asset']} {row['source']} {row['interval']} "
                f"candles={row['candles']} latest_close={row['latest_close']:.2f}"
            )

    if errors:
        print("errors:", file=sys.stderr)
        for item in errors:
            print(f"  {item}", file=sys.stderr)
        return 2 if not candles else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
