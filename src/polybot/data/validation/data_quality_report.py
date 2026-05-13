from dataclasses import asdict, dataclass, field
from datetime import datetime
from polybot.core.compat import UTC
from decimal import Decimal
import json
from typing import Any


@dataclass(frozen=True, slots=True)
class QualityIssue:
    check_name: str
    severity: str
    message: str
    timestamp: datetime | None = None
    asset_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    market_id: str
    start: datetime | None
    end: datetime | None
    generated_at: datetime
    snapshot_count: int
    trade_count: int
    price_tick_count: int
    issues: list[QualityIssue]
    observed_update_frequency_per_minute: Decimal | None
    max_collection_latency_seconds: Decimal | None

    @property
    def status(self) -> str:
        if any(issue.severity == "critical" for issue in self.issues):
            return "critical"
        if any(issue.severity == "warning" for issue in self.issues):
            return "warning"
        return "ok"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return _json_ready(data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def now_report_time() -> datetime:
    return datetime.now(UTC)


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value

