from decimal import Decimal

from polybot.data.schemas import OrderBookSnapshot, PriceTick, Trade
from polybot.data.validation.anomaly_checks import (
    check_collection_latency,
    check_data_gaps,
    check_empty_orderbooks,
    check_invalid_price_levels,
    check_negative_or_zero_trade_volume,
    check_timestamp_ordering,
    check_trade_price_tick_coherence,
)
from polybot.data.validation.data_quality_report import (
    DataQualityReport,
    QualityIssue,
    now_report_time,
)
from polybot.research.metrics import update_frequency_per_minute


def validate_market_dataset(
    *,
    market_id: str,
    snapshots: list[OrderBookSnapshot],
    trades: list[Trade],
    price_ticks: list[PriceTick],
    expected_interval_seconds: int = 5,
) -> DataQualityReport:
    issues: list[QualityIssue] = []
    if not snapshots:
        issues.append(
            QualityIssue(
                check_name="missing_snapshots",
                severity="critical",
                message="No orderbook snapshots found for market and period.",
            )
        )
    if not trades:
        issues.append(
            QualityIssue(
                check_name="missing_trades",
                severity="warning",
                message="No public trades found for market and period.",
            )
        )
    if not price_ticks:
        issues.append(
            QualityIssue(
                check_name="missing_price_ticks",
                severity="warning",
                message="No price ticks found for market and period.",
            )
        )

    issues.extend(check_empty_orderbooks(snapshots))
    issues.extend(check_invalid_price_levels(snapshots))
    issues.extend(check_negative_or_zero_trade_volume(trades))
    issues.extend(check_timestamp_ordering(snapshots))
    issues.extend(check_data_gaps(snapshots, expected_interval_seconds=expected_interval_seconds))
    latency_issues, max_latency = check_collection_latency(snapshots)
    issues.extend(latency_issues)
    issues.extend(check_trade_price_tick_coherence(trades, price_ticks))

    timestamps = [snapshot.snapshot_ts for snapshot in snapshots]
    return DataQualityReport(
        market_id=market_id,
        start=min(timestamps) if timestamps else None,
        end=max(timestamps) if timestamps else None,
        generated_at=now_report_time(),
        snapshot_count=len(snapshots),
        trade_count=len(trades),
        price_tick_count=len(price_ticks),
        issues=issues,
        observed_update_frequency_per_minute=(
            update_frequency_per_minute(snapshots) if snapshots else None
        ),
        max_collection_latency_seconds=max_latency,
    )


def quality_score(report: DataQualityReport) -> Decimal:
    score = Decimal("100")
    for issue in report.issues:
        if issue.severity == "critical":
            score -= Decimal("20")
        elif issue.severity == "warning":
            score -= Decimal("5")
    return max(score, Decimal("0"))

