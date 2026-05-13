# Data Validation

## Purpose

The validation layer checks whether stored market data is fit for research and backtesting.

## Checks

- Missing snapshots.
- Missing trades.
- Missing price ticks.
- Empty orderbooks.
- Invalid prices outside `(0, 1)`.
- Zero or negative orderbook sizes.
- Zero or negative trade volume.
- Timestamp regressions.
- Snapshot gaps.
- Collection latency.
- Trade and price tick coherence.

## CLI

```bash
PYTHONPATH=src python3 scripts/validate_data.py \
  --market-id <condition_id> \
  --from 2026-01-01T00:00:00Z \
  --to 2026-01-02T00:00:00Z \
  --json-out tmp/data_quality.json \
  --obsidian
```

## Output

- Console summary.
- JSON report.
- Optional Obsidian note in `obsidian-vault/Data`.

## Rule

Do not trust backtests on periods with critical validation issues.

