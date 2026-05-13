from decimal import Decimal

from polybot.evaluation.models import SignalPerformance
from polybot.paper_trading.models import PaperTradingResult


def compute_signal_performance(result: PaperTradingResult) -> SignalPerformance:
    signals_by_type: dict[str, int] = {}
    confidence_total = Decimal("0")
    for signal in result.signals:
        signals_by_type[signal.signal_type] = signals_by_type.get(signal.signal_type, 0) + 1
        confidence_total += signal.confidence

    signal_order_ids: dict[str, str] = {}
    for event in result.events:
        if event.event_type != "paper_order_created":
            continue
        if event.payload.get("source") != "signal_policy":
            continue
        order = event.payload.get("order")
        order_id = getattr(order, "order_id", None)
        signal_type = str(event.payload.get("signal_type") or "unknown")
        if order_id:
            signal_order_ids[str(order_id)] = signal_type

    fills_by_signal_type: dict[str, int] = {}
    for fill in result.fills:
        signal_type = signal_order_ids.get(fill.order_id)
        if not signal_type:
            continue
        fills_by_signal_type[signal_type] = fills_by_signal_type.get(signal_type, 0) + 1

    signal_count = result.signal_count
    orders_from_signals = len(signal_order_ids)
    fills_from_signals = sum(fills_by_signal_type.values())
    return SignalPerformance(
        market_id=result.market_id,
        strategy_name=result.strategy_name,
        signal_count=signal_count,
        orders_from_signals=orders_from_signals,
        fills_from_signals=fills_from_signals,
        signal_to_order_rate=_ratio(Decimal(orders_from_signals), Decimal(signal_count)),
        signal_hit_rate=_ratio(Decimal(fills_from_signals), Decimal(signal_count)),
        average_signal_confidence=_ratio(confidence_total, Decimal(signal_count)),
        signals_by_type=signals_by_type,
        fills_by_signal_type=fills_by_signal_type,
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= 0:
        return Decimal("0")
    return numerator / denominator
