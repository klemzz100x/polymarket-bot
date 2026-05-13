from dataclasses import dataclass, field
from decimal import Decimal

from polybot.backtesting.results import SimulatedFill


@dataclass(slots=True)
class Position:
    asset_id: str
    quantity: Decimal = Decimal("0")
    average_cost: Decimal = Decimal("0")

    @property
    def exposure(self) -> Decimal:
        return abs(self.quantity * self.average_cost)


@dataclass(slots=True)
class PortfolioState:
    cash: Decimal
    positions: dict[str, Position] = field(default_factory=dict)
    realized_pnl: Decimal = Decimal("0")
    fees_paid: Decimal = Decimal("0")
    equity_curve: list[Decimal] = field(default_factory=list)
    exposure_curve: list[Decimal] = field(default_factory=list)

    def position_for(self, asset_id: str) -> Position:
        if asset_id not in self.positions:
            self.positions[asset_id] = Position(asset_id=asset_id)
        return self.positions[asset_id]

    def apply_fill(self, fill: SimulatedFill) -> Decimal:
        if fill.filled_size <= 0 or fill.average_price is None:
            return Decimal("0")
        position = self.position_for(fill.asset_id)
        notional = fill.filled_size * fill.average_price
        pnl = Decimal("0")

        if fill.side == "buy":
            new_quantity = position.quantity + fill.filled_size
            if new_quantity > 0:
                position.average_cost = (
                    (position.quantity * position.average_cost) + notional
                ) / new_quantity
            position.quantity = new_quantity
            self.cash -= notional + fill.fees
        else:
            sell_size = min(fill.filled_size, position.quantity)
            pnl = sell_size * (fill.average_price - position.average_cost)
            position.quantity -= sell_size
            if position.quantity == 0:
                position.average_cost = Decimal("0")
            self.cash += notional - fill.fees
            self.realized_pnl += pnl

        self.fees_paid += fill.fees
        return pnl

    def current_exposure(self) -> Decimal:
        return sum((position.exposure for position in self.positions.values()), Decimal("0"))

    def mark(self, mark_prices: dict[str, Decimal]) -> Decimal:
        holdings_value = Decimal("0")
        for asset_id, position in self.positions.items():
            mark = mark_prices.get(asset_id, position.average_cost)
            holdings_value += position.quantity * mark
        equity = self.cash + holdings_value
        self.equity_curve.append(equity)
        self.exposure_curve.append(self.current_exposure())
        return equity
