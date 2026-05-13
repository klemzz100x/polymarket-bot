# Dashboard

The dashboard is a self-hosted, read-only Streamlit application for paper trading, shadow trading, readiness, and research operations.

## Location

```text
dashboard/app.py
dashboard/Dockerfile
dashboard/README.md
```

## Start

```bash
docker compose up -d --build dashboard
```

Open:

```text
http://localhost:8501
```

## Pages

1. Terminal Cockpit
   - one-window operating view
   - API/DB-facing health status
   - readiness score and kill switch state
   - latest snapshot freshness
   - equity, net PnL, exposure
   - paper/shadow fill status
   - latest runs, freshest markets, signal tape, runtime console
   - auto-refresh from the sidebar

2. Overview
   - current equity
   - net PnL
   - drawdown summary
   - paper trade count
   - active strategies
   - tracked markets

3. Data Coverage
   - market coverage
   - orderbook freshness
   - ingestion runs
   - latest orderbooks

4. Equity Curve
   - equity curve
   - net PnL curve
   - drawdown approximation

5. Strategy Performance
   - strategy ranking
   - PnL by strategy
   - fill rate
   - rejected orders

6. Market Performance
   - PnL by market
   - problematic markets
   - average spread

7. Signals
   - latest research signals
   - signal type
   - confidence
   - signal hit rate

8. Risk
   - exposure
   - virtual positions
   - rejected orders

9. System Health
   - API health
   - DB health
   - collector status
   - stale markets

10. Shadow Trading
   - shadow decisions
   - theoretical fills
   - missed and impossible fills
   - observed slippage
   - fill probability

11. Live Readiness
   - readiness score
   - execution quality score
   - infrastructure health score
   - strategy stability score
   - kill switch state

12. Execution Quality
   - shadow fill realism
   - spread conditions
   - liquidity depth
   - stale books
   - latency-related diagnostics

13. Wallet
   - balances
   - exposure
   - positions
   - open orders
   - sync history

14. OMS
   - open and historical orders
   - fills
   - risk gate events
   - reconciliation reports

15. Twitter Research
   - paste X/Twitter thread URLs or raw notes
   - stores raw captures in `/resources/twitter-threads`
   - creates Markdown source notes in `/obsidian-vault/Sources/Twitter-Threads`
   - creates a research index note in `/obsidian-vault/Research/Twitter-Inbox`
   - prepares notes for Obsidian Strategy Mining

## Data Sources

- Postgres: source of truth for paper runs, events, equity snapshots, shadow runs, readiness reports, wallet snapshots, OMS state, live risk events, and kill switch events.
- FastAPI: health check.
- Redis: reserved for future lower-latency widgets.
- Resources volume: raw Twitter/X captures.
- Obsidian vault volume: structured source and research notes.

## Safety

The dashboard is read-only. It must not expose:
- order placement,
- risk engine edits,
- DB mutation controls,
- live-trading toggles.

The Twitter Research page is allowed to write qualitative research files only:
- raw inbox files in `resources`,
- Markdown notes in the Obsidian vault.

It must not mutate quantitative trading tables or execution state.
