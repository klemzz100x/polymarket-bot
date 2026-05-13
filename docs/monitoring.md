# Monitoring

Monitoring is focused on research infrastructure health, paper-trading realism, shadow execution quality, and pre-live readiness.

## Prometheus Endpoint

FastAPI exposes:

```bash
GET /metrics
```

## Metrics

Collectors:
- `polybot_collector_runs_total`
- `polybot_collector_rows_seen_total`
- `polybot_collector_rows_written_total`
- `polybot_collector_duration_seconds`
- `polybot_stale_snapshots_total`

Paper trading:
- `polybot_paper_trading_runs_total`
- `polybot_paper_trading_fills_total`
- `polybot_paper_trading_rejected_orders_total`
- `polybot_paper_trading_fill_rate`
- `polybot_paper_trading_net_pnl`

Research:
- `polybot_research_signals_total`

Backtesting:
- `polybot_backtests_total`
- `polybot_backtest_net_pnl`

Shadow trading:
- `polybot_shadow_trading_runs_total`
- `polybot_shadow_trading_impossible_fills_total`
- `polybot_shadow_trading_average_slippage`
- `polybot_shadow_trading_fill_probability`

Live readiness:
- `polybot_live_readiness_score`
- `polybot_live_readiness_checks_total`

## Grafana

Grafana provisioning lives in:

```text
monitoring/grafana
```

Start observability:

```bash
docker compose --profile observability up -d prometheus grafana
```

Dashboard coverage:
- ingestion health
- paper trading activity
- fill quality
- signal activity
- stale markets
- DB row growth
- cache freshness
- shadow trading activity
- shadow execution quality
- live readiness

## Alerts

n8n workflow examples:
- `evaluation_drawdown_alert.json`
- `evaluation_low_fill_rate_alert.json`
- `evaluation_data_anomaly_alert.json`
- `evaluation_daily_report.json`
- `paper_trading_daily_report.json`
- `shadow_trading_run.json`
- `live_readiness_daily_report.json`
- `kill_switch_alert.json`
