from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from polymtrade.superpowers.barrier import BarrierInput, edge_for_yes, monte_carlo_touch_probability
from polymtrade.superpowers.demo_data import DemoMarket, make_demo_markets


def max_drawdown(equity: list[float]) -> float:
    peak = equity[0] if equity else 1.0
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value - peak) / peak)
    return abs(worst)


def profit_factor(pnls: list[float]) -> float:
    gains = sum(item for item in pnls if item > 0)
    losses = abs(sum(item for item in pnls if item < 0))
    if losses == 0:
        return gains if gains else 0.0
    return gains / losses


def evaluate_market(
    market: DemoMarket,
    fee_rate: float,
    slippage_bps: float,
    edge_threshold: float,
    stake_fraction: float,
    capital: float,
) -> dict[str, Any] | None:
    vol = 0.72 if market.asset == "BTC" else 0.86
    result = monte_carlo_touch_probability(
        BarrierInput(
            spot=market.spot,
            barrier=market.barrier,
            days_to_expiry=market.days_to_expiry,
            annual_vol=vol,
        ),
        simulations=5_000,
        steps_per_day=4,
        seed=abs(hash((market.market_id, market.spot))) % 10_000,
    )
    costs = edge_for_yes(result.adjusted_probability, market.market_ask, fee_rate, slippage_bps)
    if costs["net_ev"] < edge_threshold:
        return None

    stake = min(capital * stake_fraction, market.liquidity * 0.05)
    if stake <= 0:
        return None
    shares = stake / market.market_ask
    payout = shares if market.outcome else 0.0
    pnl = payout - stake
    return {
        "market_id": market.market_id,
        "asset": market.asset,
        "question": market.question,
        "spot": market.spot,
        "barrier": market.barrier,
        "days_to_expiry": market.days_to_expiry,
        "market_ask": market.market_ask,
        "model_probability": result.adjusted_probability,
        "net_edge": costs["net_ev"],
        "roi": costs["roi"],
        "stake": stake,
        "payout": payout,
        "pnl": pnl,
        "outcome": market.outcome,
    }


def run_demo_backtest(
    starting_capital: float = 10_000.0,
    edge_threshold: float = 0.04,
    stake_fraction: float = 0.015,
    fee_rate: float = 0.04,
    slippage_bps: float = 50.0,
) -> dict[str, Any]:
    capital = starting_capital
    equity = [capital]
    trades: list[dict[str, Any]] = []
    for market in make_demo_markets():
        trade = evaluate_market(market, fee_rate, slippage_bps, edge_threshold, stake_fraction, capital)
        if not trade:
            continue
        capital += trade["pnl"]
        equity.append(capital)
        trades.append(trade)

    pnls = [item["pnl"] for item in trades]
    wins = [item for item in trades if item["pnl"] > 0]
    run = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "demo-offline",
        "starting_capital": starting_capital,
        "ending_capital": capital,
        "total_return": (capital - starting_capital) / starting_capital,
        "max_drawdown": max_drawdown(equity),
        "trades": len(trades),
        "win_rate": len(wins) / len(trades) if trades else 0.0,
        "profit_factor": profit_factor(pnls),
        "equity_curve": equity,
    }
    return {"run": run, "trades": trades}

