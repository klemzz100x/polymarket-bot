# Pipeline Validation

This document validates the full research pipeline:

`collection -> storage -> metrics -> signals -> backtesting -> paper trading -> shadow trading -> live readiness -> Obsidian reporting`

The goal is not to trade live. The goal is to prove that the system can collect reliable data, transform it into metrics and signals, simulate execution realistically, and produce reviewable research artifacts.

## Validation Checklist

- Docker services start cleanly.
- Postgres schema is initialized.
- Redis accepts cache writes.
- FastAPI health and metrics endpoints respond.
- Market collection writes rows to Postgres.
- Orderbook collection writes snapshots and levels.
- Trade collection writes public trades when available.
- Data validation reports no critical issues for the test period.
- Metrics generation returns spreads, depth, slippage estimates, and activity scores.
- Inefficiency scanning returns structured research signals.
- Backtesting runs on stored snapshots only.
- Paper trading runs on stored snapshots and research signals only.
- Evaluation compares paper trading against backtesting on the same market and period.
- Shadow trading compares theoretical live-like decisions against observed orderbooks.
- Live readiness scores execution quality, infrastructure health, strategy stability, and kill switch state.
- Obsidian reports are written to the expected vault folders.
- n8n can trigger the FastAPI endpoints with the automation secret.

## Commands

Start the stack:

```bash
cp .env.example .env
docker compose up -d --build
docker compose --profile observability up -d prometheus grafana
```

Expected output:
- `api`, `postgres`, `redis`, and `n8n` containers are healthy or running.
- Prometheus and Grafana run when the observability profile is enabled.

Check API health:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

Expected output:
- `/health` returns an application status response.
- `/metrics` returns Prometheus-formatted metrics.

Collect markets:

```bash
PYTHONPATH=src python3 scripts/collect_markets.py --limit 100 --orderbook-only
```

Expected output:
- Active markets are fetched from Polymarket.
- Market and outcome rows are upserted in Postgres.
- Active markets are cached in Redis.

Collect orderbooks:

```bash
PYTHONPATH=src python3 scripts/collect_orderbooks.py --active-limit 10 --interval 5 --iterations 6
```

Expected output:
- Orderbook snapshots are inserted.
- Duplicate snapshots are ignored by the database constraint.
- Latest books are cached in Redis.

Collect trades:

```bash
PYTHONPATH=src python3 scripts/collect_trades.py --limit 250
```

Expected output:
- Public trades are stored when available.
- Empty trade periods are acceptable, but must be visible in validation reports.

Validate data:

```bash
PYTHONPATH=src python3 scripts/validate_data.py --market-id <condition_id> --obsidian
```

Expected output:
- Console summary with status `ok`, `warning`, or `critical`.
- JSON report file if the script is configured to write one.
- Optional Obsidian note in `obsidian-vault/Data`.

Compute metrics:

```bash
PYTHONPATH=src python3 scripts/compute_market_metrics.py --market-id <condition_id> --obsidian
```

Expected output:
- Spread, depth, imbalance, update frequency, liquidity score, activity score, and slippage estimates.
- Optional Obsidian note in `obsidian-vault/Market-Research`.

Scan inefficiencies:

```bash
PYTHONPATH=src python3 scripts/scan_inefficiencies.py --market-id <condition_id> --obsidian
```

Expected output:
- Structured signal list with timestamp, severity, confidence, hypothesis, and next action.
- Optional Obsidian note in `obsidian-vault/Research/Inefficiencies`.

Run backtest:

```bash
PYTHONPATH=src python3 scripts/run_backtest.py --strategy wide-spread-mean-reversion --market-id <condition_id> --obsidian
```

Expected output:
- Backtest result with PnL, fill rate, partial fills, slippage, fees, drawdown, and exposure metrics.
- Optional Obsidian note in `obsidian-vault/Backtests`.

Run paper trading:

```bash
PYTHONPATH=src python3 scripts/run_paper_trading.py --market-id <condition_id> --decision-mode hybrid --obsidian
```

Expected output:
- Paper run result with signals, attempted orders, fills, rejections, PnL, and execution quality metrics.
- JSONL ledger in `logs/paper-trading`.
- Optional Obsidian note in `obsidian-vault/Paper-Trading`.

Run evaluation through FastAPI:

```bash
curl -X POST http://localhost:8000/evaluation/run \
  -H "content-type: application/json" \
  -H "x-automation-secret: $POLYBOT_AUTOMATION_SECRET" \
  -d '{"market_id":"<condition_id>","strategy":"wide-spread-mean-reversion","write_obsidian":true}'
```

Expected output:
- `job_id`
- strategy performance metrics
- signal quality metrics
- fill quality metrics
- anomalies
- optional Obsidian note in `obsidian-vault/Evaluation`

Run shadow trading:

```bash
PYTHONPATH=src python3 scripts/run_shadow_trading.py --market-id <condition_id> --persist-db --obsidian
```

Expected output:
- Shadow decisions and theoretical fills.
- Missed fills, impossible fills, slippage, delay, and fill probability.
- Optional Obsidian note in `obsidian-vault/Shadow-Trading`.

Run live readiness:

```bash
PYTHONPATH=src python3 scripts/run_live_readiness.py --market-id <condition_id> --persist-db --obsidian
```

Expected output:
- `live_readiness_score`, execution quality score, infrastructure score, and strategy stability score.
- Kill switch state and any trigger events.
- Optional Obsidian note in `obsidian-vault/Live-Readiness`.

## Critical Checks

Data integrity:
- Snapshot timestamps must be timezone-aware.
- Orderbook levels must have prices inside the probability range and positive sizes.
- Snapshot gaps must be understood before trusting metrics.
- Duplicate rows must be rejected by constraints, not by manual cleanup.

Research validity:
- Metrics, signals, backtests, and paper trading must use the same market ID and period.
- Obsidian reports should point back to the corresponding data-quality report.
- A profitable backtest is not useful if fill quality is unrealistic.
- A high signal count is not useful if signal hit rate and fill quality are poor.

Execution realism:
- The simulator must use visible depth, spread, latency, slippage, fees, order size, and position limits.
- It must never fill at a price that does not exist in the stored book.
- Partial fills must remain visible in reports.
- Rejected paper orders are research data, not noise.
- Shadow fills must be checked before trusting paper trading performance.
- Any persistent paper-vs-shadow mismatch should block future live consideration.

Observability:
- Collectors should emit structured logs.
- Prometheus counters should move when jobs run.
- Evaluation anomalies should be visible in Obsidian and n8n alerts.

## Common Errors

Missing database tables:
- Rebuild the stack after checking `docker/postgres/init`.
- Confirm the `DATABASE_URL` points to the Docker Postgres service inside containers and localhost outside containers.

No active asset IDs:
- Run market collection first.
- Confirm markets have `enable_order_book=true`.

No snapshots:
- Run orderbook collection for a small active universe.
- Check Polymarket API availability and HTTP timeout settings.

Validation is critical:
- Check empty orderbooks, invalid levels, and timestamp gaps.
- Recollect the period before using it for research.

Metrics look wrong:
- Confirm you are using a condition ID where expected.
- Confirm bid/ask levels were normalized in the correct order.

Backtest and paper trading disagree heavily:
- Compare the exact market, strategy, period, latency, fees, and order size.
- Review fill quality before interpreting PnL.

Shadow trading shows impossible fills:
- Review latency, order size, visible depth, and stale books.
- Treat the strategy as not live-ready until the mismatch is explained.

Live readiness is failed:
- Review `app.live_readiness_reports` and `app.kill_switch_events`.
- Fix critical checks before running another promotion review.

Obsidian note missing:
- Confirm `OBSIDIAN_VAULT_DIR` or `obsidian_vault_dir` points to the local vault.
- Confirm the script or endpoint was called with `--obsidian` or `write_obsidian=true`.

n8n endpoint rejected:
- Confirm `POLYBOT_AUTOMATION_SECRET` is set in both n8n and the API.
- Confirm the header is `x-automation-secret`.
