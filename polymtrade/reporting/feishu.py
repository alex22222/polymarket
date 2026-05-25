from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from polymtrade.research.paper import candidate_review_report
from polymtrade.storage.db import automation_health, candle_anomaly_report, data_quality_report, scanner_observation_summary


class FeishuConfigError(RuntimeError):
    pass


def _local_now() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S %Z")


def _fmt_percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "--"


def _fmt_money(value: Any) -> str:
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return "--"


def _fmt_minutes(value: Any) -> str:
    try:
        minutes = float(value)
    except (TypeError, ValueError):
        return "--"
    if minutes < 60:
        return f"{minutes:.0f} 分钟前"
    return f"{minutes / 60:.1f} 小时前"


def build_research_report(conn) -> str:
    quality = data_quality_report(conn)
    anomalies = candle_anomaly_report(conn, threshold=0.25)
    candidates = candidate_review_report(conn, limit=20, stake=100)
    observations = scanner_observation_summary(conn)
    health = automation_health(conn, max_age_minutes=150)

    lines = [
        "Polymtrade BTC/ETH 研究报告",
        f"生成时间: {_local_now()}",
        "",
        f"自动化: {health.get('status', '--')} · 最近运行 {_fmt_minutes(health.get('age_minutes'))}",
    ]
    source_rows = health.get("sources") or []
    if source_rows:
        source_bits = [
            f"{row.get('source')}:{row.get('status')}({row.get('records') or 0}/{row.get('errors') or 0})"
            for row in source_rows[:8]
        ]
        lines.append(f"源健康: {'; '.join(source_bits)}")

    lines.extend(["", f"数据质量: {quality.get('status', '--')}"])
    for asset, row in sorted((quality.get("recommendations") or {}).items()):
        lines.append(
            f"- {asset}: {row.get('source') or '--'} · score {float(row.get('score') or 0):.1f} · "
            f"coverage {_fmt_percent(row.get('coverage'))} · {row.get('reason') or ''}"
        )

    lines.extend(
        [
            "",
            f"异常 K 线: {anomalies.get('count', 0)} 条 · 已复核 {anomalies.get('reviewed', 0)} · 未复核 {anomalies.get('unreviewed', 0)}",
        ]
    )
    for row in (anomalies.get("anomalies") or [])[:5]:
        lines.append(
            f"- {row.get('asset')} {row.get('ts')}: {_fmt_percent(row.get('move'))} · "
            f"{row.get('review_status')} / {row.get('review_decision') or '--'}"
        )

    summary = candidates.get("summary") or {}
    lines.extend(
        [
            "",
            f"候选复盘: tracked {summary.get('tracked', 0)} · resolved {summary.get('resolved', 0)} · "
            f"open {summary.get('open', 0)} · win {_fmt_percent(summary.get('win_rate'))} · "
            f"PnL {_fmt_money(summary.get('pnl'))} · ROI {_fmt_percent(summary.get('roi'))}",
            f"观测样本: runs {observations.get('runs', 0)} · rows {observations.get('rows', 0)} · candidates {observations.get('candidates', 0)}",
        ]
    )

    top_candidates = candidates.get("candidates") or []
    if top_candidates:
        lines.append("")
        lines.append("最近候选:")
        for row in top_candidates[:5]:
            lines.append(
                f"- {row.get('asset')} · edge {_fmt_percent(row.get('net_edge'))} · ROI {_fmt_percent(row.get('roi'))} · "
                f"{row.get('status')} · {str(row.get('question') or '')[:72]}"
            )

    return "\n".join(lines)


def _signed_payload(text: str, secret: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"msg_type": "text", "content": {"text": text}}
    if secret:
        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{secret}"
        sign = base64.b64encode(hmac.new(string_to_sign.encode("utf-8"), b"", hashlib.sha256).digest()).decode("utf-8")
        payload["timestamp"] = timestamp
        payload["sign"] = sign
    return payload


def _request_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"content-type": "application/json; charset=utf-8", **(headers or {})},
        method="POST",
    )
    context = None
    try:
        import certifi

        context = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        context = None
    with urllib.request.urlopen(request, timeout=10, context=context) as response:
        raw = response.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        return response.status, parsed


def _send_webhook_report(text: str, webhook_url: str, secret: str | None) -> dict[str, Any]:
    status, parsed = _request_json(webhook_url, _signed_payload(text, secret))
    ok = 200 <= status < 300 and int(parsed.get("code", 0) or 0) == 0
    return {"ok": ok, "channel": "webhook", "status": status, "response": parsed}


def _receive_id_type(receive_id: str) -> str:
    explicit = os.environ.get("FEISHU_RECEIVE_ID_TYPE", "").strip()
    if explicit:
        return explicit
    if receive_id.startswith("oc_"):
        return "chat_id"
    if receive_id.startswith("ou_"):
        return "open_id"
    if "@" in receive_id:
        return "email"
    return "chat_id"


def _tenant_access_token(app_id: str, app_secret: str) -> str:
    status, parsed = _request_json(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        {"app_id": app_id, "app_secret": app_secret},
    )
    if not (200 <= status < 300) or int(parsed.get("code", -1)) != 0:
        raise RuntimeError(f"feishu tenant token failed: {parsed}")
    token = parsed.get("tenant_access_token")
    if not token:
        raise RuntimeError("feishu tenant token missing in response")
    return str(token)


def _send_app_report(text: str, app_id: str, app_secret: str, receive_id: str) -> dict[str, Any]:
    token = _tenant_access_token(app_id, app_secret)
    receive_id_type = _receive_id_type(receive_id)
    status, parsed = _request_json(
        f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type}",
        {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        },
        headers={"authorization": f"Bearer {token}"},
    )
    ok = 200 <= status < 300 and int(parsed.get("code", -1)) == 0
    return {"ok": ok, "channel": "app", "receive_id_type": receive_id_type, "status": status, "response": parsed}


def send_feishu_report(text: str) -> dict[str, Any]:
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL", "").strip()
    webhook_secret = os.environ.get("FEISHU_WEBHOOK_SECRET", "").strip() or None
    app_id = os.environ.get("FEISHU_APP_ID", "").strip()
    app_secret = os.environ.get("FEISHU_APP_SECRET", "").strip()
    receive_id = os.environ.get("FEISHU_RECEIVE_ID", "").strip()

    try:
        if webhook_url:
            return _send_webhook_report(text, webhook_url, webhook_secret)
        if app_id and app_secret and receive_id:
            return _send_app_report(text, app_id, app_secret, receive_id)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"feishu http {exc.code}: {raw}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"feishu network error: {exc.reason}") from exc

    raise FeishuConfigError("missing Feishu configuration")
