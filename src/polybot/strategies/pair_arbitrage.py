"""Pair Cost Arbitrage Strategy for Binary Markets.

Exploits mispricing when YES + NO asks sum to less than $1.
If you can buy both outcomes for < $1, you lock in risk-free profit.

Example:
- YES ask: $0.48
- NO ask: $0.49
- Total: $0.97
- Profit: $0.03 per pair (3% risk-free)

This edge appears when market makers compete aggressively or
during high-volatility periods with stale orders.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from polybot.core.compat import UTC
from polybot.core.logging import get_logger

logger = get_logger(__name__)

# Minimum profit required to execute (covers fees + slippage)
MIN_PROFIT_PCT = Decimal("1.5")  # 1.5% minimum profit
POLYMARKET_TAKER_FEE = Decimal("0.02")  # 2% taker fee on winning side


@dataclass(frozen=True, slots=True)
class PairArbitrageSignal:
    """Signal indicating a pair cost arbitrage opportunity."""

    market_id: str
    up_asset_id: str
    down_asset_id: str
    up_ask: Decimal
    down_ask: Decimal
    total_cost: Decimal
    gross_profit_pct: Decimal
    net_profit_pct: Decimal  # After fees
    timestamp: datetime

    @property
    def is_actionable(self) -> bool:
        """Check if the arbitrage is profitable after fees."""
        return self.net_profit_pct >= MIN_PROFIT_PCT


def calculate_pair_arbitrage(
    up_ask: Decimal | None,
    down_ask: Decimal | None,
    market_id: str,
    up_asset_id: str,
    down_asset_id: str,
) -> PairArbitrageSignal | None:
    """Check if pair cost arbitrage exists.

    Args:
        up_ask: Best ask price for UP/YES outcome
        down_ask: Best ask price for DOWN/NO outcome
        market_id: Market condition ID
        up_asset_id: Token ID for UP outcome
        down_asset_id: Token ID for DOWN outcome

    Returns:
        PairArbitrageSignal if opportunity exists, None otherwise
    """
    if up_ask is None or down_ask is None:
        return None

    total_cost = up_ask + down_ask

    # If total > $1, no arbitrage (you'd pay more than the guaranteed $1 return)
    if total_cost >= Decimal("1"):
        return None

    # Calculate profits
    gross_profit = Decimal("1") - total_cost
    gross_profit_pct = (gross_profit / total_cost) * 100

    # Fee is only paid on the winning side (the $1 payout)
    # So net profit = $1 - total_cost - fee_on_$1_payout
    fee = POLYMARKET_TAKER_FEE * Decimal("1")  # 2% of $1
    net_profit = gross_profit - fee
    net_profit_pct = (net_profit / total_cost) * 100

    signal = PairArbitrageSignal(
        market_id=market_id,
        up_asset_id=up_asset_id,
        down_asset_id=down_asset_id,
        up_ask=up_ask,
        down_ask=down_ask,
        total_cost=total_cost,
        gross_profit_pct=gross_profit_pct,
        net_profit_pct=net_profit_pct,
        timestamp=datetime.now(UTC),
    )

    if signal.is_actionable:
        logger.info(
            "PAIR_ARB_SIGNAL",
            up_ask=float(up_ask),
            down_ask=float(down_ask),
            total_cost=float(total_cost),
            net_profit_pct=f"{float(net_profit_pct):.2f}%",
        )

    return signal


class PairArbitrageScanner:
    """Scans markets for pair cost arbitrage opportunities."""

    def __init__(self):
        self.signals: list[PairArbitrageSignal] = []

    def check_market(
        self,
        up_ask: Decimal | None,
        down_ask: Decimal | None,
        market_id: str,
        up_asset_id: str,
        down_asset_id: str,
    ) -> PairArbitrageSignal | None:
        """Check a single market for pair arbitrage."""
        signal = calculate_pair_arbitrage(
            up_ask=up_ask,
            down_ask=down_ask,
            market_id=market_id,
            up_asset_id=up_asset_id,
            down_asset_id=down_asset_id,
        )

        if signal and signal.is_actionable:
            self.signals.append(signal)
            return signal

        return None

    def get_best_opportunity(self) -> PairArbitrageSignal | None:
        """Get the most profitable opportunity found."""
        if not self.signals:
            return None
        return max(self.signals, key=lambda s: s.net_profit_pct)

    def clear(self):
        """Clear all recorded signals."""
        self.signals.clear()
