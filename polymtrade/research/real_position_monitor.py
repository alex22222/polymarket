from __future__ import annotations

import argparse
import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from polymtrade.data.crypto_prices import fetch_best_spot
from polymtrade.data.polymarket_markets import parse_barrier_question
from polymtrade.reporting.feishu import FeishuConfigError, send_feishu_report
from polymtrade.storage.db import connect, insert_log


DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "data" / "real_positions.json"
POSITIONS_DATA_SOURCES = (
    "https://polym.trade/data",
    "https://data-api.polymarket.com",
)


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_money(value: Any) -> str:
    numeric = _float_or_none(value)
    if numeric is None:
        return "--"
    return f"${numeric:,.2f}" if abs(numeric) < 10 else f"${numeric:,.0f}"


def _fmt_percent(value: Any) -> str:
    numeric = _float_or_none(value)
    return "--" if numeric is None else f"{numeric * 100:.1f}%"


def _fmt_datetime(value: Any) -> str:
    parsed = _parse_datetime(value)
    return "--" if not parsed else parsed.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def load_positions(path: str | Path = DEFAULT_CONFIG) -> list[dict[str, Any]]:
    config = load_position_config(path)
    positions = config.get("positions") if isinstance(config, dict) else config
    return positions if isinstance(positions, list) else []


def load_position_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return {"positions": payload}
    return payload if isinstance(payload, dict) else {}


def _normalize_key(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _portfolio_url(position: dict[str, Any]) -> str:
    event_id = str(position.get("eventId") or "")
    event_slug = str(position.get("eventSlug") or "")
    if event_id and event_slug:
        return (
            "https://polym.trade/portfolio?"
            + urllib.parse.urlencode({"eventId": event_id, "eventSlug": event_slug, "eventSource": "polymarket"})
        )
    if event_slug:
        return f"https://polym.trade/event/{event_slug}"
    return "https://polym.trade/portfolio"


def _fetch_json(url: str, timeout: int) -> Any:
    req = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "polymtrade-research/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
            return json.loads(resp.read().decode("utf-8"))


def fetch_wallet_positions(wallet: str, size_threshold: float = 0.01, timeout: int = 8) -> dict[str, Any]:
    errors: list[str] = []
    wallet = str(wallet or "").strip()
    if not wallet:
        return {"ok": False, "positions": [], "source": None, "errors": ["missing wallet"]}
    params = urllib.parse.urlencode({"user": wallet, "sizeThreshold": str(size_threshold)})
    for source in POSITIONS_DATA_SOURCES:
        url = f"{source}/positions?{params}"
        try:
            payload = _fetch_json(url, timeout=timeout)
            if not isinstance(payload, list):
                raise ValueError("positions response is not a list")
            return {"ok": True, "positions": payload, "source": source, "errors": errors}
        except Exception as exc:  # noqa: BLE001 - fallback chain should keep trying
            errors.append(f"{source}: {exc}")
    return {"ok": False, "positions": [], "source": None, "errors": errors}


def _config_rule_index(config_positions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for position in config_positions:
        for key in (
            position.get("condition_id"),
            position.get("conditionId"),
            position.get("slug"),
            position.get("question"),
        ):
            normalized = _normalize_key(key)
            if normalized:
                indexed[normalized] = position
    return indexed


def _rule_config_for(api_position: dict[str, Any], indexed: dict[str, dict[str, Any]]) -> dict[str, Any]:
    for key in (api_position.get("conditionId"), api_position.get("slug"), api_position.get("title")):
        match = indexed.get(_normalize_key(key))
        if match:
            return match
    return {}


def position_from_api(api_position: dict[str, Any], rule_config: dict[str, Any] | None = None, source: str | None = None) -> dict[str, Any]:
    rule_config = rule_config or {}
    question = str(api_position.get("title") or rule_config.get("question") or "")
    parsed = parse_barrier_question(question)
    return {
        "id": str(rule_config.get("id") or api_position.get("conditionId") or api_position.get("asset") or question),
        "asset": str(rule_config.get("asset") or (parsed.asset if parsed else "")).upper(),
        "question": question,
        "side": str(api_position.get("outcome") or rule_config.get("side") or "").upper(),
        "direction": rule_config.get("direction") or (parsed.direction if parsed else None),
        "barrier": rule_config.get("barrier") if rule_config.get("barrier") is not None else (parsed.barrier if parsed else None),
        "end_date": api_position.get("endDate") or rule_config.get("end_date"),
        "shares": api_position.get("size"),
        "portfolio_url": _portfolio_url(api_position),
        "exit_rules": rule_config.get("exit_rules") or [],
        "position_source": "polymarket-data-api",
        "position_source_url": source,
        "proxy_wallet": api_position.get("proxyWallet"),
        "condition_id": api_position.get("conditionId"),
        "token_id": api_position.get("asset"),
        "slug": api_position.get("slug"),
        "event_id": api_position.get("eventId"),
        "event_slug": api_position.get("eventSlug"),
        "avg_price": api_position.get("avgPrice"),
        "current_price": api_position.get("curPrice"),
        "initial_value": api_position.get("initialValue"),
        "current_value": api_position.get("currentValue"),
        "cash_pnl": api_position.get("cashPnl"),
        "percent_pnl": _percent_points_to_ratio(api_position.get("percentPnl")),
        "realized_pnl": api_position.get("realizedPnl"),
        "percent_realized_pnl": _percent_points_to_ratio(api_position.get("percentRealizedPnl")),
        "total_bought": api_position.get("totalBought"),
        "redeemable": api_position.get("redeemable"),
        "mergeable": api_position.get("mergeable"),
    }


def _percent_points_to_ratio(value: Any) -> float | None:
    numeric = _float_or_none(value)
    return None if numeric is None else numeric / 100.0


def load_monitor_positions(path: str | Path = DEFAULT_CONFIG, timeout: int = 8) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config = load_position_config(path)
    wallet = str(os.environ.get("POLYMTRADE_POSITION_WALLET") or config.get("wallet") or "").strip()
    size_threshold = _float_or_none(os.environ.get("POLYMTRADE_POSITION_SIZE_THRESHOLD") or config.get("size_threshold"))
    if size_threshold is None:
        size_threshold = 0.01
    configured_positions = config.get("positions") if isinstance(config.get("positions"), list) else []
    if not wallet:
        return configured_positions, {
            "mode": "manual_config",
            "wallet": None,
            "source": str(path),
            "errors": [],
            "positions_fetched": 0,
        }
    fetched = fetch_wallet_positions(wallet, size_threshold=size_threshold, timeout=timeout)
    if not fetched.get("ok"):
        return [], {
            "mode": "wallet_api",
            "wallet": wallet,
            "source": None,
            "errors": fetched.get("errors") or [],
            "positions_fetched": 0,
        }
    indexed = _config_rule_index(configured_positions)
    positions = [position_from_api(position, _rule_config_for(position, indexed), fetched.get("source")) for position in fetched["positions"]]
    return positions, {
        "mode": "wallet_api",
        "wallet": wallet,
        "source": fetched.get("source"),
        "errors": fetched.get("errors") or [],
        "positions_fetched": len(positions),
        "size_threshold": size_threshold,
    }


def _rule_triggered(rule: dict[str, Any], position: dict[str, Any], spot: float, now: datetime) -> bool:
    metric = str(rule.get("metric") or "")
    value = _float_or_none(rule.get("value"))
    if value is None:
        return False
    if metric == "spot_lte":
        return spot <= value
    if metric == "spot_gte":
        return spot >= value
    if metric == "days_lte_and_spot_lt":
        end_at = _parse_datetime(position.get("end_date"))
        days_limit = _float_or_none(rule.get("days"))
        if not end_at or days_limit is None:
            return False
        days_remaining = (end_at - now).total_seconds() / 86400
        return days_remaining <= days_limit and spot < value
    return False


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _distance_to_barrier(position: dict[str, Any], spot: float) -> float | None:
    barrier = _float_or_none(position.get("barrier"))
    if not barrier or spot <= 0:
        return None
    if position.get("direction") == "hit_below":
        return spot / barrier - 1.0
    return barrier / spot - 1.0


def latest_db_quotes(conn, assets: set[str], max_age_hours: float = 36.0) -> dict[str, dict[str, Any]]:
    quotes: dict[str, dict[str, Any]] = {}
    now = datetime.now(timezone.utc)
    for asset in assets:
        row = conn.execute(
            """
            select close, source, ts
            from crypto_candles
            where asset = ?
              and interval = '1d'
            order by ts desc
            limit 1
            """,
            (asset,),
        ).fetchone()
        if row:
            fetched_at = _parse_datetime(row["ts"])
            if fetched_at and (now - fetched_at).total_seconds() > max_age_hours * 3600:
                continue
            quotes[asset] = {
                "price": float(row["close"]),
                "source": f"{row['source']}:daily-close",
                "fetched_at": row["ts"],
                "is_realtime": False,
            }
    return quotes


def evaluate_positions(
    positions: list[dict[str, Any]],
    timeout: int = 4,
    now: datetime | None = None,
    fallback_quotes: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    quotes: dict[str, dict[str, Any]] = {}
    alerts: list[dict[str, Any]] = []
    evaluated: list[dict[str, Any]] = []
    errors: list[str] = []
    fallback_quotes = fallback_quotes or {}
    for asset in sorted({str(position.get("asset") or "").upper() for position in positions if position.get("asset")}):
        quote, source_errors = fetch_best_spot(asset, timeout=timeout)
        if quote:
            quotes[asset] = {"price": quote.price, "source": quote.source, "fetched_at": quote.fetched_at, "is_realtime": True}
        elif asset in fallback_quotes:
            quotes[asset] = fallback_quotes[asset]
            errors.extend(f"{asset} realtime unavailable; using {fallback_quotes[asset].get('source')}" for _ in [0])
            errors.extend(f"{asset} {item}" for item in source_errors)
        else:
            errors.extend(f"{asset} {item}" for item in source_errors)

    for position in positions:
        asset = str(position.get("asset") or "").upper()
        quote = quotes.get(asset)
        if not quote:
            evaluated.append({**position, "status": "spot_unavailable"})
            continue
        spot = float(quote["price"])
        distance = _distance_to_barrier(position, spot)
        row = {
            **position,
            "status": "evaluated",
            "spot": spot,
            "spot_source": quote["source"],
            "spot_fetched_at": quote.get("fetched_at"),
            "spot_is_realtime": bool(quote.get("is_realtime")),
            "distance_to_barrier": distance,
            "triggered_rules": [],
        }
        for rule in position.get("exit_rules") or []:
            if not isinstance(rule, dict):
                continue
            if _rule_triggered(rule, position, spot, now):
                if not quote.get("is_realtime"):
                    row["triggered_rules"].append(f"{rule.get('id')}:not_sent_non_realtime")
                    continue
                alert = {
                    "alert_id": f"{position.get('id')}::{rule.get('id')}",
                    "position_id": position.get("id"),
                    "asset": asset,
                    "question": position.get("question"),
                    "side": position.get("side"),
                    "barrier": position.get("barrier"),
                    "shares": position.get("shares"),
                    "spot": spot,
                    "spot_source": quote["source"],
                    "spot_fetched_at": quote.get("fetched_at"),
                    "spot_is_realtime": bool(quote.get("is_realtime")),
                    "distance_to_barrier": distance,
                    "severity": rule.get("severity") or "review",
                    "message": rule.get("message") or "真实持仓触发复核条件",
                    "portfolio_url": position.get("portfolio_url"),
                    "last_screenshot_value": position.get("last_screenshot_value"),
                    "last_screenshot_pnl": position.get("last_screenshot_pnl"),
                    "last_screenshot_pnl_pct": position.get("last_screenshot_pnl_pct"),
                    "current_value": position.get("current_value"),
                    "initial_value": position.get("initial_value"),
                    "cash_pnl": position.get("cash_pnl"),
                    "percent_pnl": position.get("percent_pnl"),
                    "avg_price": position.get("avg_price"),
                    "current_price": position.get("current_price"),
                }
                row["triggered_rules"].append(rule.get("id"))
                alerts.append(alert)
        evaluated.append(row)
    return {
        "ok": True,
        "generated_at": now.isoformat(),
        "positions": evaluated,
        "alerts": alerts,
        "quotes": quotes,
        "errors": errors,
    }


def build_alert_text(alerts: list[dict[str, Any]]) -> str:
    lines = [
        "Polymtrade 真实持仓平仓提醒",
        f"触发时间: {datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}",
        "",
    ]
    for index, alert in enumerate(alerts, start=1):
        distance = alert.get("distance_to_barrier")
        lines.extend(
            [
                f"{index}. {alert.get('asset')} {alert.get('side')} · {alert.get('severity')}",
                str(alert.get("question") or ""),
                f"现货 {_fmt_money(alert.get('spot'))} · 目标 {_fmt_money(alert.get('barrier'))} · 距触发 {_fmt_percent(distance)}",
                f"行情源 {alert.get('spot_source') or '--'} · 更新时间 {_fmt_datetime(alert.get('spot_fetched_at'))}",
                f"持仓 {alert.get('shares') or '--'} 份 · 成本 {_fmt_money(alert.get('initial_value'))} · 当前价值 {_fmt_money(alert.get('current_value'))}",
                f"合约价 {_fmt_percent(alert.get('current_price'))} · 均价 {_fmt_percent(alert.get('avg_price'))} · PnL {_fmt_money(alert.get('cash_pnl'))} ({_fmt_percent(alert.get('percent_pnl'))})",
                str(alert.get("message") or ""),
            ]
        )
        if alert.get("portfolio_url"):
            lines.append(str(alert["portfolio_url"]))
        lines.append("")
    return "\n".join(lines).strip()


def _recently_sent(conn, alert_id: str, cooldown_hours: float) -> bool:
    if cooldown_hours <= 0:
        return False
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)).isoformat()
    row = conn.execute(
        """
        select id from system_logs
        where module = 'real_positions'
          and message = ?
          and created_at >= ?
        order by id desc
        limit 1
        """,
        (f"alert:{alert_id}", cutoff),
    ).fetchone()
    return row is not None


def send_alerts(conn, alerts: list[dict[str, Any]], cooldown_hours: float) -> dict[str, Any]:
    pending = [alert for alert in alerts if not _recently_sent(conn, str(alert["alert_id"]), cooldown_hours)]
    if not pending:
        return {"ok": True, "sent": 0, "suppressed": len(alerts), "result": None}
    text = build_alert_text(pending)
    result = send_feishu_report(text)
    for alert in pending:
        insert_log(conn, "WARN", "real_positions", f"alert:{alert['alert_id']}", json.dumps(alert, ensure_ascii=False))
    return {"ok": bool(result.get("ok")), "sent": len(pending), "suppressed": len(alerts) - len(pending), "result": result}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor real Polymtrade positions and optionally send Feishu alerts")
    parser.add_argument("--db", default="polymtrade.sqlite")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--timeout", type=int, default=4)
    parser.add_argument("--max-fallback-age-hours", type=float, default=36.0)
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--cooldown-hours", type=float, default=12.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    positions, position_meta = load_monitor_positions(args.config, timeout=args.timeout)
    with connect(args.db) as conn:
        assets = {str(position.get("asset") or "").upper() for position in positions if position.get("asset")}
        report = evaluate_positions(
            positions,
            timeout=args.timeout,
            fallback_quotes=latest_db_quotes(conn, assets, max_age_hours=args.max_fallback_age_hours),
        )
        report["position_source"] = position_meta
        insert_log(conn, "INFO", "real_positions", "Real position monitor evaluated", json.dumps(report, ensure_ascii=False))
        if args.send and report.get("alerts"):
            try:
                report["notification"] = send_alerts(conn, report["alerts"], cooldown_hours=args.cooldown_hours)
            except FeishuConfigError as exc:
                report["notification"] = {"ok": False, "error": "missing Feishu configuration", "detail": str(exc)}
                insert_log(conn, "WARN", "real_positions", f"Feishu real position alert not configured: {exc}")
            except Exception as exc:  # noqa: BLE001 - command should report notification failures clearly
                report["notification"] = {"ok": False, "error": str(exc)}
                insert_log(conn, "ERROR", "real_positions", f"Feishu real position alert failed: {exc}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
