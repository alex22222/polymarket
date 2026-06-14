from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from polymtrade.storage.db import connect, data_quality_report, insert_log, insert_shadow_training_run
from polymtrade.superpowers.barrier import BarrierInput, closed_form_touch_probability, ewma_volatility, realized_volatility


HORIZONS = (1, 3, 7, 14)
DISTANCES = (0.01, 0.02, 0.05, 0.10)
FEATURE_NAMES = (
    "logit_gbm",
    "is_below",
    "log_horizon",
    "distance",
    "rv30",
    "rv90",
    "ewma",
    "momentum7",
    "momentum30",
)


@dataclass
class Example:
    asset: str
    ts: str
    direction: str
    horizon: int
    distance: float
    spot: float
    barrier: float
    gbm_probability: float
    label: int
    features: list[float]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a shadow barrier calibration model from historical BTC/ETH candles")
    parser.add_argument("--db", default="polymtrade.sqlite")
    parser.add_argument("--assets", default="BTC,ETH")
    parser.add_argument("--lookback", type=int, default=1200)
    parser.add_argument("--min-history", type=int, default=90)
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--epochs", type=int, default=350)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.002)
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--output", default="")
    return parser.parse_args()


def _selected_source(conn, asset: str) -> str | None:
    recommendation = (data_quality_report(conn).get("recommendations") or {}).get(asset) or {}
    return recommendation.get("source")


def load_candles(conn, asset: str, limit: int) -> list[dict[str, Any]]:
    source = _selected_source(conn, asset)
    source_clause = "and source = ?" if source else ""
    params: list[Any] = [asset]
    if source:
        params.append(source)
    params.append(limit)
    rows = conn.execute(
        f"""
        select asset, ts, open, high, low, close, volume, source, interval
        from crypto_candles
        where asset = ?
          and interval = '1d'
          {source_clause}
        order by ts desc
        limit ?
        """,
        params,
    ).fetchall()
    return [dict(row) for row in reversed(rows)]


def _safe_logit(value: float) -> float:
    p = min(0.999, max(0.001, value))
    return math.log(p / (1.0 - p))


def _momentum(values: list[float], index: int, window: int) -> float:
    if index < window or values[index - window] <= 0:
        return 0.0
    return math.log(values[index] / values[index - window])


def _hit_future(candles: list[dict[str, Any]], start: int, horizon: int, direction: str, barrier: float) -> int:
    future = candles[start + 1 : start + 1 + horizon]
    if direction == "hit_above":
        return int(any(float(row["high"]) >= barrier for row in future))
    return int(any(float(row["low"]) <= barrier for row in future))


def generate_examples(
    conn,
    *,
    assets: list[str],
    lookback: int,
    min_history: int,
) -> list[Example]:
    examples: list[Example] = []
    for asset in assets:
        candles = load_candles(conn, asset, lookback)
        closes = [float(row["close"]) for row in candles]
        max_horizon = max(HORIZONS)
        for index in range(min_history, len(candles) - max_horizon):
            history = closes[: index + 1]
            spot = closes[index]
            if spot <= 0:
                continue
            rv30 = realized_volatility(history[-31:]) if len(history) >= 31 else realized_volatility(history)
            rv90 = realized_volatility(history[-91:]) if len(history) >= 91 else realized_volatility(history)
            ewma = ewma_volatility(history[-91:]) if len(history) >= 91 else ewma_volatility(history)
            vol = max(0.05, min(2.5, 0.7 * ewma + 0.3 * rv90))
            momentum7 = _momentum(closes, index, 7)
            momentum30 = _momentum(closes, index, 30)
            for horizon in HORIZONS:
                for distance in DISTANCES:
                    for direction in ("hit_above", "hit_below"):
                        barrier = spot * (1.0 + distance) if direction == "hit_above" else spot * (1.0 - distance)
                        probability = closed_form_touch_probability(
                            BarrierInput(
                                spot=spot,
                                barrier=barrier,
                                days_to_expiry=float(horizon),
                                annual_vol=vol,
                                drift=0.0,
                                direction=direction,
                            )
                        )
                        label = _hit_future(candles, index, horizon, direction, barrier)
                        features = [
                            _safe_logit(probability),
                            1.0 if direction == "hit_below" else 0.0,
                            math.log(float(horizon)),
                            distance,
                            rv30,
                            rv90,
                            ewma,
                            momentum7,
                            momentum30,
                        ]
                        examples.append(
                            Example(
                                asset=asset,
                                ts=str(candles[index]["ts"]),
                                direction=direction,
                                horizon=horizon,
                                distance=distance,
                                spot=spot,
                                barrier=barrier,
                                gbm_probability=probability,
                                label=label,
                                features=features,
                            )
                        )
    examples.sort(key=lambda item: (item.ts, item.asset, item.horizon, item.distance, item.direction))
    return examples


def _standardize(train: list[Example], all_examples: list[Example]) -> tuple[list[float], list[float]]:
    columns = len(FEATURE_NAMES)
    means = []
    stds = []
    for col in range(columns):
        values = [item.features[col] for item in train]
        mean = sum(values) / len(values) if values else 0.0
        variance = sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1)
        std = math.sqrt(variance) or 1.0
        means.append(mean)
        stds.append(std)
    for item in all_examples:
        item.features = [(value - means[idx]) / stds[idx] for idx, value in enumerate(item.features)]
    return means, stds


def _sigmoid(value: float) -> float:
    value = max(-35.0, min(35.0, value))
    return 1.0 / (1.0 + math.exp(-value))


def train_logistic(
    train: list[Example],
    *,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> list[float]:
    weights = [0.0] * (len(FEATURE_NAMES) + 1)
    n = max(1, len(train))
    for _epoch in range(epochs):
        grads = [0.0] * len(weights)
        for item in train:
            x = [1.0] + item.features
            prediction = _sigmoid(sum(weight * value for weight, value in zip(weights, x)))
            error = prediction - item.label
            for idx, value in enumerate(x):
                grads[idx] += error * value
        for idx in range(len(weights)):
            penalty = l2 * weights[idx] if idx else 0.0
            weights[idx] -= learning_rate * ((grads[idx] / n) + penalty)
    return weights


def predict(weights: list[float], item: Example) -> float:
    return _sigmoid(sum(weight * value for weight, value in zip(weights, [1.0] + item.features)))


def _brier(rows: list[tuple[float, int]]) -> float | None:
    if not rows:
        return None
    return sum((probability - label) ** 2 for probability, label in rows) / len(rows)


def _logloss(rows: list[tuple[float, int]]) -> float | None:
    if not rows:
        return None
    total = 0.0
    for probability, label in rows:
        p = min(0.999, max(0.001, probability))
        total += -(label * math.log(p) + (1 - label) * math.log(1 - p))
    return total / len(rows)


def _bucket_report(examples: list[Example], shadow_probs: list[float]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for item, shadow in zip(examples, shadow_probs):
        bucket_id = min(9, max(0, int(item.gbm_probability * 10)))
        name = f"{bucket_id * 10}-{bucket_id * 10 + 10}%"
        row = buckets.setdefault(name, {"bucket": name, "samples": 0, "actual": 0.0, "gbm": 0.0, "shadow": 0.0})
        row["samples"] += 1
        row["actual"] += item.label
        row["gbm"] += item.gbm_probability
        row["shadow"] += shadow
    result = []
    for name in sorted(buckets, key=lambda value: int(value.split("-", 1)[0])):
        row = buckets[name]
        samples = row["samples"]
        result.append(
            {
                "bucket": name,
                "samples": samples,
                "actual_rate": row["actual"] / samples,
                "avg_gbm_probability": row["gbm"] / samples,
                "avg_shadow_probability": row["shadow"] / samples,
            }
        )
    return result


def run_training(
    conn,
    *,
    assets: list[str],
    lookback: int,
    min_history: int,
    train_ratio: float,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> dict[str, Any]:
    examples = generate_examples(conn, assets=assets, lookback=lookback, min_history=min_history)
    split = max(1, min(len(examples) - 1, int(len(examples) * train_ratio))) if len(examples) >= 2 else 0
    train = examples[:split]
    validation = examples[split:]
    if not train or not validation:
        return {"ok": False, "error": "not enough examples", "samples": len(examples)}
    means, stds = _standardize(train, examples)
    weights = train_logistic(train, epochs=epochs, learning_rate=learning_rate, l2=l2)
    shadow_probs = [predict(weights, item) for item in validation]
    base_rows = [(item.gbm_probability, item.label) for item in validation]
    shadow_rows = list(zip(shadow_probs, [item.label for item in validation]))
    metrics = {
        "base_brier": _brier(base_rows),
        "shadow_brier": _brier(shadow_rows),
        "base_logloss": _logloss(base_rows),
        "shadow_logloss": _logloss(shadow_rows),
    }
    return {
        "ok": True,
        "mode": "shadow-logistic",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assets": assets,
        "feature_names": FEATURE_NAMES,
        "samples": len(examples),
        "train_samples": len(train),
        "validation_samples": len(validation),
        "train_ratio": train_ratio,
        "horizons": HORIZONS,
        "distances": DISTANCES,
        "metrics": metrics,
        "improvement": {
            "brier_delta": (metrics["base_brier"] - metrics["shadow_brier"]) if metrics["base_brier"] is not None and metrics["shadow_brier"] is not None else None,
            "logloss_delta": (metrics["base_logloss"] - metrics["shadow_logloss"]) if metrics["base_logloss"] is not None and metrics["shadow_logloss"] is not None else None,
        },
        "weights": {"intercept": weights[0], **{name: weights[idx + 1] for idx, name in enumerate(FEATURE_NAMES)}},
        "standardization": {"means": dict(zip(FEATURE_NAMES, means)), "stds": dict(zip(FEATURE_NAMES, stds))},
        "calibration_buckets": _bucket_report(validation, shadow_probs),
        "decision": "observe_only",
        "warning": "Shadow model is for calibration research only; it is not used by production scanner.",
    }


def write_report(summary: dict[str, Any], output: str) -> str:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(path)


def main() -> int:
    args = parse_args()
    assets = [item.strip().upper() for item in args.assets.split(",") if item.strip()]
    with connect(args.db) as conn:
        summary = run_training(
            conn,
            assets=assets,
            lookback=args.lookback,
            min_history=args.min_history,
            train_ratio=args.train_ratio,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            l2=args.l2,
        )
        if args.output:
            summary["output"] = write_report(summary, args.output)
        if args.save and summary.get("ok"):
            summary["run_id"] = insert_shadow_training_run(conn, summary)
            insert_log(conn, "INFO", "shadow_training", "Shadow training completed", json.dumps(summary, ensure_ascii=False))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
