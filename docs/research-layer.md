# Research Layer

## Purpose

The research layer detects simple inefficiency candidates. Signals are hypotheses, not trading instructions.

## Current Signals

- Wide spread.
- Extreme orderbook imbalance.
- Liquidity vacuum.
- Rapid price jump.
- Volume spike.
- Stable exploitable spread.

## Signal Format

Each signal contains:
- market id
- asset id
- timestamp
- signal type
- severity
- confidence
- description
- metrics used
- hypothesis
- next action

## CLI

```bash
PYTHONPATH=src python3 scripts/scan_inefficiencies.py \
  --market-id <condition_id> \
  --from 2026-01-01T00:00:00Z \
  --to 2026-01-02T00:00:00Z \
  --json-out tmp/inefficiency_scan.json \
  --csv-out tmp/inefficiency_scan.csv \
  --obsidian
```

## Obsidian

Reports go to `obsidian-vault/Research/Inefficiencies`.

