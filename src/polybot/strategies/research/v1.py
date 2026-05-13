from decimal import Decimal

from polybot.backtesting.engine import make_order_id
from polybot.backtesting.portfolio import PortfolioState
from polybot.backtesting.results import BacktestConfig, SimulatedOrder
from polybot.data.schemas import OrderBookSnapshot
from polybot.research.metrics import compute_orderbook_metrics


class WideSpreadMeanReversion:
    strategy_id = "wide-spread-mean-reversion"

    def on_snapshot(
        self,
        *,
        snapshot: OrderBookSnapshot,
        portfolio: PortfolioState,
        config: BacktestConfig,
    ) -> list[SimulatedOrder]:
        metrics = compute_orderbook_metrics(snapshot)
        position = portfolio.position_for(snapshot.asset_id)
        if metrics.spread_pct is None or metrics.best_bid is None or metrics.best_ask is None:
            return []
        if position.quantity <= 0 and metrics.spread_pct >= Decimal("0.10"):
            passive_price = min(metrics.best_ask, metrics.best_bid + Decimal("0.01"))
            return [
                SimulatedOrder(
                    order_id=make_order_id(),
                    market_id=config.market_id,
                    asset_id=snapshot.asset_id,
                    side="buy",
                    size=config.order_size,
                    created_at=snapshot.snapshot_ts,
                    limit_price=passive_price,
                    reason="wide_spread_entry",
                )
            ]
        if position.quantity > 0 and metrics.spread_pct <= Decimal("0.04") and metrics.best_bid:
            return [
                SimulatedOrder(
                    order_id=make_order_id(),
                    market_id=config.market_id,
                    asset_id=snapshot.asset_id,
                    side="sell",
                    size=min(position.quantity, config.order_size),
                    created_at=snapshot.snapshot_ts,
                    limit_price=metrics.best_bid,
                    reason="spread_mean_reversion_exit",
                )
            ]
        return []


class OrderbookImbalanceMomentum:
    strategy_id = "orderbook-imbalance-momentum"

    def on_snapshot(
        self,
        *,
        snapshot: OrderBookSnapshot,
        portfolio: PortfolioState,
        config: BacktestConfig,
    ) -> list[SimulatedOrder]:
        metrics = compute_orderbook_metrics(snapshot)
        position = portfolio.position_for(snapshot.asset_id)
        if metrics.orderbook_imbalance is None or metrics.best_ask is None or metrics.best_bid is None:
            return []
        if position.quantity <= 0 and metrics.orderbook_imbalance >= Decimal("0.70"):
            return [
                SimulatedOrder(
                    order_id=make_order_id(),
                    market_id=config.market_id,
                    asset_id=snapshot.asset_id,
                    side="buy",
                    size=config.order_size,
                    created_at=snapshot.snapshot_ts,
                    order_type="market",
                    reason="bid_pressure_momentum_entry",
                )
            ]
        if position.quantity > 0 and metrics.orderbook_imbalance <= Decimal("0.10"):
            return [
                SimulatedOrder(
                    order_id=make_order_id(),
                    market_id=config.market_id,
                    asset_id=snapshot.asset_id,
                    side="sell",
                    size=min(position.quantity, config.order_size),
                    created_at=snapshot.snapshot_ts,
                    order_type="market",
                    reason="imbalance_normalized_exit",
                )
            ]
        return []


class LiquidityVacuumFade:
    strategy_id = "liquidity-vacuum-fade"

    def on_snapshot(
        self,
        *,
        snapshot: OrderBookSnapshot,
        portfolio: PortfolioState,
        config: BacktestConfig,
    ) -> list[SimulatedOrder]:
        metrics = compute_orderbook_metrics(snapshot)
        position = portfolio.position_for(snapshot.asset_id)
        if metrics.best_bid is None or metrics.best_ask is None or metrics.spread_pct is None:
            return []
        if (
            position.quantity <= 0
            and metrics.total_depth <= Decimal("25")
            and metrics.spread_pct >= Decimal("0.05")
        ):
            conservative_size = min(config.order_size, Decimal("5"))
            return [
                SimulatedOrder(
                    order_id=make_order_id(),
                    market_id=config.market_id,
                    asset_id=snapshot.asset_id,
                    side="buy",
                    size=conservative_size,
                    created_at=snapshot.snapshot_ts,
                    limit_price=metrics.best_bid + Decimal("0.01"),
                    reason="liquidity_vacuum_fade_entry",
                )
            ]
        if position.quantity > 0 and metrics.total_depth >= Decimal("50"):
            return [
                SimulatedOrder(
                    order_id=make_order_id(),
                    market_id=config.market_id,
                    asset_id=snapshot.asset_id,
                    side="sell",
                    size=min(position.quantity, config.order_size),
                    created_at=snapshot.snapshot_ts,
                    order_type="market",
                    reason="liquidity_recovered_exit",
                )
            ]
        return []

