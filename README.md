# Polymtrade Research

Offline-first research dashboard for BTC / ETH Polymarket barrier markets.

## Current Status

This is a research system, not a trading bot. It does not connect a wallet and
does not place orders.

Implemented:

- Local dashboard at `http://127.0.0.1:8765`
- Demo BTC / ETH barrier-market backtest
- BTC / ETH daily candle storage and ingestion
- BTC / ETH barrier-market metadata storage and CSV/demo ingestion
- Monte Carlo touch-probability model
- Fee and slippage adjusted YES-edge calculation
- SQLite storage for backtest runs and trades
- Existing read-only Polymarket binary-combo scanner in `polym_scanner.py`

The `superpowers` component is implemented locally as a Python package under
`polymtrade/superpowers/`. It contains the composable research capabilities for
barrier probability, cost-adjusted edge, and demo market generation.

## Run

```bash
python3 -m polymtrade.app
```

Then open:

```text
http://127.0.0.1:8765
```

Import offline demo BTC / ETH candles:

```bash
python3 -m polymtrade.research.ingest_prices --source demo --days 365
```

Try public Binance candles when the network can reach it:

```bash
python3 -m polymtrade.research.ingest_prices --source binance --days 365
```

Import demo barrier-market metadata:

```bash
python3 -m polymtrade.research.ingest_markets --demo
```

Fetch real BTC / ETH barrier-market metadata from Polymarket Gamma API:

```bash
python3 -m polymtrade.research.ingest_markets --gamma --closed both --pages 3 --limit 100
```

Fetch real BTC / ETH hit-market metadata through the Polymtrade proxy:

```bash
curl -fsSL "https://polym.trade/gapi/public-search?q=bitcoin%20hit&limit_per_type=100&search_profiles=false&search_tags=false&keep_closed_markets=1" \
  -o data/raw/polymtrade-search-bitcoin-hit.json

curl -fsSL "https://polym.trade/gapi/public-search?q=ethereum%20hit&limit_per_type=100&search_profiles=false&search_tags=false&keep_closed_markets=1" \
  -o data/raw/polymtrade-search-ethereum-hit.json

python3 -m polymtrade.research.ingest_markets \
  --json data/raw/polymtrade-search-bitcoin-hit.json \
  --json data/raw/polymtrade-search-ethereum-hit.json
```

Fetch historical market probability series through Polymtrade:

```bash
python3 -m polymtrade.research.ingest_markets \
  --json data/raw/polymtrade-search-bitcoin-hit.json \
  --json data/raw/polymtrade-search-ethereum-hit.json \
  --price-history --history-source polymtrade --history-limit 10
```

Import a real Polymarket market CSV:

```bash
python3 -m polymtrade.research.ingest_markets --csv markets.csv
```

Import a saved Gamma API JSON response:

```bash
python3 -m polymtrade.research.ingest_markets --json gamma-markets.json
```

On a machine/VPS that can reach Polymarket, collect a bundle:

```bash
./scripts/fetch_real_data_bundle.sh data/raw
```

Then import the bundle JSON files:

```bash
python3 -m polymtrade.research.ingest_markets \
  --json data/raw/gamma-search-bitcoin.json \
  --json data/raw/gamma-search-ethereum.json \
  --json data/raw/gamma-markets-open.json \
  --json data/raw/gamma-markets-closed.json
```

## Decision Philosophy

The first goal is proof or disproof:

```text
Can a BTC / ETH barrier model beat Polymarket implied probability after costs?
```

The system should only move toward paper trading after strict backtests show:

- Positive out-of-sample return after fees and slippage
- More than 100 trades
- Profit factor above 1.3
- Max drawdown below 30%
- No dependence on 1-2 lucky tail events

## Next Data Work

Priority order:

1. Historical Polymarket BTC / ETH barrier markets
2. Historical bid / ask or conservative spread estimates
3. Options IV / skew
4. Funding rate / perp basis
5. DXY, Nasdaq, VIX, yields, gold
6. Macro event calendar
7. ETF flow, stablecoin supply, on-chain data

Because the local network cannot reliably reach Polymarket APIs, live scanning
should be treated as a later VPS or proxy-hosted paper-trading step.
