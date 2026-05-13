from decimal import Decimal

from polybot.backtesting.results import BacktestResult, SimulatedFill
from polybot.evaluation.models import FillQualityMetrics, LatencyMetrics
from polybot.paper_trading.models import PaperTradingResult


def compute_fill_quality(result: BacktestResult | PaperTradingResult) -> FillQualityMetrics:
    fills = _fills(result)
    attempted_orders = _attempted_orders(result)
    filled_orders = len(fills)
    rejected_orders = int(getattr(result, "rejected_orders", 0))
    unfilled_orders = max(attempted_orders - filled_orders - rejected_orders, 0)
    requested_sizes = [fill.requested_size for fill in fills]
    filled_sizes = [fill.filled_size for fill in fills]
    fill_ratios = [
        fill.filled_size / fill.requested_size
        for fill in fills
        if fill.requested_size > 0
    ]
    slippages = [abs(fill.slippage) for fill in fills]

    return FillQualityMetrics(
        attempted_orders=attempted_orders,
        filled_orders=filled_orders,
        rejected_orders=rejected_orders,
        unfilled_orders=unfilled_orders,
        fill_rate=_ratio(Decimal(filled_orders), Decimal(attempted_orders)),
        partial_fill_rate=_ratio(
            Decimal(sum(1 for fill in fills if fill.partial)),
            Decimal(filled_orders),
        ),
        rejection_rate=_ratio(Decimal(rejected_orders), Decimal(attempted_orders)),
        average_requested_size=_average(requested_sizes),
        average_filled_size=_average(filled_sizes),
        average_fill_ratio=_average(fill_ratios),
        average_slippage=_average(slippages),
        max_slippage=max(slippages) if slippages else Decimal("0"),
        fees=Decimal(str(getattr(result, "fees", Decimal("0")))),
        latency=compute_latency_metrics(fills),
        unrealistic_fill_count=count_unrealistic_fills(result),
    )


def compute_latency_metrics(fills: list[SimulatedFill]) -> LatencyMetrics:
    latencies = [Decimal(fill.latency_ms) for fill in fills]
    latency_impact = sum((abs(fill.slippage * fill.filled_size) for fill in fills), Decimal("0"))
    return LatencyMetrics(
        average_latency_ms=_average(latencies),
        max_latency_ms=max((fill.latency_ms for fill in fills), default=0),
        latency_impact=latency_impact,
        fill_count=len(fills),
    )


def count_unrealistic_fills(result: BacktestResult | PaperTradingResult) -> int:
    orders_by_id = {trade.order.order_id: trade.order for trade in result.trades}
    count = 0
    for fill in _fills(result):
        order = orders_by_id.get(fill.order_id)
        if fill.filled_size <= 0:
            continue
        if fill.requested_size <= 0 or fill.filled_size > fill.requested_size:
            count += 1
            continue
        if fill.average_price is None or fill.average_price <= 0 or fill.average_price >= 1:
            count += 1
            continue
        if order and order.limit_price is not None:
            if order.side == "buy" and fill.average_price > order.limit_price or order.side == "sell" and fill.average_price < order.limit_price:
                count += 1
    return count


def _fills(result: BacktestResult | PaperTradingResult) -> list[SimulatedFill]:
    fills = getattr(result, "fills", None)
    if fills is not None:
        return list(fills)
    return [trade.fill for trade in result.trades]


def _attempted_orders(result: BacktestResult | PaperTradingResult) -> int:
    attempted = getattr(result, "attempted_orders", None)
    if attempted is not None:
        return int(attempted)
    metadata = getattr(result, "metadata", {})
    if "attempted_orders" in metadata:
        return int(metadata["attempted_orders"])
    fill_rate = Decimal(str(getattr(result, "fill_rate", Decimal("0"))))
    filled_orders = len(_fills(result))
    if fill_rate > 0:
        return int((Decimal(filled_orders) / fill_rate).to_integral_value())
    return filled_orders


def _average(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal(len(values))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= 0:
        return Decimal("0")
    return numerator / denominator
