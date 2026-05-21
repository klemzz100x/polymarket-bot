---
type: "shadow-trading-report"
run_id: "a72d9ec2-2d77-4472-9edf-80be5523b20b"
market_id: "0xe06a7e94cf2fa8dc2085b7610fe16e9be1cde6654f34d365c13da1149b276c61"
strategy: "wide-spread-mean-reversion"
status: "warning"
tags: ["shadow-trading", "execution-quality", "pre-live"]
---
# Shadow Trading Daily Report - wide-spread-mean-reversion

## Executive Summary
- Status: `warning`
- Market ID: `0xe06a7e94cf2fa8dc2085b7610fe16e9be1cde6654f34d365c13da1149b276c61`
- Decisions: `66`
- Theoretical fills: `0`
- Missed fills: `66`
- Impossible fills: `0`

## Metrics
- Average slippage: `0`
- Average delay ms: `11917.60606060606060606060606`
- Fill probability: `0`
- Signals: `128`
- Snapshots: `66`

## Anomalies
- critical latency spike detected: 246613ms
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
