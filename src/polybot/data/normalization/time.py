from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, int | float | Decimal):
        return normalize_unix_timestamp(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.isdigit():
            return normalize_unix_timestamp(Decimal(stripped))
        return datetime.fromisoformat(stripped.replace("Z", "+00:00")).astimezone(UTC)
    raise TypeError(f"Unsupported datetime value: {type(value)!r}")


def normalize_unix_timestamp(value: int | float | Decimal | str) -> datetime:
    numeric = Decimal(str(value))
    if numeric > Decimal("1000000000000"):
        seconds = numeric / Decimal("1000")
    elif numeric > Decimal("10000000000"):
        seconds = numeric / Decimal("1000")
    else:
        seconds = numeric
    return datetime.fromtimestamp(float(seconds), UTC)

