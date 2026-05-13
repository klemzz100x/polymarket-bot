# Architecture

## Official documentation decisions

Obsidian stores notes as Markdown plain-text files in a local vault folder. This project therefore writes clean knowledge directly as `.md` files under `obsidian-vault` and keeps raw inbox material outside the vault.

n8n workflows are built from nodes passing JSON-like items between nodes. Webhook nodes expose separate test and production URLs, support authentication, and can return either immediately, after the final node, or through a dedicated Respond to Webhook node. This project treats n8n as an orchestration layer, not as the source of truth.

n8n queue mode uses Redis as the message broker and Postgres as persistent storage. The Docker setup is therefore ready for n8n main plus worker processes.

## System planes

1. Research plane: raw resources, source parsing, note generation, RAG ingestion.
2. Knowledge plane: Obsidian vault with curated Markdown notes, linked concepts, journals, post-mortems.
3. Automation plane: n8n webhooks and scheduled workflows calling the FastAPI automation API.
4. Data plane: market ingestion, normalized events, feature generation, vector indexing.
5. Strategy plane: isolated strategies with explicit configuration and risk budgets.
6. Execution plane: deterministic order routing, heartbeat, fills, reconciliation, and kill switches.
7. Monitoring plane: structured logs, metrics, alerts, dashboards, post-trade review.
8. AI plane: slow-path research, summarization, agent documentation, experiment design, and post-mortems.

## Project tree

```text
polymarket-bot/
  resources/
    twitter-threads/
    agents-list/
  obsidian-vault/
    Research/
    Strategies/
    Backtests/
    Architecture/
    Trading-Journal/
    Post-Mortems/
    Market-Research/
    Execution/
    Risk-Management/
    Ideas/
    Tools/
      Agents/
      Skills/
    Sources/
      Twitter-Threads/
      Articles/
      Papers/
  external-agents/
  src/polybot/
    api/
    core/
    domain/
    resources/
    knowledge/
    agents/
    automation/
    data/
    execution/
    strategies/
    risk/
    backtesting/
    monitoring/
    rag/
    ai/
    storage/
  scripts/
  n8n/workflows/
  configs/
  docs/
  tests/
```

## Production rules

- Raw material never becomes project memory until cleaned into Markdown notes.
- AI never sends live orders directly.
- Execution code must stay deterministic and observable.
- Research scripts can be flexible; production services must be typed, tested, logged, and configured centrally.
- Secrets stay in `.env`, Docker secrets, or a secret manager. Never commit wallet keys.
- External repositories are untrusted by default and are reviewed before integration.

## Recommended next layers

- Data Layer now starts with Gamma markets, CLOB orderbooks, Data API public trades, Postgres tables, Redis hot cache, and replay scripts.
- Add Alembic migrations for app schema evolution.
- Add pgvector/Qdrant ingestion jobs for Obsidian notes.
- Add Polymarket CLOB V2 execution adapter only after research/backtesting is stable.
- Add strategy sandbox with paper trading before live mode.
- Add Grafana dashboards for collector health, row counts, stale data, spread, depth, and anomalies.
