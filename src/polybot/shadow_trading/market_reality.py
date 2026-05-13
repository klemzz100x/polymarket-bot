from datetime import datetime
from decimal import Decimal

from polybot.data.schemas import OrderBookSnapshot
from polybot.research.metrics import compute_orderbook_metrics
from polybot.shadow_trading.models import MarketRealitySnapshot


def build_market_reality_snapshot(
    snapshot: OrderBookSnapshot,
    *,
    now: datetime | None = None,
) -> MarketRealitySnapshot:
    metrics = compute_orderbook_metrics(snapshot)
    stale_age = None
    if now is not None:
        stale_age = Decimal(str((now - snapshot.snapshot_ts).total_seconds()))
    return MarketRealitySnapshot(
        market_id=snapshot.condition_id,
        asset_id=snapshot.asset_id,
        snapshot_ts=snapshot.snapshot_ts,
        best_bid=metrics.best_bid,
        best_ask=metrics.best_ask,
        mid_price=metrics.mid_price,
        spread_abs=metrics.spread_abs,
        spread_pct=metrics.spread_pct,
        bid_depth=metrics.bid_depth,
        ask_depth=metrics.ask_depth,
        total_depth=metrics.total_depth,
        orderbook_imbalance=metrics.orderbook_imbalance,
        stale_age_seconds=stale_age,
    )
