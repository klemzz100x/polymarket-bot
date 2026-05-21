---
type: "shadow-trading-report"
run_id: "cd04cb0d-20d7-48cc-b448-cf3ff0f2c71a"
market_id: "0x1fad72fae204143ff1c3035e99e7c0f65ea8d5cd9bd1070987bd1a3316f772be"
strategy: "wide-spread-mean-reversion"
status: "ok"
tags: ["shadow-trading", "execution-quality", "pre-live"]
---
# Shadow Trading Daily Report - wide-spread-mean-reversion

## Executive Summary
- Status: `ok`
- Market ID: `0x1fad72fae204143ff1c3035e99e7c0f65ea8d5cd9bd1070987bd1a3316f772be`
- Decisions: `4`
- Theoretical fills: `0`
- Missed fills: `4`
- Impossible fills: `0`

## Metrics
- Average slippage: `0`
- Average delay ms: `0`
- Fill probability: `0`
- Signals: `4`
- Snapshots: `4`

## Anomalies
- shadow fill impossible for at least one theoretical order

## Problems Detected
- Review missed fills, partial fills, latency spikes, stale books, and high slippage.

## Strategies Concerned
- `wide-spread-mean-reversion`

## Recommendations
- Do not promote a strategy if shadow fills diverge materially from paper assumptions.
- Tighten latency and fill models before micro-live consideration.

## Next Actions
- Compare with the equivalent paper trading run.
- Run live readiness checks.
- Review execution quality dashboard.

## Links
- [[Paper Trading]]
- [[Execution Quality]]
- [[Risk Management]]
- [[Backtesting]]
