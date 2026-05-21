---
type: "market-metrics-report"
market_id: "0x1fad72fae204143ff1c3035e99e7c0f65ea8d5cd9bd1070987bd1a3316f772be"
created: "2026-05-13"
tags: ["metrics", "research", "data-layer"]
---
# Market Metrics Report - 0x1fad72fae204143ff1c3035e99e7c0f65ea8d5cd9bd1070987bd1a3316f772be

## Summary
- Snapshots: `4`
- Trades: `0`
- Price ticks: `0`

## Main Metrics
- Average spread abs: `0.98`
- Average spread pct: `1.96`
- Average bid depth: `70293.7475`
- Average ask depth: `70293.7475`
- Average imbalance: `0`
- Traded volume: `0`
- Realized volatility: `n/a`
- Price change: `n/a`
- Update frequency / minute: `14.05261925208837536107424467`
- Liquidity score: `6824.635679611650485436893202`
- Market activity score: `96.66397246465626200645933338`

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
