# Evaluation Layer

The Evaluation Layer answers one question: are paper trading results and research signals credible enough to keep studying?

It does not approve live trading.

## Modules

- `src/polybot/evaluation/performance.py`: strategy-level performance metrics for paper trading and backtests.
- `src/polybot/evaluation/signal_quality.py`: signal counts, confidence, signal-to-order rate, and signal hit rate.
- `src/polybot/evaluation/fill_quality.py`: fill rate, partial fills, slippage, rejected orders, unrealistic fills, and latency.
- `src/polybot/evaluation/paper_vs_backtest.py`: same-period comparison between backtesting and paper trading.
- `src/polybot/evaluation/anomaly_detection.py`: warnings for optimistic backtests, weak fills, unstable signals, and abnormal behavior.
- `src/polybot/evaluation/reporting.py`: Markdown reports for Obsidian.

## Key Metrics

Paper trading:
- gross PnL
- net PnL
- win rate
- average win/loss
- average and max exposure
- fill rate
- partial fill rate
- average slippage
- rejected trades
- latency impact
- signal hit rate
- profit factor
- drawdown

Comparison:
- backtest net PnL vs paper net PnL
- backtest fill rate vs paper fill rate
- backtest slippage vs paper slippage
- backtest drawdown vs paper drawdown
- trade count delta

## API

```bash
POST /evaluation/run
POST /evaluation/daily-report
POST /evaluation/backtest-vs-paper
POST /evaluation/fill-quality
```

Every endpoint requires `x-automation-secret`.

Example:

```bash
curl -X POST http://localhost:8000/evaluation/run \
  -H "content-type: application/json" \
  -H "x-automation-secret: $POLYBOT_AUTOMATION_SECRET" \
  -d '{"market_id":"<condition_id>","strategy":"wide-spread-mean-reversion","write_obsidian":true}'
```

## Obsidian Outputs

- `obsidian-vault/Evaluation`: strategy evaluation, fill quality, signal quality, backtest-vs-paper reports.
- `obsidian-vault/Performance`: daily paper-trading reports.
- `obsidian-vault/Paper-Trading`: paper-trading run notes and templates.

## Promotion Rule

A signal or strategy should not advance unless:
- data quality is acceptable,
- paper trading and backtest behavior are directionally consistent,
- fill quality is realistic,
- drawdown is controlled,
- anomalies are understood and documented.
