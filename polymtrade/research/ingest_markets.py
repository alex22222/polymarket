from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from polymtrade.data.polymarket_api import (
    fetch_gamma_markets,
    price_history_records,
    records_from_gamma_payload,
    search_gamma_barrier_markets,
)
from polymtrade.data.polymarket_markets import parse_barrier_question
from polymtrade.storage.db import (
    barrier_market_summary,
    connect,
    market_price_history_summary,
    upsert_barrier_markets,
    upsert_market_price_history,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import BTC/ETH barrier market metadata")
    parser.add_argument("--csv", dest="csv_path", help="CSV with at least market_id/id and question/title columns")
    parser.add_argument(
        "--json",
        dest="json_paths",
        action="append",
        help="Gamma market JSON file or API response JSON; can be repeated",
    )
    parser.add_argument("--gamma", action="store_true", help="Fetch real markets from Polymarket Gamma API")
    parser.add_argument("--gamma-search", action="store_true", help="Fetch real markets from Gamma public-search")
    parser.add_argument("--pages", type=int, default=3)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--closed", choices=("both", "open", "closed"), default="both")
    parser.add_argument("--price-history", action="store_true", help="Fetch CLOB price history for parsed markets")
    parser.add_argument("--history-source", choices=("clob", "polymtrade"), default="clob")
    parser.add_argument("--history-fidelity", type=int, default=720)
    parser.add_argument("--history-limit", type=int, default=20, help="Max markets to fetch price history for")
    parser.add_argument("--db", default="polymtrade.sqlite")
    return parser.parse_args()


def record_from_row(row: dict[str, str], source: str) -> dict | None:
    question = row.get("question") or row.get("title") or row.get("name") or ""
    parsed = parse_barrier_question(question)
    if not parsed:
        return None
    market_id = row.get("market_id") or row.get("id") or row.get("condition_id") or question
    return {
        "market_id": market_id,
        "question": question,
        "asset": parsed.asset,
        "barrier": parsed.barrier,
        "direction": parsed.direction,
        "deadline_text": parsed.deadline_text,
        "source": source,
        "raw_json": json.dumps(row, ensure_ascii=False),
    }


def csv_records(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            record = record_from_row(row, source=path.name)
            if record:
                records.append(record)
    return records


def json_records(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = records_from_gamma_payload(payload, source=path.name)
    if records:
        return records
    if not isinstance(payload, list):
        return []
    fallback: list[dict] = []
    for item in payload:
        if isinstance(item, dict):
            record = record_from_row({key: str(value) for key, value in item.items()}, source=path.name)
            if record:
                record["raw_json"] = json.dumps(item, ensure_ascii=False)
                fallback.append(record)
    return fallback


def main() -> int:
    args = parse_args()
    records: list[dict] = []
    if args.csv_path:
        records.extend(csv_records(Path(args.csv_path)))
    for json_path in args.json_paths or []:
        records.extend(json_records(Path(json_path)))
    if args.gamma:
        try:
            if args.closed == "both":
                records.extend(fetch_gamma_markets(limit=args.limit, pages=args.pages, closed=False, active=True))
                records.extend(fetch_gamma_markets(limit=args.limit, pages=args.pages, closed=True, active=None))
            elif args.closed == "open":
                records.extend(fetch_gamma_markets(limit=args.limit, pages=args.pages, closed=False, active=True))
            else:
                records.extend(fetch_gamma_markets(limit=args.limit, pages=args.pages, closed=True, active=None))
        except Exception as exc:  # noqa: BLE001 - make network failures actionable, not noisy
            print(f"gamma fetch failed: {exc}")
    if args.gamma_search:
        try:
            records.extend(search_gamma_barrier_markets())
        except Exception as exc:  # noqa: BLE001 - make network failures actionable, not noisy
            print(f"gamma search failed: {exc}")
    if not records:
        print("no barrier markets parsed")
        return 1

    with connect(args.db) as conn:
        inserted = upsert_barrier_markets(conn, records)
        print(f"inserted={inserted}")
        if args.price_history:
            history_rows = []
            for record in records[: args.history_limit]:
                try:
                    history_rows.extend(
                        price_history_records(
                            record,
                            fidelity=args.history_fidelity,
                            history_source=args.history_source,
                        )
                    )
                except Exception as exc:  # noqa: BLE001 - keep ingest moving across flaky markets
                    print(f"history error {record['market_id']}: {exc}")
            inserted_history = upsert_market_price_history(conn, history_rows)
            print(f"price_history_inserted={inserted_history}")
        for row in barrier_market_summary(conn):
            print(f"{row['asset']} {row['direction']} {row['source']} markets={row['markets']}")
        for row in market_price_history_summary(conn):
            print(f"{row['outcome']} {row['source']} prices={row['prices']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
