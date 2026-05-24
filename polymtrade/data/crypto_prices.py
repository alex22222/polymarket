from __future__ import annotations

import json
import math
import random
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
COINBASE_CANDLES_URL = "https://api.exchange.coinbase.com/products/{product}/candles"
OKX_HISTORY_CANDLES_URL = "https://www.okx.com/api/v5/market/history-candles"
SYMBOLS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT"}
COINBASE_PRODUCTS = {"BTC": "BTC-USD", "ETH": "ETH-USD"}
OKX_PRODUCTS = {"BTC": "BTC-USDT", "ETH": "ETH-USDT"}


@dataclass(frozen=True)
class Candle:
    asset: str
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str
    interval: str


def _get_json(url: str, params: dict[str, Any], timeout: int = 8, retries: int = 1) -> Any:
    request_url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        request_url,
        headers={
            "accept": "application/json",
            "user-agent": "polymtrade-research/0.1",
        },
    )
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (TimeoutError, urllib.error.URLError) as exc:
            if "CERTIFICATE_VERIFY_FAILED" in str(exc):
                context = ssl._create_unverified_context()
                with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            if attempt >= retries:
                raise
            time.sleep(1 + attempt)
    raise RuntimeError("unreachable")


def fetch_binance_daily(asset: str, limit: int = 365) -> list[Candle]:
    asset = asset.upper()
    symbol = SYMBOLS[asset]
    rows = _get_json(BINANCE_KLINES_URL, {"symbol": symbol, "interval": "1d", "limit": limit})
    candles: list[Candle] = []
    for row in rows:
        opened_ms = int(row[0])
        candles.append(
            Candle(
                asset=asset,
                ts=datetime.fromtimestamp(opened_ms / 1000, timezone.utc).isoformat(),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
                source="binance",
                interval="1d",
            )
        )
    return candles


def fetch_coinbase_daily(asset: str, limit: int = 300) -> list[Candle]:
    asset = asset.upper()
    product = COINBASE_PRODUCTS[asset]
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=limit)
    rows = _get_json(
        COINBASE_CANDLES_URL.format(product=product),
        {
            "granularity": 86_400,
            "start": start.isoformat().replace("+00:00", "Z"),
            "end": end.isoformat().replace("+00:00", "Z"),
        },
    )
    candles: list[Candle] = []
    for row in sorted(rows, key=lambda item: item[0]):
        candles.append(
            Candle(
                asset=asset,
                ts=datetime.fromtimestamp(int(row[0]), timezone.utc).isoformat(),
                low=float(row[1]),
                high=float(row[2]),
                open=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
                source="coinbase",
                interval="1d",
            )
        )
    return candles


def fetch_okx_daily(asset: str, limit: int = 365) -> list[Candle]:
    asset = asset.upper()
    inst_id = OKX_PRODUCTS[asset]
    rows: list[list[Any]] = []
    cursor: str | None = None
    remaining = limit
    while remaining > 0:
        params: dict[str, Any] = {
            "instId": inst_id,
            "bar": "1Dutc",
            "limit": min(100, remaining),
        }
        if cursor:
            params["after"] = cursor
        payload = _get_json(OKX_HISTORY_CANDLES_URL, params)
        if str(payload.get("code")) != "0":
            raise RuntimeError(f"OKX error {payload.get('code')}: {payload.get('msg')}")
        batch = payload.get("data") or []
        if not batch:
            break
        rows.extend(batch)
        oldest_ts = min(int(item[0]) for item in batch)
        next_cursor = str(oldest_ts)
        if next_cursor == cursor:
            break
        cursor = next_cursor
        remaining = limit - len(rows)
        if len(batch) < params["limit"]:
            break

    dedup: dict[int, list[Any]] = {}
    for row in rows:
        dedup[int(row[0])] = row
    candles: list[Candle] = []
    for row in sorted(dedup.values(), key=lambda item: int(item[0]))[-limit:]:
        opened_ms = int(row[0])
        candles.append(
            Candle(
                asset=asset,
                ts=datetime.fromtimestamp(opened_ms / 1000, timezone.utc).isoformat(),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
                source="okx",
                interval="1d",
            )
        )
    return candles


def fetch_best_daily(asset: str, limit: int = 365) -> tuple[list[Candle], list[str]]:
    errors: list[str] = []
    for name, fetcher in (
        ("okx", fetch_okx_daily),
        ("binance", fetch_binance_daily),
        ("coinbase", fetch_coinbase_daily),
    ):
        try:
            return fetcher(asset, limit), errors
        except Exception as exc:  # noqa: BLE001 - caller needs source-level failure context
            errors.append(f"{name}: {exc}")
    return [], errors


def make_demo_daily(asset: str, days: int = 365, seed: int = 11) -> list[Candle]:
    asset = asset.upper()
    rng = random.Random((seed * 97) + (1 if asset == "BTC" else 2))
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    price = 66_000.0 if asset == "BTC" else 3_400.0
    vol = 0.035 if asset == "BTC" else 0.045
    candles: list[Candle] = []
    for index in range(days, 0, -1):
        ts = start.timestamp() - index * 86_400
        drift = 0.0004 if asset == "BTC" else 0.0002
        shock = rng.gauss(drift, vol)
        open_price = price
        close = max(1.0, price * math.exp(shock))
        spread = abs(rng.gauss(0.0, vol * 0.55))
        high = max(open_price, close) * (1.0 + spread)
        low = min(open_price, close) * max(0.2, 1.0 - spread)
        volume = rng.uniform(25_000.0, 140_000.0)
        candles.append(
            Candle(
                asset=asset,
                ts=datetime.fromtimestamp(ts, timezone.utc).isoformat(),
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
                source="demo",
                interval="1d",
            )
        )
        price = close
    return candles
