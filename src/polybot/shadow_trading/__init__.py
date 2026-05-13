"""Shadow trading layer: theoretical live decisions without real orders."""

from polybot.shadow_trading.engine import ShadowTradingEngine
from polybot.shadow_trading.models import (
    ExecutionComparison,
    MarketRealitySnapshot,
    ShadowDecision,
    ShadowFill,
    ShadowOrder,
    ShadowTradingResult,
)

__all__ = [
    "ExecutionComparison",
    "MarketRealitySnapshot",
    "ShadowDecision",
    "ShadowFill",
    "ShadowOrder",
    "ShadowTradingEngine",
    "ShadowTradingResult",
]
