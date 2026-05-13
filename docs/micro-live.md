# Micro-Live Workflow

Micro-live is not active by default. It is a future controlled mode for very small real orders.

## Required Before Any Micro-Live

- `LIVE_TRADING_ENABLED=true`
- `LIVE_EXECUTION_MODE=MICRO_LIVE`
- readiness status `ready`
- kill switch armed
- risk gate active
- manual confirmation
- dedicated wallet with small capital
- dashboard and Telegram monitoring operational
- Obsidian reporting loop active

## Hard Limits

- max order size: `$1`
- max daily loss: `$5`
- max open positions: `2`

## Protections

- cooldown after loss
- order rate limit
- emergency stop
- duplicate order protection
- manual confirmation

## Current State

The current repository implements the foundation and read-only/simulation surfaces. It does not activate live trading automatically.
