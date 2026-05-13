# Execution Quality

Execution quality measures whether research and paper trading assumptions survive contact with real orderbook conditions.

Tracked metrics:

- fill realism
- impossible fills
- missed fills
- average slippage
- execution delay
- visible depth
- stale books
- spread conditions
- fill probability
- paper vs shadow mismatch

## Data Sources

- `app.orderbook_snapshots`
- `app.orderbook_levels`
- `app.shadow_trading_runs`
- `app.shadow_trading_decisions`
- `app.paper_trading_runs`

## Dashboard

Use the self-hosted dashboard:

```bash
docker compose up -d --build dashboard
```

Open:

```text
http://localhost:8501
```

Pages:

- Shadow Trading
- Live Readiness
- Execution Quality

The dashboard is read-only and cannot place orders, edit risk settings, or enable live trading.

## n8n

Relevant workflow examples:

- `n8n/workflows/shadow_trading_run.json`
- `n8n/workflows/live_readiness_daily_report.json`
- `n8n/workflows/kill_switch_alert.json`
