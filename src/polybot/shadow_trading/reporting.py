from polybot.resources.markdown import render_frontmatter
from polybot.shadow_trading.models import ShadowTradingResult
from polybot.shadow_trading.paper_vs_shadow import PaperShadowComparison


def render_shadow_trading_report(result: ShadowTradingResult) -> str:
    metadata = {
        "type": "shadow-trading-report",
        "run_id": result.run_id,
        "market_id": result.market_id,
        "strategy": result.strategy_name,
        "status": result.status,
        "tags": ["shadow-trading", "execution-quality", "pre-live"],
    }
    anomalies = "\n".join(f"- {item}" for item in result.anomalies) or "- No anomalies detected."
    return f"""{render_frontmatter(metadata)}
# Shadow Trading Daily Report - {result.strategy_name}

## Executive Summary
- Status: `{result.status}`
- Market ID: `{result.market_id}`
- Decisions: `{result.decision_count}`
- Theoretical fills: `{result.theoretical_fill_count}`
- Missed fills: `{result.missed_fill_count}`
- Impossible fills: `{result.impossible_fill_count}`

## Metrics
- Average slippage: `{result.average_slippage}`
- Average delay ms: `{result.average_delay_ms}`
- Fill probability: `{result.fill_probability}`
- Signals: `{result.signal_count}`
- Snapshots: `{result.snapshot_count}`

## Anomalies
{anomalies}

## Problems Detected
- Review missed fills, partial fills, latency spikes, stale books, and high slippage.

## Strategies Concerned
- `{result.strategy_name}`

## Recommendations
- Do not promote a strategy if shadow fills diverge materially from paper assumptions.
- Tighten latency and fill models before micro-live consideration.

## Next Actions
- Compare with the equivalent paper trading run.
- Run live readiness checks.
- Review execution quality dashboard.

## Links
- [[Paper Trading]]
- [[Execution Quality]]
- [[Risk Management]]
- [[Backtesting]]
"""


def render_paper_vs_shadow_report(comparison: PaperShadowComparison, *, market_id: str) -> str:
    metadata = {
        "type": "shadow-vs-paper-analysis",
        "market_id": market_id,
        "tags": ["shadow-trading", "paper-trading", "execution-quality"],
    }
    anomalies = "\n".join(f"- {item}" for item in comparison.anomalies)
    return f"""{render_frontmatter(metadata)}
# Shadow vs Paper Analysis

## Executive Summary
- Paper fill rate: `{comparison.paper_fill_rate}`
- Shadow fill probability: `{comparison.shadow_fill_probability}`
- Fill rate delta: `{comparison.fill_rate_delta}`
- Opportunity decay: `{comparison.opportunity_decay}`

## Paper Results
- Average slippage: `{comparison.paper_average_slippage}`

## Shadow Results
- Average slippage: `{comparison.shadow_average_slippage}`

## Execution Gap
- Slippage delta: `{comparison.slippage_delta}`

## Opportunity Decay
- `{comparison.opportunity_decay}`

## Unrealistic Assumptions
{anomalies or "- No major mismatch detected."}

## Recommendations
- Treat any persistent mismatch as a blocker for future live execution.
- Re-run shadow trading with the same market, period, order size, and latency assumptions.

## Next Actions
- Review fill quality in the dashboard.
- Link this analysis to the relevant Strategy Candidate.

## Links
- [[Paper Trading]]
- [[Shadow Trading]]
- [[Backtesting]]
- [[Execution Quality]]
"""
