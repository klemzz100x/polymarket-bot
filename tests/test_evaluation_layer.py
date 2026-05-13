from datetime import datetime
from datetime import timedelta
from polybot.core.compat import UTC
from decimal import Decimal

from polybot.backtesting import BacktestConfig, BacktestEngine
from polybot.data.normalization import normalize_orderbook
from polybot.evaluation import (
    compare_backtest_vs_paper,
    compute_fill_quality,
    compute_signal_performance,
    compute_strategy_performance,
    detect_evaluation_anomalies,
)
from polybot.evaluation.reporting import render_evaluation_report
from polybot.evaluation.models import EvaluationReport, now_utc
from polybot.paper_trading import PaperTradingConfig, PaperTradingEngine
from polybot.strategies.research import get_research_strategy


def test_evaluation_metrics_and_report_render() -> None:
    snapshots = _snapshots()
    paper = PaperTradingEngine(
        PaperTradingConfig(
            market_id="market-1",
            strategy_name="wide-spread-mean-reversion",
            decision_mode="signals",
            latency_ms=0,
            order_size=Decimal("5"),
        )
    ).run(snapshots=snapshots, trades=[])

    performance = compute_strategy_performance(paper, source="paper")
    fill_quality = compute_fill_quality(paper)
    signal_quality = compute_signal_performance(paper)
    anomalies = detect_evaluation_anomalies(
        paper=performance,
        fill_quality=fill_quality,
        signal_quality=signal_quality,
    )
    report = EvaluationReport(
        report_id="report-1",
        market_id="market-1",
        strategy_name="wide-spread-mean-reversion",
        generated_at=now_utc(),
        period_start=snapshots[0].snapshot_ts,
        period_end=snapshots[-1].snapshot_ts,
        paper_performance=performance,
        backtest_performance=None,
        signal_performance=signal_quality,
        fill_quality=fill_quality,
        comparison={},
        anomalies=anomalies,
    )
    rendered = render_evaluation_report(report)

    assert performance.filled_orders >= 1
    assert fill_quality.fill_rate > Decimal("0")
    assert signal_quality.signal_count >= 1
    assert "Strategy Evaluation Report" in rendered
    assert "[[Backtesting]]" in rendered


def test_backtest_vs_paper_comparison_returns_deltas() -> None:
    snapshots = _snapshots()
    paper = PaperTradingEngine(
        PaperTradingConfig(
            market_id="market-1",
            strategy_name="wide-spread-mean-reversion",
            decision_mode="hybrid",
            latency_ms=0,
            order_size=Decimal("5"),
        ),
        strategy=get_research_strategy("wide-spread-mean-reversion"),
    ).run(snapshots=snapshots, trades=[])
    backtest = BacktestEngine(
        BacktestConfig(
            strategy_name="wide-spread-mean-reversion",
            market_id="market-1",
            latency_ms=0,
            order_size=Decimal("5"),
        )
    ).run(strategy=get_research_strategy("wide-spread-mean-reversion"), snapshots=snapshots)

    comparison = compare_backtest_vs_paper(backtest=backtest, paper=paper)

    assert comparison["market_id"] == "market-1"
    assert "net_pnl_delta" in comparison


def _snapshots():
    base = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        normalize_orderbook(
            {
                "market": "market-1",
                "asset_id": "asset-1",
                "timestamp": (base + timedelta(seconds=index)).isoformat(),
                "bids": [{"price": "0.50", "size": "100"}],
                "asks": [{"price": "0.52", "size": "10"}],
            }
        )
        for index in range(3)
    ]
