# Live Readiness Layer

The Live Readiness Layer scores whether the system is mature enough for future micro-live trading. It is a validation framework, not a live trading feature.

Readiness is based on:

- data quality and stale data checks
- collector and WebSocket health
- shadow fill realism
- paper drawdown and exposure
- slippage and latency
- rejected shadow orders
- Telegram, dashboard, and Obsidian reporting availability
- kill switch state

## Scores

- `live_readiness_score`
- `execution_quality_score`
- `infrastructure_health_score`
- `strategy_stability_score`

Any failed critical check or triggered kill switch makes readiness `failed`.

## CLI

```bash
PYTHONPATH=src python3 scripts/run_live_readiness.py \
  --market-id <condition_id> \
  --persist-db \
  --obsidian
```

## API

```http
POST /live-readiness/run
GET /live-readiness/latest
```

## Outputs

- `app.live_readiness_reports`
- `app.kill_switch_events`
- `obsidian-vault/Live-Readiness`
- Dashboard page: Live Readiness

## Rule

Even when status is `ready`, the system remains paper/shadow only. The score means the infrastructure is improving, not that live trading is enabled.
