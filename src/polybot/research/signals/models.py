from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
import json
from typing import Any


@dataclass(frozen=True, slots=True)
class ResearchSignal:
    market_id: str
    timestamp: datetime
    signal_type: str
    severity: str
    confidence: Decimal
    description: str
    metrics: dict[str, str | int | float | bool | None]
    hypothesis: str
    next_action: str
    asset_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


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

