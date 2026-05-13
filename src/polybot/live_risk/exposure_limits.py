from decimal import Decimal

from polybot.live_execution.models import LiveOrder, PositionExposure
from polybot.live_risk.live_constraints import LiveRiskConstraints


def projected_total_exposure(
    *,
    current: list[PositionExposure],
    order: LiveOrder,
) -> Decimal:
    return sum((item.exposure_usd for item in current), Decimal("0")) + order.notional_usd


def projected_strategy_exposure(
    *,
    current: list[PositionExposure],
    order: LiveOrder,
) -> Decimal:
    return (
        sum(
            (
                item.exposure_usd
                for item in current
                if item.strategy_name == order.strategy_name
            ),
            Decimal("0"),
        )
        + order.notional_usd
    )


def exposure_checks(
    *,
    current: list[PositionExposure],
    order: LiveOrder,
    constraints: LiveRiskConstraints,
) -> dict[str, bool]:
    return {
        "max_exposure": projected_total_exposure(current=current, order=order)
        <= constraints.max_exposure_usd,
        "max_strategy_exposure": projected_strategy_exposure(current=current, order=order)
        <= constraints.max_strategy_exposure_usd,
        "max_open_positions": len({item.asset_id for item in current if item.quantity != 0})
        <= constraints.max_open_positions,
    }
