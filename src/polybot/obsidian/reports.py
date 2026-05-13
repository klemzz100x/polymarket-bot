from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polybot.backtesting.results import BacktestResult
from polybot.data.validation import DataQualityReport
from polybot.data.schemas import Market
from polybot.paper_trading.models import PaperTradingResult
from polybot.research.inefficiencies import InefficiencyScanReport
from polybot.research.metrics import MarketMetricsSummary
from polybot.research.metrics import OrderBookMetrics
from polybot.resources.markdown import render_frontmatter


def render_market_analysis_note(
    market: Market,
    metrics: list[OrderBookMetrics] | None = None,
    observed_inefficiencies: list[str] | None = None,
    risks: list[str] | None = None,
    next_actions: list[str] | None = None,
) -> str:
    metadata = {
        "type": "market-analysis",
        "market_id": market.market_id,
        "condition_id": market.condition_id or "",
        "slug": market.slug or "",
        "created": _today(),
        "tags": ["market-research", "data-layer", "polymarket"],
    }
    metrics = metrics or []

    return f"""{render_frontmatter(metadata)}
# Market Analysis - {market.question}

## Metadata
- Market ID: `{market.market_id}`
- Condition ID: `{market.condition_id or ""}`
- Slug: `{market.slug or ""}`
- Active: `{market.active}`
- Closed: `{market.closed}`
- Category: `{market.category or ""}`

## Data Summary
- Outcomes: {", ".join(outcome.name for outcome in market.outcomes) or "n/a"}
- Volume: {_format_decimal(market.volume)}
- Liquidity: {_format_decimal(market.liquidity)}

## Liquidity
{_render_metric_lines(metrics, "total_depth")}

## Spread
{_render_metric_lines(metrics, "spread")}

## Observed Inefficiencies
{_bullet_list(observed_inefficiencies or ["A completer apres analyse."])}

## Risks
{_bullet_list(risks or ["Qualite de donnees a verifier.", "Liquidite potentiellement instable."])}

## Next Actions
{_bullet_list(next_actions or ["Collecter davantage de snapshots.", "Comparer spread et profondeur par outcome.", "Preparer un backtest si une anomalie persiste."])}

## Links
- [[Data Layer]]
- [[Orderbook]]
- [[Backtesting]]
"""


def render_collection_report(
    *,
    title: str,
    rows_seen: int,
    rows_written: int,
    source: str,
    notes: list[str] | None = None,
) -> str:
    metadata = {
        "type": "collection-report",
        "source": source,
        "created": _today(),
        "tags": ["data-layer", "collection"],
    }
    return f"""{render_frontmatter(metadata)}
# {title}

## Summary
- Source: `{source}`
- Rows seen: `{rows_seen}`
- Rows written: `{rows_written}`
- Generated at: `{datetime.now(UTC).isoformat()}`

## Notes
{_bullet_list(notes or ["No notes."])}

## Links
- [[Data Layer]]
- [[Research Loop]]
"""


def render_incident_report(
    *,
    title: str,
    severity: str,
    body: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    frontmatter = {
        "type": "incident",
        "severity": severity,
        "created": _today(),
        "tags": ["incident", "data-layer", "operations"],
        **(metadata or {}),
    }
    return f"""{render_frontmatter(frontmatter)}
# {title}

## Summary
{body.strip()}

## Impact
A completer.

## Detection
A completer.

## Resolution
A completer.

## Preventive Actions
- A definir.

## Links
- [[Risk Framework]]
- [[Data Layer]]
"""


def render_data_quality_report(report: DataQualityReport) -> str:
    metadata = {
        "type": "data-quality-report",
        "market_id": report.market_id,
        "status": report.status,
        "created": _today(),
        "tags": ["data-quality", "data-layer"],
    }
    issue_lines = [
        f"- `{issue.severity}` `{issue.check_name}` {issue.message}"
        for issue in report.issues
    ] or ["- No issues detected."]
    return f"""{render_frontmatter(metadata)}
# Data Quality Report - {report.market_id}

## Period
- From: `{report.start.isoformat() if report.start else ""}`
- To: `{report.end.isoformat() if report.end else ""}`

## Summary
- Status: `{report.status}`
- Snapshots: `{report.snapshot_count}`
- Trades: `{report.trade_count}`
- Price ticks: `{report.price_tick_count}`
- Update frequency / minute: `{_format_decimal(report.observed_update_frequency_per_minute)}`
- Max collection latency seconds: `{_format_decimal(report.max_collection_latency_seconds)}`

## Issues
{chr(10).join(issue_lines)}

## Observations
- Review critical issues before trusting backtests.
- Warnings may still be acceptable for exploratory research if documented.

## Limits
- This report validates collected data only; it does not prove market truth.

## Next Actions
- Recollect missing intervals if possible.
- Compare trades, orderbooks, and price ticks when mismatches appear.

## Links
- [[Data Layer]]
- [[Orderbook]]
- [[Backtesting]]
- [[Execution Quality]]
- [[Risk Management]]
"""


def render_market_metrics_report(summary: MarketMetricsSummary) -> str:
    metadata = {
        "type": "market-metrics-report",
        "market_id": summary.market_id,
        "created": _today(),
        "tags": ["metrics", "research", "data-layer"],
    }
    return f"""{render_frontmatter(metadata)}
# Market Metrics Report - {summary.market_id}

## Summary
- Snapshots: `{summary.snapshot_count}`
- Trades: `{summary.trade_count}`
- Price ticks: `{summary.price_tick_count}`

## Main Metrics
- Average spread abs: `{_format_decimal(summary.average_spread_abs)}`
- Average spread pct: `{_format_decimal(summary.average_spread_pct)}`
- Average bid depth: `{_format_decimal(summary.average_bid_depth)}`
- Average ask depth: `{_format_decimal(summary.average_ask_depth)}`
- Average imbalance: `{_format_decimal(summary.average_imbalance)}`
- Traded volume: `{_format_decimal(summary.traded_volume)}`
- Realized volatility: `{_format_decimal(summary.realized_volatility)}`
- Price change: `{_format_decimal(summary.price_change)}`
- Update frequency / minute: `{_format_decimal(summary.update_frequency_per_minute)}`
- Liquidity score: `{_format_decimal(summary.liquidity_score)}`
- Market activity score: `{_format_decimal(summary.market_activity_score)}`

## Observations
- Compare spread and depth stability before designing any strategy.

## Hypotheses
- Wide persistent spread may be a candidate for passive backtesting.
- Extreme imbalance may be a candidate for momentum tests.

## Limits
- Metrics are only as reliable as the underlying collection cadence.

## Next Actions
- Run an inefficiency scan.
- Validate data quality before trusting results.

## Links
- [[Data Layer]]
- [[Orderbook]]
- [[Backtesting]]
- [[Risk Management]]
"""


def render_inefficiency_scan_report(report: InefficiencyScanReport) -> str:
    metadata = {
        "type": "inefficiency-scan-report",
        "market_id": report.market_id,
        "created": _today(),
        "tags": ["inefficiency", "research", "signals"],
    }
    signal_lines = [
        f"- `{signal.severity}` `{signal.signal_type}` {signal.timestamp.isoformat()} "
        f"confidence={signal.confidence}: {signal.description}"
        for signal in report.signals
    ] or ["- No inefficiency signals detected."]
    return f"""{render_frontmatter(metadata)}
# Inefficiency Scan Report - {report.market_id}

## Summary
- Snapshots: `{report.snapshot_count}`
- Trades: `{report.trade_count}`
- Signals: `{report.signal_count}`

## Signals
{chr(10).join(signal_lines)}

## Observations
- Signals are research hypotheses, not trading instructions.

## Hypotheses
- Promote only persistent signals into strategy research notes.

## Limits
- Current scanner is single-market and simple by design.

## Next Actions
- Backtest relevant signal families with realistic fills.

## Links
- [[Data Layer]]
- [[Orderbook]]
- [[Backtesting]]
- [[Execution Quality]]
- [[Risk Management]]
"""


def render_backtest_result_report(result: BacktestResult) -> str:
    metadata = {
        "type": "backtest-result",
        "strategy": result.strategy_id,
        "market_id": result.market_id,
        "created": _today(),
        "tags": ["backtest", "research", "strategy"],
    }
    return f"""{render_frontmatter(metadata)}
# Backtest Result - {result.strategy_id}

## Summary
- Market ID: `{result.market_id}`
- Trades: `{result.trade_count}`
- Gross PnL: `{_format_decimal(result.gross_pnl)}`
- Net PnL: `{_format_decimal(result.net_pnl)}`
- Win rate: `{_format_decimal(result.win_rate)}`
- Max drawdown: `{_format_decimal(result.max_drawdown)}`

## Execution Quality
- Fill rate: `{_format_decimal(result.fill_rate)}`
- Partial fill rate: `{_format_decimal(result.partial_fill_rate)}`
- Average slippage: `{_format_decimal(result.average_slippage)}`
- Fees: `{_format_decimal(result.fees)}`
- Latency impact: `{_format_decimal(result.latency_impact)}`

## Risk Metrics
- Average exposure: `{_format_decimal(result.average_exposure)}`
- Max exposure: `{_format_decimal(result.max_exposure)}`
- Profit factor: `{_format_decimal(result.profit_factor)}`
- Sharpe approx: `{_format_decimal(result.sharpe_approx)}`

## Observations
- Review fills and partial fills before interpreting PnL.

## Hypotheses
- A profitable result is only a candidate for deeper validation.

## Limits
- V1 backtester uses visible book depth and simplified queue assumptions.
- This is research-only and not live-trading approval.

## Next Actions
- Run on multiple markets and periods.
- Add fee/reward assumptions explicitly.
- Compare with data quality report.

## Links
- [[Data Layer]]
- [[Backtesting]]
- [[Orderbook]]
- [[Execution Quality]]
- [[Risk Management]]
"""


def render_paper_trading_report(result: PaperTradingResult) -> str:
    metadata = {
        "type": "paper-trading-report",
        "run_id": result.run_id,
        "strategy": result.strategy_name,
        "market_id": result.market_id,
        "created": _today(),
        "tags": ["paper-trading", "research", "execution-quality"],
    }
    signal_counts: dict[str, int] = {}
    for signal in result.signals:
        signal_counts[signal.signal_type] = signal_counts.get(signal.signal_type, 0) + 1
    signal_lines = [
        f"- `{signal_type}`: `{count}`" for signal_type, count in sorted(signal_counts.items())
    ] or ["- No signals detected."]
    return f"""{render_frontmatter(metadata)}
# Paper Trading Report - {result.strategy_name}

## Summary
- Run ID: `{result.run_id}`
- Market ID: `{result.market_id}`
- Snapshots processed: `{result.snapshot_count}`
- Signals detected: `{result.signal_count}`
- Attempted orders: `{result.attempted_orders}`
- Filled orders: `{result.filled_orders}`
- Rejected orders: `{result.rejected_orders}`
- Net PnL: `{_format_decimal(result.net_pnl)}`
- Final equity: `{_format_decimal(result.final_equity)}`

## Execution Quality
- Fill rate: `{_format_decimal(result.fill_rate)}`
- Partial fill rate: `{_format_decimal(result.partial_fill_rate)}`
- Fees: `{_format_decimal(result.fees)}`
- Max exposure: `{_format_decimal(result.max_exposure)}`

## Signals
{chr(10).join(signal_lines)}

## Observations
- Paper trading uses collected snapshots and simulated fills only.
- No live order was sent.

## Hypotheses
- Compare this run with the equivalent backtest on the same period.
- Investigate signals that generated orders but no fills.

## Limits
- Queue priority is not modeled yet.
- Fills use visible depth and fixed latency assumptions.

## Next Actions
- Run across multiple periods.
- Compare signal-only, strategy-only, and hybrid decision modes.
- Review data quality for the same period.

## Links
- [[Data Layer]]
- [[Backtesting]]
- [[Orderbook]]
- [[Execution Quality]]
- [[Risk Management]]
"""


def render_strategy_research_note(strategy_name: str, body: str = "") -> str:
    metadata = {
        "type": "strategy-research",
        "strategy": strategy_name,
        "created": _today(),
        "tags": ["strategy", "research", "backtesting"],
    }
    return f"""{render_frontmatter(metadata)}
# Strategy Research - {strategy_name}

## Summary
{body or "A completer apres backtests."}

## Hypothesis

## Metrics Used

## Backtests

## Risks

## Limits
- Research-only strategy. Not approved for live trading.

## Next Actions

## Links
- [[Data Layer]]
- [[Backtesting]]
- [[Orderbook]]
- [[Execution Quality]]
- [[Risk Management]]
"""


def _render_metric_lines(metrics: list[OrderBookMetrics], field: str) -> str:
    if not metrics:
        return "- Not enough data yet."
    lines: list[str] = []
    for metric in metrics:
        value = getattr(metric, field)
        lines.append(f"- `{metric.asset_id}`: {_format_decimal(value)}")
    return "\n".join(lines)


def _bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    return str(value.normalize())


def _today() -> str:
    return datetime.now(UTC).date().isoformat()
