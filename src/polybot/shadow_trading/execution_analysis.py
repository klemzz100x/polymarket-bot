from decimal import Decimal

from polybot.shadow_trading.models import (
    ExecutionComparison,
    MarketRealitySnapshot,
    ShadowDecision,
    ShadowFill,
)


def compare_execution(
    *,
    decision: ShadowDecision,
    fill: ShadowFill,
    reality: MarketRealitySnapshot | None,
) -> ExecutionComparison:
    theoretical_price = decision.order.limit_price
    visible_depth = Decimal("0")
    if reality is not None:
        visible_depth = reality.ask_depth if decision.order.side == "buy" else reality.bid_depth

    notes: list[str] = []
    if not fill.fill_possible:
        notes.append("Shadow order was not executable after latency.")
    if fill.partial:
        notes.append("Only partial visible depth was available.")
    if reality and reality.spread_pct and reality.spread_pct > Decimal("0.10"):
        notes.append("Spread was wide at observed execution time.")

    return ExecutionComparison(
        decision_id=decision.decision_id,
        order_id=decision.order.order_id,
        executable=fill.fill_possible,
        theoretical_price=theoretical_price,
        observed_average_price=fill.average_price,
        slippage_abs=fill.slippage_abs,
        slippage_pct=fill.slippage_pct,
        requested_size=fill.requested_size,
        filled_size=fill.filled_size,
        visible_depth=visible_depth,
        delay_ms=fill.delay_ms,
        missed_fill=not fill.fill_possible,
        notes=notes,
    )
