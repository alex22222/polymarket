from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVENTS_PATH = Path(__file__).resolve().parents[2] / "data" / "macro_events.json"
HIGH_IMPACT_TYPES = {"cpi", "fomc", "employment", "gdp"}


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_macro_events(path: Path = EVENTS_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    events = payload.get("events") if isinstance(payload, dict) else payload
    if not isinstance(events, list):
        return []
    normalized: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        scheduled_at = parse_datetime(event.get("scheduled_at"))
        if not scheduled_at:
            continue
        normalized.append(
            {
                "id": str(event.get("id") or f"macro-{scheduled_at.isoformat()}"),
                "type": str(event.get("type") or "macro"),
                "title": str(event.get("title") or "Macro event"),
                "scheduled_at": scheduled_at.isoformat(),
                "impact": str(event.get("impact") or "medium"),
                "pre_window_hours": float(event.get("pre_window_hours") or 24),
                "post_window_hours": float(event.get("post_window_hours") or 6),
                "source": str(event.get("source") or "manual"),
                "notes": str(event.get("notes") or ""),
            }
        )
    return sorted(normalized, key=lambda item: item["scheduled_at"])


def macro_context(now: datetime | None = None, horizon_hours: float = 168.0) -> dict[str, Any]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    horizon_seconds = max(0.0, horizon_hours) * 3600
    events = load_macro_events()
    upcoming: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []
    for event in events:
        scheduled_at = parse_datetime(event.get("scheduled_at"))
        if not scheduled_at:
            continue
        delta_seconds = (scheduled_at - now).total_seconds()
        event_with_delta = {**event, "hours_until": delta_seconds / 3600}
        if 0 <= delta_seconds <= horizon_seconds:
            upcoming.append(event_with_delta)
        pre_seconds = float(event.get("pre_window_hours") or 0) * 3600
        post_seconds = float(event.get("post_window_hours") or 0) * 3600
        if -post_seconds <= delta_seconds <= pre_seconds:
            active.append(event_with_delta)
    return {
        "source": "data/macro_events.json",
        "generated_at": now.isoformat(),
        "horizon_hours": horizon_hours,
        "active": active,
        "upcoming": upcoming,
        "active_count": len(active),
        "upcoming_count": len(upcoming),
    }


def macro_risk_for_market(now: datetime, end_at: datetime | None, limit: int = 4) -> dict[str, Any]:
    if not end_at:
        return {"risk_level": "unknown", "events": [], "labels": []}
    now = now.astimezone(timezone.utc)
    end_at = end_at.astimezone(timezone.utc)
    relevant: list[dict[str, Any]] = []
    for event in load_macro_events():
        scheduled_at = parse_datetime(event.get("scheduled_at"))
        if not scheduled_at:
            continue
        post_seconds = float(event.get("post_window_hours") or 0) * 3600
        if now <= scheduled_at <= end_at:
            relevant.append({**event, "hours_until": (scheduled_at - now).total_seconds() / 3600})
        elif -post_seconds <= (scheduled_at - now).total_seconds() <= 0:
            relevant.append({**event, "hours_until": (scheduled_at - now).total_seconds() / 3600})
    labels = [f"{event['title']} {event['hours_until']:.1f}h" for event in relevant[:limit]]
    high_events = [event for event in relevant if event.get("impact") == "high" or event.get("type") in HIGH_IMPACT_TYPES]
    if high_events:
        risk_level = "high"
    elif relevant:
        risk_level = "medium"
    else:
        risk_level = "normal"
    return {
        "risk_level": risk_level,
        "events": relevant[:limit],
        "labels": labels,
        "event_count": len(relevant),
    }
