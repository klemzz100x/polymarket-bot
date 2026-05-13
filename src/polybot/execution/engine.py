from dataclasses import dataclass

from polybot.core.compat import StrEnum


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class TimeInForce(StrEnum):
    GTC = "gtc"
    GTD = "gtd"
    FOK = "fok"
    FAK = "fak"


@dataclass(frozen=True, slots=True)
class OrderRequest:
    market_id: str
    outcome_id: str
    side: OrderSide
    price: float
    size: float
    time_in_force: TimeInForce = TimeInForce.GTC
    post_only: bool = True
    strategy_id: str = "manual"


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    accepted: bool
    order_id: str | None = None
    reason: str = ""


class ExecutionEngine:
    def __init__(self, live_trading_enabled: bool = False) -> None:
        self.live_trading_enabled = live_trading_enabled

    async def submit_order(self, order: OrderRequest) -> ExecutionResult:
        if not self.live_trading_enabled:
            return ExecutionResult(accepted=False, reason="live_trading_disabled")
        return ExecutionResult(accepted=False, reason=f"adapter_not_configured:{order.market_id}")

