---
type: "shadow-trading-report"
run_id: "d185ef44-ad95-4e81-bcd3-e1be581aab64"
market_id: "0x32b09f6390252b37d674501527e709016d55581b2c1e544bd4b8167f5f732f4c"
strategy: "wide-spread-mean-reversion"
status: "ok"
tags: ["shadow-trading", "execution-quality", "pre-live"]
---
# Shadow Trading Daily Report - wide-spread-mean-reversion

## Executive Summary
- Status: `ok`
- Market ID: `0x32b09f6390252b37d674501527e709016d55581b2c1e544bd4b8167f5f732f4c`
- Decisions: `8`
- Theoretical fills: `0`
- Missed fills: `8`
- Impossible fills: `0`

## Metrics
- Average slippage: `0`
- Average delay ms: `0`
- Fill probability: `0`
- Signals: `12`
- Snapshots: `8`

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
