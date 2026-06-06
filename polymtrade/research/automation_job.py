from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from polymtrade.data.crypto_prices import fetch_best_daily
from polymtrade.data.polymarket_api import (
    fetch_gamma_markets,
    fetch_polymtrade_crypto_events,
    search_gamma_barrier_markets,
    search_polymtrade_barrier_markets,
)
from polymtrade.research.real_position_monitor import evaluate_positions, latest_db_quotes, load_positions, send_alerts
from polymtrade.research.scanner import scan_opportunities
from polymtrade.storage.db import (
    candle_summary,
    connect,
    insert_automation_source_health,
    insert_log,
    insert_scanner_observation_run,
    scanner_observation_summary,
    upsert_barrier_markets,
    upsert_candles,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh Polymtrade research data and optionally save scanner observations")
    parser.add_argument("--db", default="polymtrade.sqlite")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--skip-prices", action="store_true")
    parser.add_argument("--skip-markets", action="store_true")
    parser.add_argument("--skip-scanner", action="store_true")
    parser.add_argument("--save-observation", action="store_true")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--edge", type=float, default=0.02)
    parser.add_argument("--min-liquidity", type=float, default=500.0)
    parser.add_argument("--simulations", type=int, default=800)
    parser.add_argument("--vol-window", choices=("30d", "90d", "180d"), default="90d")
    parser.add_argument("--vol-model", choices=("factor", "rv"), default="factor")
    parser.add_argument("--iv-timeout", type=int, default=3)
    parser.add_argument("--orderbook", dest="orderbook", action="store_true", default=True)
    parser.add_argument("--no-orderbook", dest="orderbook", action="store_false")
    parser.add_argument("--book-limit", type=int, default=8)
    parser.add_argument("--book-timeout", type=int, default=4)
    parser.add_argument("--executable-notional", type=float, default=100.0)
    parser.add_argument("--max-book-age-seconds", type=int, default=120)
    parser.add_argument("--max-spread", type=float, default=0.04)
    parser.add_argument("--min-expiry-minutes", type=int, default=30)
    parser.add_argument("--skip-real-positions", action="store_true")
    parser.add_argument("--real-position-config", default="data/real_positions.json")
    parser.add_argument("--real-position-cooldown-hours", type=float, default=12.0)
    parser.add_argument("--real-position-max-fallback-age-hours", type=float, default=36.0)
    return parser.parse_args()


def refresh_prices(db_path: str, days: int) -> dict:
    candles = []
    errors: list[str] = []
    asset_sources: dict[str, str] = {}
    for asset in ("BTC", "ETH"):
        fetched, source_errors = fetch_best_daily(asset, limit=days)
        candles.extend(fetched)
        if fetched:
            asset_sources[asset] = fetched[0].source
        errors.extend(f"{asset} {item}" for item in source_errors)
    with connect(db_path) as conn:
        inserted = upsert_candles(conn, candles)
        return {
            "inserted": inserted,
            "errors": errors,
            "asset_sources": asset_sources,
            "summary": candle_summary(conn),
        }


def refresh_markets(db_path: str) -> dict:
    records = []
    errors: list[str] = []
    sources: list[dict] = []
    for label, fetcher in (
        ("polymtrade-search", lambda: search_polymtrade_barrier_markets(timeout=5, retries=0)),
        ("polymtrade-events", lambda: fetch_polymtrade_crypto_events(timeout=5, retries=0)),
        ("gamma-search", lambda: search_gamma_barrier_markets(queries=["bitcoin", "ethereum"], limit_per_type=20, timeout=5, retries=0)),
        ("gamma-markets-open", lambda: fetch_gamma_markets(limit=50, pages=1, closed=False, active=True, timeout=5, retries=0)),
        ("gamma-markets-closed", lambda: fetch_gamma_markets(limit=50, pages=1, closed=True, active=None, timeout=5, retries=0)),
    ):
        try:
            fetched = fetcher()
            records.extend(fetched)
            sources.append({"label": label, "records": len(fetched), "errors": []})
        except Exception as exc:  # noqa: BLE001 - automation should keep partial data moving
            errors.append(f"{label}: {exc}")
            sources.append({"label": label, "records": 0, "errors": [str(exc)]})
    with connect(db_path) as conn:
        inserted = upsert_barrier_markets(conn, records)
    return {"inserted": inserted, "errors": errors, "sources": sources}


def run_scanner(db_path: str, args: argparse.Namespace) -> dict:
    with connect(db_path) as conn:
        payload = scan_opportunities(
            conn,
            limit=args.limit,
            edge_threshold=args.edge,
            min_liquidity=args.min_liquidity,
            simulations=args.simulations,
            vol_window=args.vol_window,
            vol_model=args.vol_model,
            iv_timeout=args.iv_timeout,
            orderbook=args.orderbook,
            book_limit=args.book_limit,
            executable_notional=args.executable_notional,
            book_timeout=args.book_timeout,
            max_book_age_seconds=args.max_book_age_seconds,
            max_spread=args.max_spread,
            min_expiry_minutes=args.min_expiry_minutes,
        )
        observation_run_id = None
        if args.save_observation:
            observation_run_id = insert_scanner_observation_run(conn, payload)
        observation_summary = scanner_observation_summary(conn)
    return {
        "payload": {
            "summary": payload.get("summary"),
            "generated_at": payload.get("generated_at"),
            "contexts": payload.get("contexts"),
        },
        "observation_run_id": observation_run_id,
        "observation_summary": observation_summary,
    }


def monitor_real_positions(db_path: str, args: argparse.Namespace) -> dict:
    positions = load_positions(args.real_position_config)
    with connect(db_path) as conn:
        assets = {str(position.get("asset") or "").upper() for position in positions if position.get("asset")}
        report = evaluate_positions(
            positions,
            timeout=args.book_timeout,
            fallback_quotes=latest_db_quotes(conn, assets, max_age_hours=args.real_position_max_fallback_age_hours),
        )
        if report.get("alerts"):
            try:
                report["notification"] = send_alerts(
                    conn,
                    report["alerts"],
                    cooldown_hours=args.real_position_cooldown_hours,
                )
            except Exception as exc:  # noqa: BLE001 - monitor should not break data automation
                report["notification"] = {"ok": False, "error": str(exc)}
                insert_log(conn, "ERROR", "real_positions", f"Real position alert failed: {exc}", json.dumps(report, ensure_ascii=False))
    return report


_NETWORK_UNAVAILABLE_PATTERNS = (
    "timed out", "timeout", "connection refused", "no route to host",
    "unreachable", "name or service not known", "getaddrinfo failed",
    "certificate verify failed", "ssl", "temporary failure in name resolution",
    "host is down", "network is unreachable", "nodename nor servname provided",
)


def _is_network_unavailable(error_msg: str) -> bool:
    lower = error_msg.lower()
    return any(p in lower for p in _NETWORK_UNAVAILABLE_PATTERNS)


def _source_row(source: str, component: str, status: str, records: int | None, errors: list[str], message: str) -> dict:
    return {
        "source": source,
        "component": component,
        "status": status,
        "records": records,
        "errors": len(errors),
        "message": message,
        "detail": {"errors": errors},
    }


def _resolve_status(records: int, errors: list[str]) -> str:
    if records and not errors:
        return "healthy"
    if records and errors:
        return "degraded"
    if not errors:
        return "skipped"
    if all(_is_network_unavailable(err) for err in errors):
        return "network_unavailable"
    return "error"


def source_health_rows(result: dict) -> list[dict]:
    rows: list[dict] = []
    prices = result.get("prices") or {}
    price_errors = list(prices.get("errors") or [])
    asset_sources = prices.get("asset_sources") or {}
    for source in ("okx", "binance", "coinbase"):
        source_errors = [item for item in price_errors if f" {source}:" in item]
        records = sum(1 for value in asset_sources.values() if value == source)
        status = _resolve_status(records, source_errors)
        if status == "healthy":
            message = f"{records} assets fetched"
        elif status == "degraded":
            message = f"{records} assets fetched, {len(source_errors)} errors"
        elif status == "skipped":
            message = "not selected by fallback chain"
        elif status == "network_unavailable":
            message = f"{len(source_errors)} network unreachable"
        else:
            message = f"{len(source_errors)} fetch errors"
        rows.append(_source_row(source, "price-candles", status, records, source_errors, message))

    markets = result.get("markets") or {}
    market_sources = markets.get("sources") or []
    grouped = {
        "polymtrade": [item for item in market_sources if str(item.get("label", "")).startswith("polymtrade")],
        "gamma": [item for item in market_sources if str(item.get("label", "")).startswith("gamma")],
    }
    for source, items in grouped.items():
        records = sum(int(item.get("records") or 0) for item in items)
        errors = [f"{item.get('label')}: {err}" for item in items for err in item.get("errors", [])]
        status = _resolve_status(records, errors)
        if status == "network_unavailable":
            message = f"{records} markets, network unreachable"
        else:
            message = f"{records} markets, {len(errors)} errors"
        rows.append(_source_row(source, "market-metadata", status, records, errors, message))

    scanner = result.get("scanner") or {}
    payload = scanner.get("payload") or {}
    summary = payload.get("summary") or {}
    contexts = payload.get("contexts") or {}
    deribit_errors = []
    for asset, context in contexts.items():
        if context.get("iv_error"):
            deribit_errors.append(f"{asset}: {context.get('iv_error')}")
    iv_assets = int(summary.get("iv_assets") or 0)
    if iv_assets:
        deribit_status = "healthy"
    elif not deribit_errors:
        deribit_status = "skipped"
    elif all(_is_network_unavailable(err) for err in deribit_errors):
        deribit_status = "network_unavailable"
    else:
        deribit_status = "error"
    deribit_msg = (
        f"{iv_assets} assets with IV"
        if deribit_status in ("healthy", "skipped")
        else "network unreachable"
        if deribit_status == "network_unavailable"
        else f"{len(deribit_errors)} fetch errors"
    )
    rows.append(_source_row("deribit", "option-iv", deribit_status, iv_assets, deribit_errors, deribit_msg))

    binance_spot_assets = sum(1 for context in contexts.values() if str(context.get("source") or "").startswith("binance"))
    binance_spot_errors = [
        f"{asset}: {'; '.join(context.get('spot_errors') or [])}"
        for asset, context in contexts.items()
        if context.get("spot_errors") and str(context.get("source") or "").startswith("binance")
    ]
    if binance_spot_assets:
        status = "healthy" if not binance_spot_errors else "degraded"
        message = f"{binance_spot_assets} live spot assets"
    elif binance_spot_errors:
        status = "error"
        message = f"{len(binance_spot_errors)} spot errors"
    else:
        status = "skipped"
        message = "scanner skipped live spot"
    rows.append(_source_row("binance", "spot-ticker", status, binance_spot_assets, binance_spot_errors, message))
    return rows


def main() -> int:
    args = parse_args()
    result: dict = {
        "ok": True,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "prices": None,
        "markets": None,
        "scanner": None,
        "real_positions": None,
    }
    try:
        if not args.skip_prices:
            result["prices"] = refresh_prices(args.db, args.days)
        if not args.skip_markets:
            result["markets"] = refresh_markets(args.db)
        if not args.skip_scanner:
            result["scanner"] = run_scanner(args.db, args)
        if not args.skip_real_positions:
            result["real_positions"] = monitor_real_positions(args.db, args)
        with connect(args.db) as conn:
            log_id = insert_log(conn, "INFO", "automation", "Automated data refresh completed", json.dumps(result, ensure_ascii=False))
            insert_automation_source_health(conn, log_id, source_health_rows(result))
    except Exception as exc:  # noqa: BLE001 - cron output should clearly show failure
        result["ok"] = False
        result["error"] = str(exc)
        with connect(args.db) as conn:
            log_id = insert_log(conn, "ERROR", "automation", f"Automated data refresh failed: {exc}", json.dumps(result, ensure_ascii=False))
            insert_automation_source_health(conn, log_id, source_health_rows(result))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
