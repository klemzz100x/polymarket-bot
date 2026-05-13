"""Common JSON serialization utilities."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


def json_ready(value: Any) -> Any:
    """Convert Python objects to JSON-serializable types.

    Handles:
    - datetime -> ISO format string
    - Decimal -> string (to preserve precision)
    - StrEnum (str + Enum) -> value string
    - dict -> recursive conversion
    - list -> recursive conversion
    """
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum) and isinstance(value, str):
        return value.value
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    return value


__all__ = ["json_ready"]
