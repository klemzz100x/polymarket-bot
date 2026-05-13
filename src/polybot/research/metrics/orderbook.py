from dataclasses import asdict, dataclass
from decimal import Decimal, DivisionByZero, InvalidOperation
from statistics import pstdev
from typing import Any

from polybot.data.schemas import OrderBookSnapshot, PriceTick, Trade


@dataclass(frozen=True, slots=True)
class SlippageEstimate:
    side: str
    requested_size: Decimal
    filled_size: Decimal
    fill_ratio: Decimal
    average_price: Decimal | None
    worst_price: Decimal | None
    reference_price: Decimal | None
    slippage_abs: Decimal | None
    slippage_pct: Decimal | None

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class OrderBookMetrics:
    asset_id: str
    condition_id: str
    best_bid: Decimal | None
    best_ask: Decimal | None
    mid_price: Decimal | None
    spread_abs: Decimal | None
    spread_pct: Decimal | None
    bid_depth: Decimal
    ask_depth: Decimal
    total_depth: Decimal
    orderbook_imbalance: Decimal | None
    levels_bid: int
    levels_ask: int
    liquidity_score: Decimal
    slippage: dict[str, SlippageEstimate]

    @property
    def spread(self) -> Decimal | None:
        return self.spread_abs

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


@dataclass(frozen=True, slots=True)
class MarketMetricsSummary:
    market_id: str
    snapshot_count: int
    trade_count: int
    price_tick_count: int
    average_spread_abs: Decimal | None
    average_spread_pct: Decimal | None
    average_bid_depth: Decimal | None
    average_ask_depth: Decimal | None
    average_imbalance: Decimal | None
    traded_volume: Decimal
    realized_volatility: Decimal | None
    price_change: Decimal | None
    update_frequency_per_minute: Decimal | None
    liquidity_score: Decimal
    market_activity_score: Decimal

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


DEFAULT_SLIPPAGE_SIZES = (Decimal("10"), Decimal("50"), Decimal("100"))


def compute_orderbook_metrics(
    snapshot: OrderBookSnapshot,
    slippage_sizes: tuple[Decimal, ...] = DEFAULT_SLIPPAGE_SIZES,
) -> OrderBookMetrics:
    bid_depth = sum((level.size for level in snapshot.bids), Decimal("0"))
    ask_depth = sum((level.size for level in snapshot.asks), Decimal("0"))
    total_depth = bid_depth + ask_depth
    mid_price = None
    spread_pct = None
    if snapshot.best_bid is not None and snapshot.best_ask is not None:
        mid_price = (snapshot.best_bid + snapshot.best_ask) / Decimal("2")
        if mid_price > 0:
            spread_pct = (snapshot.best_ask - snapshot.best_bid) / mid_price

    imbalance = None
    if total_depth > 0:
        imbalance = (bid_depth - ask_depth) / total_depth

    slippage: dict[str, SlippageEstimate] = {}
    for size in slippage_sizes:
        slippage[f"buy_{size}"] = estimate_slippage(snapshot, side="buy", order_size=size)
        slippage[f"sell_{size}"] = estimate_slippage(snapshot, side="sell", order_size=size)

    return OrderBookMetrics(
        asset_id=snapshot.asset_id,
        condition_id=snapshot.condition_id,
        best_bid=snapshot.best_bid,
        best_ask=snapshot.best_ask,
        mid_price=mid_price,
        spread_abs=snapshot.spread,
        spread_pct=spread_pct,
        bid_depth=bid_depth,
        ask_depth=ask_depth,
        total_depth=total_depth,
        orderbook_imbalance=imbalance,
        levels_bid=len(snapshot.bids),
        levels_ask=len(snapshot.asks),
        liquidity_score=_liquidity_score(total_depth=total_depth, spread_pct=spread_pct),
        slippage=slippage,
    )


def estimate_slippage(
    snapshot: OrderBookSnapshot,
    *,
    side: str,
    order_size: Decimal,
) -> SlippageEstimate:
    levels = snapshot.asks if side == "buy" else snapshot.bids
    reference_price = snapshot.best_ask if side == "buy" else snapshot.best_bid
    filled = Decimal("0")
    notional = Decimal("0")
    worst_price: Decimal | None = None

    for level in levels:
        take = min(order_size - filled, level.size)
        if take <= 0:
            break
        filled += take
        notional += take * level.price
        worst_price = level.price
        if filled >= order_size:
            break

    average_price = notional / filled if filled > 0 else None
    fill_ratio = filled / order_size if order_size > 0 else Decimal("0")
    slippage_abs = None
    slippage_pct = None
    if average_price is not None and reference_price is not None:
        if side == "buy":
            slippage_abs = average_price - reference_price
        else:
            slippage_abs = reference_price - average_price
        slippage_pct = _safe_div(slippage_abs, reference_price)

    return SlippageEstimate(
        side=side,
        requested_size=order_size,
        filled_size=filled,
        fill_ratio=fill_ratio,
        average_price=average_price,
        worst_price=worst_price,
        reference_price=reference_price,
        slippage_abs=slippage_abs,
        slippage_pct=slippage_pct,
    )


def compute_market_metrics_summary(
    *,
    market_id: str,
    snapshots: list[OrderBookSnapshot],
    trades: list[Trade],
    price_ticks: list[PriceTick],
) -> MarketMetricsSummary:
    metrics = [compute_orderbook_metrics(snapshot) for snapshot in snapshots]
    traded_volume = sum((trade.size for trade in trades), Decimal("0"))
    average_spread_abs = _average([metric.spread_abs for metric in metrics])
    average_spread_pct = _average([metric.spread_pct for metric in metrics])
    average_bid_depth = _average([metric.bid_depth for metric in metrics])
    average_ask_depth = _average([metric.ask_depth for metric in metrics])
    average_imbalance = _average([metric.orderbook_imbalance for metric in metrics])
    volatility = realized_volatility(price_ticks)
    change = price_change(price_ticks)
    update_frequency = update_frequency_per_minute(snapshots)
    liquidity_score = _average([metric.liquidity_score for metric in metrics]) or Decimal("0")
    activity_score = _activity_score(
        trade_count=len(trades),
        traded_volume=traded_volume,
        update_frequency=update_frequency,
        liquidity_score=liquidity_score,
    )

    return MarketMetricsSummary(
        market_id=market_id,
        snapshot_count=len(snapshots),
        trade_count=len(trades),
        price_tick_count=len(price_ticks),
        average_spread_abs=average_spread_abs,
        average_spread_pct=average_spread_pct,
        average_bid_depth=average_bid_depth,
        average_ask_depth=average_ask_depth,
        average_imbalance=average_imbalance,
        traded_volume=traded_volume,
        realized_volatility=volatility,
        price_change=change,
        update_frequency_per_minute=update_frequency,
        liquidity_score=liquidity_score,
        market_activity_score=activity_score,
    )


def average_spread(snapshots: list[OrderBookSnapshot]) -> Decimal | None:
    return _average([snapshot.spread for snapshot in snapshots])


def update_frequency_per_minute(snapshots: list[OrderBookSnapshot]) -> Decimal | None:
    if len(snapshots) < 2:
        return None
    ordered = sorted(snapshots, key=lambda item: item.snapshot_ts)
    seconds = Decimal(str((ordered[-1].snapshot_ts - ordered[0].snapshot_ts).total_seconds()))
    if seconds <= 0:
        return None
    return Decimal(len(ordered) - 1) / (seconds / Decimal("60"))


def realized_volatility(price_ticks: list[PriceTick]) -> Decimal | None:
    if len(price_ticks) < 3:
        return None
    ordered = sorted(price_ticks, key=lambda tick: tick.ts)
    returns: list[float] = []
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if previous.price <= 0:
            continue
        returns.append(float((current.price - previous.price) / previous.price))
    if len(returns) < 2:
        return None
    return Decimal(str(pstdev(returns)))


def price_change(price_ticks: list[PriceTick]) -> Decimal | None:
    if len(price_ticks) < 2:
        return None
    ordered = sorted(price_ticks, key=lambda tick: tick.ts)
    return ordered[-1].price - ordered[0].price


def _liquidity_score(total_depth: Decimal, spread_pct: Decimal | None) -> Decimal:
    if total_depth <= 0:
        return Decimal("0")
    penalty = Decimal("1") + (spread_pct or Decimal("0")) * Decimal("10")
    return total_depth / penalty


def _activity_score(
    *,
    trade_count: int,
    traded_volume: Decimal,
    update_frequency: Decimal | None,
    liquidity_score: Decimal,
) -> Decimal:
    volume_component = traded_volume.sqrt() if traded_volume > 0 else Decimal("0")
    liquidity_component = liquidity_score.sqrt() if liquidity_score > 0 else Decimal("0")
    return Decimal(trade_count) + volume_component + (update_frequency or Decimal("0")) + liquidity_component


def _average(values: list[Decimal | None]) -> Decimal | None:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    return sum(clean, Decimal("0")) / Decimal(len(clean))


def _safe_div(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    try:
        if denominator == 0:
            return None
        return numerator / denominator
    except (DivisionByZero, InvalidOperation):
        return None


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
