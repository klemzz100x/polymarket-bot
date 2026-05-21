---
type: "data-quality-report"
market_id: "0x75bba4219ae6645bb3bd0c86cc0dcbedc91df7f748389dd8f8af638d33db12d6"
status: "critical"
created: "2026-05-20"
tags: ["data-quality", "data-layer"]
---
# Data Quality Report - 0x75bba4219ae6645bb3bd0c86cc0dcbedc91df7f748389dd8f8af638d33db12d6

## Period
- From: `2026-05-13T12:33:58.875000+00:00`
- To: `2026-05-13T12:34:27.993000+00:00`

## Summary
- Status: `critical`
- Snapshots: `30`
- Trades: `124`
- Price ticks: `0`
- Update frequency / minute: `59.75685143210385328662682877`
- Max collection latency seconds: `-0.90838`

## Issues
- `warning` `missing_price_ticks` No price ticks found for market and period.
- `critical` `empty_orderbook` Orderbook snapshot has no bid or ask levels.
- `critical` `empty_orderbook` Orderbook snapshot has no bid or ask levels.
- `critical` `empty_orderbook` Orderbook snapshot has no bid or ask levels.
- `critical` `empty_orderbook` Orderbook snapshot has no bid or ask levels.
- `critical` `empty_orderbook` Orderbook snapshot has no bid or ask levels.
- `critical` `empty_orderbook` Orderbook snapshot has no bid or ask levels.
- `critical` `empty_orderbook` Orderbook snapshot has no bid or ask levels.
- `critical` `empty_orderbook` Orderbook snapshot has no bid or ask levels.

## Observations
- Review critical issues before trusting backtests.
- Warnings may still be acceptable for exploratory research if documented.

## Limits
- This report validates collected data only; it does not prove market truth.

## Next Actions
- Recollect missing intervals if possible.
- Compare trades, orderbooks, and price ticks when mismatches appear.

## Links
- [[Data Layer]]
- [[Orderbook]]
- [[Backtesting]]
- [[Execution Quality]]
- [[Risk Management]]
