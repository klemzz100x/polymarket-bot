# Obsidian Integration

Obsidian is the qualitative memory. It stores Markdown notes, not critical quantitative data.

## Vault Structure

- `Research`
- `Market-Research`
- `Architecture`
- `Data`
- `Backtests`
- `Trading-Journal`
- `Post-Mortems`
- `Strategies`
- `Risk-Management`
- `Execution`
- `Sources`
- `Tools`

## Generated Notes

The app can generate:
- collection reports
- market analysis notes
- incidents
- strategy ideas
- generic notes from n8n

Endpoints:
- `POST /webhooks/generate-note`
- `POST /webhooks/market-alert`
- `POST /webhooks/incident`
- `POST /webhooks/collection-report`

All webhook calls should include `x-automation-secret`.

## Principle

Postgres answers: "what happened quantitatively?"

Obsidian answers: "what did we learn, decide, and test next?"

