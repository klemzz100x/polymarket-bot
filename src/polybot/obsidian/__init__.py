"""Obsidian note generation for data and research outputs."""

from polybot.obsidian.reports import (
    render_backtest_result_report,
    render_collection_report,
    render_data_quality_report,
    render_inefficiency_scan_report,
    render_incident_report,
    render_market_metrics_report,
    render_market_analysis_note,
    render_paper_trading_report,
    render_strategy_research_note,
)

__all__ = [
    "render_backtest_result_report",
    "render_collection_report",
    "render_data_quality_report",
    "render_incident_report",
    "render_inefficiency_scan_report",
    "render_market_analysis_note",
    "render_market_metrics_report",
    "render_paper_trading_report",
    "render_strategy_research_note",
]
