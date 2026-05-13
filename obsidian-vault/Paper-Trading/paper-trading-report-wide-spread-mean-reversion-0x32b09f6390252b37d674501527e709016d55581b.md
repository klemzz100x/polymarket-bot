---
type: "paper-trading-report"
run_id: "3830d31c-fda4-4d5f-ad65-c3c2686197b0"
strategy: "wide-spread-mean-reversion"
market_id: "0x32b09f6390252b37d674501527e709016d55581b2c1e544bd4b8167f5f732f4c"
created: "2026-05-13"
tags: ["paper-trading", "research", "execution-quality"]
---
# Paper Trading Report - wide-spread-mean-reversion

## Summary
- Run ID: `3830d31c-fda4-4d5f-ad65-c3c2686197b0`
- Market ID: `0x32b09f6390252b37d674501527e709016d55581b2c1e544bd4b8167f5f732f4c`
- Snapshots processed: `8`
- Signals detected: `12`
- Attempted orders: `16`
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
- `stable_exploitable_spread`: `4`
- `wide_spread`: `8`

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
