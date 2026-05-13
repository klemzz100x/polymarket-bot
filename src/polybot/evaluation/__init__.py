"""Evaluation layer for paper trading, signal quality, and backtest comparison."""

from polybot.evaluation.anomaly_detection import detect_evaluation_anomalies
from polybot.evaluation.fill_quality import compute_fill_quality
from polybot.evaluation.models import (
    DrawdownMetrics,
    EvaluationAnomaly,
    EvaluationReport,
    FillQualityMetrics,
    LatencyMetrics,
    SignalPerformance,
    StrategyPerformance,
)
from polybot.evaluation.paper_vs_backtest import compare_backtest_vs_paper
from polybot.evaluation.performance import compute_strategy_performance
from polybot.evaluation.signal_quality import compute_signal_performance

__all__ = [
    "DrawdownMetrics",
    "EvaluationAnomaly",
    "EvaluationReport",
    "FillQualityMetrics",
    "LatencyMetrics",
    "SignalPerformance",
    "StrategyPerformance",
    "compare_backtest_vs_paper",
    "compute_fill_quality",
    "compute_signal_performance",
    "compute_strategy_performance",
    "detect_evaluation_anomalies",
]
