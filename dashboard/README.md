# Polybot Dashboard

Self-hosted read-only dashboard for paper trading, shadow trading, readiness, and research operations.

It displays:
- a dense Terminal Cockpit with the main live validation data in one page
- current equity
- net PnL
- drawdown approximation
- strategy performance
- market performance
- active and recent signals
- rejected paper orders
- exposure
- collector health
- stale market data
- shadow decisions and theoretical fills
- live readiness scores
- kill switch events
- execution quality diagnostics
- wallet balances, positions, and exposure
- OMS orders, fills, risk blocks, and reconciliation
- a Twitter Research Inbox that writes raw sources to `/resources` and Markdown notes to the Obsidian vault

It does not:
- place orders
- edit the database
- modify the risk engine
- enable live trading

## Local Docker

```bash
docker compose up -d --build dashboard
```

Default URL:

```text
http://localhost:8501
```

## Data Sources

The dashboard reads:
- Postgres: `app.paper_trading_runs`, `app.paper_trading_events`, `app.paper_equity_snapshots`
- Postgres: `app.shadow_trading_runs`, `app.shadow_trading_decisions`
- Postgres: `app.live_readiness_reports`, `app.kill_switch_events`
- Postgres: `app.wallet_snapshots`, `app.live_orders`, `app.live_fills`, `app.live_risk_events`, `app.oms_reconciliation_reports`
- Postgres data health tables: `app.ingestion_logs`, `app.orderbook_snapshots`
- FastAPI health endpoint for API status

Redis can be added later for faster real-time widgets, but Postgres remains the source of truth.

## Terminal Cockpit

Open the `Terminal Cockpit` page for a one-window operating view:

- API health, live mode, readiness, kill switch, latest snapshot freshness
- equity, net PnL, exposure, paper fills, shadow fills
- latest validation runs
- freshest markets and orderbook pressure
- equity/PnL curve
- signal tape
- runtime console
- recent shadow decisions

The page supports sidebar auto-refresh. It only reads from Postgres/FastAPI.

## Twitter Research Inbox

Open `Twitter Research`, paste X/Twitter thread URLs or raw research notes, then click `Add to research vault`.

The dashboard writes:

- raw capture: `/app/resources/twitter-threads/dashboard-inbox-*.txt`
- source notes: `/app/obsidian-vault/Sources/Twitter-Threads/*.md`
- research index note: `/app/obsidian-vault/Research/Twitter-Inbox/*.md`

The generated notes are structured for Obsidian Strategy Mining and later Strategy Candidate promotion.
