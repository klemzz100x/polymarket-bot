# Polymarket Bot Roadmap

This roadmap prioritizes validation, data quality, paper-trading realism, and observability before any live execution work.

## 1. Immediate Validation

Goal: prove the full research pipeline can run end-to-end on a small, controlled universe.

1. Start the local stack with Postgres, Redis, FastAPI, n8n, Prometheus, and Grafana.
2. Collect a small active market universe.
3. Collect orderbook snapshots for a limited set of token IDs.
4. Collect public trades and price history when available.
5. Validate the collected dataset before using it for research.
6. Compute market metrics on the same time window.
7. Scan simple inefficiency signals.
8. Run a research-only backtest using realistic fill assumptions.
9. Run paper trading in `signals`, `strategy`, and `hybrid` modes.
10. Generate Obsidian reports for data quality, metrics, inefficiencies, backtests, and paper trading.
11. Compare paper trading against the equivalent backtest on the same market and period.
12. Mine Obsidian Twitter-thread notes into Strategy Candidates when the notes contain real strategy content.
13. Review paper equity snapshots in the read-only dashboard.

Acceptance criteria:
- Every command has a documented expected output.
- Postgres remains the quantitative source of truth.
- Obsidian contains only qualitative reports and research notes.
- No live order path is introduced.

## 2. Data Quality Hardening

Goal: make data collection trustworthy enough for research and backtesting.

Priorities:
- Add retry/backoff policy to collectors.
- Add timeout handling around external API calls.
- Preserve duplicate protection through database constraints and repository behavior.
- Detect stale snapshots and missing update intervals.
- Detect ingestion anomalies such as empty books, invalid levels, negative sizes, timestamp regressions, and unusual collection latency.
- Add collector heartbeat and health reporting.
- Add Alembic migrations before schema evolution becomes frequent.
- Add data retention jobs for raw payloads and high-frequency snapshots.
- Track cache freshness in Redis.

Acceptance criteria:
- A bad collection run produces a structured log and validation report.
- Duplicate snapshots do not inflate metrics or backtests.
- Data gaps are visible before research jobs run.

## 3. Evaluation Layer

Goal: decide whether paper trading and research signals show credible early edge.

Priorities:
- Measure paper-trading performance: gross/net PnL, win rate, average win/loss, exposure, fill rate, partial fill rate, slippage, rejected trades, latency impact, signal hit rate, profit factor, and drawdown.
- Compare backtest results against paper-trading results on identical market windows.
- Detect an overly optimistic simulator.
- Detect unrealistic fills, unstable signals, illiquid markets, and abnormal behavior.
- Produce Obsidian reports for daily paper trading, strategy evaluation, fill quality, signal quality, and backtest-vs-paper comparison.
- Expose evaluation endpoints for n8n workflows.
- Mine Obsidian research notes for Strategy Candidates and link candidates to backtest and paper-trading results.
- Maintain a Strategy Candidate Registry with `new`, `tested`, `promising`, and `rejected` states.

Acceptance criteria:
- A strategy can be evaluated without reading raw notebooks manually.
- Evaluation reports clearly separate hypothesis, observation, limitation, and next action.
- Paper trading is treated as a validation mechanism, not an execution approval.

## 4. Monitoring & Observability

Goal: make the system observable while it is still research-only.

Priorities:
- Add Prometheus metrics for ingestion, research signals, backtests, and paper trading.
- Track collector success/failure, rows written, stale markets, cache freshness, paper-trading activity, rejected orders, fill quality, and signal counts.
- Add Grafana dashboard stubs for ingestion health, paper trading activity, fill quality, signal activity, stale markets, DB row growth, and cache freshness.
- Add n8n alerts for high drawdown, low fill rate, and data anomalies.
- Keep structured logs consistent across collectors, API jobs, paper trading, and evaluation jobs.
- Add a read-only self-hosted dashboard for paper equity, PnL, exposure, fills, signals, stale data, and collector health.
- Use Grafana for infrastructure monitoring and the dashboard for trading/research observability.

Acceptance criteria:
- Failures are visible without opening the database first.
- A daily run can be reviewed from logs, metrics, and Obsidian reports.

## 5. WebSocket Layer

Goal: prepare real-time market microstructure research without enabling live trading.

Priorities:
- Add a WebSocket collector for market orderbook and trade updates.
- Implement reconnect, heartbeat, auto-resubscribe, and error recovery.
- Store WebSocket-derived data in Postgres and Redis.
- Compare WebSocket update cadence against polling snapshots.
- Feed WebSocket snapshots into validation, metrics, signal scans, backtests, and paper trading.

Acceptance criteria:
- WebSocket collection can fail and recover without corrupting stored data.
- Real-time data still flows through the same validation and reporting discipline.

## 6. Future Live Trading

Live trading is intentionally out of scope for the current phase.

Add live execution only after evaluation, monitoring, and risk controls are proven.

Before any live execution work:
- Evaluation must show repeatable signal quality across markets and periods.
- Paper trading must behave close enough to backtests under realistic assumptions.
- Monitoring must catch data, fill, latency, and drawdown anomalies.
- Risk controls must block invalid exposure, stale data, excessive order rate, and abnormal market conditions.
- A post-mortem loop must exist for every incident or unexpected behavior.
