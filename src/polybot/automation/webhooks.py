from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WebhookEnvelope:
    source: str
    event_type: str
    payload: dict[str, object]

