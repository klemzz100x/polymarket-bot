# Live Risk

The live risk gate blocks orders when any required safety condition fails.

## Checks

- max order size
- max daily loss
- max exposure
- max strategy exposure
- max open positions
- stale data
- latency
- readiness
- kill switch
- manual confirmation
- duplicate order protection
- order rate limit
- cooldown after loss
- emergency stop

If a check fails, the result is:

```text
ORDER_BLOCKED
```

## Defaults

```text
MAX_ORDER_SIZE_USD=1
MAX_DAILY_LOSS_USD=5
MAX_OPEN_POSITIONS=2
KILL_SWITCH_ENABLED=true
REQUIRE_MANUAL_CONFIRMATION=true
```

## Storage

Risk decisions can be stored in `app.live_risk_events`.

## Rule

Future live execution must call the risk gate before any exchange submission.
