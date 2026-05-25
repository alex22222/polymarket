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
from polymtrade.research.paper import candidate_quality_report, paper_trading_report
from polymtrade.storage.db import (
    automation_health,
    barrier_market_summary,
    candle_summary,
    candles_for_asset,
    connect,
    data_quality_report,
    insert_log,
    latest_logs,
    clear_logs,
    market_price_history_summary,
    insert_scanner_observation_run,
    latest_scanner_observation_runs,
    latest_scanner_observations,
    scanner_observation_summary,
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

    def log_event(self, level: str, module: str, message: str, detail: str | None = None) -> None:
        try:
            with connect(DB_PATH) as conn:
                insert_log(conn, level, module, message, detail)
        except Exception:
            pass

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/logs/clear":
            with connect(DB_PATH) as conn:
                deleted = clear_logs(conn, keep=1000)
                remaining = conn.execute("select count(*) from system_logs").fetchone()[0]
            self.log_event("INFO", "system", f"Logs cleared: {deleted} deleted, {remaining} remaining")
            self.send_json({"ok": True, "deleted": deleted, "remaining": remaining})
            return
        if path == "/api/scanner-observations":
            try:
                length = int(self.headers.get("content-length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
                if not isinstance(payload, dict) or not isinstance(payload.get("opportunities"), list):
                    raise ValueError("scanner payload missing opportunities")
                with connect(DB_PATH) as conn:
                    run_id = insert_scanner_observation_run(conn, payload)
                    summary = scanner_observation_summary(conn)
                rows = len(payload.get("opportunities") or [])
                candidates = int((payload.get("summary") or {}).get("candidates") or 0)
                self.log_event("INFO", "scanner", f"Scanner observation saved: run={run_id}, rows={rows}, candidates={candidates}")
                self.send_json({"ok": True, "run_id": run_id, "summary": summary})
            except Exception as exc:
                self.log_event("ERROR", "scanner", f"Observation save failed: {exc}")
                self.send_json({"ok": False, "error": str(exc)}, status=400)
            return
        self.send_json({"ok": False, "error": "POST not supported for this path"}, status=405)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/api/health":
            self.send_json({"ok": True, "mode": "real-first"})
            return
        if path == "/api/logs":
            limit = int(query.get("limit", ["100"])[0])
            level = query.get("level", [None])[0]
            module = query.get("module", [None])[0]
            with connect(DB_PATH) as conn:
                rows = latest_logs(conn, limit=limit, level=level, module=module)
                count = conn.execute("select count(*) from system_logs").fetchone()[0]
            self.send_json({"logs": rows, "total": count})
            return
        if path == "/api/data-summary":
            with connect(DB_PATH) as conn:
                self.send_json(
                    {
                        "candles": candle_summary(conn),
                        "markets": barrier_market_summary(conn),
                        "priceHistory": market_price_history_summary(conn),
                        "observations": scanner_observation_summary(conn),
                    }
                )
            return
        if path == "/api/data-quality":
            with connect(DB_PATH) as conn:
                self.send_json(data_quality_report(conn))
            return
        if path == "/api/scanner-observations":
            limit = int(query.get("limit", ["25"])[0])
            with connect(DB_PATH) as conn:
                self.send_json(
                    {
                        "summary": scanner_observation_summary(conn),
                        "runs": latest_scanner_observation_runs(conn, limit=10),
                        "observations": latest_scanner_observations(conn, limit=limit),
                    }
                )
            return
        if path == "/api/paper-trading":
            limit = int(query.get("limit", ["100"])[0])
            stake = float(query.get("stake", ["100"])[0])
            with connect(DB_PATH) as conn:
                self.send_json(paper_trading_report(conn, limit=limit, stake=stake))
            return
        if path == "/api/quality-analysis":
            limit = int(query.get("limit", ["500"])[0])
            stake = float(query.get("stake", ["100"])[0])
            with connect(DB_PATH) as conn:
                self.send_json(candidate_quality_report(conn, limit=limit, stake=stake))
            return
        if path == "/api/automation-health":
            max_age = int(query.get("max_age_minutes", ["150"])[0])
            with connect(DB_PATH) as conn:
                self.send_json(automation_health(conn, max_age_minutes=max_age))
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
            vol_model = query.get("vol_model", ["factor"])[0]
            iv_timeout = int(query.get("iv_timeout", ["3"])[0])
            orderbook = query.get("orderbook", ["0"])[0] in {"1", "true", "yes"}
            book_limit = int(query.get("book_limit", ["30"])[0])
            executable_notional = float(query.get("executable_notional", ["100"])[0])
            book_timeout = int(query.get("book_timeout", ["4"])[0])
            max_book_age_seconds = int(query.get("max_book_age_seconds", ["120"])[0])
            max_spread = float(query.get("max_spread", ["0.04"])[0])
            realtime_spot = query.get("spot", ["realtime"])[0] != "daily"
            require_realtime_spot = query.get("require_realtime_spot", ["1"])[0] in {"1", "true", "yes"}
            spot_timeout = int(query.get("spot_timeout", ["4"])[0])
            self.log_event("INFO", "scanner", f"Scanner started: limit={limit}, edge={edge_threshold}, vol={vol_window}")
            with connect(DB_PATH) as conn:
                try:
                    result = scan_opportunities(
                        conn,
                        limit=limit,
                        edge_threshold=edge_threshold,
                        min_liquidity=min_liquidity,
                        simulations=simulations,
                        vol_window=vol_window,
                        vol_model=vol_model,
                        iv_timeout=iv_timeout,
                        orderbook=orderbook,
                        book_limit=book_limit,
                        executable_notional=executable_notional,
                        book_timeout=book_timeout,
                        max_book_age_seconds=max_book_age_seconds,
                        max_spread=max_spread,
                        realtime_spot=realtime_spot,
                        require_realtime_spot=require_realtime_spot,
                        spot_timeout=spot_timeout,
                    )
                    cand = result.get("summary", {}).get("candidates", 0)
                    scanned = result.get("summary", {}).get("markets_scanned", 0)
                    self.log_event("INFO", "scanner", f"Scanner completed: {cand} candidates from {scanned} markets")
                    self.send_json(result)
                except Exception as exc:
                    self.log_event("ERROR", "scanner", str(exc))
                    self.send_json({"ok": False, "error": str(exc)}, status=500)
            return
        if path == "/api/fetch-crypto-prices":
            self.log_event("INFO", "data", "Fetching crypto prices from Binance...")
            candles = []
            errors: list[str] = []
            for asset in ("BTC", "ETH"):
                fetched, source_errors = fetch_best_daily(asset, limit=365)
                candles.extend(fetched)
                errors.extend(f"{asset} {item}" for item in source_errors)
            with connect(DB_PATH) as conn:
                inserted = upsert_candles(conn, candles)
                if errors:
                    self.log_event("WARN", "data", f"Price fetch partial: {len(errors)} errors", "; ".join(errors))
                else:
                    self.log_event("INFO", "data", f"Price fetch OK: {inserted} candles inserted")
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
            self.log_event("INFO", "data", "Fetching real markets from Polymarket...")
            errors: list[str] = []
            records = []
            try:
                records.extend(search_polymtrade_barrier_markets())
                records.extend(fetch_polymtrade_crypto_events())
            except Exception as exc:
                errors.append(f"polymtrade: {exc}")
                self.log_event("WARN", "data", f"Polymtrade fetch failed: {exc}")
            try:
                records.extend(
                    search_gamma_barrier_markets(
                        queries=["bitcoin", "ethereum"],
                        limit_per_type=20,
                        timeout=5,
                        retries=0,
                    )
                )
            except Exception as exc:
                errors.append(f"search: {exc}")
                self.log_event("WARN", "data", f"Gamma search failed: {exc}")
            try:
                records.extend(fetch_gamma_markets(limit=50, pages=1, closed=False, active=True, timeout=5, retries=0))
                records.extend(fetch_gamma_markets(limit=50, pages=1, closed=True, active=None, timeout=5, retries=0))
            except Exception as exc:
                errors.append(f"markets: {exc}")
                self.log_event("WARN", "data", f"Gamma markets failed: {exc}")
            with connect(DB_PATH) as conn:
                inserted = upsert_barrier_markets(conn, records)
                if errors:
                    self.log_event("WARN", "data", f"Market fetch partial: {inserted} inserted, {len(errors)} errors")
                else:
                    self.log_event("INFO", "data", f"Market fetch OK: {inserted} markets inserted")
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
    try:
        with connect(DB_PATH) as conn:
            insert_log(conn, "INFO", "system", "Polymtrade server started", "http://127.0.0.1:8765")
    except Exception:
        pass
    server = ThreadingHTTPServer(("127.0.0.1", 8765), AppHandler)
    print("Polymtrade dashboard: http://127.0.0.1:8765", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
