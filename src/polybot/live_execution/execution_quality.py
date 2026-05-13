from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from polybot.live_execution.models import LiveFill, LiveOrder, now_utc
from polybot.shadow_trading.models import ShadowFill


@dataclass(frozen=True, slots=True)
class LiveExecutionQualityReport:
    generated_at: datetime
    order_count: int
    fill_count: int
    fill_ratio: Decimal
    cancel_ratio: Decimal
    rejected_ratio: Decimal
    average_slippage: Decimal
    average_fill_delay_ms: Decimal
    average_order_latency_ms: Decimal
    paper_shadow_live_gap: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            key: str(value) if isinstance(value, Decimal) else value
            for key, value in asdict(self).items()
        }


def compute_live_execution_quality(
    *,
    orders: list[LiveOrder],
    fills: list[LiveFill],
    shadow_fills: list[ShadowFill] | None = None,
    cancelled_count: int = 0,
    rejected_count: int = 0,
    order_latency_ms: list[Decimal] | None = None,
) -> LiveExecutionQualityReport:
    order_count = len(orders)
    fill_count = len(fills)
    fill_ratio = _ratio(fill_count, order_count)
    average_slippage = _average_live_slippage(orders=orders, fills=fills)
    shadow_average = _average_shadow_slippage(shadow_fills or [])
    return LiveExecutionQualityReport(
        generated_at=now_utc(),
        order_count=order_count,
        fill_count=fill_count,
        fill_ratio=fill_ratio,
        cancel_ratio=_ratio(cancelled_count, order_count),
        rejected_ratio=_ratio(rejected_count, order_count + rejected_count),
        average_slippage=average_slippage,
        average_fill_delay_ms=_average_fill_delay_ms(orders=orders, fills=fills),
        average_order_latency_ms=_average(order_latency_ms or []),
        paper_shadow_live_gap={
            "shadow_average_slippage": str(shadow_average),
            "live_minus_shadow_slippage": str(average_slippage - shadow_average),
        },
    )


def _average_live_slippage(*, orders: list[LiveOrder], fills: list[LiveFill]) -> Decimal:
    orders_by_id = {order.client_order_id: order for order in orders}
    values: list[Decimal] = []
    for fill in fills:
        order = orders_by_id.get(fill.client_order_id)
        if order is None:
            continue
        if order.side == "buy":
            values.append(fill.price - order.price)
        else:
            values.append(order.price - fill.price)
    return _average([abs(item) for item in values])


def _average_shadow_slippage(fills: list[ShadowFill]) -> Decimal:
    return _average([abs(fill.slippage_abs) for fill in fills])


def _average_fill_delay_ms(*, orders: list[LiveOrder], fills: list[LiveFill]) -> Decimal:
    orders_by_id = {order.client_order_id: order for order in orders}
    delays: list[Decimal] = []
    for fill in fills:
        order = orders_by_id.get(fill.client_order_id)
        if order is not None:
            delays.append(Decimal(str((fill.filled_at - order.created_at).total_seconds() * 1000)))
    return _average(delays)


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator <= 0:
        return Decimal("0")
    return Decimal(numerator) / Decimal(denominator)


def _average(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal(len(values))
