from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from polymtrade.data.crypto_prices import fetch_best_spot
from polymtrade.reporting.feishu import FeishuConfigError, send_feishu_report
from polymtrade.storage.db import connect, insert_log


DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "data" / "real_positions.json"


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_money(value: Any) -> str:
    numeric = _float_or_none(value)
    return "--" if numeric is None else f"${numeric:,.0f}"


def _fmt_percent(value: Any) -> str:
    numeric = _float_or_none(value)
    return "--" if numeric is None else f"{numeric * 100:.1f}%"


def _fmt_datetime(value: Any) -> str:
    parsed = _parse_datetime(value)
    return "--" if not parsed else parsed.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def load_positions(path: str | Path = DEFAULT_CONFIG) -> list[dict[str, Any]]:
    config_path = Path(path)
    if not config_path.exists():
        return []
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    positions = payload.get("positions") if isinstance(payload, dict) else payload
    return positions if isinstance(positions, list) else []


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
                f"持仓 {alert.get('shares') or '--'} 份 · 截图价值 {_fmt_money(alert.get('last_screenshot_value'))} · 截图盈亏 {_fmt_money(alert.get('last_screenshot_pnl'))} ({_fmt_percent(alert.get('last_screenshot_pnl_pct'))})",
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
    positions = load_positions(args.config)
    with connect(args.db) as conn:
        assets = {str(position.get("asset") or "").upper() for position in positions if position.get("asset")}
        report = evaluate_positions(
            positions,
            timeout=args.timeout,
            fallback_quotes=latest_db_quotes(conn, assets, max_age_hours=args.max_fallback_age_hours),
        )
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
