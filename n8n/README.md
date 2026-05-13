# n8n Workflows

These workflows are examples for the automation plane.

Recommended pattern:
1. n8n receives a webhook or scheduled trigger.
2. n8n normalizes the payload.
3. n8n calls the FastAPI automation API.
4. FastAPI writes clean Markdown into `obsidian-vault`.
5. Pre-live workflows remain shadow-only and never place real orders.

Security:
- Use the `x-automation-secret` header.
- Keep n8n credentials in n8n or environment variables.
- Do not give n8n wallet private keys.
- Prefer production webhook URLs only after testing the workflow.

Environment variables expected by the workflow examples:
- `POLYBOT_API_URL`, for example `http://api:8000`.
- `POLYBOT_AUTOMATION_SECRET`.
- `POLYBOT_DAILY_MARKET_ID`, for scheduled shadow/readiness reports.
- `POLYBOT_DAILY_STRATEGY`, optional strategy label.
- `POLYBOT_DAILY_LIMIT`, optional snapshot limit.

Pre-live workflow examples:
- `shadow_trading_run.json`: webhook-triggered theoretical execution run.
- `live_readiness_daily_report.json`: scheduled readiness report and optional Telegram alerts.
- `kill_switch_alert.json`: webhook-triggered readiness check for anomalies.
