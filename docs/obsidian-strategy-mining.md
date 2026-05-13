# Obsidian Strategy Mining

Obsidian is the qualitative research memory. The mining layer reads Markdown notes in the vault and turns useful Twitter-thread research into testable Strategy Candidates.

## Modules

- `src/polybot/research/obsidian_mining/vault_reader.py`: reads Markdown notes, frontmatter, titles, and sections.
- `src/polybot/research/obsidian_mining/thread_parser.py`: identifies Polymarket-related Twitter thread notes.
- `src/polybot/research/obsidian_mining/strategy_extractor.py`: detects edge families and extracts evidence sentences.
- `src/polybot/research/obsidian_mining/hypothesis_generator.py`: maps edge families to data, metrics, signals, and backtest designs.
- `src/polybot/research/obsidian_mining/strategy_candidate.py`: typed Strategy Candidate model.
- `src/polybot/research/obsidian_mining/reporting.py`: Obsidian Markdown reports.

## Edge Families

- spread capture
- market making
- orderbook imbalance
- liquidity vacuum
- stale orderbook
- delayed repricing
- cross-market arbitrage
- news latency
- event-driven repricing
- behavioral overreaction
- resolution edge

## Command

```bash
PYTHONPATH=src python3 scripts/mine_obsidian_strategies.py --vault obsidian-vault --overwrite
```

Dry run:

```bash
PYTHONPATH=src python3 scripts/mine_obsidian_strategies.py --dry-run
```

## Output

Strategy Candidate notes are written to:

```text
obsidian-vault/Research/Strategy-Candidates
```

The registry JSON is written to:

```text
obsidian-vault/Research/Strategy-Candidates/strategy-candidate-registry.json
```

## Important

The miner does not invent content. Placeholder thread notes marked `to_summarize` will not produce candidates unless they contain actual strategy evidence.

## Workflow

1. Import Twitter/X thread links into Obsidian.
2. Extract or summarize thread content into the note.
3. Run the miner.
4. Review generated candidates.
5. Promote candidates into backtests only after data-quality checks.
6. Link backtest and paper-trading results in the strategy registry.
