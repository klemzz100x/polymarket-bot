# Live Execution Foundation V0

This layer prepares the future live execution stack without enabling active live trading.

Default state:

```text
LIVE_TRADING_ENABLED=false
LIVE_EXECUTION_MODE=DISABLED
```

## Components

- `src/polybot/live_execution`: live models, modes, micro-live safety, execution quality.
- `src/polybot/wallet`: wallet balance, position, open-order sync.
- `src/polybot/exchange`: Polymarket exchange adapter abstraction.
- `src/polybot/oms`: order state machine, fill tracking, reconciliation.
- `src/polybot/live_risk`: pre-trade risk gate and live constraints.

## Modes

- `DISABLED`: no wallet sync requirement and no order preparation/submission.
- `READ_ONLY`: wallet sync only.
- `SHADOW`: live-like order preparation only.
- `MICRO_LIVE`: future micro orders, still gated by readiness, kill switch, limits, and manual confirmation.

## API

```http
GET /live-execution/status
POST /live-execution/prepare-order
```

`prepare-order` never submits orders automatically. It returns a prepared order and a risk decision.

## Database

New tables:

- `app.wallet_snapshots`
- `app.live_orders`
- `app.live_execution_reports`
- `app.live_fills`
- `app.live_risk_events`
- `app.oms_reconciliation_reports`

## Rule

No live order can be submitted unless the future execution path passes mode checks, readiness, kill switch, risk gates, duplicate protection, rate limits, cooldowns, and manual confirmation.
