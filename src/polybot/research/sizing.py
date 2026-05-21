"""Quarter-Kelly position sizing for all Polymarket research scanners.

Formula (binary prediction market):
    f_full = edge / (1 - signal_price)
    f_quarter = f_full / 4
    size_usd = clamp(f_quarter × bankroll, min_usd, max_usd, max_pct × bankroll)

Caps applied in order:
    1. Quarter-Kelly fraction
    2. Hard % cap per trade (default 2% of bankroll — from crptatlas thread)
    3. 50% of visible orderbook depth (from 0x-discover thread)
    4. Absolute max_usd
    5. Floor at min_usd (else 0.0 if edge is negative/zero)

Sources:
    - crptatlas: "Never risk more than 2% of capital per signal regardless of Kelly"
    - crptatlas: "Half Kelly gives up 25% growth but cuts max drawdowns by half" → we use Quarter
    - 0x-discover: "Position cap at 50% of available order book depth"
    - 0xmovez/gengar: "Quarter-Kelly, Brownian motion model, circuit breaker"
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SizingResult:
    size_usd: float
    kelly_full_pct: float      # full Kelly fraction as %
    kelly_quarter_pct: float   # quarter Kelly fraction as %
    cap_applied: str           # which cap was binding: "kelly" | "pct_cap" | "depth_cap" | "max_cap" | "floor"
    bankroll: float

    def __str__(self) -> str:
        return (
            f"${self.size_usd:.2f} "
            f"(K¼={self.kelly_quarter_pct:.1f}% | cap={self.cap_applied})"
        )


def quarter_kelly_size(
    *,
    edge_decimal: float,
    signal_price: float,
    bankroll: float,
    max_pct: float = 0.02,
    min_usd: float = 0.50,
    max_usd: float = 10.0,
    book_depth_usd: float | None = None,
) -> SizingResult:
    """Compute Quarter-Kelly position size in USD.

    Args:
        edge_decimal: Estimated edge as decimal (0.07 = 7%). Must be > 0 for a size > 0.
        signal_price: Price of the side we're buying (0..1). E.g., 0.30 for a 30¢ contract.
        bankroll: Total available capital in USD.
        max_pct: Hard cap as fraction of bankroll (default 0.02 = 2%).
        min_usd: Minimum size if we trade at all (default $0.50).
        max_usd: Absolute maximum size (default $10).
        book_depth_usd: Available depth in the book on signal side. Cap at 50% of this.

    Returns:
        SizingResult with final size and diagnostics.
    """
    if edge_decimal <= 0 or signal_price <= 0 or signal_price >= 1 or bankroll <= 0:
        return SizingResult(
            size_usd=0.0,
            kelly_full_pct=0.0,
            kelly_quarter_pct=0.0,
            cap_applied="no_edge",
            bankroll=bankroll,
        )

    # Full Kelly fraction: f* = edge / (1 - signal_price)
    # This is the standard binary bet Kelly where:
    #   p = signal_price + edge (true prob)
    #   b = (1 - signal_price) / signal_price (net odds)
    #   f* = (p*b - (1-p)) / b = edge / (1 - signal_price)
    denom = 1.0 - signal_price
    if denom < 1e-9:
        return SizingResult(0.0, 0.0, 0.0, "no_edge", bankroll)

    f_full = edge_decimal / denom
    f_quarter = f_full * 0.25

    kelly_usd = f_quarter * bankroll
    cap = "kelly"

    # Cap 1: 2% of bankroll hard limit
    pct_cap_usd = max_pct * bankroll
    if kelly_usd > pct_cap_usd:
        kelly_usd = pct_cap_usd
        cap = "pct_cap"

    # Cap 2: 50% of visible orderbook depth
    if book_depth_usd is not None and book_depth_usd > 0:
        depth_cap_usd = book_depth_usd * 0.50
        if kelly_usd > depth_cap_usd:
            kelly_usd = depth_cap_usd
            cap = "depth_cap"

    # Cap 3: absolute maximum
    if kelly_usd > max_usd:
        kelly_usd = max_usd
        cap = "max_cap"

    # Floor: if the computed size is below minimum, either trade minimum or don't trade
    if kelly_usd < min_usd:
        # Only trade at floor if Kelly recommends at least half the floor (edge is real)
        if kelly_usd >= min_usd * 0.5:
            kelly_usd = min_usd
            cap = "floor"
        else:
            kelly_usd = 0.0
            cap = "below_floor"

    return SizingResult(
        size_usd=round(kelly_usd, 2),
        kelly_full_pct=round(f_full * 100, 2),
        kelly_quarter_pct=round(f_quarter * 100, 2),
        cap_applied=cap,
        bankroll=bankroll,
    )


def size_from_score(
    *,
    score: float,
    signal_price: float,
    bankroll: float,
    max_pct: float = 0.02,
    min_usd: float = 0.50,
    max_usd: float = 10.0,
    score_to_edge_factor: float = 0.001,
) -> SizingResult:
    """Convert a 0–100 score (e.g., reflexivity) to a Kelly size.

    Uses score × factor as a conservative edge estimate.
    Default factor 0.001 → score 70 = 7% edge estimate (upper bound assumption).
    """
    edge_decimal = score * score_to_edge_factor
    return quarter_kelly_size(
        edge_decimal=edge_decimal,
        signal_price=signal_price,
        bankroll=bankroll,
        max_pct=max_pct,
        min_usd=min_usd,
        max_usd=max_usd,
    )
