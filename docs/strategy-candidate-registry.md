# Strategy Candidate Registry

The Strategy Candidate Registry prevents research ideas from disappearing across threads, reports, and experiments.

## Module

```text
src/polybot/research/strategy_registry.py
```

## Functions

- list candidates
- rank candidates
- mark as tested
- mark as rejected
- mark as promising
- link candidate to backtest results
- link candidate to paper-trading results

## Storage

Default registry path:

```text
obsidian-vault/Research/Strategy-Candidates/strategy-candidate-registry.json
```

This is qualitative research metadata. It does not replace Postgres quantitative results.

## Status Values

- `new`
- `tested`
- `promising`
- `rejected`

## Ranking

Ranking is based on:
- priority
- implementation difficulty
- promising status boost

The ranking is intentionally simple and reviewable. It is a research triage aid, not a trading signal.

## Promotion Rule

A candidate becomes promising only after:
- clean data validation,
- measurable signal definition,
- realistic backtest,
- paper-trading comparison,
- documented risk.
