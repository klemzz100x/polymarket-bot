from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import json
from typing import Any


@dataclass(frozen=True, slots=True)
class DrawdownMetrics:
    max_drawdown: Decimal
    max_drawdown_abs: Decimal
    peak_equity: Decimal
    trough_equity: Decimal
    recovery_equity: Decimal | None = None

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class LatencyMetrics:
    average_latency_ms: Decimal
    max_latency_ms: int
    latency_impact: Decimal
    fill_count: int

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class FillQualityMetrics:
    attempted_orders: int
    filled_orders: int
    rejected_orders: int
    unfilled_orders: int
    fill_rate: Decimal
    partial_fill_rate: Decimal
    rejection_rate: Decimal
    average_requested_size: Decimal
    average_filled_size: Decimal
    average_fill_ratio: Decimal
    average_slippage: Decimal
    max_slippage: Decimal
    fees: Decimal
    latency: LatencyMetrics
    unrealistic_fill_count: int

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class StrategyPerformance:
    strategy_name: str
    market_id: str
    source: str
    gross_pnl: Decimal
    net_pnl: Decimal
    trade_count: int
    attempted_orders: int
    filled_orders: int
    rejected_trades: int
    win_rate: Decimal
    average_win: Decimal
    average_loss: Decimal
    average_exposure: Decimal
    max_exposure: Decimal
    fill_rate: Decimal
    partial_fill_rate: Decimal
    average_slippage: Decimal
    fees: Decimal
    latency_impact: Decimal
    signal_hit_rate: Decimal | None
    profit_factor: Decimal | None
    drawdown: DrawdownMetrics

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class SignalPerformance:
    market_id: str
    strategy_name: str
    signal_count: int
    orders_from_signals: int
    fills_from_signals: int
    signal_to_order_rate: Decimal
    signal_hit_rate: Decimal
    average_signal_confidence: Decimal
    signals_by_type: dict[str, int] = field(default_factory=dict)
    fills_by_signal_type: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class EvaluationAnomaly:
    anomaly_type: str
    severity: str
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)
    next_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    report_id: str
    market_id: str
    strategy_name: str
    generated_at: datetime
    period_start: datetime | None
    period_end: datetime | None
    paper_performance: StrategyPerformance | None
    backtest_performance: StrategyPerformance | None
    signal_performance: SignalPerformance | None
    fill_quality: FillQualityMetrics | None
    comparison: dict[str, Any]
    anomalies: list[EvaluationAnomaly]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        if any(item.severity == "critical" for item in self.anomalies):
            return "critical"
        if any(item.severity == "warning" for item in self.anomalies):
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
