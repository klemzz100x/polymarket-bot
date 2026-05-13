from dataclasses import dataclass

from polybot.execution.engine import OrderRequest


@dataclass(frozen=True, slots=True)
class RiskDecision:
    allowed: bool
    reason: str = ""


class RiskManager:
    def __init__(self, max_order_notional_usd: float) -> None:
        self.max_order_notional_usd = max_order_notional_usd

    def validate_order(self, order: OrderRequest) -> RiskDecision:
        notional = order.price * order.size
        if notional > self.max_order_notional_usd:
            return RiskDecision(False, f"order_notional_exceeds_limit:{notional:.2f}")
        if order.price <= 0 or order.price >= 1:
            return RiskDecision(False, "invalid_probability_price")
        if order.size <= 0:
            return RiskDecision(False, "invalid_size")
        return RiskDecision(True)

