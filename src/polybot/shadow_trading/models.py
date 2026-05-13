from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import json
from typing import Any


@dataclass(frozen=True, slots=True)
class ShadowOrder:
    order_id: str
    market_id: str
    asset_id: str
    side: str
    size: Decimal
    created_at: datetime
    order_type: str = "limit"
    limit_price: Decimal | None = None
    source: str = "shadow"
    signal_type: str | None = None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ShadowFill:
    order_id: str
    asset_id: str
    side: str
    requested_size: Decimal
    filled_size: Decimal
    average_price: Decimal | None
    fill_possible: bool
    partial: bool
    slippage_abs: Decimal
    slippage_pct: Decimal | None
    observed_at: datetime
    delay_ms: int
    fill_probability: Decimal
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ShadowDecision:
    decision_id: str
    market_id: str
    asset_id: str
    timestamp: datetime
    action: str
    order: ShadowOrder
    signal_type: str | None = None
    confidence: Decimal | None = None
    status: str = "created"
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ExecutionComparison:
    decision_id: str
    order_id: str
    executable: bool
    theoretical_price: Decimal | None
    observed_average_price: Decimal | None
    slippage_abs: Decimal
    slippage_pct: Decimal | None
    requested_size: Decimal
    filled_size: Decimal
    visible_depth: Decimal
    delay_ms: int
    missed_fill: bool
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class MarketRealitySnapshot:
    market_id: str
    asset_id: str
    snapshot_ts: datetime
    best_bid: Decimal | None
    best_ask: Decimal | None
    mid_price: Decimal | None
    spread_abs: Decimal | None
    spread_pct: Decimal | None
    bid_depth: Decimal
    ask_depth: Decimal
    total_depth: Decimal
    orderbook_imbalance: Decimal | None
    stale_age_seconds: Decimal | None = None


@dataclass(frozen=True, slots=True)
class ShadowTradingResult:
    run_id: str
    market_id: str
    strategy_name: str
    started_at: datetime
    finished_at: datetime
    snapshot_count: int
    signal_count: int
    decision_count: int
    theoretical_fill_count: int
    missed_fill_count: int
    impossible_fill_count: int
    average_slippage: Decimal
    average_delay_ms: Decimal
    fill_probability: Decimal
    decisions: list[ShadowDecision]
    fills: list[ShadowFill]
    comparisons: list[ExecutionComparison]
    market_snapshots: list[MarketRealitySnapshot]
    anomalies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        if self.impossible_fill_count > 0 or any("critical" in item.lower() for item in self.anomalies):
            return "warning"
        return "ok"

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def now_utc() -> datetime:
    return datetime.now(UTC)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
