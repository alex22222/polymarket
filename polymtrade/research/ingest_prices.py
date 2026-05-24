from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from polymtrade.data.crypto_prices import (
    Candle,
    fetch_best_daily,
    fetch_binance_daily,
    fetch_coinbase_daily,
    fetch_okx_daily,
)
from polymtrade.storage.db import candle_summary, connect, upsert_candles


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import BTC/ETH daily candles")
    parser.add_argument("--source", choices=("auto", "okx", "binance", "coinbase"), default="auto")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--csv", dest="csv_paths", action="append", help="CSV file with OHLCV columns; can be repeated")
    parser.add_argument("--asset", help="Asset symbol for CSV import, inferred from filename when omitted")
    parser.add_argument("--csv-source", default="csv")
    parser.add_argument("--db", default="polymtrade.sqlite")
    return parser.parse_args()


def infer_asset(path: Path, override: str | None) -> str:
    if override:
        return override.upper()
    name = path.name.upper()
    if "ETH" in name:
        return "ETH"
    if "BTC" in name:
        return "BTC"
    raise ValueError(f"cannot infer asset from filename: {path}")


def csv_candles(path: Path, asset: str, source: str) -> list[Candle]:
    candles: list[Candle] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            ts = row.get("datetime") or row.get("timestamp") or row.get("date") or row.get("open_time")
            if ts is None:
                raise ValueError(f"missing datetime/timestamp column in {path}")
            if ts.isdigit():
                value = int(ts)
                if value > 10_000_000_000:
                    value = value // 1000
                from datetime import datetime, timezone

                ts = datetime.fromtimestamp(value, timezone.utc).isoformat()
            candles.append(
                Candle(
                    asset=asset,
                    ts=ts,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume") or 0),
                    source=source,
                    interval="1d",
                )
            )
    return candles


def main() -> int:
    args = parse_args()
    candles = []
    errors: list[str] = []
    for csv_path in args.csv_paths or []:
        path = Path(csv_path)
        try:
            asset = infer_asset(path, args.asset)
            candles.extend(csv_candles(path, asset, args.csv_source))
        except Exception as exc:  # noqa: BLE001 - CLI should show source failures plainly
            errors.append(f"{csv_path}: {exc}")

    if args.csv_paths:
        with connect(args.db) as conn:
            inserted = upsert_candles(conn, candles)
            print(f"inserted={inserted} source={args.csv_source}")
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

    for asset in ("BTC", "ETH"):
        try:
            if args.source == "auto":
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
