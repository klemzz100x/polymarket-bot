from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from polybot.core.compat import UTC
from decimal import Decimal
import json
from typing import Any

from polybot.backtesting.results import BacktestTrade, SimulatedFill, SimulatedOrder
from polybot.research.signals import ResearchSignal


@dataclass(frozen=True, slots=True)
class PaperTradingConfig:
    market_id: str
    strategy_name: str = "wide-spread-mean-reversion"
    run_id: str | None = None
    initial_cash: Decimal = Decimal("1000")
    order_size: Decimal = Decimal("10")
    max_position: Decimal = Decimal("100")
    max_market_exposure: Decimal = Decimal("250")
    fee_bps: Decimal = Decimal("0")
    latency_ms: int = 500
    signal_window: int = 20
    decision_mode: str = "hybrid"
    ledger_path: str | None = None


@dataclass(frozen=True, slots=True)
class PaperTradingEvent:
    run_id: str
    event_type: str
    timestamp: datetime
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass(frozen=True, slots=True)
class PaperTradingResult:
    run_id: str
    market_id: str
    strategy_name: str
    started_at: datetime
    finished_at: datetime
    snapshot_count: int
    signal_count: int
    attempted_orders: int
    filled_orders: int
    rejected_orders: int
    fills: list[SimulatedFill]
    trades: list[BacktestTrade]
    signals: list[ResearchSignal]
    events: list[PaperTradingEvent]
    final_cash: Decimal
    final_equity: Decimal
    net_pnl: Decimal
    fees: Decimal
    max_exposure: Decimal
    fill_rate: Decimal
    partial_fill_rate: Decimal
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True, slots=True)
class PaperTradingOrderDecision:
    order: SimulatedOrder
    source: str
    signal_type: str | None = None
    reason: str = ""


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
