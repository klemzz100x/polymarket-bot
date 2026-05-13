from decimal import Decimal

from polybot.evaluation.models import (
    EvaluationReport,
    FillQualityMetrics,
    SignalPerformance,
)
from polybot.resources.markdown import render_frontmatter


def render_evaluation_report(report: EvaluationReport) -> str:
    metadata = {
        "type": "strategy-evaluation",
        "market_id": report.market_id,
        "strategy": report.strategy_name,
        "status": report.status,
        "created": report.generated_at.date().isoformat(),
        "tags": ["evaluation", "paper-trading", "backtesting"],
    }
    return f"""{render_frontmatter(metadata)}
# Strategy Evaluation Report - {report.strategy_name}

## Executive Summary
- Status: `{report.status}`
- Market ID: `{report.market_id}`
- Strategy: `{report.strategy_name}`
- Period start: `{report.period_start.isoformat() if report.period_start else ""}`
- Period end: `{report.period_end.isoformat() if report.period_end else ""}`

## Key Metrics
{_render_strategy_block("Paper Trading", report.paper_performance)}
{_render_strategy_block("Backtest", report.backtest_performance)}

## Signal Quality
{_render_signal_quality(report.signal_performance)}

## Fill Quality
{_render_fill_quality(report.fill_quality)}

## Backtest vs Paper
{_render_comparison(report.comparison)}

## Anomalies
{_render_anomalies(report)}

## Performing Markets
- Review markets with stable fill quality, low slippage, and repeatable signal hit rate.

## Problematic Markets
- Prioritize markets with stale books, weak fills, high slippage, or large backtest/paper divergence.

## Hypotheses
- Signals with stable fill quality may deserve multi-market testing.
- Backtest-only edge should be discounted until paper trading behaves similarly.

## Limits
- This report validates research and paper-trading behavior only.
- No live execution approval is implied.

## Next Actions
- Re-run on adjacent periods.
- Compare with data-quality and metrics reports for the same market.
- Promote only robust hypotheses into strategy research notes.

## Links
- [[Data Layer]]
- [[Backtesting]]
- [[Orderbook]]
- [[Execution Quality]]
- [[Risk Management]]
"""


def render_daily_paper_trading_report(report: EvaluationReport) -> str:
    metadata = {
        "type": "daily-paper-trading-report",
        "market_id": report.market_id,
        "strategy": report.strategy_name,
        "status": report.status,
        "created": report.generated_at.date().isoformat(),
        "tags": ["paper-trading", "performance", "evaluation"],
    }
    return f"""{render_frontmatter(metadata)}
# Daily Paper Trading Report - {report.strategy_name}

## Executive Summary
- Status: `{report.status}`
- Market ID: `{report.market_id}`
- Strategy: `{report.strategy_name}`

## Key Metrics
{_render_strategy_block("Paper Trading", report.paper_performance)}

## Fill Quality
{_render_fill_quality(report.fill_quality)}

## Signal Quality
{_render_signal_quality(report.signal_performance)}

## Anomalies
{_render_anomalies(report)}

## Markets Performing
- Markets with better fill rate and lower slippage should be reviewed first.

## Markets Problematic
- Markets with stale data, low fill rate, high rejected order count, or high drawdown need caution.

## Hypotheses
- Paper-trading behavior should remain stable before any strategy promotion.

## Next Actions
- Compare with the latest backtest on the same window.
- Review rejected orders and partial fills.

## Links
- [[Paper Trading]]
- [[Execution Quality]]
- [[Backtesting]]
- [[Risk Management]]
"""


def render_fill_quality_report(fill_quality: FillQualityMetrics, *, title: str = "Fill Quality Report") -> str:
    metadata = {
        "type": "fill-quality-report",
        "tags": ["fill-quality", "paper-trading", "execution-quality"],
    }
    return f"""{render_frontmatter(metadata)}
# {title}

## Executive Summary
- Fill rate: `{_fmt(fill_quality.fill_rate)}`
- Partial fill rate: `{_fmt(fill_quality.partial_fill_rate)}`
- Rejection rate: `{_fmt(fill_quality.rejection_rate)}`
- Unrealistic fills: `{fill_quality.unrealistic_fill_count}`

## Key Metrics
{_render_fill_quality(fill_quality)}

## Anomalies
- Review unrealistic fills, high slippage, and low fill rate before interpreting PnL.

## Hypotheses
- Poor fill quality may invalidate apparent edge.

## Next Actions
- Compare order size to visible book depth.
- Re-run with stricter latency and slippage assumptions.

## Links
- [[Execution Quality]]
- [[Backtesting]]
- [[Risk Management]]
"""


def render_signal_quality_report(signal_quality: SignalPerformance) -> str:
    metadata = {
        "type": "signal-quality-report",
        "market_id": signal_quality.market_id,
        "strategy": signal_quality.strategy_name,
        "tags": ["signal-quality", "research", "evaluation"],
    }
    return f"""{render_frontmatter(metadata)}
# Signal Quality Report - {signal_quality.strategy_name}

## Executive Summary
- Market ID: `{signal_quality.market_id}`
- Signals: `{signal_quality.signal_count}`
- Signal hit rate: `{_fmt(signal_quality.signal_hit_rate)}`
- Signal-to-order rate: `{_fmt(signal_quality.signal_to_order_rate)}`

## Key Metrics
{_render_signal_quality(signal_quality)}

## Anomalies
- Weak hit rate or low confidence should block strategy promotion.

## Hypotheses
- Signal families with repeated fills and controlled slippage deserve deeper testing.

## Next Actions
- Review signals by type.
- Compare against data-quality issues for the same period.

## Links
- [[Research Loop]]
- [[Backtesting]]
- [[Orderbook]]
- [[Risk Management]]
"""


def render_backtest_vs_paper_report(report: EvaluationReport) -> str:
    metadata = {
        "type": "backtest-vs-paper-comparison",
        "market_id": report.market_id,
        "strategy": report.strategy_name,
        "status": report.status,
        "created": report.generated_at.date().isoformat(),
        "tags": ["backtesting", "paper-trading", "evaluation"],
    }
    return f"""{render_frontmatter(metadata)}
# Backtest vs Paper Comparison - {report.strategy_name}

## Executive Summary
- Status: `{report.status}`
- Market ID: `{report.market_id}`
- Strategy: `{report.strategy_name}`

## Key Metrics
{_render_comparison(report.comparison)}

## Anomalies
{_render_anomalies(report)}

## Hypotheses
- Backtest and paper results should converge before trusting any edge.

## Limits
- Backtest and paper comparison is only valid when using the same period and configuration.

## Next Actions
- Tighten fill model if backtest is materially better than paper.
- Review data-quality report for this period.

## Links
- [[Backtesting]]
- [[Paper Trading]]
- [[Execution Quality]]
- [[Risk Management]]
"""


def _render_strategy_block(title: str, performance) -> str:
    if performance is None:
        return f"### {title}\n- Not available."
    return f"""### {title}
- Gross PnL: `{_fmt(performance.gross_pnl)}`
- Net PnL: `{_fmt(performance.net_pnl)}`
- Trades: `{performance.trade_count}`
- Win rate: `{_fmt(performance.win_rate)}`
- Average win: `{_fmt(performance.average_win)}`
- Average loss: `{_fmt(performance.average_loss)}`
- Fill rate: `{_fmt(performance.fill_rate)}`
- Partial fill rate: `{_fmt(performance.partial_fill_rate)}`
- Average slippage: `{_fmt(performance.average_slippage)}`
- Fees: `{_fmt(performance.fees)}`
- Latency impact: `{_fmt(performance.latency_impact)}`
- Max exposure: `{_fmt(performance.max_exposure)}`
- Max drawdown: `{_fmt(performance.drawdown.max_drawdown)}`
- Profit factor: `{_fmt(performance.profit_factor)}`
"""


def _render_fill_quality(fill_quality: FillQualityMetrics | None) -> str:
    if fill_quality is None:
        return "- Not available."
    return f"""- Attempted orders: `{fill_quality.attempted_orders}`
- Filled orders: `{fill_quality.filled_orders}`
- Rejected orders: `{fill_quality.rejected_orders}`
- Unfilled orders: `{fill_quality.unfilled_orders}`
- Fill rate: `{_fmt(fill_quality.fill_rate)}`
- Partial fill rate: `{_fmt(fill_quality.partial_fill_rate)}`
- Average requested size: `{_fmt(fill_quality.average_requested_size)}`
- Average filled size: `{_fmt(fill_quality.average_filled_size)}`
- Average fill ratio: `{_fmt(fill_quality.average_fill_ratio)}`
- Average slippage: `{_fmt(fill_quality.average_slippage)}`
- Max slippage: `{_fmt(fill_quality.max_slippage)}`
- Fees: `{_fmt(fill_quality.fees)}`
- Average latency ms: `{_fmt(fill_quality.latency.average_latency_ms)}`
- Max latency ms: `{fill_quality.latency.max_latency_ms}`
- Latency impact: `{_fmt(fill_quality.latency.latency_impact)}`
- Unrealistic fills: `{fill_quality.unrealistic_fill_count}`"""


def _render_signal_quality(signal_quality: SignalPerformance | None) -> str:
    if signal_quality is None:
        return "- Not available."
    signal_lines = [
        f"- `{signal_type}`: `{count}`"
        for signal_type, count in sorted(signal_quality.signals_by_type.items())
    ] or ["- No signals."]
    fill_lines = [
        f"- `{signal_type}`: `{count}`"
        for signal_type, count in sorted(signal_quality.fills_by_signal_type.items())
    ] or ["- No signal-driven fills."]
    return f"""- Signals: `{signal_quality.signal_count}`
- Orders from signals: `{signal_quality.orders_from_signals}`
- Fills from signals: `{signal_quality.fills_from_signals}`
- Signal-to-order rate: `{_fmt(signal_quality.signal_to_order_rate)}`
- Signal hit rate: `{_fmt(signal_quality.signal_hit_rate)}`
- Average confidence: `{_fmt(signal_quality.average_signal_confidence)}`

Signals by type:
{chr(10).join(signal_lines)}

Fills by signal type:
{chr(10).join(fill_lines)}"""


def _render_comparison(comparison: dict[str, object]) -> str:
    if not comparison:
        return "- Not available."
    return "\n".join(f"- {key}: `{value}`" for key, value in sorted(comparison.items()))


def _render_anomalies(report: EvaluationReport) -> str:
    if not report.anomalies:
        return "- No evaluation anomalies detected."
    return "\n".join(
        f"- `{item.severity}` `{item.anomaly_type}` {item.description} "
        f"Next: {item.next_action or 'Review manually.'}"
        for item in report.anomalies
    )


def _fmt(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    return str(value.normalize())
