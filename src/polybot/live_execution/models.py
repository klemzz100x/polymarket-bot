from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import json
from typing import Any

from polybot.live_execution.modes import LiveExecutionMode


@dataclass(frozen=True, slots=True)
class LiveOrder:
    client_order_id: str
    market_id: str
    asset_id: str
    side: str
    size: Decimal
    price: Decimal
    strategy_name: str
    created_at: datetime
    mode: LiveExecutionMode = LiveExecutionMode.DISABLED
    time_in_force: str = "gtc"
    post_only: bool = True
    reduce_only: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def notional_usd(self) -> Decimal:
        return self.size * self.price

    def fingerprint(self) -> str:
        return "|".join(
            [
                self.market_id,
                self.asset_id,
                self.side,
                str(self.size),
                str(self.price),
                self.strategy_name,
            ]
        )

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class LiveFill:
    fill_id: str
    exchange_order_id: str
    client_order_id: str
    market_id: str
    asset_id: str
    side: str
    price: Decimal
    size: Decimal
    fee: Decimal
    filled_at: datetime
    liquidity: str = "unknown"
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class RiskDecision:
    allowed: bool
    reason: str = "ok"
    severity: str = "info"
    checks: dict[str, bool] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class OrderRejection:
    client_order_id: str
    reason: str
    rejected_at: datetime
    source: str = "risk_gate"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    client_order_id: str
    status: str
    generated_at: datetime
    exchange_order_id: str | None = None
    accepted: bool = False
    reason: str = ""
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class PositionExposure:
    market_id: str
    asset_id: str
    strategy_name: str
    quantity: Decimal
    mark_price: Decimal
    exposure_usd: Decimal
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class LivePnL:
    strategy_name: str
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    fees: Decimal
    net_pnl: Decimal
    generated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


def now_utc() -> datetime:
    return datetime.now(UTC)


def to_json(value: Any) -> str:
    return json.dumps(_json_ready(value), indent=2, sort_keys=True)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, LiveExecutionMode):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
