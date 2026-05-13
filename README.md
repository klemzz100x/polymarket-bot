# Polymarket Bot Infrastructure

Production-grade research, automation, and execution scaffold for a Polymarket trading system.

Core boundaries:
- `resources/`: raw inbox for threads, PDFs, screenshots, links, and rough dumps.
- `obsidian-vault/`: clean strategic memory in Markdown only.
- `external-agents/`: downloaded third-party agent and skill repositories.
- `src/`: production Python code for API, ingestion, execution, risk, research automation, and monitoring.
- `n8n/`: importable workflow examples.
- `scripts/`: operational scripts for imports, note generation, and webhook automation.
- `docker/postgres/init`: Postgres schema initialization for the data layer.

Quick start:

```bash
cp .env.example .env
# Use Python 3.11+.
python3 -m pip install -e ".[dev,research]"
PYTHONPATH=src python3 scripts/import_twitter_threads.py
PYTHONPATH=src python3 scripts/import_agents_git.py --no-clone
uvicorn polybot.main:app --reload
```

Data layer:

```bash
PYTHONPATH=src python3 scripts/collect_markets.py --limit 100 --orderbook-only
PYTHONPATH=src python3 scripts/collect_orderbooks.py --active-limit 10 --interval 5 --iterations 6
PYTHONPATH=src python3 scripts/collect_trades.py --limit 250
PYTHONPATH=src python3 scripts/replay_market.py --asset-id <token_id> --limit 100
```

Research and backtesting:

```bash
PYTHONPATH=src python3 scripts/validate_data.py --market-id <condition_id> --obsidian
PYTHONPATH=src python3 scripts/compute_market_metrics.py --market-id <condition_id> --obsidian
PYTHONPATH=src python3 scripts/scan_inefficiencies.py --market-id <condition_id> --obsidian
PYTHONPATH=src python3 scripts/run_backtest.py --strategy wide-spread-mean-reversion --market-id <condition_id> --obsidian
PYTHONPATH=src python3 scripts/run_paper_trading.py --market-id <condition_id> --decision-mode hybrid --obsidian
PYTHONPATH=src python3 scripts/mine_obsidian_strategies.py --dry-run
```

Pre-live validation:

```bash
PYTHONPATH=src python3 scripts/run_shadow_trading.py --market-id <condition_id> --persist-db --obsidian
PYTHONPATH=src python3 scripts/run_live_readiness.py --market-id <condition_id> --persist-db --obsidian
```

Live execution foundation:

```bash
# Safe default: no live orders.
LIVE_TRADING_ENABLED=false
LIVE_EXECUTION_MODE=DISABLED

# Wallet sync is read-only and requires LIVE_EXECUTION_MODE=READ_ONLY or SHADOW.
PYTHONPATH=src python3 scripts/sync_wallet.py --persist-db --obsidian

# Inspect current mode and limits.
curl http://localhost:8000/live-execution/status \
  -H "x-automation-secret: $POLYBOT_AUTOMATION_SECRET"
```

Pipeline validation:

```bash
# Validate the complete path:
# collection -> storage -> metrics -> signals -> backtesting -> paper trading -> reporting.
sed -n '1,220p' docs/pipeline-validation.md
```

FastAPI/n8n endpoints:

- `POST /research/validate-data`
- `POST /research/compute-metrics`
- `POST /research/scan-inefficiencies`
- `POST /backtesting/run`
- `POST /paper-trading/run`
- `GET /paper-trading/equity`
- `GET /paper-trading/performance/live`
- `POST /evaluation/run`
- `POST /evaluation/daily-report`
- `POST /evaluation/backtest-vs-paper`
- `POST /evaluation/fill-quality`
- `POST /shadow-trading/run`
- `GET /shadow-trading/latest`
- `POST /live-readiness/run`
- `GET /live-readiness/latest`
- `GET /live-execution/status`
- `POST /live-execution/prepare-order`
- `POST /obsidian/generate-report`

Telegram alerts:

```bash
PYTHONPATH=src python3 scripts/test_telegram.py
```

Evaluation example:

```bash
curl -X POST http://localhost:8000/evaluation/run \
  -H "content-type: application/json" \
  -H "x-automation-secret: $POLYBOT_AUTOMATION_SECRET" \
  -d '{"market_id":"<condition_id>","strategy":"wide-spread-mean-reversion","write_obsidian":true}'
```

Docker:

```bash
cp .env.example .env
docker compose up -d --build
docker compose up -d --build dashboard
docker compose --profile observability up -d prometheus grafana
```

Dashboard:

```text
http://localhost:8501
```

Use `Terminal Cockpit` for the single-window real-time validation view. Use `Twitter Research` to paste X/Twitter threads; it stores raw captures in `resources/twitter-threads` and creates Markdown research notes in the Obsidian vault.

Roadmap:

- `next-step.md`
- `docs/next-steps.md`

Core docs:

- `docs/pipeline-validation.md`
- `docs/evaluation-layer.md`
- `docs/paper-trading-validation.md`
- `docs/monitoring.md`
- `docs/websocket-layer.md`
- `docs/obsidian-strategy-mining.md`
- `docs/strategy-candidate-registry.md`
- `docs/dashboard.md`
- `docs/equity-monitoring.md`
- `docs/telegram.md`
- `docs/shadow-trading.md`
- `docs/live-readiness.md`
- `docs/kill-switch.md`
- `docs/execution-quality.md`
- `docs/live-execution-foundation.md`
- `docs/wallet-integration.md`
- `docs/oms.md`
- `docs/live-risk.md`
- `docs/micro-live.md`

Operational rule: live trading is out of scope until evaluation, monitoring, and risk controls are proven.
Even future micro-live mode must pass readiness, kill switch, risk gate, hard order limits, and manual confirmation.
