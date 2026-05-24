from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from polymtrade.data.polymarket_markets import parse_barrier_question


GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"
GAMMA_PUBLIC_SEARCH_URL = "https://gamma-api.polymarket.com/public-search"
CLOB_PRICES_HISTORY_URL = "https://clob.polymarket.com/prices-history"
POLYMTRADE_PUBLIC_SEARCH_URL = "https://polym.trade/gapi/public-search"
POLYMTRADE_EVENTS_KEYSET_URL = "https://polym.trade/gapi/events/keyset"
POLYMTRADE_CLOB_PRICES_HISTORY_URL = "https://polym.trade/clob/prices-history"


def get_json(url: str, params: dict[str, Any] | None = None, timeout: int = 8, retries: int = 1) -> Any:
    request_url = url
    if params:
        request_url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    req = urllib.request.Request(
        request_url,
        headers={
            "accept": "application/json",
            "user-agent": "polymtrade-research/0.1",
        },
    )
    last_error: BaseException | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (TimeoutError, urllib.error.URLError) as exc:
            last_error = exc
            if "CERTIFICATE_VERIFY_FAILED" in str(exc):
                context = ssl._create_unverified_context()
                with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            if attempt < retries:
                time.sleep(1.0 + attempt)
                continue
            raise
    raise RuntimeError(f"request failed: {request_url}") from last_error


def parse_jsonish(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def floatish(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def bool_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return 1 if value else 0
    if isinstance(value, str):
        return 1 if value.lower() in {"true", "1", "yes"} else 0
    return None


def extract_yes_no(market: dict[str, Any]) -> tuple[str | None, str | None, float | None, float | None]:
    token_ids = parse_jsonish(market.get("clobTokenIds"))
    outcomes = parse_jsonish(market.get("outcomes"))
    prices = parse_jsonish(market.get("outcomePrices"))
    if not isinstance(token_ids, list) or len(token_ids) < 2:
        return None, None, None, None

    yes_idx = 0
    no_idx = 1
    if isinstance(outcomes, list):
        labels = [str(item).strip().lower() for item in outcomes]
        if "yes" in labels and "no" in labels:
            yes_idx = labels.index("yes")
            no_idx = labels.index("no")

    yes_token_id = str(token_ids[yes_idx]) if yes_idx < len(token_ids) else None
    no_token_id = str(token_ids[no_idx]) if no_idx < len(token_ids) else None
    yes_price = None
    no_price = None
    if isinstance(prices, list):
        yes_price = floatish(prices[yes_idx]) if yes_idx < len(prices) else None
        no_price = floatish(prices[no_idx]) if no_idx < len(prices) else None
    return yes_token_id, no_token_id, yes_price, no_price


def record_from_gamma_market(market: dict[str, Any], source: str = "gamma") -> dict[str, Any] | None:
    question = str(market.get("question") or market.get("title") or "")
    parsed = parse_barrier_question(question)
    if not parsed:
        return None
    yes_token_id, no_token_id, yes_price, no_price = extract_yes_no(market)
    market_id = str(market.get("id") or market.get("conditionId") or market.get("slug") or question)
    return {
        "market_id": market_id,
        "question": question,
        "asset": parsed.asset,
        "barrier": parsed.barrier,
        "direction": parsed.direction,
        "deadline_text": parsed.deadline_text,
        "slug": market.get("slug"),
        "end_date": market.get("endDate") or market.get("end_date") or market.get("endDateIso"),
        "active": bool_int(market.get("active")),
        "closed": bool_int(market.get("closed")),
        "yes_token_id": yes_token_id,
        "no_token_id": no_token_id,
        "yes_price": yes_price,
        "no_price": no_price,
        "volume": floatish(market.get("volume") or market.get("volumeNum")),
        "liquidity": floatish(market.get("liquidity") or market.get("liquidityNum")),
        "source": source,
        "raw_json": json.dumps(market, ensure_ascii=False),
    }


def fetch_gamma_markets(
    limit: int = 100,
    pages: int = 3,
    closed: bool | None = None,
    active: bool | None = None,
    timeout: int = 8,
    retries: int = 1,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(pages):
        params: dict[str, Any] = {
            "limit": limit,
            "offset": page * limit,
            "archived": "false",
            "order": "volume",
            "ascending": "false",
        }
        if closed is not None:
            params["closed"] = "true" if closed else "false"
        if active is not None:
            params["active"] = "true" if active else "false"
        data = get_json(GAMMA_MARKETS_URL, params, timeout=timeout, retries=retries)
        markets = data if isinstance(data, list) else data.get("markets", []) if isinstance(data, dict) else []
        if not markets:
            break
        for market in markets:
            if not isinstance(market, dict):
                continue
            record = record_from_gamma_market(market)
            if not record or record["market_id"] in seen:
                continue
            seen.add(record["market_id"])
            records.append(record)
    return records


def _walk_market_dicts(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if value.get("question") and (value.get("clobTokenIds") or value.get("outcomes")):
            found.append(value)
        for child in value.values():
            found.extend(_walk_market_dicts(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_market_dicts(child))
    return found


def search_gamma_barrier_markets(
    queries: list[str] | None = None,
    limit_per_type: int = 50,
    timeout: int = 8,
    retries: int = 1,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query in queries or ["bitcoin", "btc", "ethereum", "eth"]:
        data = get_json(
            GAMMA_PUBLIC_SEARCH_URL,
            {
                "q": query,
                "limit_per_type": limit_per_type,
                "search_profiles": "false",
                "search_tags": "false",
                "keep_closed_markets": 1,
            },
            timeout=timeout,
            retries=retries,
        )
        for market in _walk_market_dicts(data):
            record = record_from_gamma_market(market, source="gamma-search")
            if not record or record["market_id"] in seen:
                continue
            seen.add(record["market_id"])
            records.append(record)
    return records


def search_polymtrade_barrier_markets(
    queries: list[str] | None = None,
    limit_per_type: int = 100,
    timeout: int = 30,
    retries: int = 1,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query in queries or ["bitcoin hit", "ethereum hit"]:
        data = get_json(
            POLYMTRADE_PUBLIC_SEARCH_URL,
            {
                "q": query,
                "limit_per_type": limit_per_type,
                "search_profiles": "false",
                "search_tags": "false",
                "keep_closed_markets": 1,
            },
            timeout=timeout,
            retries=retries,
        )
        for record in records_from_gamma_payload(data, source=f"polymtrade-search:{query}"):
            if record["market_id"] in seen:
                continue
            seen.add(record["market_id"])
            records.append(record)
    return records


def fetch_polymtrade_crypto_events(limit: int = 20, timeout: int = 30, retries: int = 1) -> list[dict[str, Any]]:
    data = get_json(
        POLYMTRADE_EVENTS_KEYSET_URL,
        {
            "active": "true",
            "ascending": "true",
            "closed": "false",
            "limit": limit,
            "order": "endDate",
            "tag_slug": "crypto",
        },
        timeout=timeout,
        retries=retries,
    )
    return records_from_gamma_payload(data, source="polymtrade-events:crypto")


def records_from_gamma_payload(payload: Any, source: str) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("markets", "data", "results"):
            if isinstance(payload.get(key), list):
                markets = payload[key]
                break
        else:
            markets = _walk_market_dicts(payload)
    elif isinstance(payload, list):
        markets = payload
    else:
        markets = []

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in markets:
        if not isinstance(item, dict):
            continue
        record = record_from_gamma_market(item, source=source)
        if not record or record["market_id"] in seen:
            continue
        seen.add(record["market_id"])
        records.append(record)
    return records


def fetch_prices_history(
    token_id: str,
    interval: str = "max",
    fidelity: int = 720,
    source: str = "clob",
) -> list[dict[str, Any]]:
    url = POLYMTRADE_CLOB_PRICES_HISTORY_URL if source == "polymtrade" else CLOB_PRICES_HISTORY_URL
    data = get_json(url, {"market": token_id, "interval": interval, "fidelity": fidelity}, timeout=20, retries=1)
    rows = data.get("history", []) if isinstance(data, dict) else []
    parsed: list[dict[str, Any]] = []
    for row in rows:
        try:
            parsed.append({"ts": int(row["t"]), "price": float(row["p"])})
        except (KeyError, TypeError, ValueError):
            continue
    return parsed


def price_history_records(
    market: dict[str, Any],
    interval: str = "max",
    fidelity: int = 720,
    history_source: str = "clob",
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for outcome, token_key in (("YES", "yes_token_id"), ("NO", "no_token_id")):
        token_id = market.get(token_key)
        if not token_id:
            continue
        for item in fetch_prices_history(str(token_id), interval=interval, fidelity=fidelity, source=history_source):
            rows.append(
                {
                    "market_id": market["market_id"],
                    "token_id": str(token_id),
                    "outcome": outcome,
                    "ts": item["ts"],
                    "price": item["price"],
                    "source": f"{history_source}:{interval}",
                }
            )
    return rows
