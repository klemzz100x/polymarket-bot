from dataclasses import asdict, dataclass
from datetime import datetime
from polybot.core.compat import UTC
from decimal import Decimal
import json
from typing import Any

from polybot.data.schemas import OrderBookSnapshot, Trade
from polybot.research.signals import ResearchSignal, detect_research_signals


@dataclass(frozen=True, slots=True)
class InefficiencyScanReport:
    market_id: str
    generated_at: datetime
    snapshot_count: int
    trade_count: int
    signal_count: int
    signals: list[ResearchSignal]

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def scan_inefficiencies(
    *,
    market_id: str,
    snapshots: list[OrderBookSnapshot],
    trades: list[Trade],
) -> InefficiencyScanReport:
    signals = detect_research_signals(market_id=market_id, snapshots=snapshots, trades=trades)
    return InefficiencyScanReport(
        market_id=market_id,
        generated_at=datetime.now(UTC),
        snapshot_count=len(snapshots),
        trade_count=len(trades),
        signal_count=len(signals),
        signals=signals,
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
