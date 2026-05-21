---
type: "paper-trading-report"
run_id: "860cddeb-d4e2-4a60-a7e9-7a8570f540bc"
strategy: "wide-spread-mean-reversion"
market_id: "0x1fad72fae204143ff1c3035e99e7c0f65ea8d5cd9bd1070987bd1a3316f772be"
created: "2026-05-13"
tags: ["paper-trading", "research", "execution-quality"]
---
# Paper Trading Report - wide-spread-mean-reversion

## Summary
- Run ID: `860cddeb-d4e2-4a60-a7e9-7a8570f540bc`
- Market ID: `0x1fad72fae204143ff1c3035e99e7c0f65ea8d5cd9bd1070987bd1a3316f772be`
- Snapshots processed: `4`
- Signals detected: `4`
- Attempted orders: `8`
- Filled orders: `0`
- Rejected orders: `0`
- Net PnL: `0`
- Final equity: `1E+3`

## Execution Quality
- Fill rate: `0`
- Partial fill rate: `0`
- Fees: `0`
- Max exposure: `0`

## Signals
- `wide_spread`: `4`

## Observations
- Paper trading uses collected snapshots and simulated fills only.
- No live order was sent.

## Hypotheses
- Compare this run with the equivalent backtest on the same period.
- Investigate signals that generated orders but no fills.

## Limits
- Queue priority is not modeled yet.
- Fills use visible depth and fixed latency assumptions.

## Next Actions
- Run across multiple periods.
- Compare signal-only, strategy-only, and hybrid decision modes.
- Review data quality for the same period.

## Links
- [[Data Layer]]
- [[Backtesting]]
- [[Orderbook]]
- [[Execution Quality]]
- [[Risk Management]]
