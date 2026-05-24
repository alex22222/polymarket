from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class DemoMarket:
    market_id: str
    asset: str
    question: str
    spot: float
    barrier: float
    days_to_expiry: float
    market_ask: float
    liquidity: float
    resolved: bool
    outcome: int


def make_demo_markets(seed: int = 42) -> list[DemoMarket]:
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    specs = [
        ("BTC", 68_500.0, [72_000, 75_000, 80_000, 85_000, 90_000]),
        ("ETH", 3_650.0, [3_900, 4_200, 4_500, 5_000, 5_500]),
    ]
    markets: list[DemoMarket] = []
    idx = 1
    for asset, base_spot, barriers in specs:
        for barrier in barriers:
            for days in (3, 7, 14, 30):
                distance = max(0.01, barrier / base_spot - 1.0)
                rough_prob = math.exp(-distance * 11.0) * min(1.0, math.sqrt(days / 14.0))
                mispricing = rng.uniform(-0.09, 0.08)
                ask = min(0.92, max(0.01, rough_prob + mispricing))
                outcome = 1 if rng.random() < rough_prob else 0
                deadline = (now + timedelta(days=days)).strftime("%b %-d")
                markets.append(
                    DemoMarket(
                        market_id=f"demo-{idx}",
                        asset=asset,
                        question=f"Will {asset} hit ${barrier:,.0f} before {deadline}?",
                        spot=base_spot * rng.uniform(0.965, 1.035),
                        barrier=float(barrier),
                        days_to_expiry=float(days),
                        market_ask=ask,
                        liquidity=rng.uniform(450.0, 8_500.0),
                        resolved=True,
                        outcome=outcome,
                    )
                )
                idx += 1
    return markets

