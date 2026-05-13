# Data Layer

## Goal

The first production-grade layer is read-only. It collects, normalizes, stores, and analyzes Polymarket data without placing orders.

## Source Roles

- Gamma API: market discovery and market metadata.
- CLOB API: orderbooks, price history, pricing endpoints, and future websocket streams.
- Data API: public trades and activity data.
- Postgres: quantitative source of truth.
- Redis: hot state, active market cache, latest known orderbook, future pub/sub and queues.
- Obsidian: qualitative memory and research reports.

## Tables

Core normalized tables:
- `app.markets`
- `app.market_outcomes`
- `app.orderbook_snapshots`
- `app.orderbook_levels`
- `app.trades`
- `app.price_ticks`
- `app.ingestion_logs`

Raw retention table:
- `app.raw_api_payloads`

Raw payloads are kept as JSONB for audit/debugging. Normalized fields are extracted into typed columns for research and backtesting.

## Collectors

```bash
PYTHONPATH=src python3 scripts/collect_markets.py --limit 100 --orderbook-only
PYTHONPATH=src python3 scripts/collect_orderbooks.py --market-id <market_or_condition_id> --interval 5 --iterations 12
PYTHONPATH=src python3 scripts/collect_orderbooks.py --active-limit 20 --interval 5 --iterations 12
PYTHONPATH=src python3 scripts/collect_trades.py --market-id <condition_id> --limit 500
PYTHONPATH=src python3 scripts/replay_market.py --asset-id <token_id> --limit 100
```

Use `--dry-run` to fetch and normalize without writing to Postgres.

## Data Quality Rules

- Store raw payloads before relying on normalized fields.
- Normalize all timestamps to UTC.
- Keep outcome token IDs distinct from market IDs and condition IDs.
- Treat public trade data as market activity, not as your personal fills.
- Use ingestion logs to track collector success, failure, and row counts.

## Research Metrics

Initial metrics live in `src/polybot/research/metrics.py`:
- best bid
- best ask
- spread
- mid price
- bid depth
- ask depth
- total depth
- update frequency

## Backtesting Preparation

`scripts/replay_market.py` reads stored orderbook snapshots and replays them in timestamp order. This is the base for strategy replay and simulated fills.

