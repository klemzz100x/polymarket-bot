"""Latency Arbitrage Strategy for BTC 5-minute markets.

Exploits the ~2.7 second gap between Binance price movements and Polymarket repricing.
When BTC moves significantly on Binance, Polymarket odds should adjust but are delayed.

Edge: If BTC drops 0.5% in 30 seconds, fair probability shifts to ~70-75% DOWN,
but market might still show 50/50 - that's a 20+ point edge.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal

import httpx

from polybot.core.compat import UTC
from polybot.core.logging import get_logger
from polybot.data.schemas import OrderBookSnapshot

logger = get_logger(__name__)


# Binance price change thresholds for signal generation
PRICE_CHANGE_THRESHOLD_PCT = Decimal("0.3")  # 0.3% move triggers signal
STRONG_SIGNAL_THRESHOLD_PCT = Decimal("0.5")  # 0.5% move = strong signal

# Edge calculation parameters
# Based on empirical data: 1% BTC move ≈ 15-20% probability shift
PROB_SHIFT_PER_PCT_MOVE = Decimal("18")  # 18% prob shift per 1% price move

# Minimum edge required to trade (after fees)
MIN_EDGE_PCT = Decimal("5")  # Need at least 5% edge to trade


@dataclass(frozen=True, slots=True)
class BinancePrice:
    """Current BTC price from Binance."""

    symbol: str
    price: Decimal
    timestamp: datetime

    @classmethod
    async def fetch(cls, symbol: str = "BTCUSDT") -> "BinancePrice":
        """Fetch current price from Binance API."""
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(
                f"https://api.binance.com/api/v3/ticker/price",
                params={"symbol": symbol},
            )
            r.raise_for_status()
            data = r.json()
            return cls(
                symbol=data["symbol"],
                price=Decimal(data["price"]),
                timestamp=datetime.now(UTC),
            )


@dataclass(frozen=True, slots=True)
class PriceChange:
    """BTC price change over a time window."""

    start_price: Decimal
    end_price: Decimal
    change_pct: Decimal
    window_seconds: int
    direction: Literal["up", "down", "flat"]
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class LatencyArbitrageSignal:
    """Signal indicating a latency arbitrage opportunity."""

    signal_type: str
    direction: Literal["up", "down"]
    binance_change_pct: Decimal
    fair_probability: Decimal
    market_probability: Decimal
    edge_pct: Decimal
    confidence: Decimal
    timestamp: datetime
    asset_id: str
    market_id: str

    @property
    def is_actionable(self) -> bool:
        """Check if signal has enough edge to trade."""
        return self.edge_pct >= MIN_EDGE_PCT


class BinancePriceTracker:
    """Tracks BTC price changes over time windows."""

    def __init__(self, window_seconds: int = 30):
        self.window_seconds = window_seconds
        self.price_history: list[BinancePrice] = []
        self.max_history_size = 100

    async def update(self) -> BinancePrice:
        """Fetch and store current price."""
        price = await BinancePrice.fetch()
        self.price_history.append(price)

        # Prune old prices
        cutoff = datetime.now(UTC) - timedelta(seconds=self.window_seconds * 2)
        self.price_history = [p for p in self.price_history if p.timestamp > cutoff]

        return price

    def get_price_change(self, window_seconds: int | None = None) -> PriceChange | None:
        """Calculate price change over the window."""
        if len(self.price_history) < 2:
            return None

        window = window_seconds or self.window_seconds
        cutoff = datetime.now(UTC) - timedelta(seconds=window)

        # Find oldest price in window
        old_prices = [p for p in self.price_history if p.timestamp <= cutoff]
        if not old_prices:
            old_prices = [self.price_history[0]]

        start_price = old_prices[-1].price
        end_price = self.price_history[-1].price

        change_pct = ((end_price - start_price) / start_price) * 100

        if change_pct > Decimal("0.01"):
            direction = "up"
        elif change_pct < Decimal("-0.01"):
            direction = "down"
        else:
            direction = "flat"

        return PriceChange(
            start_price=start_price,
            end_price=end_price,
            change_pct=change_pct,
            window_seconds=window,
            direction=direction,
            timestamp=datetime.now(UTC),
        )


class LatencyArbitrageDetector:
    """Detects latency arbitrage opportunities between Binance and Polymarket."""

    def __init__(self):
        self.price_tracker = BinancePriceTracker(window_seconds=30)

    async def update_price(self) -> BinancePrice:
        """Update Binance price."""
        return await self.price_tracker.update()

    def calculate_fair_probability(
        self,
        price_change: PriceChange,
        base_probability: Decimal = Decimal("0.5"),
    ) -> tuple[Decimal, Decimal]:
        """Calculate fair UP/DOWN probabilities based on price change.

        Returns:
            (fair_up_prob, fair_down_prob)
        """
        # Price change affects probability
        # Positive change = higher UP probability
        prob_shift = (price_change.change_pct * PROB_SHIFT_PER_PCT_MOVE) / 100

        fair_up = base_probability + prob_shift
        fair_up = max(Decimal("0.05"), min(Decimal("0.95"), fair_up))
        fair_down = Decimal("1") - fair_up

        return fair_up, fair_down

    def detect_signal(
        self,
        snapshot: OrderBookSnapshot,
        market_id: str,
        up_asset_id: str,
        down_asset_id: str,
    ) -> LatencyArbitrageSignal | None:
        """Detect latency arbitrage signal.

        Args:
            snapshot: Current orderbook snapshot (for either UP or DOWN token)
            market_id: Polymarket market condition ID
            up_asset_id: Token ID for UP outcome
            down_asset_id: Token ID for DOWN outcome
        """
        price_change = self.price_tracker.get_price_change()
        if not price_change:
            return None

        # Check if price moved enough
        if abs(price_change.change_pct) < PRICE_CHANGE_THRESHOLD_PCT:
            return None

        # Calculate fair probabilities
        fair_up, fair_down = self.calculate_fair_probability(price_change)

        # Get market probability from orderbook
        # Best ask for a token represents market's implied probability
        if not snapshot.asks:
            return None

        market_price = snapshot.asks[0].price

        # Determine which direction to trade
        is_up_token = snapshot.asset_id == up_asset_id

        if is_up_token:
            market_up_prob = market_price
            fair_prob = fair_up
            edge = fair_up - market_up_prob
            direction = "up" if edge > 0 else "down"
            target_asset = up_asset_id if edge > 0 else down_asset_id
        else:
            market_down_prob = market_price
            fair_prob = fair_down
            edge = fair_down - market_down_prob
            direction = "down" if edge > 0 else "up"
            target_asset = down_asset_id if edge > 0 else up_asset_id

        edge_pct = abs(edge) * 100

        # Calculate confidence based on price change magnitude
        if abs(price_change.change_pct) >= STRONG_SIGNAL_THRESHOLD_PCT:
            confidence = Decimal("0.85")
        else:
            confidence = Decimal("0.70")

        if edge_pct < MIN_EDGE_PCT:
            return None

        return LatencyArbitrageSignal(
            signal_type="latency_arbitrage",
            direction=direction,
            binance_change_pct=price_change.change_pct,
            fair_probability=fair_prob,
            market_probability=market_price,
            edge_pct=edge_pct,
            confidence=confidence,
            timestamp=datetime.now(UTC),
            asset_id=target_asset,
            market_id=market_id,
        )


async def run_latency_scan(
    market_id: str,
    up_asset_id: str,
    down_asset_id: str,
    duration_seconds: int = 60,
    interval_ms: int = 500,
) -> list[LatencyArbitrageSignal]:
    """Run a latency arbitrage scan for a specified duration.

    Args:
        market_id: Polymarket condition ID
        up_asset_id: Token ID for UP outcome
        down_asset_id: Token ID for DOWN outcome
        duration_seconds: How long to scan
        interval_ms: Milliseconds between price checks

    Returns:
        List of detected signals
    """
    import asyncio

    from polybot.core.config import get_settings
    from polybot.polymarket.api import PolymarketClient

    settings = get_settings()
    detector = LatencyArbitrageDetector()
    signals: list[LatencyArbitrageSignal] = []

    start_time = datetime.now(UTC)
    end_time = start_time + timedelta(seconds=duration_seconds)

    logger.info(
        "latency_scan_started",
        market_id=market_id[:20],
        duration_seconds=duration_seconds,
    )

    async with PolymarketClient(settings) as client:
        while datetime.now(UTC) < end_time:
            try:
                # Update Binance price
                binance_price = await detector.update_price()

                # Get Polymarket orderbooks
                books = await client.get_orderbooks([up_asset_id, down_asset_id])

                for book in books:
                    from polybot.data.normalization import normalize_orderbook
                    snapshot = normalize_orderbook(book, received_at=datetime.now(UTC))

                    signal = detector.detect_signal(
                        snapshot=snapshot,
                        market_id=market_id,
                        up_asset_id=up_asset_id,
                        down_asset_id=down_asset_id,
                    )

                    if signal and signal.is_actionable:
                        signals.append(signal)
                        logger.info(
                            "latency_signal_detected",
                            direction=signal.direction,
                            edge_pct=float(signal.edge_pct),
                            binance_change=float(signal.binance_change_pct),
                            confidence=float(signal.confidence),
                        )

            except Exception as e:
                logger.warning("latency_scan_error", error=str(e))

            await asyncio.sleep(interval_ms / 1000)

    logger.info(
        "latency_scan_completed",
        signals_found=len(signals),
        duration_seconds=duration_seconds,
    )

    return signals
