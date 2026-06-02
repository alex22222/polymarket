from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


DERIBIT_BOOK_SUMMARY_URL = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency"
MONTHS = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}


@dataclass(frozen=True)
class ImpliedVolQuote:
    asset: str
    annual_vol: float
    source: str
    instrument_name: str
    expiry: str
    strike: float
    underlying_price: float | None
    fetched_at: str


def _get_json(url: str, params: dict[str, Any], timeout: int = 3) -> Any:
    request_url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        request_url,
        headers={
            "accept": "application/json",
            "user-agent": "polymtrade-research/0.1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (TimeoutError, urllib.error.URLError):
        raise


def parse_deribit_instrument(name: str) -> dict[str, Any] | None:
    parts = name.split("-")
    if len(parts) != 4:
        return None
    asset, expiry_text, strike_text, option_type = parts
    match = re.fullmatch(r"(\d{1,2})([A-Z]{3})(\d{2})", expiry_text.upper())
    if not match:
        return None
    try:
        day = int(match.group(1))
        month = MONTHS[match.group(2)]
        year = 2000 + int(match.group(3))
        strike = float(strike_text)
    except (KeyError, TypeError, ValueError):
        return None
    return {
        "asset": asset,
        "expiry": datetime(year, month, day, tzinfo=timezone.utc),
        "strike": strike,
        "option_type": option_type,
    }


def fetch_deribit_option_summaries(asset: str, timeout: int = 3) -> list[dict[str, Any]]:
    payload = _get_json(
        DERIBIT_BOOK_SUMMARY_URL,
        {"currency": asset.upper(), "kind": "option"},
        timeout=timeout,
    )
    rows = payload.get("result") if isinstance(payload, dict) else None
    return rows if isinstance(rows, list) else []


def _normalized_iv(value: Any) -> float | None:
    try:
        vol = float(value)
    except (TypeError, ValueError):
        return None
    if vol <= 0:
        return None
    if vol > 10.0:
        vol /= 100.0
    return max(0.01, min(5.0, vol))


def select_atm_iv(
    asset: str,
    summaries: list[dict[str, Any]],
    spot: float,
    days_to_expiry: float,
    now: datetime | None = None,
) -> ImpliedVolQuote | None:
    now = now or datetime.now(timezone.utc)
    candidates = []
    for row in summaries:
        name = str(row.get("instrument_name") or "")
        parsed = parse_deribit_instrument(name)
        if not parsed:
            continue
        expiry = parsed["expiry"]
        if expiry <= now:
            continue
        iv = _normalized_iv(row.get("mark_iv") or row.get("mid_iv") or row.get("ask_iv") or row.get("bid_iv"))
        if iv is None:
            continue
        term_days = (expiry - now).total_seconds() / 86_400.0
        strike_distance = abs(float(parsed["strike"]) / spot - 1.0) if spot > 0 else 99.0
        term_distance = abs(term_days - max(1.0, days_to_expiry)) / max(7.0, days_to_expiry)
        option_penalty = 0.02 if parsed["option_type"] == "C" else 0.0
        candidates.append((term_distance + strike_distance + option_penalty, row, parsed, iv))
    if not candidates:
        return None
    _score, row, parsed, iv = min(candidates, key=lambda item: item[0])
    return ImpliedVolQuote(
        asset=asset.upper(),
        annual_vol=iv,
        source="deribit-atm-iv",
        instrument_name=str(row.get("instrument_name")),
        expiry=parsed["expiry"].isoformat(),
        strike=float(parsed["strike"]),
        underlying_price=float(row["underlying_price"]) if row.get("underlying_price") is not None else None,
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )
