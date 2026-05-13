from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class LiveRiskConstraints:
    max_order_size_usd: Decimal = Decimal("1")
    max_daily_loss_usd: Decimal = Decimal("5")
    max_exposure_usd: Decimal = Decimal("25")
    max_correlated_exposure_usd: Decimal = Decimal("10")
    max_strategy_exposure_usd: Decimal = Decimal("10")
    max_open_positions: int = 2
    max_latency_ms: Decimal = Decimal("5000")
    max_stale_age_seconds: Decimal = Decimal("30")
    require_manual_confirmation: bool = True
