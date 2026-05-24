from __future__ import annotations

import sqlite3
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

create table if not exists barrier_markets (
  market_id text primary key,
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
"""


def connect(path: str | Path = "polymtrade.sqlite") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    ensure_schema(conn)
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("pragma table_info(barrier_markets)").fetchall()}
    additions = {
        "slug": "text",
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
    if source is None:
        row = conn.execute(
            """
            select source
            from crypto_candles
            where asset = ?
            group by source
            order by case source when 'binance' then 0 when 'coinbase' then 1 when 'demo' then 2 else 3 end,
                     count(*) desc
            limit 1
            """,
            (asset.upper(),),
        ).fetchone()
        source = row["source"] if row else None
    source_clause = "and source = ?" if source else ""
    params: list[Any] = [asset.upper()]
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


def upsert_barrier_markets(conn: sqlite3.Connection, markets: list[dict[str, Any]]) -> int:
    if not markets:
        return 0
    conn.executemany(
        """
        insert or replace into barrier_markets (
          market_id, question, asset, barrier, direction, deadline_text, slug, end_date,
          active, closed, yes_token_id, no_token_id, yes_price, no_price, volume,
          liquidity, source, raw_json
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["market_id"],
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
