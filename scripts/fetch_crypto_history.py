#!/usr/bin/env python3
"""
BTC / ETH 历史数据批量下载脚本
支持 Binance (推荐) 和 CryptoCompare
无需 API Key
"""

import csv
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

import requests


# ============ Binance ============

def fetch_binance_klines(symbol: str, interval: str, start_ms: int, end_ms: int | None = None):
    """Fetch all klines from Binance public data API."""
    url = "https://data-api.binance.vision/api/v3/klines"
    all_data = []
    current = start_ms
    end_limit = end_ms or int(time.time() * 1000)

    while current < end_limit:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current,
            "limit": 1000,
        }
        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list) or len(data) == 0:
                break
            all_data.extend(data)
            current = data[-1][0] + 1
            print(f"  [{symbol} {interval}] Fetched {len(data)} candles, total {len(all_data)}, up to {datetime.fromtimestamp(current//1000, tz=timezone.utc)}")
            if len(data) < 1000:
                break
            time.sleep(0.15)
        except requests.RequestException as e:
            print(f"  Request error: {e}, retrying...")
            time.sleep(1)
            continue
    return all_data


def binance_klines_to_dicts(rows: list) -> list[dict]:
    """Convert Binance kline array to dicts."""
    cols = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_volume", "taker_buy_quote_volume", "ignore",
    ]
    return [dict(zip(cols, row)) for row in rows]


# ============ CryptoCompare ============

def fetch_cryptocompare_daily(fsym: str, tsym: str, limit: int = 2000, to_ts: int | None = None):
    """Fetch daily OHLCV from CryptoCompare."""
    url = "https://min-api.cryptocompare.com/data/v2/histoday"
    all_data = []
    current_to = to_ts or int(time.time())

    while True:
        params = {
            "fsym": fsym,
            "tsym": tsym,
            "limit": limit,
            "toTs": current_to,
        }
        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            payload = r.json()
            if payload.get("Response") != "Success":
                print(f"  CryptoCompare error: {payload.get('Message')}")
                break
            data = payload["Data"]["Data"]
            if not data:
                break
            all_data = data + all_data
            earliest = data[0]["time"]
            print(f"  [{fsym}/{tsym} daily] Fetched {len(data)} days, total {len(all_data)}, earliest {datetime.fromtimestamp(earliest, tz=timezone.utc)}")
            if len(data) < limit:
                break
            current_to = earliest - 1
            time.sleep(0.3)
        except requests.RequestException as e:
            print(f"  Request error: {e}, retrying...")
            time.sleep(1)
            continue
    return all_data


# ============ Save ============

def save_to_csv(records: list[dict], path: Path) -> None:
    if not records:
        print("No records to save.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved {len(records)} rows to {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch BTC/ETH historical OHLCV")
    parser.add_argument("--source", choices=["binance", "cryptocompare"], default="binance")
    parser.add_argument("--symbol", default="BTCUSDT", help="e.g. BTCUSDT, ETHUSDT")
    parser.add_argument("--interval", default="1d", help="Binance: 1m,5m,15m,1h,4h,1d,1w")
    parser.add_argument("--start", default="2017-08-17", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="End date YYYY-MM-DD (optional)")
    parser.add_argument("--out", default="data/raw", help="Output directory")
    parser.add_argument("--format", choices=["csv", "json"], default="csv")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    start_dt = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = None
    if args.end:
        end_dt = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_ms = int(end_dt.timestamp() * 1000)

    if args.source == "binance":
        print(f"Fetching {args.symbol} {args.interval} from Binance...")
        raw = fetch_binance_klines(args.symbol, args.interval, start_ms, end_ms)
        records = binance_klines_to_dicts(raw)
        # Add human-readable datetime
        for r in records:
            r["datetime"] = datetime.fromtimestamp(r["open_time"] // 1000, tz=timezone.utc).isoformat()
        filename = f"{args.symbol}_{args.interval}_binance.{args.format}"
    else:
        fsym = args.symbol.replace("USDT", "").replace("USD", "")
        print(f"Fetching {fsym}/USD daily from CryptoCompare...")
        to_ts = end_ms // 1000 if end_ms else None
        raw = fetch_cryptocompare_daily(fsym, "USD", limit=2000, to_ts=to_ts)
        records = raw
        for r in records:
            r["datetime"] = datetime.fromtimestamp(r["time"], tz=timezone.utc).isoformat()
        filename = f"{fsym}_USD_daily_cryptocompare.{args.format}"

    out_path = out_dir / filename
    if args.format == "csv":
        save_to_csv(records, out_path)
    else:
        out_path.write_text(json.dumps(records, indent=2, default=str))
        print(f"Saved {len(records)} rows to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
