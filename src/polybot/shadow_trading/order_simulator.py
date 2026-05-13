from collections.abc import Sequence
from decimal import Decimal

from polybot.data.schemas import OrderBookSnapshot
from polybot.shadow_trading.models import ShadowFill, ShadowOrder


def simulate_shadow_fill(
    order: ShadowOrder,
    future_snapshots: Sequence[OrderBookSnapshot],
    *,
    latency_ms: int,
) -> ShadowFill:
    effective_time = order.created_at.timestamp() + latency_ms / 1000
    snapshot = next(
        (
            item
            for item in future_snapshots
            if item.asset_id == order.asset_id and item.snapshot_ts.timestamp() >= effective_time
        ),
        None,
    )
    if snapshot is None:
        return ShadowFill(
            order_id=order.order_id,
            asset_id=order.asset_id,
            side=order.side,
            requested_size=order.size,
            filled_size=Decimal("0"),
            average_price=None,
            fill_possible=False,
            partial=False,
            slippage_abs=Decimal("0"),
            slippage_pct=None,
            observed_at=order.created_at,
            delay_ms=latency_ms,
            fill_probability=Decimal("0"),
            reason="no_snapshot_after_latency",
        )

    levels = snapshot.asks if order.side == "buy" else snapshot.bids
    reference_price = snapshot.best_ask if order.side == "buy" else snapshot.best_bid
    filled = Decimal("0")
    notional = Decimal("0")
    for level in levels:
        if order.limit_price is not None:
            if order.side == "buy" and level.price > order.limit_price:
                break
            if order.side == "sell" and level.price < order.limit_price:
                break
        take = min(order.size - filled, level.size)
        if take <= 0:
            break
        filled += take
        notional += take * level.price
        if filled >= order.size:
            break

    average_price = notional / filled if filled > 0 else None
    if average_price is None or reference_price is None:
        slippage_abs = Decimal("0")
        slippage_pct = None
    elif order.side == "buy":
        slippage_abs = average_price - reference_price
        slippage_pct = slippage_abs / reference_price if reference_price > 0 else None
    else:
        slippage_abs = reference_price - average_price
        slippage_pct = slippage_abs / reference_price if reference_price > 0 else None

    delay = int((snapshot.snapshot_ts - order.created_at).total_seconds() * 1000)
    return ShadowFill(
        order_id=order.order_id,
        asset_id=order.asset_id,
        side=order.side,
        requested_size=order.size,
        filled_size=filled,
        average_price=average_price,
        fill_possible=filled > 0,
        partial=Decimal("0") < filled < order.size,
        slippage_abs=slippage_abs,
        slippage_pct=slippage_pct,
        observed_at=snapshot.snapshot_ts,
        delay_ms=max(delay, latency_ms),
        fill_probability=filled / order.size if order.size > 0 else Decimal("0"),
        reason="filled" if filled >= order.size else ("partial" if filled > 0 else "not_executable"),
    )
