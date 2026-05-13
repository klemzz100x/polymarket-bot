# Paper Trading Validation

Paper trading is a research validation layer, not a live execution layer.

## What It Validates

- Data Layer connectivity.
- Research signal stability.
- Strategy order generation.
- Risk constraints.
- Execution simulation behavior.
- Fill quality.
- Reporting and observability.

## Required Checks

Before trusting a paper run:
- Validate data for the same market and period.
- Confirm snapshots are not stale.
- Confirm orderbooks have non-empty bid and ask levels.
- Compare order size against visible depth.
- Review rejected orders.
- Review partial fills.
- Review slippage and latency impact.
- Compare against an equivalent backtest.

## Command

```bash
PYTHONPATH=src python3 scripts/run_paper_trading.py \
  --market-id <condition_id> \
  --decision-mode hybrid \
  --obsidian
```

## API

```bash
POST /paper-trading/run
POST /evaluation/daily-report
POST /evaluation/fill-quality
```

## Failure Modes

- High paper PnL with poor fill quality.
- Good backtest but weak paper result.
- High signal count but low signal hit rate.
- Low fill rate due to thin markets.
- High partial fill rate from order sizes exceeding visible depth.
- Rejected orders caused by risk limits or repeated signals.

## Rule

Paper trading must remain read-only and simulated. No live order path belongs in this layer.
