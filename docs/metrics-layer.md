# Metrics Layer

## Purpose

The metrics layer turns stored orderbook, trade, and price data into quantitative research features.

## Metrics

- Best bid.
- Best ask.
- Mid price.
- Absolute spread.
- Percentage spread.
- Bid depth.
- Ask depth.
- Total depth.
- Orderbook imbalance.
- Traded volume.
- Realized volatility.
- Price change.
- Update frequency.
- Liquidity score.
- Market activity score.
- Estimated slippage for multiple order sizes.

## CLI

```bash
PYTHONPATH=src python3 scripts/compute_market_metrics.py \
  --market-id <condition_id> \
  --from 2026-01-01T00:00:00Z \
  --to 2026-01-02T00:00:00Z \
  --json-out tmp/market_metrics.json \
  --csv-out tmp/orderbook_metrics.csv \
  --obsidian
```

## Design

Metrics are pure Python functions over typed schemas. They are testable without a database.

