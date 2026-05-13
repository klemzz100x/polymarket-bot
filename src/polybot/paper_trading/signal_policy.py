from decimal import Decimal

from polybot.backtesting.engine import make_order_id
from polybot.backtesting.portfolio import PortfolioState
from polybot.backtesting.results import SimulatedOrder
from polybot.data.schemas import OrderBookSnapshot
from polybot.paper_trading.models import PaperTradingConfig, PaperTradingOrderDecision
from polybot.research.metrics import compute_orderbook_metrics
from polybot.research.signals import ResearchSignal


class SignalDrivenPaperPolicy:
    """Simple research-only signal policy for paper trading.

    This intentionally stays conservative and transparent. It maps research signals into
    virtual orders so the infrastructure can be tested before paper/live strategy work.
    """

    def decide(
        self,
        *,
        snapshot: OrderBookSnapshot,
        signals: list[ResearchSignal],
        portfolio: PortfolioState,
        config: PaperTradingConfig,
    ) -> list[PaperTradingOrderDecision]:
        metrics = compute_orderbook_metrics(snapshot)
        position = portfolio.position_for(snapshot.asset_id)
        decisions: list[PaperTradingOrderDecision] = []

        signal_types = {signal.signal_type for signal in signals if signal.asset_id == snapshot.asset_id}

        if (
            position.quantity <= 0
            and {"wide_spread", "stable_exploitable_spread"} & signal_types
            and metrics.best_bid is not None
            and metrics.best_ask is not None
        ):
            price = min(metrics.best_ask, metrics.best_bid + Decimal("0.01"))
            decisions.append(
                PaperTradingOrderDecision(
                    order=SimulatedOrder(
                        order_id=make_order_id(),
                        market_id=config.market_id,
                        asset_id=snapshot.asset_id,
                        side="buy",
                        size=config.order_size,
                        created_at=snapshot.snapshot_ts,
                        limit_price=price,
                        reason="paper_signal_wide_spread_entry",
                    ),
                    source="signal_policy",
                    signal_type="wide_spread",
                    reason="wide spread mapped to passive buy",
                )
            )

        if (
            position.quantity <= 0
            and "extreme_orderbook_imbalance" in signal_types
            and metrics.orderbook_imbalance is not None
            and metrics.orderbook_imbalance >= Decimal("0.70")
        ):
            decisions.append(
                PaperTradingOrderDecision(
                    order=SimulatedOrder(
                        order_id=make_order_id(),
                        market_id=config.market_id,
                        asset_id=snapshot.asset_id,
                        side="buy",
                        size=config.order_size,
                        created_at=snapshot.snapshot_ts,
                        order_type="market",
                        reason="paper_signal_imbalance_entry",
                    ),
                    source="signal_policy",
                    signal_type="extreme_orderbook_imbalance",
                    reason="bid-heavy imbalance mapped to marketable paper buy",
                )
            )

        if (
            position.quantity > 0
            and metrics.spread_pct is not None
            and metrics.spread_pct <= Decimal("0.04")
            and metrics.best_bid is not None
        ):
            decisions.append(
                PaperTradingOrderDecision(
                    order=SimulatedOrder(
                        order_id=make_order_id(),
                        market_id=config.market_id,
                        asset_id=snapshot.asset_id,
                        side="sell",
                        size=min(position.quantity, config.order_size),
                        created_at=snapshot.snapshot_ts,
                        limit_price=metrics.best_bid,
                        reason="paper_signal_spread_exit",
                    ),
                    source="signal_policy",
                    signal_type="spread_normalized",
                    reason="spread normalized while paper position is open",
                )
            )

        return decisions

