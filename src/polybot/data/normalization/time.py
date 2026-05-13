import re
from datetime import datetime
from decimal import Decimal
from typing import Any

from polybot.core.compat import UTC


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
        normalized = _normalize_iso_string(stripped.replace("Z", "+00:00"))
        return datetime.fromisoformat(normalized).astimezone(UTC)
    raise TypeError(f"Unsupported datetime value: {type(value)!r}")


def _normalize_iso_string(iso_string: str) -> str:
    """Normalize ISO datetime string to handle variable-length microseconds.

    Python's datetime.fromisoformat() requires exactly 0, 3, or 6 digits for
    fractional seconds. This normalizes strings like '2025-05-02T15:48:16.6+00:00'
    to have 6 digits of precision.
    """
    # Match pattern: datetime part + fractional seconds + timezone
    match = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d+)([+-]\d{2}:\d{2})?$", iso_string)
    if match:
        base, frac, tz = match.groups()
        # Pad or truncate fractional seconds to 6 digits
        frac = frac[:6].ljust(6, "0")
        return f"{base}.{frac}{tz or ''}"
    return iso_string


def normalize_unix_timestamp(value: int | float | Decimal | str) -> datetime:
    numeric = Decimal(str(value))
    if numeric > Decimal("1000000000000") or numeric > Decimal("10000000000"):
        seconds = numeric / Decimal("1000")
    else:
        seconds = numeric
    return datetime.fromtimestamp(float(seconds), UTC)

