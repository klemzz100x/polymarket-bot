from dataclasses import dataclass
from decimal import Decimal

from polybot.backtesting.portfolio import PortfolioState
from polybot.backtesting.results import SimulatedOrder
from polybot.paper_trading.models import PaperTradingConfig


@dataclass(frozen=True, slots=True)
class PaperRiskDecision:
    allowed: bool
    reason: str = ""


class PaperRiskManager:
    def __init__(self, config: PaperTradingConfig) -> None:
        self.config = config

    def validate_order(self, order: SimulatedOrder, portfolio: PortfolioState) -> PaperRiskDecision:
        if order.size <= 0:
            return PaperRiskDecision(False, "invalid_size")
        if order.limit_price is not None and (order.limit_price <= 0 or order.limit_price >= 1):
            return PaperRiskDecision(False, "invalid_limit_price")
        position = portfolio.position_for(order.asset_id)
        if order.side == "buy" and position.quantity + order.size > self.config.max_position:
            return PaperRiskDecision(False, "max_position_exceeded")
        if order.side == "sell" and position.quantity <= 0:
            return PaperRiskDecision(False, "no_position_to_sell")
        projected_exposure = portfolio.current_exposure()
        if order.side == "buy":
            estimated_price = order.limit_price or Decimal("1")
            projected_exposure += order.size * estimated_price
        if projected_exposure > self.config.max_market_exposure:
            return PaperRiskDecision(False, "max_market_exposure_exceeded")
        return PaperRiskDecision(True)

