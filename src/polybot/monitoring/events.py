from dataclasses import dataclass, field
from datetime import datetime
from polybot.core.compat import UTC


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_type: str
    actor: str
    payload: dict[str, object]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

