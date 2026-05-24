from __future__ import annotations

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from polymtrade.data.crypto_prices import fetch_best_daily
from polymtrade.data.polymarket_api import (
    fetch_gamma_markets,
    fetch_polymtrade_crypto_events,
    search_gamma_barrier_markets,
    search_polymtrade_barrier_markets,
)
from polymtrade.research.scanner import scan_opportunities
from polymtrade.storage.db import (
    barrier_market_summary,
    candle_summary,
    candles_for_asset,
    connect,
    market_price_history_summary,
    upsert_candles,
    upsert_barrier_markets,
)


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
DB_PATH = ROOT.parent / "polymtrade.sqlite"


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def send_json(self, payload: dict | list, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/api/health":
            self.send_json({"ok": True, "mode": "real-first"})
            return
        if path == "/api/data-summary":
            with connect(DB_PATH) as conn:
                self.send_json(
                    {
                        "candles": candle_summary(conn),
                        "markets": barrier_market_summary(conn),
                        "priceHistory": market_price_history_summary(conn),
                    }
                )
            return
        if path == "/api/candles":
            asset = query.get("asset", ["BTC"])[0].upper()
            source = query.get("source", [None])[0]
            limit = int(query.get("limit", ["365"])[0])
            with connect(DB_PATH) as conn:
                self.send_json({"asset": asset, "candles": candles_for_asset(conn, asset, source, limit)})
            return
        if path == "/api/scanner":
            limit = int(query.get("limit", ["50"])[0])
            edge_threshold = float(query.get("edge", ["0.02"])[0])
            min_liquidity = float(query.get("min_liquidity", ["500"])[0])
            simulations = int(query.get("simulations", ["1500"])[0])
            vol_window = query.get("vol_window", ["90d"])[0]
            with connect(DB_PATH) as conn:
                self.send_json(
                    scan_opportunities(
                        conn,
                        limit=limit,
                        edge_threshold=edge_threshold,
                        min_liquidity=min_liquidity,
                        simulations=simulations,
                        vol_window=vol_window,
                    )
                )
            return
        if path == "/api/fetch-crypto-prices":
            candles = []
            errors: list[str] = []
            for asset in ("BTC", "ETH"):
                fetched, source_errors = fetch_best_daily(asset, limit=365)
                candles.extend(fetched)
                errors.extend(f"{asset} {item}" for item in source_errors)
            with connect(DB_PATH) as conn:
                inserted = upsert_candles(conn, candles)
                self.send_json(
                    {
                        "ok": not errors,
                        "source": "binance",
                        "candles": inserted,
                        "errors": errors,
                        "summary": candle_summary(conn),
                    },
                    status=200 if candles else 502,
                )
            return
        if path == "/api/fetch-real-markets":
            errors: list[str] = []
            records = []
            try:
                records.extend(search_polymtrade_barrier_markets())
                records.extend(fetch_polymtrade_crypto_events())
            except Exception as exc:  # noqa: BLE001 - expose real data blocker in UI
                errors.append(f"polymtrade: {exc}")
            try:
                records.extend(
                    search_gamma_barrier_markets(
                        queries=["bitcoin", "ethereum"],
                        limit_per_type=20,
                        timeout=5,
                        retries=0,
                    )
                )
            except Exception as exc:  # noqa: BLE001 - expose real data blocker in UI
                errors.append(f"search: {exc}")
            try:
                records.extend(fetch_gamma_markets(limit=50, pages=1, closed=False, active=True, timeout=5, retries=0))
                records.extend(fetch_gamma_markets(limit=50, pages=1, closed=True, active=None, timeout=5, retries=0))
            except Exception as exc:  # noqa: BLE001 - expose real data blocker in UI
                errors.append(f"markets: {exc}")
            with connect(DB_PATH) as conn:
                inserted = upsert_barrier_markets(conn, records)
                self.send_json(
                    {
                        "ok": bool(records),
                        "source": "gamma",
                        "markets": inserted,
                        "errors": errors,
                        "summary": barrier_market_summary(conn),
                    },
                    status=200 if records else 502,
                )
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), AppHandler)
    print("Polymtrade dashboard: http://127.0.0.1:8765", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
