from __future__ import annotations

import re
from dataclasses import dataclass


ASSET_RE = re.compile(r"\b(bitcoin|btc|ethereum|ether|eth)\b", re.IGNORECASE)
PRICE_RE = re.compile(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)(\s*[kK])?")
DATE_RE = re.compile(r"\bby\s+([A-Za-z]+\s+\d{1,2}(?:,\s*\d{4})?)", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedBarrierMarket:
    asset: str
    barrier: float
    direction: str
    deadline_text: str | None


def parse_barrier_question(question: str) -> ParsedBarrierMarket | None:
    asset_match = ASSET_RE.search(question)
    price_match = PRICE_RE.search(question)
    if not asset_match or not price_match:
        return None

    asset_raw = asset_match.group(1).lower()
    asset = "BTC" if asset_raw in {"bitcoin", "btc"} else "ETH"
    price_text = price_match.group(1).replace(",", "")
    barrier = float(price_text)
    if price_match.group(2):
        barrier *= 1_000.0

    lowered = question.lower()
    direction = "hit_above"
    if "below" in lowered or "under" in lowered or "drop" in lowered:
        direction = "hit_below"

    date_match = DATE_RE.search(question)
    deadline_text = date_match.group(1) if date_match else None
    return ParsedBarrierMarket(asset=asset, barrier=barrier, direction=direction, deadline_text=deadline_text)
