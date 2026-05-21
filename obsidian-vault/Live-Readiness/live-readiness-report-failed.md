---
type: "live-readiness-report"
status: "failed"
score: "88.11111111111111111111111111"
tags: ["live-readiness", "pre-live", "risk"]
---
# Live Readiness Report

## Executive Summary
- Status: `failed`
- Live readiness score: `88.11111111111111111111111111`
- Execution quality score: `80`
- Infrastructure health score: `88.88888888888888888888888889`
- Strategy stability score: `100`
- Kill switch state: `triggered`

## Metrics
- `critical` `shadow_market_data_available` passed=`True` score=`100` ok
- `warning` `shadow_decision_flow_active` passed=`True` score=`100` ok
- `critical` `execution_shadow_slippage` passed=`True` score=`100` ok
- `critical` `execution_shadow_latency` passed=`False` score=`0` Shadow execution delay is too high.
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
- `critical` `infra_stale_data_absent` passed=`False` score=`0` Stale data detected.

## Anomalies
- Any failed critical check forces readiness to `failed`.

## Problems Detected
- Fix execution_shadow_latency: Shadow execution delay is too high.
- Fix infra_stale_data_absent: Stale data detected.

## Strategies Concerned
- See shadow trading and paper trading reports for strategy-level details.

## Recommendations
- Fix execution_shadow_latency: Shadow execution delay is too high.
- Fix infra_stale_data_absent: Stale data detected.

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
