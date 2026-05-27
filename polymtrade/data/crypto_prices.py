from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


BINANCE_KLINES_URL = "https://data-api.binance.vision/api/v3/klines"
BINANCE_DATA_API_TICKER_URL = "https://data-api.binance.vision/api/v3/ticker/price"
COINBASE_CANDLES_URL = "https://api.exchange.coinbase.com/products/{product}/candles"
OKX_HISTORY_CANDLES_URL = "https://www.okx.com/api/v5/market/history-candles"
OKX_CANDLES_URL = "https://www.okx.com/api/v5/market/candles"
OKX_TICKER_URL = "https://www.okx.com/api/v5/market/ticker"
OKX_FUNDING_RATE_URL = "https://www.okx.com/api/v5/public/funding-rate"
SYMBOLS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT"}
COINBASE_PRODUCTS = {"BTC": "BTC-USD", "ETH": "ETH-USD"}
OKX_PRODUCTS = {"BTC": "BTC-USDT", "ETH": "ETH-USDT"}
OKX_SWAP_PRODUCTS = {"BTC": "BTC-USDT-SWAP", "ETH": "ETH-USDT-SWAP"}


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


@dataclass(frozen=True)
class SpotQuote:
    asset: str
    price: float
    source: str
    fetched_at: str


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


def _okx_candle_from_row(asset: str, row: list[Any], interval: str) -> Candle:
    opened_ms = int(row[0])
    return Candle(
        asset=asset,
        ts=datetime.fromtimestamp(opened_ms / 1000, timezone.utc).isoformat(),
        open=float(row[1]),
        high=float(row[2]),
        low=float(row[3]),
        close=float(row[4]),
        volume=float(row[5]),
        source="okx",
        interval=interval,
    )


def fetch_okx_intraday(asset: str, bar: str = "5m", limit: int = 48, timeout: int = 4) -> list[Candle]:
    asset = asset.upper()
    inst_id = OKX_PRODUCTS[asset]
    payload = _get_json(
        OKX_CANDLES_URL,
        {"instId": inst_id, "bar": bar, "limit": max(1, min(300, limit))},
        timeout=timeout,
        retries=0,
    )
    if str(payload.get("code")) != "0":
        raise RuntimeError(f"OKX error {payload.get('code')}: {payload.get('msg')}")
    rows = payload.get("data") or []
    return [_okx_candle_from_row(asset, row, bar) for row in sorted(rows, key=lambda item: int(item[0]))]


def fetch_okx_funding_rate(asset: str, timeout: int = 4) -> dict[str, Any]:
    asset = asset.upper()
    payload = _get_json(
        OKX_FUNDING_RATE_URL,
        {"instId": OKX_SWAP_PRODUCTS[asset]},
        timeout=timeout,
        retries=0,
    )
    if str(payload.get("code")) != "0":
        raise RuntimeError(f"OKX error {payload.get('code')}: {payload.get('msg')}")
    rows = payload.get("data") or []
    if not rows:
        raise RuntimeError("OKX returned no funding rows")
    row = rows[0]

    def iso_ms(value: Any) -> str | None:
        if value in (None, ""):
            return None
        return datetime.fromtimestamp(int(value) / 1000, timezone.utc).isoformat()

    return {
        "asset": asset,
        "source": "okx-funding",
        "inst_id": row.get("instId"),
        "funding_rate": float(row["fundingRate"]) if row.get("fundingRate") not in (None, "") else None,
        "next_funding_rate": float(row["nextFundingRate"]) if row.get("nextFundingRate") not in (None, "") else None,
        "funding_time": iso_ms(row.get("fundingTime")),
        "next_funding_time": iso_ms(row.get("nextFundingTime")),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_binance_data_api_spot(asset: str, timeout: int = 4) -> SpotQuote:
    asset = asset.upper()
    payload = _get_json(BINANCE_DATA_API_TICKER_URL, {"symbol": SYMBOLS[asset]}, timeout=timeout, retries=0)
    return SpotQuote(
        asset=asset,
        price=float(payload["price"]),
        source="binance-data-api-ticker",
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


def fetch_okx_spot(asset: str, timeout: int = 4) -> SpotQuote:
    asset = asset.upper()
    payload = _get_json(OKX_TICKER_URL, {"instId": OKX_PRODUCTS[asset]}, timeout=timeout, retries=0)
    if str(payload.get("code")) != "0":
        raise RuntimeError(f"OKX error {payload.get('code')}: {payload.get('msg')}")
    rows = payload.get("data") or []
    if not rows:
        raise RuntimeError("OKX returned no ticker rows")
    return SpotQuote(
        asset=asset,
        price=float(rows[0]["last"]),
        source="okx-ticker",
        fetched_at=datetime.fromtimestamp(int(rows[0]["ts"]) / 1000, timezone.utc).isoformat(),
    )


def fetch_best_spot(asset: str, timeout: int = 4) -> tuple[SpotQuote | None, list[str]]:
    errors: list[str] = []
    for name, fetcher in (
        ("binance-data-api", fetch_binance_data_api_spot),
        ("okx", fetch_okx_spot),
    ):
        try:
            return fetcher(asset, timeout=timeout), errors
        except Exception as exc:  # noqa: BLE001 - caller needs source-level failure context
            errors.append(f"{name}: {exc}")
    return None, errors


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
