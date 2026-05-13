from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from datetime import timedelta
from polybot.core.compat import UTC
from decimal import Decimal

from polybot.live_execution.models import LiveOrder


@dataclass(frozen=True, slots=True)
class MicroLiveSafetyConfig:
    max_order_size_usd: Decimal = Decimal("1")
    max_daily_loss_usd: Decimal = Decimal("5")
    max_open_positions: int = 2
    order_rate_limit_per_minute: int = 3
    cooldown_after_loss_seconds: int = 300
    require_manual_confirmation: bool = True


@dataclass(slots=True)
class EmergencyStop:
    enabled: bool = True
    triggered: bool = False
    reason: str = ""
    triggered_at: datetime | None = None

    def trigger(self, reason: str) -> None:
        self.triggered = True
        self.reason = reason
        self.triggered_at = datetime.now(UTC)

    def clear(self) -> None:
        self.triggered = False
        self.reason = ""
        self.triggered_at = None


@dataclass(slots=True)
class DuplicateOrderProtector:
    fingerprints: set[str] = field(default_factory=set)

    def is_duplicate(self, order: LiveOrder) -> bool:
        return order.fingerprint() in self.fingerprints

    def remember(self, order: LiveOrder) -> None:
        self.fingerprints.add(order.fingerprint())


@dataclass(slots=True)
class OrderRateLimiter:
    max_orders_per_minute: int = 3
    timestamps: deque[datetime] = field(default_factory=deque)

    def allow(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        cutoff = current - timedelta(minutes=1)
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()
        return len(self.timestamps) < self.max_orders_per_minute

    def record(self, now: datetime | None = None) -> None:
        self.timestamps.append(now or datetime.now(UTC))


@dataclass(slots=True)
class LossCooldown:
    cooldown_seconds: int = 300
    last_loss_at: datetime | None = None

    def record_loss(self, now: datetime | None = None) -> None:
        self.last_loss_at = now or datetime.now(UTC)

    def active(self, now: datetime | None = None) -> bool:
        if self.last_loss_at is None:
            return False
        current = now or datetime.now(UTC)
        return current - self.last_loss_at < timedelta(seconds=self.cooldown_seconds)
