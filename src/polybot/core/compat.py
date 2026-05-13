"""Compatibility module for Python 3.10/3.11 differences."""

import sys
from datetime import timezone
from enum import Enum

# Python 3.11+ has datetime.UTC, but 3.10 needs timezone.utc
UTC = timezone.utc

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    # Python 3.10 compatibility: StrEnum backport
    class StrEnum(str, Enum):
        """String enum compatible with Python 3.10."""

        def __new__(cls, value: str) -> "StrEnum":
            member = str.__new__(cls, value)
            member._value_ = value
            return member

        def __str__(self) -> str:
            return self.value

        @staticmethod
        def _generate_next_value_(
            name: str, start: int, count: int, last_values: list
        ) -> str:
            return name.lower()


__all__ = ["StrEnum", "UTC"]
