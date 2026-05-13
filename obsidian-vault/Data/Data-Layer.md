---
type: architecture
status: active
tags: [data-layer, postgres, redis, polymarket]
---
# Data Layer

## Principle
Postgres is the quantitative source of truth. Obsidian is qualitative memory.

## Sources
- Gamma API: market discovery and metadata.
- CLOB API: orderbooks, prices, spreads, price history.
- Data API: public trades and activity.
- WebSocket market channel: future real-time stream.

## Storage
- `markets`
- `market_outcomes`
- `orderbook_snapshots`
- `orderbook_levels`
- `trades`
- `price_ticks`
- `ingestion_logs`
- `raw_api_payloads`

## Links
- [[Orderbook]]
- [[Backtesting]]
- [[Research Loop]]

