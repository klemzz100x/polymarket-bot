"""Spread Detection Strategy for Binary Markets.

Monitors bid-ask spreads to identify:
1. Tight spreads = good liquidity = tradeable
2. Spread compression = market makers entering = opportunity incoming
3. Spread blowout = liquidity crisis = avoid

Key insight from Twitter threads:
- 98% spread = extremely illiquid, avoid
- 5-10% spread = normal, wait for signal
- 2-5% spread = good liquidity, act on signals
- <2% spread = excellent, prioritize this market
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

from polybot.core.compat import UTC
from polybot.core.logging import get_logger

logger = get_logger(__name__)


class LiquidityRegime(str, Enum):
    """Market liquidity classification."""

    EXCELLENT = "excellent"  # <2% spread
    GOOD = "good"  # 2-5% spread
    NORMAL = "normal"  # 5-10% spread
    POOR = "poor"  # 10-20% spread
    ILLIQUID = "illiquid"  # >20% spread
    NO_MARKET = "no_market"  # No bids/asks


# Spread thresholds (as decimal, e.g., 0.02 = 2%)
SPREAD_EXCELLENT = Decimal("0.02")
SPREAD_GOOD = Decimal("0.05")
SPREAD_NORMAL = Decimal("0.10")
SPREAD_POOR = Decimal("0.20")


@dataclass(frozen=True, slots=True)
class SpreadAnalysis:
    """Analysis of current market spread."""

    market_id: str
    up_bid: Decimal | None
    up_ask: Decimal | None
    down_bid: Decimal | None
    down_ask: Decimal | None
    spread: Decimal | None  # up_ask + down_ask - 1
    regime: LiquidityRegime
    is_tradeable: bool
    timestamp: datetime

    @classmethod
    def from_prices(
        cls,
        market_id: str,
        up_bid: Decimal | None,
        up_ask: Decimal | None,
        down_bid: Decimal | None,
        down_ask: Decimal | None,
    ) -> "SpreadAnalysis":
        """Create analysis from orderbook prices."""
        now = datetime.now(UTC)

        # Calculate spread
        if up_ask is None or down_ask is None:
            return cls(
                market_id=market_id,
                up_bid=up_bid,
                up_ask=up_ask,
                down_bid=down_bid,
                down_ask=down_ask,
                spread=None,
                regime=LiquidityRegime.NO_MARKET,
                is_tradeable=False,
                timestamp=now,
            )

        spread = up_ask + down_ask - Decimal("1")

        # Classify regime
        if spread < SPREAD_EXCELLENT:
            regime = LiquidityRegime.EXCELLENT
        elif spread < SPREAD_GOOD:
            regime = LiquidityRegime.GOOD
        elif spread < SPREAD_NORMAL:
            regime = LiquidityRegime.NORMAL
        elif spread < SPREAD_POOR:
            regime = LiquidityRegime.POOR
        else:
            regime = LiquidityRegime.ILLIQUID

        # Tradeable if spread is acceptable (< 10%)
        is_tradeable = regime in (
            LiquidityRegime.EXCELLENT,
            LiquidityRegime.GOOD,
            LiquidityRegime.NORMAL,
        )

        return cls(
            market_id=market_id,
            up_bid=up_bid,
            up_ask=up_ask,
            down_bid=down_bid,
            down_ask=down_ask,
            spread=spread,
            regime=regime,
            is_tradeable=is_tradeable,
            timestamp=now,
        )


@dataclass(frozen=True, slots=True)
class SpreadTransition:
    """Detects when spread regime changes."""

    market_id: str
    previous_regime: LiquidityRegime
    current_regime: LiquidityRegime
    previous_spread: Decimal | None
    current_spread: Decimal | None
    is_improving: bool
    is_deteriorating: bool
    timestamp: datetime


class SpreadTracker:
    """Tracks spread over time to detect regime transitions."""

    def __init__(self):
        self.history: list[SpreadAnalysis] = []
        self.max_history = 100

    def update(self, analysis: SpreadAnalysis) -> SpreadTransition | None:
        """Update with new spread analysis, return transition if regime changed."""
        transition = None

        if self.history:
            prev = self.history[-1]
            if prev.regime != analysis.regime:
                # Regime changed
                regime_order = [
                    LiquidityRegime.EXCELLENT,
                    LiquidityRegime.GOOD,
                    LiquidityRegime.NORMAL,
                    LiquidityRegime.POOR,
                    LiquidityRegime.ILLIQUID,
                    LiquidityRegime.NO_MARKET,
                ]

                prev_idx = regime_order.index(prev.regime) if prev.regime in regime_order else 5
                curr_idx = regime_order.index(analysis.regime) if analysis.regime in regime_order else 5

                is_improving = curr_idx < prev_idx
                is_deteriorating = curr_idx > prev_idx

                transition = SpreadTransition(
                    market_id=analysis.market_id,
                    previous_regime=prev.regime,
                    current_regime=analysis.regime,
                    previous_spread=prev.spread,
                    current_spread=analysis.spread,
                    is_improving=is_improving,
                    is_deteriorating=is_deteriorating,
                    timestamp=analysis.timestamp,
                )

                if is_improving:
                    logger.info(
                        "SPREAD_IMPROVING",
                        from_regime=prev.regime.value,
                        to_regime=analysis.regime.value,
                        spread=f"{float(analysis.spread)*100:.1f}%" if analysis.spread else "N/A",
                    )
                elif is_deteriorating:
                    logger.warning(
                        "SPREAD_DETERIORATING",
                        from_regime=prev.regime.value,
                        to_regime=analysis.regime.value,
                        spread=f"{float(analysis.spread)*100:.1f}%" if analysis.spread else "N/A",
                    )

        self.history.append(analysis)

        # Prune old entries
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        return transition

    def get_average_spread(self, last_n: int = 10) -> Decimal | None:
        """Get average spread over last N observations."""
        recent = [h for h in self.history[-last_n:] if h.spread is not None]
        if not recent:
            return None
        return sum(h.spread for h in recent) / len(recent)

    def is_currently_tradeable(self) -> bool:
        """Check if market is currently tradeable based on recent data."""
        if not self.history:
            return False
        return self.history[-1].is_tradeable

    def get_current_regime(self) -> LiquidityRegime | None:
        """Get current liquidity regime."""
        if not self.history:
            return None
        return self.history[-1].regime
