# n8n Automation

## Role

n8n is an orchestration layer. It should trigger workflows, call FastAPI, and fan out alerts. It is not the quantitative source of truth.

## Available FastAPI Webhooks

- `POST /webhooks/market-alert`
- `POST /webhooks/incident`
- `POST /webhooks/generate-note`
- `POST /webhooks/collection-report`

Headers:

```http
x-automation-secret: <POLYBOT_AUTOMATION_SECRET>
```

## Workflow Examples

Import these JSON workflows from `n8n/workflows`:
- `market_alert_to_obsidian.json`
- `incident_to_postmortem.json`
- `research_webhook_to_note.json`
- `twitter_threads_to_obsidian.json`
- `agent_repo_to_obsidian.json`

## Recommended Workflows

- Scheduled market collection report.
- Incident to post-mortem draft.
- Market alert to Obsidian note.
- Weekly research digest.
- Thread/resource intake to clean Markdown note.

## Production Notes

- Use n8n test webhook URLs while developing.
- Use production webhook URLs only after activation.
- Keep n8n behind authentication and HTTPS outside local dev.
- Queue mode uses Redis and Postgres; keep the worker process running.

