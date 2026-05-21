---
type: "backtest-result"
strategy: "wide-spread-mean-reversion"
market_id: "0xe06a7e94cf2fa8dc2085b7610fe16e9be1cde6654f34d365c13da1149b276c61"
created: "2026-05-20"
tags: ["backtest", "research", "strategy"]
---
# Backtest Result - wide-spread-mean-reversion

## Summary
- Market ID: `0xe06a7e94cf2fa8dc2085b7610fe16e9be1cde6654f34d365c13da1149b276c61`
- Trades: `1`
- Gross PnL: `0`
- Net PnL: `0`
- Win rate: `0`
- Max drawdown: `0.004866204261162913353700405019`

## Execution Quality
- Fill rate: `0.02941176470588235294117647059`
- Partial fill rate: `0`
- Average slippage: `0`
- Fees: `0`
- Latency impact: `0`

## Risk Metrics
- Average exposure: `0.1066666666666666666666666667`
- Max exposure: `0.11`
- Profit factor: `n/a`
- Sharpe approx: `0.002181539317415301`

## Observations
- Review fills and partial fills before interpreting PnL.

## Hypotheses
- A profitable result is only a candidate for deeper validation.

## Limits
- V1 backtester uses visible book depth and simplified queue assumptions.
- This is research-only and not live-trading approval.

## Next Actions
- Run on multiple markets and periods.
- Add fee/reward assumptions explicitly.
- Compare with data quality report.

## Links
- [[Data Layer]]
- [[Backtesting]]
- [[Orderbook]]
- [[Execution Quality]]
- [[Risk Management]]
