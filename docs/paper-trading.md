# Paper Trading Engine

## Purpose

The Paper Trading Engine connects the Data Layer, Research Layer, and Backtesting primitives without sending live orders.

It is designed to answer:
- Which research signals would have generated virtual orders?
- Would those virtual orders fill against visible book depth?
- How much slippage, latency impact, and partial fill risk appears?
- How does a paper run compare with an equivalent backtest?

## Inputs

- Orderbook snapshots from Postgres.
- Public trades from Postgres for signal context.
- Research signals from `src/polybot/research`.
- Research-only strategies from `src/polybot/strategies/research`.

## Execution

Paper fills reuse the backtesting execution simulator:
- visible orderbook depth only
- fixed latency
- configurable fees
- partial fills
- position limits
- market exposure limits

## Decision Modes

- `strategy`: use a research-only strategy.
- `signals`: map research signals directly into conservative virtual orders.
- `hybrid`: combine both, with duplicate decisions removed.

## CLI

```bash
PYTHONPATH=src python3 scripts/run_paper_trading.py \
  --market-id <condition_id> \
  --strategy wide-spread-mean-reversion \
  --decision-mode hybrid \
  --from 2026-01-01T00:00:00Z \
  --to 2026-01-02T00:00:00Z \
  --order-size 10 \
  --fee-bps 0 \
  --latency-ms 500 \
  --persist-db \
  --obsidian
```

## API

`POST /paper-trading/run`

```json
{
  "market_id": "0x...",
  "strategy": "wide-spread-mean-reversion",
  "decision_mode": "hybrid",
  "start": "2026-01-01T00:00:00Z",
  "end": "2026-01-02T00:00:00Z",
  "limit": 5000,
  "initial_cash": "1000",
  "order_size": "10",
  "fee_bps": "0",
  "latency_ms": 500,
  "signal_window": 20,
  "persist_db": true,
  "write_obsidian": true
}
```

## Outputs

- JSON result in `tmp/paper_trading`.
- JSONL ledger in `logs/paper-trading`.
- Optional Postgres persistence.
- Optional Obsidian report in `obsidian-vault/Paper-Trading`.

## Rule

Paper trading is not live trading approval. It is an execution-quality rehearsal over collected data.

