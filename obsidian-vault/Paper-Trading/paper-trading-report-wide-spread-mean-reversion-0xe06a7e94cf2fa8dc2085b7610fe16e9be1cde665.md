---
type: "paper-trading-report"
run_id: "4ddbb0cf-e432-406a-ba4f-ae8fba839134"
strategy: "wide-spread-mean-reversion"
market_id: "0xe06a7e94cf2fa8dc2085b7610fe16e9be1cde6654f34d365c13da1149b276c61"
created: "2026-05-20"
tags: ["paper-trading", "research", "execution-quality"]
---
# Paper Trading Report - wide-spread-mean-reversion

## Summary
- Run ID: `4ddbb0cf-e432-406a-ba4f-ae8fba839134`
- Market ID: `0xe06a7e94cf2fa8dc2085b7610fe16e9be1cde6654f34d365c13da1149b276c61`
- Snapshots processed: `66`
- Signals detected: `128`
- Attempted orders: `68`
- Filled orders: `2`
- Rejected orders: `0`
- Net PnL: `9.78`
- Final equity: `1009.78`

## Execution Quality
- Fill rate: `0.02941176470588235294117647059`
- Partial fill rate: `0`
- Fees: `0`
- Max exposure: `0.22`

## Signals
- `stable_exploitable_spread`: `62`
- `wide_spread`: `66`

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
