# n8n Research Workflows

n8n orchestrates research and reporting jobs. It does not execute live trades.

## Existing Workflow Families

- Resource ingestion to Obsidian.
- Market alerts to Obsidian.
- Data validation.
- Metrics computation.
- Inefficiency scans.
- Paper-trading runs.
- Evaluation and alerting.
- Shadow trading and live readiness reports.

## Evaluation Workflows

Files:
- `n8n/workflows/evaluation_drawdown_alert.json`
- `n8n/workflows/evaluation_low_fill_rate_alert.json`
- `n8n/workflows/evaluation_data_anomaly_alert.json`
- `n8n/workflows/evaluation_daily_report.json`
- `n8n/workflows/paper_trading_daily_report.json`
- `n8n/workflows/shadow_trading_run.json`
- `n8n/workflows/live_readiness_daily_report.json`
- `n8n/workflows/kill_switch_alert.json`

Required environment variables:

```text
POLYBOT_API_URL=http://api:8000
POLYBOT_AUTOMATION_SECRET=<secret>
POLYBOT_DAILY_MARKET_ID=<condition_id>
POLYBOT_DAILY_STRATEGY=wide-spread-mean-reversion
POLYBOT_DAILY_LIMIT=5000
POLYBOT_DRAWDOWN_ALERT_THRESHOLD=0.2
POLYBOT_FILL_RATE_ALERT_THRESHOLD=0.3
```

## API Endpoints Used

```bash
POST /research/validate-data
POST /evaluation/run
POST /evaluation/daily-report
POST /evaluation/backtest-vs-paper
POST /evaluation/fill-quality
POST /shadow-trading/run
POST /live-readiness/run
```

## Alert Logic

- Drawdown alert: paper max drawdown exceeds threshold.
- Low fill rate alert: fill rate falls below threshold.
- Data anomaly alert: data quality status is not `ok`.
- Live readiness alert: readiness is degraded or failed.
- Kill switch alert: any critical pre-live trigger is recorded and notified.

## Rule

n8n can trigger validation, reporting, and research jobs. It must not bypass the risk engine or create live execution paths.
