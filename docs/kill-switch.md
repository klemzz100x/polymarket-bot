# Kill Switch Framework

The kill switch is implemented before live trading so that the risk architecture exists before any real execution is considered.

Current triggers:

- excessive drawdown
- stale data
- API failure
- DB issue
- Redis issue
- excessive slippage
- excessive rejected orders
- collector crash
- latency spike
- missing market data

## Module

`src/polybot/risk/kill_switch.py`

The evaluator returns:

- `state`: `armed` or `triggered`
- `events`: trigger, severity, reason, metadata

Critical events force the state to `triggered`.

## Storage

Kill switch events are stored in `app.kill_switch_events`.

## Alerts

Telegram templates are available in `src/polybot/monitoring/telegram_templates.py` for:

- kill switch triggered
- readiness degraded
- stale collectors
- abnormal latency
- excessive slippage
- shadow vs paper mismatch

## Future Live Rule

Future live execution must call the kill switch before any order can be sent. This repository currently has no live order-sending path.
