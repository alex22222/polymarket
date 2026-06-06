from __future__ import annotations

import subprocess
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from polymtrade.data.crypto_prices import fetch_best_daily
from polymtrade.data.macro_events import macro_context
from polymtrade.data.polymarket_api import (
    fetch_gamma_markets,
    fetch_polymtrade_crypto_events,
    search_gamma_barrier_markets,
    search_polymtrade_barrier_markets,
)
from polymtrade.research.scanner import scan_opportunities
from polymtrade.research.paper import (
    calibration_attribution_report,
    candidate_quality_report,
    candidate_review_report,
    paper_trading_report,
    position_management_report,
)
from polymtrade.research.real_position_monitor import evaluate_positions, latest_db_quotes, load_positions
from polymtrade.reporting.feishu import FeishuConfigError, build_research_report, send_feishu_report
from polymtrade.storage.db import (
    automation_health,
    barrier_market_summary,
    candle_anomaly_report,
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
    upsert_candle_anomaly_review,
    upsert_candles,
    upsert_barrier_markets,
)


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
DB_PATH = ROOT.parent / "polymtrade.sqlite"
VERSION_PATH = ROOT.parent / ".deploy_version.json"


def query_int(query: dict, name: str, default: int) -> int:
    value = query.get(name, [default])[0]
    if value in (None, ""):
        return default
    return int(value)


def query_float(query: dict, name: str, default: float) -> float:
    value = query.get(name, [default])[0]
    if value in (None, ""):
        return default
    return float(value)


def version_info() -> dict:
    if VERSION_PATH.exists():
        try:
            payload = json.loads(VERSION_PATH.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except (OSError, json.JSONDecodeError):
            pass
    info = {"version": "local", "sha": None, "branch": None, "deployed_at": None, "source": "local"}
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT.parent, text=True).strip()
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT.parent, text=True).strip()
        dirty = subprocess.call(["git", "diff", "--quiet"], cwd=ROOT.parent) != 0
        info.update({"version": f"{sha}{'-dirty' if dirty else ''}", "sha": sha, "branch": branch})
    except Exception:
        pass
    return info


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
                deleted = clear_logs(conn, keep=0)
                insert_log(conn, "INFO", "system", f"Logs cleared: {deleted} deleted")
                remaining = conn.execute("select count(*) from system_logs").fetchone()[0]
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
        if path == "/api/candle-anomaly-review":
            try:
                length = int(self.headers.get("content-length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
                required = ("asset", "source", "interval", "ts", "status", "decision")
                missing = [key for key in required if not payload.get(key)]
                if missing:
                    raise ValueError(f"missing fields: {', '.join(missing)}")
                with connect(DB_PATH) as conn:
                    upsert_candle_anomaly_review(
                        conn,
                        asset=str(payload["asset"]),
                        source=str(payload["source"]),
                        interval=str(payload["interval"]),
                        ts=str(payload["ts"]),
                        status=str(payload["status"]),
                        decision=str(payload["decision"]),
                        note=str(payload.get("note") or ""),
                    )
                    report = candle_anomaly_report(conn, threshold=float(payload.get("threshold") or 0.25))
                self.log_event("INFO", "data", f"Candle anomaly reviewed: {payload['asset']} {payload['ts']}")
                self.send_json({"ok": True, "report": report})
            except Exception as exc:
                self.log_event("ERROR", "data", f"Candle anomaly review failed: {exc}")
                self.send_json({"ok": False, "error": str(exc)}, status=400)
            return
        if path == "/api/send-report":
            try:
                length = int(self.headers.get("content-length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
                channel = str(payload.get("channel") or "feishu")
                if channel != "feishu":
                    raise ValueError(f"unsupported report channel: {channel}")
                with connect(DB_PATH) as conn:
                    report = build_research_report(conn)
                result = send_feishu_report(report)
                self.log_event("INFO", "report", f"Report sent via Feishu: status={result.get('status')}")
                self.send_json({"ok": True, "channel": "feishu", "result": result, "preview": report[:500]})
            except FeishuConfigError as exc:
                self.log_event("WARN", "report", f"Feishu report not configured: {exc}")
                self.send_json(
                    {
                        "ok": False,
                        "error": "missing Feishu configuration",
                        "hint": "Set FEISHU_WEBHOOK_URL, or set FEISHU_APP_ID, FEISHU_APP_SECRET, and FEISHU_RECEIVE_ID before starting the server.",
                    },
                    status=400,
                )
            except Exception as exc:
                self.log_event("ERROR", "report", f"Feishu report failed: {exc}")
                self.send_json({"ok": False, "error": str(exc)}, status=502)
            return
        self.send_json({"ok": False, "error": "POST not supported for this path"}, status=405)

    def do_GET(self) -> None:
        try:
            self.handle_get()
        except (TypeError, ValueError) as exc:
            self.send_json({"ok": False, "error": f"bad request: {exc}"}, status=400)
        except Exception as exc:
            self.log_event("ERROR", "system", f"GET {self.path} failed: {exc}")
            self.send_json({"ok": False, "error": str(exc)}, status=500)

    def handle_get(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/api/health":
            self.send_json({"ok": True, "mode": "real-first"})
            return
        if path == "/api/version":
            self.send_json(version_info())
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
        if path == "/api/candle-anomalies":
            threshold = float(query.get("threshold", ["0.25"])[0])
            with connect(DB_PATH) as conn:
                self.send_json(candle_anomaly_report(conn, threshold=threshold))
            return
        if path == "/api/report-preview":
            with connect(DB_PATH) as conn:
                self.send_json({"ok": True, "channel": "feishu", "text": build_research_report(conn)})
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
            current_only = query.get("current_only", ["1"])[0] in {"1", "true", "yes"}
            max_days = float(query.get("max_days", ["14"])[0])
            max_spread = float(query.get("max_spread", ["0.04"])[0])
            max_book_age = float(query.get("max_book_age_seconds", ["120"])[0])
            with connect(DB_PATH) as conn:
                self.send_json(
                    paper_trading_report(
                        conn,
                        limit=limit,
                        stake=stake,
                        current_only=current_only,
                        max_days_to_expiry=max_days,
                        max_spread=max_spread,
                        max_book_age_seconds=max_book_age,
                    )
                )
            return
        if path == "/api/candidate-review":
            limit = int(query.get("limit", ["100"])[0])
            stake = float(query.get("stake", ["100"])[0])
            with connect(DB_PATH) as conn:
                self.send_json(candidate_review_report(conn, limit=limit, stake=stake))
            return
        if path == "/api/position-management":
            limit = int(query.get("limit", ["100"])[0])
            stake = float(query.get("stake", ["100"])[0])
            book_timeout = int(query.get("book_timeout", ["4"])[0])
            max_book_age = int(query.get("max_book_age_seconds", ["120"])[0])
            with connect(DB_PATH) as conn:
                self.send_json(
                    position_management_report(
                        conn,
                        limit=limit,
                        stake=stake,
                        book_timeout=book_timeout,
                        max_book_age_seconds=max_book_age,
                    )
                )
            return
        if path == "/api/real-positions":
            timeout = int(query.get("timeout", ["4"])[0])
            max_fallback_age = float(query.get("max_fallback_age_hours", ["36"])[0])
            positions = load_positions()
            with connect(DB_PATH) as conn:
                assets = {str(position.get("asset") or "").upper() for position in positions if position.get("asset")}
                self.send_json(
                    evaluate_positions(
                        positions,
                        timeout=timeout,
                        fallback_quotes=latest_db_quotes(conn, assets, max_age_hours=max_fallback_age),
                    )
                )
            return
        if path == "/api/quality-analysis":
            limit = int(query.get("limit", ["500"])[0])
            stake = float(query.get("stake", ["100"])[0])
            with connect(DB_PATH) as conn:
                self.send_json(candidate_quality_report(conn, limit=limit, stake=stake))
            return
        if path == "/api/calibration-attribution":
            limit = int(query.get("limit", ["500"])[0])
            stake = float(query.get("stake", ["100"])[0])
            with connect(DB_PATH) as conn:
                self.send_json(calibration_attribution_report(conn, limit=limit, stake=stake))
            return
        if path == "/api/automation-health":
            max_age = int(query.get("max_age_minutes", ["150"])[0])
            with connect(DB_PATH) as conn:
                self.send_json(automation_health(conn, max_age_minutes=max_age))
            return
        if path == "/api/macro-events":
            horizon_hours = query_float(query, "horizon_hours", 720.0)
            self.send_json(macro_context(horizon_hours=horizon_hours))
            return
        if path == "/api/candles":
            asset = query.get("asset", ["BTC"])[0].upper()
            source = query.get("source", [None])[0]
            limit = int(query.get("limit", ["365"])[0])
            with connect(DB_PATH) as conn:
                self.send_json({"asset": asset, "candles": candles_for_asset(conn, asset, source, limit)})
            return
        if path == "/api/scanner":
            limit = query_int(query, "limit", 50)
            edge_threshold = query_float(query, "edge", 0.02)
            min_liquidity = query_float(query, "min_liquidity", 500.0)
            simulations = query_int(query, "simulations", 1500)
            vol_window = query.get("vol_window", ["90d"])[0]
            vol_model = query.get("vol_model", ["factor"])[0]
            iv_timeout = query_int(query, "iv_timeout", 3)
            orderbook = query.get("orderbook", ["0"])[0] in {"1", "true", "yes"}
            book_limit = query_int(query, "book_limit", 30)
            executable_notional = query_float(query, "executable_notional", 100.0)
            book_timeout = query_int(query, "book_timeout", 4)
            max_book_age_seconds = query_int(query, "max_book_age_seconds", 120)
            max_spread = query_float(query, "max_spread", 0.04)
            realtime_spot = query.get("spot", ["realtime"])[0] != "daily"
            require_realtime_spot = query.get("require_realtime_spot", ["1"])[0] in {"1", "true", "yes"}
            spot_timeout = query_int(query, "spot_timeout", 4)
            min_expiry_minutes = query_int(query, "min_expiry_minutes", 30)
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
                        min_expiry_minutes=min_expiry_minutes,
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
                        "ok": bool(candles),
                        "partial": bool(errors),
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
