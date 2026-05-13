from collections.abc import Sequence
from decimal import Decimal

from polybot.backtesting.fee_model import FeeModel
from polybot.backtesting.latency_model import LatencyModel
from polybot.backtesting.results import SimulatedFill, SimulatedOrder
from polybot.backtesting.slippage_model import SlippageModel
from polybot.data.schemas import OrderBookSnapshot


class ExecutionSimulator:
    def __init__(
        self,
        *,
        fee_model: FeeModel,
        latency_model: LatencyModel,
        slippage_model: SlippageModel | None = None,
    ) -> None:
        self.fee_model = fee_model
        self.latency_model = latency_model
        self.slippage_model = slippage_model or SlippageModel()

    def execute(
        self,
        order: SimulatedOrder,
        future_snapshots: Sequence[OrderBookSnapshot],
    ) -> SimulatedFill:
        effective_time = self.latency_model.effective_time(order.created_at)
        snapshot = next(
            (
                item
                for item in future_snapshots
                if item.asset_id == order.asset_id and item.snapshot_ts >= effective_time
            ),
            None,
        )
        if snapshot is None:
            return _empty_fill(order, latency_ms=self.latency_model.latency_ms, reason="no_snapshot_after_latency")

        depth_fill = self.slippage_model.simulate_depth_fill(
            snapshot,
            side=order.side,
            size=order.size,
            limit_price=order.limit_price if order.order_type == "limit" else None,
        )
        if depth_fill.filled_size <= 0 or depth_fill.average_price is None:
            return _empty_fill(order, latency_ms=self.latency_model.latency_ms, reason="not_executable")

        notional = depth_fill.filled_size * depth_fill.average_price
        fees = self.fee_model.calculate(notional)
        return SimulatedFill(
            order_id=order.order_id,
            asset_id=order.asset_id,
            side=order.side,
            requested_size=order.size,
            filled_size=depth_fill.filled_size,
            average_price=depth_fill.average_price,
            fees=fees,
            slippage=depth_fill.slippage,
            filled_at=snapshot.snapshot_ts,
            partial=depth_fill.partial,
            latency_ms=self.latency_model.latency_ms,
            reason="filled",
        )


def _empty_fill(order: SimulatedOrder, *, latency_ms: int, reason: str) -> SimulatedFill:
    return SimulatedFill(
        order_id=order.order_id,
        asset_id=order.asset_id,
        side=order.side,
        requested_size=order.size,
        filled_size=Decimal("0"),
        average_price=None,
        fees=Decimal("0"),
        slippage=Decimal("0"),
        filled_at=order.created_at,
        partial=False,
        latency_ms=latency_ms,
        reason=reason,
    )

