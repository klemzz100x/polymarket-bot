# Equity Monitoring

The equity feed provides a clean read-only source for dashboard and API monitoring.

## Table

```text
app.paper_equity_snapshots
```

For a fresh Docker volume this table is created by `docker/postgres/init/03-paper-trading.sql`.
If you already have an existing Postgres volume, apply the `paper_equity_snapshots` DDL from that file manually or recreate the local development volume.

Columns:
- run_id
- market_id
- strategy_name
- snapshot_ts
- equity
- cash
- net_pnl
- exposure
- positions
- source

## Writer

```text
src/polybot/paper_trading/equity.py
src/polybot/paper_trading/equity_storage.py
```

When a paper-trading result is persisted, equity snapshots are written alongside the run and events.

## API

Read-only endpoints:

```bash
GET /paper-trading/equity
GET /paper-trading/performance/live
```

Examples:

```bash
curl -H "x-automation-secret: $POLYBOT_AUTOMATION_SECRET" \
  "http://localhost:8000/paper-trading/equity?strategy=wide-spread-mean-reversion&limit=500"
```

```bash
curl -H "x-automation-secret: $POLYBOT_AUTOMATION_SECRET" \
  "http://localhost:8000/paper-trading/performance/live"
```

## Dashboard

The Streamlit dashboard reads `app.paper_equity_snapshots` directly from Postgres.

## Rule

Equity monitoring is observational only. It does not approve or trigger live execution.
