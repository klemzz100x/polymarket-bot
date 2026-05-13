---
type: "live-readiness-report"
status: "ready"
score: "100.00"
tags: ["live-readiness", "pre-live", "risk"]
---
# Live Readiness Report

## Executive Summary
- Status: `ready`
- Live readiness score: `100.00`
- Execution quality score: `100`
- Infrastructure health score: `100`
- Strategy stability score: `100`
- Kill switch state: `armed`

## Metrics
- `critical` `shadow_market_data_available` passed=`True` score=`100` ok
- `warning` `shadow_decision_flow_active` passed=`True` score=`100` ok
- `critical` `execution_shadow_slippage` passed=`True` score=`100` ok
- `critical` `execution_shadow_latency` passed=`True` score=`100` ok
- `critical` `shadow_fill_realism` passed=`True` score=`100` ok
- `critical` `paper_drawdown` passed=`True` score=`100` ok
- `critical` `paper_exposure` passed=`True` score=`100` ok
- `warning` `strategy_rejected_shadow_orders` passed=`True` score=`100` ok
- `critical` `db_healthy` passed=`True` score=`100` ok
- `warning` `redis_healthy` passed=`True` score=`100` ok
- `critical` `api_healthy` passed=`True` score=`100` ok
- `critical` `infra_collectors_healthy` passed=`True` score=`100` ok
- `warning` `infra_websocket_healthy` passed=`True` score=`100` ok
- `warning` `infra_telegram_ready` passed=`True` score=`100` ok
- `warning` `infra_dashboard_ready` passed=`True` score=`100` ok
- `warning` `infra_obsidian_ready` passed=`True` score=`100` ok
- `critical` `infra_stale_data_absent` passed=`True` score=`100` ok

## Anomalies
- Any failed critical check forces readiness to `failed`.

## Problems Detected
- Continue shadow validation; do not enable live trading yet.

## Strategies Concerned
- See shadow trading and paper trading reports for strategy-level details.

## Recommendations
- Continue shadow validation; do not enable live trading yet.

## Next Actions
- Resolve failed checks.
- Re-run shadow trading.
- Re-run readiness scoring.
- Review kill switch events.

## Links
- [[Shadow Trading]]
- [[Execution Quality]]
- [[Risk Management]]
- [[Paper Trading]]
