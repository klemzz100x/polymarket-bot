---
type: risk-framework
status: active
tags: [risk, execution, production]
---
# Risk Framework

## Risk budgets
- Per market.
- Per strategy.
- Per event family.
- Per day.
- Per wallet.

## Circuit breakers
- Daily loss limit reached.
- Market data stale.
- Order rejects spike.
- Heartbeat failure.
- Inventory imbalance.
- Unexpected tick size or market rule change.

## Required strategy fields
- Strategy owner.
- Universe.
- Signal source.
- Sizing logic.
- Exit logic.
- Kill-switch rules.
- Backtest link.
- Post-mortem link.

