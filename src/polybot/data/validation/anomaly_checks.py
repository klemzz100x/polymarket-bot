from datetime import datetime
from decimal import Decimal

from polybot.data.schemas import OrderBookSnapshot, PriceTick, Trade
from polybot.data.validation.data_quality_report import QualityIssue


def check_empty_orderbooks(snapshots: list[OrderBookSnapshot]) -> list[QualityIssue]:
    return [
        QualityIssue(
            check_name="empty_orderbook",
            severity="critical",
            message="Orderbook snapshot has no bid or ask levels.",
            timestamp=snapshot.snapshot_ts,
            asset_id=snapshot.asset_id,
        )
        for snapshot in snapshots
        if not snapshot.bids or not snapshot.asks
    ]


def check_invalid_price_levels(snapshots: list[OrderBookSnapshot]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for snapshot in snapshots:
        for level in [*snapshot.bids, *snapshot.asks]:
            if level.price <= 0 or level.price >= 1:
                issues.append(
                    QualityIssue(
                        check_name="invalid_price_level",
                        severity="critical",
                        message="Orderbook level price is outside the probability range.",
                        timestamp=snapshot.snapshot_ts,
                        asset_id=snapshot.asset_id,
                        details={"price": str(level.price), "side": level.side.value},
                    )
                )
            if level.size <= 0:
                issues.append(
                    QualityIssue(
                        check_name="invalid_level_size",
                        severity="critical",
                        message="Orderbook level size is zero or negative.",
                        timestamp=snapshot.snapshot_ts,
                        asset_id=snapshot.asset_id,
                        details={"size": str(level.size), "side": level.side.value},
                    )
                )
    return issues


def check_negative_or_zero_trade_volume(trades: list[Trade]) -> list[QualityIssue]:
    return [
        QualityIssue(
            check_name="invalid_trade_volume",
            severity="critical",
            message="Trade has zero or negative size.",
            timestamp=trade.traded_at,
            asset_id=trade.asset_id,
            details={"trade_id": trade.trade_id, "size": str(trade.size)},
        )
        for trade in trades
        if trade.size <= 0
    ]


def check_timestamp_ordering(snapshots: list[OrderBookSnapshot]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    ordered = sorted(snapshots, key=lambda snapshot: (snapshot.asset_id, snapshot.snapshot_ts))
    previous_by_asset: dict[str, datetime] = {}
    for snapshot in ordered:
        previous = previous_by_asset.get(snapshot.asset_id)
        if previous and snapshot.snapshot_ts < previous:
            issues.append(
                QualityIssue(
                    check_name="timestamp_regression",
                    severity="critical",
                    message="Snapshot timestamp regressed for asset.",
                    timestamp=snapshot.snapshot_ts,
                    asset_id=snapshot.asset_id,
                )
            )
        previous_by_asset[snapshot.asset_id] = snapshot.snapshot_ts
    return issues


def check_data_gaps(
    snapshots: list[OrderBookSnapshot],
    expected_interval_seconds: int,
    gap_multiplier: int = 3,
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    by_asset: dict[str, list[OrderBookSnapshot]] = {}
    for snapshot in snapshots:
        by_asset.setdefault(snapshot.asset_id, []).append(snapshot)
    threshold = Decimal(expected_interval_seconds * gap_multiplier)
    for asset_id, asset_snapshots in by_asset.items():
        ordered = sorted(asset_snapshots, key=lambda snapshot: snapshot.snapshot_ts)
        for previous, current in zip(ordered, ordered[1:], strict=False):
            gap = Decimal(str((current.snapshot_ts - previous.snapshot_ts).total_seconds()))
            if gap > threshold:
                issues.append(
                    QualityIssue(
                        check_name="snapshot_gap",
                        severity="warning",
                        message="Gap between snapshots exceeds expected interval threshold.",
                        timestamp=current.snapshot_ts,
                        asset_id=asset_id,
                        details={"gap_seconds": str(gap), "threshold_seconds": str(threshold)},
                    )
                )
    return issues


def check_collection_latency(
    snapshots: list[OrderBookSnapshot],
    warning_seconds: int = 10,
) -> tuple[list[QualityIssue], Decimal | None]:
    issues: list[QualityIssue] = []
    max_latency: Decimal | None = None
    for snapshot in snapshots:
        latency = Decimal(str((snapshot.received_at - snapshot.snapshot_ts).total_seconds()))
        max_latency = latency if max_latency is None else max(max_latency, latency)
        if latency > Decimal(warning_seconds):
            issues.append(
                QualityIssue(
                    check_name="collection_latency",
                    severity="warning",
                    message="Collection latency exceeded threshold.",
                    timestamp=snapshot.snapshot_ts,
                    asset_id=snapshot.asset_id,
                    details={"latency_seconds": str(latency), "threshold_seconds": warning_seconds},
                )
            )
    return issues, max_latency


def check_trade_price_tick_coherence(
    trades: list[Trade],
    ticks: list[PriceTick],
    tolerance: Decimal = Decimal("0.10"),
) -> list[QualityIssue]:
    if not trades or not ticks:
        return []
    ticks_by_asset: dict[str, list[PriceTick]] = {}
    for tick in ticks:
        ticks_by_asset.setdefault(tick.asset_id, []).append(tick)

    issues: list[QualityIssue] = []
    for trade in trades:
        if not trade.asset_id:
            continue
        candidates = ticks_by_asset.get(trade.asset_id, [])
        if not candidates:
            continue
        nearest = min(candidates, key=lambda tick: abs((tick.ts - trade.traded_at).total_seconds()))
        diff = abs(nearest.price - trade.price)
        if diff > tolerance:
            issues.append(
                QualityIssue(
                    check_name="trade_tick_price_mismatch",
                    severity="warning",
                    message="Nearest price tick differs materially from trade price.",
                    timestamp=trade.traded_at,
                    asset_id=trade.asset_id,
                    details={
                        "trade_id": trade.trade_id,
                        "trade_price": str(trade.price),
                        "tick_price": str(nearest.price),
                        "diff": str(diff),
                    },
                )
            )
    return issues

