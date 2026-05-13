# Shadow Trading Layer

The Shadow Trading Layer is the pre-live execution realism layer. It takes live-like research signals, creates theoretical orders, and checks whether those orders would have been executable against observed orderbooks.

It never sends real orders.

## Modules

- `src/polybot/shadow_trading/engine.py`: orchestrates signal scanning, theoretical decisions, risk validation, and fill simulation.
- `src/polybot/shadow_trading/order_simulator.py`: checks visible depth, partial fills, slippage, and latency.
- `src/polybot/shadow_trading/market_reality.py`: converts stored orderbooks into execution condition snapshots.
- `src/polybot/shadow_trading/execution_analysis.py`: compares theoretical intent with observed market reality.
- `src/polybot/shadow_trading/paper_vs_shadow.py`: detects mismatches between paper trading assumptions and shadow fills.
- `src/polybot/shadow_trading/storage.py`: persists runs and decisions in Postgres.
- `src/polybot/shadow_trading/reporting.py`: renders Obsidian reports.

## CLI

```bash
PYTHONPATH=src python3 scripts/run_shadow_trading.py \
  --market-id <condition_id> \
  --strategy wide-spread-mean-reversion \
  --persist-db \
  --obsidian
```

## API

```http
POST /shadow-trading/run
GET /shadow-trading/latest
```

Use the `x-automation-secret` header for n8n or local automation.

## Outputs

- `app.shadow_trading_runs`
- `app.shadow_trading_decisions`
- `obsidian-vault/Shadow-Trading`
- Dashboard pages: Shadow Trading, Execution Quality

## Safety

Shadow orders are theoretical only. The layer uses the paper risk manager before simulating fills, but there is no live execution adapter and no private key usage.
