---
type: "market-metrics-report"
market_id: "0xe06a7e94cf2fa8dc2085b7610fe16e9be1cde6654f34d365c13da1149b276c61"
created: "2026-05-20"
tags: ["metrics", "research", "data-layer"]
---
# Market Metrics Report - 0xe06a7e94cf2fa8dc2085b7610fe16e9be1cde6654f34d365c13da1149b276c61

## Summary
- Snapshots: `66`
- Trades: `0`
- Price ticks: `0`

## Main Metrics
- Average spread abs: `0.998`
- Average spread pct: `1.996`
- Average bid depth: `9340095.021666666666666666667`
- Average ask depth: `9340095.021666666666666666667`
- Average imbalance: `0`
- Traded volume: `0`
- Realized volatility: `n/a`
- Price change: `n/a`
- Update frequency / minute: `9.929197186218274305529035264`
- Liquidity score: `891230.4409987277353689567433`
- Market activity score: `953.9792175764133485118219113`

## Observations
- Compare spread and depth stability before designing any strategy.

## Hypotheses
- Wide persistent spread may be a candidate for passive backtesting.
- Extreme imbalance may be a candidate for momentum tests.

## Limits
- Metrics are only as reliable as the underlying collection cadence.

## Next Actions
- Run an inefficiency scan.
- Validate data quality before trusting results.

## Links
- [[Data Layer]]
- [[Orderbook]]
- [[Backtesting]]
- [[Risk Management]]
