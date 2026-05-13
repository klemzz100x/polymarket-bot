# Claude Code Operating Model

Claude Code should operate as a research and engineering partner, not as the live trader.

## Allowed
- Read raw resources.
- Create and update clean Obsidian notes.
- Summarize threads and papers.
- Generate strategy specs.
- Write tests and backtests.
- Document agents and workflows.
- Review logs and post-mortems.

## Restricted
- No direct live order submission.
- No private key handling in prompts or notes.
- No unchecked external code execution.
- No production config changes without review.

## Ideal workflow

1. Resource enters `resources`.
2. Claude or n8n generates a clean note in `obsidian-vault`.
3. A hypothesis note links sources, risks, and test plan.
4. Backtest is implemented under `src/polybot/backtesting`.
5. Strategy moves through paper mode before any live mode.
6. Every incident creates a post-mortem.

