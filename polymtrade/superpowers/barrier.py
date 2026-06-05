from __future__ import annotations

import math
import random
from dataclasses import dataclass


TRADING_DAYS = 365.0


@dataclass(frozen=True)
class BarrierInput:
    spot: float
    barrier: float
    days_to_expiry: float
    annual_vol: float
    drift: float = 0.0
    direction: str = "hit_above"


@dataclass(frozen=True)
class BarrierResult:
    base_probability: float
    adjusted_probability: float
    simulations: int
    touched_paths: int
    annual_vol: float
    standard_error: float
    ci_low: float
    ci_high: float


def realized_volatility(prices: list[float], periods_per_year: float = TRADING_DAYS) -> float:
    if len(prices) < 3:
        return 0.75
    returns: list[float] = []
    for previous, current in zip(prices, prices[1:]):
        if previous > 0 and current > 0:
            returns.append(math.log(current / previous))
    if len(returns) < 2:
        return 0.75
    mean = sum(returns) / len(returns)
    variance = sum((item - mean) ** 2 for item in returns) / (len(returns) - 1)
    return max(0.05, min(2.5, math.sqrt(variance * periods_per_year)))


def ewma_volatility(prices: list[float], decay: float = 0.94, periods_per_year: float = TRADING_DAYS) -> float:
    if len(prices) < 3:
        return realized_volatility(prices, periods_per_year=periods_per_year)
    returns: list[float] = []
    for previous, current in zip(prices, prices[1:]):
        if previous > 0 and current > 0:
            returns.append(math.log(current / previous))
    if len(returns) < 2:
        return realized_volatility(prices, periods_per_year=periods_per_year)
    variance = returns[0] * returns[0]
    alpha = max(0.0, min(0.999, decay))
    for item in returns[1:]:
        variance = alpha * variance + (1.0 - alpha) * item * item
    return max(0.05, min(2.5, math.sqrt(variance * periods_per_year)))


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _first_passage_probability(distance: float, log_drift: float, sigma: float, years: float) -> float:
    if distance <= 0:
        return 1.0
    if sigma <= 0 or years <= 0:
        return 0.0
    scale = sigma * math.sqrt(years)
    first = _normal_cdf((log_drift * years - distance) / scale)
    exponent = max(-700.0, min(700.0, 2.0 * log_drift * distance / (sigma * sigma)))
    second = math.exp(exponent) * _normal_cdf(-(log_drift * years + distance) / scale)
    return max(0.0, min(1.0, first + second))


def closed_form_touch_probability(item: BarrierInput) -> float:
    if item.spot <= 0 or item.barrier <= 0 or item.days_to_expiry <= 0:
        return 0.0
    sigma = max(0.01, item.annual_vol)
    years = item.days_to_expiry / TRADING_DAYS
    log_drift = item.drift - 0.5 * sigma * sigma
    if item.direction == "hit_below":
        if item.spot <= item.barrier:
            return 1.0
        return _first_passage_probability(math.log(item.spot / item.barrier), -log_drift, sigma, years)
    if item.spot >= item.barrier:
        return 1.0
    return _first_passage_probability(math.log(item.barrier / item.spot), log_drift, sigma, years)


def monte_carlo_touch_probability(
    item: BarrierInput,
    simulations: int = 8_000,
    steps_per_day: int = 4,
    seed: int = 7,
) -> BarrierResult:
    if item.spot <= 0 or item.barrier <= 0 or item.days_to_expiry <= 0:
        return BarrierResult(0.0, 0.0, simulations, 0, item.annual_vol, 0.0, 0.0, 0.0)

    steps = max(1, int(item.days_to_expiry * steps_per_day))
    dt = item.days_to_expiry / TRADING_DAYS / steps
    sigma = max(0.01, item.annual_vol)
    drift_term = (item.drift - 0.5 * sigma * sigma) * dt
    vol_term = sigma * math.sqrt(dt)
    rng = random.Random(seed)
    touched = 0

    for _ in range(simulations):
        price = item.spot
        hit = price >= item.barrier if item.direction == "hit_above" else price <= item.barrier
        for _step in range(steps):
            if hit:
                break
            price *= math.exp(drift_term + vol_term * rng.gauss(0.0, 1.0))
            if item.direction == "hit_above":
                hit = price >= item.barrier
            else:
                hit = price <= item.barrier
        if hit:
            touched += 1

    base = touched / simulations
    if touched == simulations:
        adjusted = 1.0
    elif touched == 0:
        adjusted = 0.0
    else:
        adjusted = min(0.995, max(0.005, base))
    standard_error = math.sqrt(max(0.0, base * (1.0 - base)) / simulations) if simulations > 0 else 0.0
    ci_low = max(0.0, base - 1.96 * standard_error)
    ci_high = min(1.0, base + 1.96 * standard_error)
    return BarrierResult(base, adjusted, simulations, touched, sigma, standard_error, ci_low, ci_high)


def edge_for_yes(model_probability: float, ask_price: float, fee_rate: float, slippage_bps: float) -> dict[str, float]:
    taker_fee = fee_rate * ask_price * (1.0 - ask_price)
    slippage = ask_price * slippage_bps / 10_000.0
    net_ev = model_probability - ask_price - taker_fee - slippage
    roi = net_ev / ask_price if ask_price > 0 else 0.0
    return {
        "taker_fee": taker_fee,
        "slippage": slippage,
        "net_ev": net_ev,
        "roi": roi,
    }
