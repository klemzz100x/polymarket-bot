from dataclasses import asdict, dataclass, field
from datetime import datetime
from polybot.core.compat import UTC
from enum import Enum
from typing import Any

from polybot.core.compat import StrEnum

from polybot.resources.cleaners import slugify


class EdgeFamily(StrEnum):
    SPREAD_CAPTURE = "spread_capture"
    MARKET_MAKING = "market_making"
    ORDERBOOK_IMBALANCE = "orderbook_imbalance"
    LIQUIDITY_VACUUM = "liquidity_vacuum"
    STALE_ORDERBOOK = "stale_orderbook"
    DELAYED_REPRICING = "delayed_repricing"
    CROSS_MARKET_ARBITRAGE = "cross_market_arbitrage"
    NEWS_LATENCY = "news_latency"
    EVENT_DRIVEN_REPRICING = "event_driven_repricing"
    BEHAVIORAL_OVERREACTION = "behavioral_overreaction"
    RESOLUTION_EDGE = "resolution_edge"


class CandidateStatus(StrEnum):
    NEW = "new"
    TESTED = "tested"
    REJECTED = "rejected"
    PROMISING = "promising"


@dataclass(frozen=True, slots=True)
class StrategyCandidate:
    name: str
    source_obsidian_path: str
    source_title: str
    summary: str
    hypothesis: str
    edge_family: EdgeFamily
    required_data: list[str]
    metrics_to_measure: list[str]
    testable_signal: str
    backtest_design: str
    main_risk: str
    implementation_difficulty: str
    priority: str
    next_action: str
    source_url: str | None = None
    evidence: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def candidate_id(self) -> str:
        key = f"{self.edge_family.value}-{self.source_obsidian_path}-{self.name}"
        return slugify(key)

    @property
    def note_title(self) -> str:
        return f"Strategy Candidate - {self.name}"

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self) | {"candidate_id": self.candidate_id})


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum) and isinstance(value, str):
        return value.value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
