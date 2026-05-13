from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import json
from typing import Any


@dataclass(frozen=True, slots=True)
class WalletBalance:
    asset: str
    total: Decimal
    available: Decimal
    locked: Decimal
    source: str = "exchange"

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class WalletPosition:
    market_id: str
    asset_id: str
    outcome: str | None
    quantity: Decimal
    average_price: Decimal | None
    mark_price: Decimal | None
    exposure_usd: Decimal
    source: str = "exchange"

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class OpenOrderState:
    exchange_order_id: str
    client_order_id: str | None
    market_id: str
    asset_id: str
    side: str
    price: Decimal
    original_size: Decimal
    remaining_size: Decimal
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class WalletSnapshot:
    wallet_address: str
    captured_at: datetime
    balances: list[WalletBalance] = field(default_factory=list)
    positions: list[WalletPosition] = field(default_factory=list)
    open_orders: list[OpenOrderState] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_exposure_usd(self) -> Decimal:
        return sum((position.exposure_usd for position in self.positions), Decimal("0"))

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self) | {"total_exposure_usd": self.total_exposure_usd})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True, slots=True)
class WalletHealthStatus:
    wallet_address: str
    generated_at: datetime
    connected: bool
    status: str
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


def now_utc() -> datetime:
    return datetime.now(UTC)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
