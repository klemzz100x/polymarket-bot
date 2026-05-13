# Backtesting Engine V1

## Purpose

The V1 backtester is research-only. It is designed to reject impossible fills and approximate execution quality with visible orderbook depth.

## Execution Assumptions

- Orders can only fill against visible book levels.
- Limit buys fill against asks at or below the limit.
- Limit sells fill against bids at or above the limit.
- Market orders consume visible depth.
- Partial fills are supported.
- Fees are configurable in basis points.
- Latency is simulated by moving execution to a future snapshot.
- Position limits and market exposure limits are enforced.

## Modules

- `engine.py`: replay loop and result aggregation.
- `execution_simulator.py`: fill simulation.
- `portfolio.py`: positions, cash, exposure, equity.
- `fee_model.py`: configurable fee model.
- `slippage_model.py`: depth-aware fill and slippage.
- `latency_model.py`: fixed latency model.
- `results.py`: typed result models.

## CLI

```bash
PYTHONPATH=src python3 scripts/run_backtest.py \
  --strategy wide-spread-mean-reversion \
  --market-id <condition_id> \
  --from 2026-01-01T00:00:00Z \
  --to 2026-01-02T00:00:00Z \
  --order-size 10 \
  --fee-bps 0 \
  --latency-ms 500 \
  --obsidian
```

## Research Strategies

- `wide-spread-mean-reversion`
- `orderbook-imbalance-momentum`
- `liquidity-vacuum-fade`

These strategies exist only to test the infrastructure.

