from dataclasses import dataclass
from decimal import Decimal

from polybot.data.schemas import OrderBookLevel, OrderBookSnapshot


@dataclass(frozen=True, slots=True)
class DepthFill:
    requested_size: Decimal
    filled_size: Decimal
    average_price: Decimal | None
    worst_price: Decimal | None
    slippage: Decimal
    partial: bool


class SlippageModel:
    def simulate_depth_fill(
        self,
        snapshot: OrderBookSnapshot,
        *,
        side: str,
        size: Decimal,
        limit_price: Decimal | None,
    ) -> DepthFill:
        levels = snapshot.asks if side == "buy" else snapshot.bids
        executable = [
            level
            for level in levels
            if _is_executable(side=side, level=level, limit_price=limit_price)
        ]
        filled = Decimal("0")
        notional = Decimal("0")
        worst_price: Decimal | None = None
        reference = executable[0].price if executable else None

        for level in executable:
            take = min(size - filled, level.size)
            if take <= 0:
                break
            filled += take
            notional += take * level.price
            worst_price = level.price
            if filled >= size:
                break

        average_price = notional / filled if filled > 0 else None
        slippage = Decimal("0")
        if average_price is not None and reference is not None:
            slippage = average_price - reference if side == "buy" else reference - average_price

        return DepthFill(
            requested_size=size,
            filled_size=filled,
            average_price=average_price,
            worst_price=worst_price,
            slippage=slippage,
            partial=Decimal("0") < filled < size,
        )


def _is_executable(side: str, level: OrderBookLevel, limit_price: Decimal | None) -> bool:
    if limit_price is None:
        return True
    if side == "buy":
        return level.price <= limit_price
    return level.price >= limit_price

