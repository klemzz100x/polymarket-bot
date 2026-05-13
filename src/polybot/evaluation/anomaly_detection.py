from decimal import Decimal

from polybot.evaluation.models import (
    EvaluationAnomaly,
    FillQualityMetrics,
    SignalPerformance,
    StrategyPerformance,
)


def detect_evaluation_anomalies(
    *,
    paper: StrategyPerformance | None,
    backtest: StrategyPerformance | None = None,
    fill_quality: FillQualityMetrics | None = None,
    signal_quality: SignalPerformance | None = None,
) -> list[EvaluationAnomaly]:
    anomalies: list[EvaluationAnomaly] = []
    if fill_quality:
        anomalies.extend(_fill_anomalies(fill_quality))
    if signal_quality:
        anomalies.extend(_signal_anomalies(signal_quality))
    if paper:
        anomalies.extend(_paper_anomalies(paper))
    if paper and backtest:
        anomalies.extend(_comparison_anomalies(paper=paper, backtest=backtest))
    return anomalies


def _fill_anomalies(fill_quality: FillQualityMetrics) -> list[EvaluationAnomaly]:
    anomalies: list[EvaluationAnomaly] = []
    if fill_quality.unrealistic_fill_count > 0:
        anomalies.append(
            EvaluationAnomaly(
                anomaly_type="unrealistic_fills",
                severity="critical",
                description="Filled orders violate size, price, or limit-price constraints.",
                evidence={"unrealistic_fill_count": fill_quality.unrealistic_fill_count},
                next_action="Inspect fills before trusting PnL or signal quality.",
            )
        )
    if fill_quality.fill_rate < Decimal("0.30") and fill_quality.attempted_orders >= 5:
        anomalies.append(
            EvaluationAnomaly(
                anomaly_type="low_fill_rate",
                severity="warning",
                description="Paper trading fill rate is low for the tested period.",
                evidence={"fill_rate": str(fill_quality.fill_rate)},
                next_action="Review order size, limit prices, market depth, and latency assumptions.",
            )
        )
    if fill_quality.average_slippage > Decimal("0.03"):
        anomalies.append(
            EvaluationAnomaly(
                anomaly_type="high_slippage",
                severity="warning",
                description="Average slippage is high relative to Polymarket probability prices.",
                evidence={"average_slippage": str(fill_quality.average_slippage)},
                next_action="Lower order size or restrict strategy to deeper markets.",
            )
        )
    if fill_quality.rejection_rate > Decimal("0.25"):
        anomalies.append(
            EvaluationAnomaly(
                anomaly_type="high_rejection_rate",
                severity="warning",
                description="Risk or portfolio constraints rejected a large share of paper orders.",
                evidence={"rejection_rate": str(fill_quality.rejection_rate)},
                next_action="Inspect risk limits and repeated signal behavior.",
            )
        )
    return anomalies


def _signal_anomalies(signal_quality: SignalPerformance) -> list[EvaluationAnomaly]:
    anomalies: list[EvaluationAnomaly] = []
    if signal_quality.signal_count == 0:
        anomalies.append(
            EvaluationAnomaly(
                anomaly_type="no_signals",
                severity="warning",
                description="No research signals were emitted for the period.",
                next_action="Confirm the market period has enough snapshots and activity.",
            )
        )
    elif signal_quality.signal_hit_rate < Decimal("0.10") and signal_quality.signal_count >= 10:
        anomalies.append(
            EvaluationAnomaly(
                anomaly_type="weak_signal_hit_rate",
                severity="warning",
                description="Signals rarely translated into filled paper orders.",
                evidence={"signal_hit_rate": str(signal_quality.signal_hit_rate)},
                next_action="Review signal thresholds and execution assumptions.",
            )
        )
    if signal_quality.average_signal_confidence < Decimal("0.35") and signal_quality.signal_count > 0:
        anomalies.append(
            EvaluationAnomaly(
                anomaly_type="low_signal_confidence",
                severity="warning",
                description="Average signal confidence is weak.",
                evidence={"average_confidence": str(signal_quality.average_signal_confidence)},
                next_action="Treat results as exploratory only.",
            )
        )
    return anomalies


def _paper_anomalies(paper: StrategyPerformance) -> list[EvaluationAnomaly]:
    anomalies: list[EvaluationAnomaly] = []
    if paper.drawdown.max_drawdown > Decimal("0.20"):
        anomalies.append(
            EvaluationAnomaly(
                anomaly_type="high_drawdown",
                severity="warning",
                description="Paper trading drawdown is high for a research-only strategy.",
                evidence={"max_drawdown": str(paper.drawdown.max_drawdown)},
                next_action="Reduce sizing or investigate adverse market regimes.",
            )
        )
    if paper.profit_factor is not None and paper.profit_factor < Decimal("1"):
        anomalies.append(
            EvaluationAnomaly(
                anomaly_type="negative_profit_factor",
                severity="warning",
                description="Losses exceed wins in the paper-trading sample.",
                evidence={"profit_factor": str(paper.profit_factor)},
                next_action="Do not promote the signal without broader validation.",
            )
        )
    return anomalies


def _comparison_anomalies(
    *,
    paper: StrategyPerformance,
    backtest: StrategyPerformance,
) -> list[EvaluationAnomaly]:
    anomalies: list[EvaluationAnomaly] = []
    pnl_gap = backtest.net_pnl - paper.net_pnl
    fill_rate_gap = backtest.fill_rate - paper.fill_rate
    if pnl_gap > Decimal("10") and backtest.net_pnl > 0:
        anomalies.append(
            EvaluationAnomaly(
                anomaly_type="backtest_too_optimistic",
                severity="warning",
                description="Backtest materially outperforms paper trading on the same setup.",
                evidence={"net_pnl_delta": str(pnl_gap)},
                next_action="Review latency, fill, queue-position, and stale-data assumptions.",
            )
        )
    if fill_rate_gap > Decimal("0.25"):
        anomalies.append(
            EvaluationAnomaly(
                anomaly_type="fill_rate_gap",
                severity="warning",
                description="Backtest fill rate is materially higher than paper-trading fill rate.",
                evidence={"fill_rate_delta": str(fill_rate_gap)},
                next_action="Tighten the execution simulator before interpreting backtest PnL.",
            )
        )
    if paper.average_slippage - backtest.average_slippage > Decimal("0.02"):
        anomalies.append(
            EvaluationAnomaly(
                anomaly_type="paper_slippage_gap",
                severity="warning",
                description="Paper-trading slippage is materially worse than backtest slippage.",
                evidence={
                    "paper_average_slippage": str(paper.average_slippage),
                    "backtest_average_slippage": str(backtest.average_slippage),
                },
                next_action="Review order size and depth assumptions.",
            )
        )
    return anomalies
