from __future__ import annotations

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = """
create table if not exists backtest_runs (
  id integer primary key autoincrement,
  created_at text not null,
  mode text not null,
  starting_capital real not null,
  ending_capital real not null,
  total_return real not null,
  max_drawdown real not null,
  trades integer not null,
  win_rate real not null,
  profit_factor real not null
);

create table if not exists backtest_trades (
  id integer primary key autoincrement,
  run_id integer not null,
  market_id text not null,
  asset text not null,
  question text not null,
  spot real not null,
  barrier real not null,
  days_to_expiry real not null,
  market_ask real not null,
  model_probability real not null,
  net_edge real not null,
  roi real not null,
  stake real not null,
  payout real not null,
  pnl real not null,
  outcome integer not null,
  foreign key(run_id) references backtest_runs(id)
);

create table if not exists crypto_candles (
  asset text not null,
  ts text not null,
  open real not null,
  high real not null,
  low real not null,
  close real not null,
  volume real not null,
  source text not null,
  interval text not null,
  primary key(asset, ts, source, interval)
);

create table if not exists candle_anomaly_reviews (
  asset text not null,
  source text not null,
  interval text not null,
  ts text not null,
  status text not null,
  decision text not null,
  note text,
  reviewed_at text not null,
  primary key(asset, source, interval, ts)
);

create table if not exists barrier_markets (
  market_id text primary key,
  event_id text,
  event_slug text,
  question text not null,
  asset text not null,
  barrier real not null,
  direction text not null,
  deadline_text text,
  slug text,
  end_date text,
  active integer,
  closed integer,
  yes_token_id text,
  no_token_id text,
  yes_price real,
  no_price real,
  volume real,
  liquidity real,
  source text not null,
  raw_json text
);

create table if not exists market_price_history (
  market_id text not null,
  token_id text not null,
  outcome text not null,
  ts integer not null,
  price real not null,
  source text not null,
  primary key(market_id, token_id, outcome, ts, source)
);

create table if not exists scanner_observation_runs (
  id integer primary key autoincrement,
  created_at text not null,
  generated_at text,
  assumptions_json text not null,
  contexts_json text not null,
  rows integer not null,
  candidates integer not null
);

create table if not exists scanner_observations (
  id integer primary key autoincrement,
  run_id integer not null,
  created_at text not null,
  market_id text not null,
  asset text not null,
  question text not null,
  direction text not null,
  spot real,
  barrier real,
  days_to_expiry real,
  market_yes_price real,
  model_probability real,
  net_edge real,
  roi real,
  action text not null,
  review_status text not null,
  pricing_source text,
  best_bid real,
  best_ask real,
  spread real,
  orderbook_age_seconds real,
  executable_notional real,
  complete_fill integer,
  liquidity real,
  annual_vol real,
  review_json text not null,
  raw_json text not null,
  foreign key(run_id) references scanner_observation_runs(id)
);

create table if not exists system_logs (
  id integer primary key autoincrement,
  created_at text not null,
  level text not null,
  module text not null,
  message text not null,
  detail text
);

create table if not exists automation_source_health (
  id integer primary key autoincrement,
  created_at text not null,
  run_log_id integer,
  source text not null,
  component text not null,
  status text not null,
  records integer,
  errors integer not null,
  message text,
  detail_json text,
  foreign key(run_log_id) references system_logs(id)
);

create index if not exists idx_system_logs_created_at on system_logs(created_at desc);
create index if not exists idx_system_logs_level on system_logs(level);
create index if not exists idx_system_logs_module on system_logs(module);
create index if not exists idx_automation_source_health_created_at on automation_source_health(created_at desc);
create index if not exists idx_automation_source_health_run_log_id on automation_source_health(run_log_id);
create index if not exists idx_automation_source_health_source on automation_source_health(source);
create index if not exists idx_candle_anomaly_reviews_reviewed_at on candle_anomaly_reviews(reviewed_at desc);
create index if not exists idx_scanner_observations_run_id on scanner_observations(run_id);
create index if not exists idx_scanner_observations_market_id on scanner_observations(market_id);
create index if not exists idx_scanner_observations_action on scanner_observations(action);
create index if not exists idx_scanner_observation_runs_created_at on scanner_observation_runs(created_at desc);
"""


def connect(path: str | Path = "polymtrade.sqlite") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma busy_timeout = 5000")
    conn.execute("pragma journal_mode = wal")
    conn.execute("pragma synchronous = normal")
    conn.executescript(SCHEMA)
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("pragma table_info(barrier_markets)").fetchall()}
    additions = {
        "slug": "text",
        "event_id": "text",
        "event_slug": "text",
        "end_date": "text",
        "active": "integer",
        "closed": "integer",
        "yes_token_id": "text",
        "no_token_id": "text",
        "yes_price": "real",
        "no_price": "real",
        "volume": "real",
        "liquidity": "real",
    }
    for column, column_type in additions.items():
        if column not in existing:
            conn.execute(f"alter table barrier_markets add column {column} {column_type}")
    conn.commit()


def insert_run(conn: sqlite3.Connection, run: dict[str, Any], trades: list[dict[str, Any]]) -> int:
    cur = conn.execute(
        """
        insert into backtest_runs (
          created_at, mode, starting_capital, ending_capital, total_return,
          max_drawdown, trades, win_rate, profit_factor
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run["created_at"],
            run["mode"],
            run["starting_capital"],
            run["ending_capital"],
            run["total_return"],
            run["max_drawdown"],
            run["trades"],
            run["win_rate"],
            run["profit_factor"],
        ),
    )
    run_id = int(cur.lastrowid)
    conn.executemany(
        """
        insert into backtest_trades (
          run_id, market_id, asset, question, spot, barrier, days_to_expiry,
          market_ask, model_probability, net_edge, roi, stake, payout, pnl, outcome
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                run_id,
                item["market_id"],
                item["asset"],
                item["question"],
                item["spot"],
                item["barrier"],
                item["days_to_expiry"],
                item["market_ask"],
                item["model_probability"],
                item["net_edge"],
                item["roi"],
                item["stake"],
                item["payout"],
                item["pnl"],
                item["outcome"],
            )
            for item in trades
        ],
    )
    conn.commit()
    return run_id


def latest_runs(conn: sqlite3.Connection, limit: int = 10) -> list[dict[str, Any]]:
    rows = conn.execute(
        "select * from backtest_runs order by id desc limit ?",
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def latest_trades(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select t.* from backtest_trades t
        join backtest_runs r on r.id = t.run_id
        order by t.id desc
        limit ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def upsert_candles(conn: sqlite3.Connection, candles: list[Any]) -> int:
    if not candles:
        return 0
    conn.executemany(
        """
        insert or replace into crypto_candles (
          asset, ts, open, high, low, close, volume, source, interval
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item.asset,
                item.ts,
                item.open,
                item.high,
                item.low,
                item.close,
                item.volume,
                item.source,
                item.interval,
            )
            for item in candles
        ],
    )
    conn.commit()
    return len(candles)


def candle_summary(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select
          asset,
          source,
          interval,
          count(*) as candles,
          min(ts) as first_ts,
          max(ts) as last_ts,
          (
            select close from crypto_candles c2
            where c2.asset = c.asset
              and c2.source = c.source
              and c2.interval = c.interval
            order by ts desc
            limit 1
          ) as latest_close
        from crypto_candles c
        group by asset, source, interval
        order by asset, source, interval
        """
    ).fetchall()
    return [dict(row) for row in rows]


def candles_for_asset(
    conn: sqlite3.Connection,
    asset: str,
    source: str | None = None,
    limit: int = 365,
) -> list[dict[str, Any]]:
    asset = asset.upper()
    if source is None:
        recommended = (data_quality_report(conn).get("recommendations") or {}).get(asset) or {}
        source = recommended.get("source")
        if not source:
            row = conn.execute(
                """
                select source
                from crypto_candles
                where asset = ?
                group by source
                order by case source
                           when 'binance' then 0
                           when 'binance-data-api' then 1
                           when 'okx' then 2
                           when 'coinbase' then 3
                           else 5
                         end,
                         count(*) desc
                limit 1
                """,
                (asset,),
            ).fetchone()
            source = row["source"] if row else None
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
        {source_clause}
        order by ts desc
        limit ?
        """,
        params,
    ).fetchall()
    return [dict(row) for row in reversed(rows)]


def _date_from_ts(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def data_quality_report(conn: sqlite3.Connection) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    source_rows = conn.execute(
        """
        select asset, source, interval
        from crypto_candles
        group by asset, source, interval
        order by asset, source, interval
        """
    ).fetchall()
    priority = {
        "binance-data-api": 0,
        "binance": 1,
        "okx": 2,
        "coinbase": 3,
    }
    sources: list[dict[str, Any]] = []
    for source_row in source_rows:
        asset = str(source_row["asset"])
        source = str(source_row["source"])
        interval = str(source_row["interval"])
        rows = conn.execute(
            """
            select ts, open, high, low, close, volume
            from crypto_candles
            where asset = ? and source = ? and interval = ?
            order by ts asc
            """,
            (asset, source, interval),
        ).fetchall()
        dates = [_date_from_ts(row["ts"]).date() for row in rows]
        first_date = dates[0] if dates else None
        last_date = dates[-1] if dates else None
        unique_dates = set(dates)
        expected_days = ((last_date - first_date).days + 1) if first_date and last_date and interval == "1d" else len(unique_dates)
        missing_dates = []
        if first_date and last_date and interval == "1d":
            for offset in range(expected_days):
                candidate = first_date.toordinal() + offset
                day = datetime.fromordinal(candidate).date()
                if day not in unique_dates:
                    missing_dates.append(day.isoformat())

        anomalies = []
        ohlc_errors = []
        previous_close = None
        for row in rows:
            day = _date_from_ts(row["ts"]).date().isoformat()
            open_price = float(row["open"])
            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])
            if min(open_price, high, low, close) <= 0 or high < max(open_price, close, low) or low > min(open_price, close, high):
                ohlc_errors.append({"date": day, "open": open_price, "high": high, "low": low, "close": close})
            if previous_close and previous_close > 0:
                move = (close / previous_close) - 1
                if abs(move) >= 0.25:
                    anomalies.append({"date": day, "move": move, "close": close, "previous_close": previous_close})
            previous_close = close

        stale_days = (now.date() - last_date).days if last_date else None
        coverage = (len(unique_dates) / expected_days) if expected_days else 0.0
        score = 100.0
        score -= min(45.0, len(missing_dates) * 1.5)
        score -= min(30.0, len(anomalies) * 5.0)
        score -= min(30.0, len(ohlc_errors) * 8.0)
        if stale_days is None:
            score = 0.0
        elif stale_days > 2:
            score -= min(25.0, (stale_days - 2) * 4.0)
        score = max(0.0, min(100.0, score))
        if not rows:
            status = "error"
        elif stale_days is not None and stale_days > 3:
            status = "stale"
        elif missing_dates or anomalies or ohlc_errors:
            status = "degraded"
        else:
            status = "healthy"

        sources.append(
            {
                "asset": asset,
                "source": source,
                "interval": interval,
                "candles": len(rows),
                "expected_days": expected_days,
                "coverage": coverage,
                "first_ts": rows[0]["ts"] if rows else None,
                "last_ts": rows[-1]["ts"] if rows else None,
                "latest_close": rows[-1]["close"] if rows else None,
                "missing_days": len(missing_dates),
                "missing_sample": missing_dates[:10],
                "stale_days": stale_days,
                "anomalies": len(anomalies),
                "anomaly_sample": anomalies[:5],
                "ohlc_errors": len(ohlc_errors),
                "ohlc_error_sample": ohlc_errors[:5],
                "score": score,
                "status": status,
                "priority": priority.get(source, 9),
            }
        )

    recommendations: dict[str, dict[str, Any]] = {}
    for asset in sorted({row["asset"] for row in sources} | {"BTC", "ETH"}):
        candidates = [row for row in sources if row["asset"] == asset and row["interval"] == "1d"]
        if not candidates:
            recommendations[asset] = {"asset": asset, "source": None, "status": "error", "reason": "no daily candles"}
            continue
        selected = sorted(candidates, key=lambda row: (-row["score"], row["priority"], -row["candles"]))[0]
        selected["selected"] = True
        recommendations[asset] = {
            "asset": asset,
            "source": selected["source"],
            "status": selected["status"],
            "score": selected["score"],
            "coverage": selected["coverage"],
            "candles": selected["candles"],
            "last_ts": selected["last_ts"],
            "reason": f"{selected['candles']} candles, {selected['missing_days']} missing days, {selected['anomalies']} jumps",
        }
    for row in sources:
        row.setdefault("selected", False)

    overall_status = "healthy"
    if any(item["status"] == "error" for item in recommendations.values()):
        overall_status = "error"
    elif any(item["status"] in {"stale", "degraded"} for item in recommendations.values()):
        overall_status = "degraded"
    return {
        "generated_at": now.isoformat(),
        "status": overall_status,
        "sources": sorted(sources, key=lambda row: (row["asset"], row["priority"], row["source"])),
        "recommendations": recommendations,
    }


def upsert_candle_anomaly_review(
    conn: sqlite3.Connection,
    *,
    asset: str,
    source: str,
    interval: str,
    ts: str,
    status: str,
    decision: str,
    note: str | None = None,
    reviewed_at: str | None = None,
) -> None:
    reviewed_at = reviewed_at or datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        insert into candle_anomaly_reviews (
          asset, source, interval, ts, status, decision, note, reviewed_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?)
        on conflict(asset, source, interval, ts) do update set
          status = excluded.status,
          decision = excluded.decision,
          note = excluded.note,
          reviewed_at = excluded.reviewed_at
        """,
        (asset.upper(), source, interval, ts, status, decision, note, reviewed_at),
    )
    conn.commit()


def _candle_anomaly_review_map(conn: sqlite3.Connection) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    rows = conn.execute(
        """
        select asset, source, interval, ts, status, decision, note, reviewed_at
        from candle_anomaly_reviews
        """
    ).fetchall()
    return {
        (row["asset"], row["source"], row["interval"], row["ts"]): {
            "status": row["status"],
            "decision": row["decision"],
            "note": row["note"],
            "reviewed_at": row["reviewed_at"],
        }
        for row in rows
    }


def candle_anomaly_report(conn: sqlite3.Connection, threshold: float = 0.25) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    reviews = _candle_anomaly_review_map(conn)
    source_rows = conn.execute(
        """
        select asset, source, interval
        from crypto_candles
        group by asset, source, interval
        order by asset, source, interval
        """
    ).fetchall()
    anomalies: list[dict[str, Any]] = []
    for source_row in source_rows:
        rows = conn.execute(
            """
            select ts, open, high, low, close
            from crypto_candles
            where asset = ? and source = ? and interval = ?
            order by ts asc
            """,
            (source_row["asset"], source_row["source"], source_row["interval"]),
        ).fetchall()
        previous = None
        for row in rows:
            close = float(row["close"])
            if previous and previous["close"] > 0:
                move = (close / previous["close"]) - 1.0
                if abs(move) >= threshold:
                    key = (source_row["asset"], source_row["source"], source_row["interval"], row["ts"])
                    review = reviews.get(key, {})
                    anomalies.append(
                        {
                            "asset": source_row["asset"],
                            "source": source_row["source"],
                            "interval": source_row["interval"],
                            "ts": row["ts"],
                            "previous_ts": previous["ts"],
                            "previous_close": previous["close"],
                            "close": close,
                            "move": move,
                            "open": row["open"],
                            "high": row["high"],
                            "low": row["low"],
                            "review_status": review.get("status", "unreviewed"),
                            "review_decision": review.get("decision"),
                            "review_note": review.get("note"),
                            "reviewed_at": review.get("reviewed_at"),
                        }
                    )
            previous = {"ts": row["ts"], "close": close}
    anomalies.sort(key=lambda row: (abs(float(row["move"])), row["ts"]), reverse=True)
    reviewed = sum(1 for row in anomalies if row.get("review_status") != "unreviewed")
    return {
        "generated_at": now.isoformat(),
        "threshold": threshold,
        "count": len(anomalies),
        "reviewed": reviewed,
        "unreviewed": len(anomalies) - reviewed,
        "anomalies": anomalies,
    }


def upsert_barrier_markets(conn: sqlite3.Connection, markets: list[dict[str, Any]]) -> int:
    if not markets:
        return 0
    conn.executemany(
        """
        insert or replace into barrier_markets (
          market_id, event_id, event_slug, question, asset, barrier, direction, deadline_text, slug, end_date,
          active, closed, yes_token_id, no_token_id, yes_price, no_price, volume,
          liquidity, source, raw_json
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["market_id"],
                item.get("event_id"),
                item.get("event_slug"),
                item["question"],
                item["asset"],
                item["barrier"],
                item["direction"],
                item.get("deadline_text"),
                item.get("slug"),
                item.get("end_date"),
                item.get("active"),
                item.get("closed"),
                item.get("yes_token_id"),
                item.get("no_token_id"),
                item.get("yes_price"),
                item.get("no_price"),
                item.get("volume"),
                item.get("liquidity"),
                item["source"],
                item.get("raw_json"),
            )
            for item in markets
        ],
    )
    conn.executemany(
        """
        update barrier_markets
        set event_id = coalesce(nullif(event_id, ''), ?),
            event_slug = coalesce(nullif(event_slug, ''), ?)
        where slug = ?
          and ? is not null
          and ? != ''
        """,
        [
            (
                item.get("event_id"),
                item.get("event_slug"),
                item.get("slug"),
                item.get("event_id") or item.get("event_slug"),
                item.get("slug") or "",
            )
            for item in markets
            if item.get("slug") and (item.get("event_id") or item.get("event_slug"))
        ],
    )
    conn.executemany(
        """
        update barrier_markets
        set event_id = coalesce(nullif(event_id, ''), ?),
            event_slug = coalesce(nullif(event_slug, ''), ?)
        where asset = ?
          and direction = ?
          and abs(barrier - ?) < 0.000001
          and coalesce(end_date, '') = coalesce(?, '')
          and ? is not null
          and ? != ''
        """,
        [
            (
                item.get("event_id"),
                item.get("event_slug"),
                item.get("asset"),
                item.get("direction"),
                float(item.get("barrier")),
                item.get("end_date"),
                item.get("event_id") or item.get("event_slug"),
                item.get("asset") or "",
            )
            for item in markets
            if item.get("asset")
            and item.get("direction")
            and item.get("barrier") is not None
            and (item.get("event_id") or item.get("event_slug"))
        ],
    )
    conn.commit()
    return len(markets)


def barrier_market_summary(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select
          asset,
          direction,
          source,
          count(*) as markets,
          sum(case when closed = 1 then 1 else 0 end) as closed_markets,
          sum(case when active = 1 then 1 else 0 end) as active_markets
        from barrier_markets
        group by asset, direction, source
        order by asset, direction, source
        """
    ).fetchall()
    return [dict(row) for row in rows]


def latest_barrier_markets(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select *
        from barrier_markets
        order by case when end_date is null then 1 else 0 end, end_date desc, market_id desc
        limit ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def upsert_market_price_history(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    conn.executemany(
        """
        insert or replace into market_price_history (
          market_id, token_id, outcome, ts, price, source
        ) values (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["market_id"],
                item["token_id"],
                item["outcome"],
                item["ts"],
                item["price"],
                item["source"],
            )
            for item in rows
        ],
    )
    conn.commit()
    return len(rows)


def market_price_history_summary(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select outcome, source, count(*) as prices, min(ts) as first_ts, max(ts) as last_ts
        from market_price_history
        group by outcome, source
        order by outcome, source
        """
    ).fetchall()
    return [dict(row) for row in rows]


def insert_scanner_observation_run(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    rows = payload.get("opportunities") or []
    summary = payload.get("summary") or {}
    cur = conn.execute(
        """
        insert into scanner_observation_runs (
          created_at, generated_at, assumptions_json, contexts_json, rows, candidates
        ) values (?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            payload.get("generated_at"),
            json.dumps(payload.get("assumptions") or {}, ensure_ascii=False),
            json.dumps(payload.get("contexts") or {}, ensure_ascii=False),
            len(rows),
            int(summary.get("candidates") or sum(1 for row in rows if row.get("action") == "candidate")),
        ),
    )
    run_id = int(cur.lastrowid)
    conn.executemany(
        """
        insert into scanner_observations (
          run_id, created_at, market_id, asset, question, direction, spot, barrier,
          days_to_expiry, market_yes_price, model_probability, net_edge, roi, action,
          review_status, pricing_source, best_bid, best_ask, spread, orderbook_age_seconds,
          executable_notional, complete_fill, liquidity, annual_vol, review_json, raw_json
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                run_id,
                created_at,
                str(row.get("market_id") or ""),
                str(row.get("asset") or ""),
                str(row.get("question") or ""),
                str(row.get("direction") or ""),
                row.get("spot"),
                row.get("barrier"),
                row.get("days_to_expiry"),
                row.get("market_yes_price"),
                row.get("model_probability"),
                row.get("net_edge"),
                row.get("roi"),
                str(row.get("action") or "watch"),
                str(row.get("review_status") or "unreviewed"),
                row.get("pricing_source"),
                row.get("best_bid"),
                row.get("best_ask"),
                row.get("spread"),
                row.get("orderbook_age_seconds"),
                row.get("executable_notional"),
                None if row.get("complete_fill") is None else 1 if row.get("complete_fill") else 0,
                row.get("liquidity"),
                row.get("annual_vol"),
                json.dumps(
                    {
                        "checks": row.get("review_checks") or [],
                        "blockers": row.get("review_blockers") or [],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(row, ensure_ascii=False),
            )
            for row in rows
        ],
    )
    conn.commit()
    return run_id


def scanner_observation_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    run_row = conn.execute(
        """
        select count(*) as runs, coalesce(sum(rows), 0) as rows, coalesce(sum(candidates), 0) as candidates,
               max(created_at) as latest_at
        from scanner_observation_runs
        """
    ).fetchone()
    action_rows = conn.execute(
        """
        select action, count(*) as observations
        from scanner_observations
        group by action
        order by observations desc
        """
    ).fetchall()
    return {
        "runs": int(run_row["runs"] or 0),
        "rows": int(run_row["rows"] or 0),
        "candidates": int(run_row["candidates"] or 0),
        "latest_at": run_row["latest_at"],
        "actions": [dict(row) for row in action_rows],
    }


def latest_scanner_observation_runs(conn: sqlite3.Connection, limit: int = 10) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select *
        from scanner_observation_runs
        order by id desc
        limit ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def latest_scanner_observations(conn: sqlite3.Connection, limit: int = 25) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select *
        from scanner_observations
        order by id desc
        limit ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def insert_log(conn: sqlite3.Connection, level: str, module: str, message: str, detail: str | None = None) -> int:
    cur = conn.execute(
        "insert into system_logs (created_at, level, module, message, detail) values (?, ?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), level, module, message, detail),
    )
    conn.commit()
    return int(cur.lastrowid)


def insert_automation_source_health(
    conn: sqlite3.Connection,
    run_log_id: int | None,
    rows: list[dict[str, Any]],
) -> int:
    if not rows:
        return 0
    created_at = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        """
        insert into automation_source_health (
          created_at, run_log_id, source, component, status, records, errors, message, detail_json
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                created_at,
                run_log_id,
                str(row.get("source") or "unknown"),
                str(row.get("component") or "unknown"),
                str(row.get("status") or "unknown"),
                row.get("records"),
                int(row.get("errors") or 0),
                row.get("message"),
                json.dumps(row.get("detail") or {}, ensure_ascii=False),
            )
            for row in rows
        ],
    )
    conn.commit()
    return len(rows)


def automation_source_health_summary(conn: sqlite3.Connection, recent_runs: int = 10) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        with recent_run_ids as (
          select run_log_id, max(id) as max_id
          from automation_source_health
          where run_log_id is not null
          group by run_log_id
          order by max_id desc
          limit ?
        )
        select h.*
        from automation_source_health h
        join recent_run_ids r on r.run_log_id = h.run_log_id
        order by h.source, h.component, h.id desc
        """,
        (recent_runs,),
    ).fetchall()
    if not rows:
        rows = conn.execute(
            """
            select *
            from automation_source_health
            order by source, component, id desc
            limit 100
            """
        ).fetchall()

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        item = dict(row)
        key = (str(item["source"]), str(item["component"]))
        bucket = grouped.setdefault(
            key,
            {
                "source": item["source"],
                "component": item["component"],
                "checks": 0,
                "healthy": 0,
                "degraded": 0,
                "error": 0,
                "network_unavailable": 0,
                "skipped": 0,
                "records": 0,
                "errors": 0,
                "latest_status": item["status"],
                "latest_message": item.get("message"),
                "latest_at": item["created_at"],
            },
        )
        status = str(item.get("status") or "unknown")
        bucket["checks"] += 1
        if status in {"healthy", "degraded", "error", "skipped"}:
            bucket[status] += 1
        elif status == "network_unavailable":
            bucket["network_unavailable"] += 1
            bucket["error"] += 1
        bucket["records"] += int(item.get("records") or 0)
        bucket["errors"] += int(item.get("errors") or 0)

    summary = []
    for item in grouped.values():
        meaningful = item["checks"] - item["skipped"]
        okish = item["healthy"] + item["degraded"]
        item["success_rate"] = (okish / meaningful) if meaningful else None
        summary.append(item)
    return sorted(summary, key=lambda item: (item["source"], item["component"]))


def latest_logs(conn: sqlite3.Connection, limit: int = 100, level: str | None = None, module: str | None = None) -> list[dict[str, Any]]:
    clauses = []
    params: list[Any] = []
    if level:
        clauses.append("level = ?")
        params.append(level)
    if module:
        clauses.append("module = ?")
        params.append(module)
    where = "where " + " and ".join(clauses) if clauses else ""
    rows = conn.execute(
        f"select * from system_logs {where} order by id desc limit ?",
        params + [limit],
    ).fetchall()
    return [dict(row) for row in rows]


def automation_health(conn: sqlite3.Connection, max_age_minutes: int = 150) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    latest = conn.execute(
        """
        select *
        from system_logs
        where module = 'automation'
        order by id desc
        limit 1
        """
    ).fetchone()
    latest_success = conn.execute(
        """
        select *
        from system_logs
        where module = 'automation' and level = 'INFO'
        order by id desc
        limit 1
        """
    ).fetchone()
    latest_error = conn.execute(
        """
        select *
        from system_logs
        where module = 'automation' and level = 'ERROR'
        order by id desc
        limit 1
        """
    ).fetchone()
    latest_run = conn.execute(
        """
        select *
        from scanner_observation_runs
        order by id desc
        limit 1
        """
    ).fetchone()
    counts = conn.execute(
        """
        select
          (select count(*) from scanner_observation_runs) as observation_runs,
          (select count(*) from scanner_observations) as observations,
          (select count(*) from scanner_observations where action = 'candidate') as candidates
        """
    ).fetchone()
    latest_source_rows: list[dict[str, Any]] = []
    if latest:
        source_rows = conn.execute(
            """
            select *
            from automation_source_health
            where run_log_id = ?
            order by source, component
            """,
            (latest["id"],),
        ).fetchall()
        latest_source_rows = [dict(row) for row in source_rows]
    if not latest_source_rows:
        source_rows = conn.execute(
            """
            select *
            from automation_source_health
            order by id desc
            limit 20
            """
        ).fetchall()
        latest_source_rows = [dict(row) for row in reversed(source_rows)]

    def parsed(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if not row:
            return None
        item = dict(row)
        try:
            item["detail_json"] = json.loads(item.get("detail") or "{}")
        except json.JSONDecodeError:
            item["detail_json"] = None
        return item

    latest_item = parsed(latest)
    success_item = parsed(latest_success)
    error_item = parsed(latest_error)
    age_minutes = None
    status = "unknown"
    if latest_item:
        try:
            created = datetime.fromisoformat(str(latest_item["created_at"]).replace("Z", "+00:00"))
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_minutes = (now - created.astimezone(timezone.utc)).total_seconds() / 60.0
        except ValueError:
            age_minutes = None
        if latest_item["level"] == "ERROR":
            status = "error"
        elif age_minutes is not None and age_minutes <= max_age_minutes:
            status = "healthy"
        else:
            status = "stale"

    return {
        "generated_at": now.isoformat(),
        "status": status,
        "max_age_minutes": max_age_minutes,
        "latest": latest_item,
        "latest_success": success_item,
        "latest_error": error_item,
        "age_minutes": age_minutes,
        "latest_observation_run": dict(latest_run) if latest_run else None,
        "counts": dict(counts) if counts else {"observation_runs": 0, "observations": 0, "candidates": 0},
        "sources": latest_source_rows,
        "source_summary": automation_source_health_summary(conn, recent_runs=10),
        "candles": candle_summary(conn),
        "markets": barrier_market_summary(conn),
    }


def clear_logs(conn: sqlite3.Connection, keep: int = 1000) -> int:
    if keep <= 0:
        cur = conn.execute("delete from system_logs")
        conn.commit()
        return int(cur.rowcount if cur.rowcount is not None else 0)
    conn.execute(
        "delete from system_logs where id <= (select id from system_logs order by id desc limit 1 offset ?)",
        (keep,),
    )
    conn.commit()
    return conn.total_changes
