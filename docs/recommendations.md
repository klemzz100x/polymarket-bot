# Recommendations

## Python dependencies

Core:
- `fastapi`, `uvicorn`: API and automation webhooks.
- `pydantic`, `pydantic-settings`: strict schemas and config.
- `structlog`, `python-json-logger`: structured logs.
- `SQLAlchemy`, `asyncpg`, `alembic`: database access and migrations.
- `redis`: queues, locks, caches, and event fanout.
- `pgvector`, `qdrant-client`: vector search and RAG.
- `httpx`: external API clients.
- `prometheus-client`: metrics.

Research:
- `pandas`, `polars`, `duckdb`: data exploration.
- `numpy`, `scikit-learn`: feature research and models.
- `beautifulsoup4`: article extraction.
- `jupyter`: notebooks and experiments.

AI:
- `openai`: embeddings and summarization.
- Add model provider SDKs only when needed.
- Use Langfuse or OpenTelemetry for LLM traces.

Quality:
- `pytest`, `pytest-asyncio`.
- `ruff`.
- `mypy`.

## Obsidian plugins

Useful:
- Dataview: dashboards over notes and metadata.
- Templater: reusable note templates.
- Tasks: operational follow-ups.
- Calendar: trading journal navigation.
- Excalidraw: diagrams and strategy sketches.
- Advanced Tables: cleaner research tables.
- Obsidian Git: vault backups and reviewable changes.
- Omnisearch: fast local search.

Keep plugin count small. The vault should remain portable Markdown first.

## n8n workflows

Recommended workflows:
- Twitter thread inbox to Obsidian note.
- Agent repo list to Obsidian agent note.
- Research webhook to generic note.
- Scheduled source review.
- Daily trading journal creation.
- Post-mortem draft creation after incident webhook.
- Weekly research digest.
- Alert fanout from API to Slack/Discord/email.

Production notes:
- Use webhook auth headers.
- Use test URLs for development, production URLs only when active.
- Keep payloads below n8n webhook limits.
- Use queue mode with Redis and Postgres when workflows grow.

## Docker and infra

Local:
- API, Postgres with pgvector, Redis, Qdrant, n8n.
- Optional Prometheus and Grafana profile.

Production:
- Pin all image versions.
- Use managed Postgres if possible.
- Use managed Redis if workflows become critical.
- Keep n8n workers separate from the main UI process.
- Put n8n behind HTTPS and authentication.
- Add backups for Postgres, n8n volume, and Obsidian vault.

## Security

- Never commit wallet private keys.
- Use a dedicated wallet with capped capital.
- Keep trading keys server-side.
- Separate research credentials from execution credentials.
- Treat external agent repos as untrusted.
- Pin external repos to commit SHAs before integration.
- Add branch protection and required CI before merging execution code.
- Use kill switches and paper mode by default.

## GitHub structure

Recommended branches:
- `main`: production-stable.
- `develop`: integration.
- `research/*`: experiments.
- `strategy/*`: strategy implementation.
- `infra/*`: Docker, deployment, monitoring.

Recommended checks:
- lint.
- typecheck.
- unit tests.
- config validation.
- Docker build.
- security scan.
- no-secrets scan.

Recommended issues:
- `research-hypothesis`.
- `strategy`.
- `risk`.
- `execution`.
- `data`.
- `automation`.
- `obsidian`.
- `security`.

