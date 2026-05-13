from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
import json
from typing import Any


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    strategy_name: str
    market_id: str
    initial_cash: Decimal = Decimal("1000")
    order_size: Decimal = Decimal("10")
    max_position: Decimal = Decimal("100")
    max_market_exposure: Decimal = Decimal("250")
    fee_bps: Decimal = Decimal("0")
    latency_ms: int = 500


@dataclass(frozen=True, slots=True)
class SimulatedOrder:
    order_id: str
    market_id: str
    asset_id: str
    side: str
    size: Decimal
    created_at: datetime
    order_type: str = "limit"
    limit_price: Decimal | None = None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class SimulatedFill:
    order_id: str
    asset_id: str
    side: str
    requested_size: Decimal
    filled_size: Decimal
    average_price: Decimal | None
    fees: Decimal
    slippage: Decimal
    filled_at: datetime
    partial: bool
    latency_ms: int
    reason: str = ""


@dataclass(frozen=True, slots=True)
class BacktestTrade:
    order: SimulatedOrder
    fill: SimulatedFill
    gross_pnl: Decimal = Decimal("0")
    net_pnl: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class BacktestResult:
    strategy_id: str
    market_id: str
    trades: list[BacktestTrade]
    gross_pnl: Decimal
    net_pnl: Decimal
    trade_count: int
    win_rate: Decimal
    average_win: Decimal
    average_loss: Decimal
    max_drawdown: Decimal
    average_exposure: Decimal
    max_exposure: Decimal
    fill_rate: Decimal
    partial_fill_rate: Decimal
    average_slippage: Decimal
    fees: Decimal
    latency_impact: Decimal
    sharpe_approx: Decimal | None
    profit_factor: Decimal | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value

