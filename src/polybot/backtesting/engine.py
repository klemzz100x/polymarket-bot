from decimal import Decimal
from statistics import mean, pstdev
from typing import Protocol
import uuid

from polybot.backtesting.execution_simulator import ExecutionSimulator
from polybot.backtesting.fee_model import FeeModel
from polybot.backtesting.latency_model import LatencyModel
from polybot.backtesting.portfolio import PortfolioState
from polybot.backtesting.results import BacktestConfig, BacktestResult, BacktestTrade, SimulatedOrder
from polybot.backtesting.slippage_model import SlippageModel
from polybot.data.schemas import OrderBookSnapshot
from polybot.research.metrics import compute_orderbook_metrics


class BacktestStrategy(Protocol):
    strategy_id: str

    def on_snapshot(
        self,
        *,
        snapshot: OrderBookSnapshot,
        portfolio: PortfolioState,
        config: BacktestConfig,
    ) -> list[SimulatedOrder]:
        ...


class BacktestEngine:
    def __init__(self, config: BacktestConfig) -> None:
        self.config = config
        self.simulator = ExecutionSimulator(
            fee_model=FeeModel(config.fee_bps),
            latency_model=LatencyModel(config.latency_ms),
            slippage_model=SlippageModel(),
        )

    def run(
        self,
        *,
        strategy: BacktestStrategy,
        snapshots: list[OrderBookSnapshot],
    ) -> BacktestResult:
        ordered = sorted(snapshots, key=lambda snapshot: snapshot.snapshot_ts)
        portfolio = PortfolioState(cash=self.config.initial_cash)
        trades: list[BacktestTrade] = []
        attempted_orders = 0
        latency_impact = Decimal("0")

        for index, snapshot in enumerate(ordered):
            mark_price = compute_orderbook_metrics(snapshot).mid_price
            if mark_price is not None:
                portfolio.mark({snapshot.asset_id: mark_price})

            for order in strategy.on_snapshot(
                snapshot=snapshot,
                portfolio=portfolio,
                config=self.config,
            ):
                attempted_orders += 1
                if not self._risk_allows(order, portfolio):
                    continue
                fill = self.simulator.execute(order, ordered[index:])
                if fill.filled_size <= 0:
                    continue
                gross_pnl = portfolio.apply_fill(fill)
                net_pnl = gross_pnl - fill.fees
                latency_impact += abs(fill.slippage * fill.filled_size)
                trades.append(BacktestTrade(order=order, fill=fill, gross_pnl=gross_pnl, net_pnl=net_pnl))

        final_equity = portfolio.equity_curve[-1] if portfolio.equity_curve else self.config.initial_cash
        net_pnl = final_equity - self.config.initial_cash
        gross_pnl = net_pnl + portfolio.fees_paid
        wins = [trade.net_pnl for trade in trades if trade.net_pnl > 0]
        losses = [trade.net_pnl for trade in trades if trade.net_pnl < 0]
        slippages = [trade.fill.slippage for trade in trades if trade.fill.filled_size > 0]
        returns = [float(value) for value in _equity_returns(portfolio.equity_curve)]

        return BacktestResult(
            strategy_id=strategy.strategy_id,
            market_id=self.config.market_id,
            trades=trades,
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
            trade_count=len(trades),
            win_rate=_ratio(Decimal(len(wins)), Decimal(len(trades))),
            average_win=_average(wins),
            average_loss=_average(losses),
            max_drawdown=_max_drawdown(portfolio.equity_curve),
            average_exposure=_average(portfolio.exposure_curve),
            max_exposure=max(portfolio.exposure_curve) if portfolio.exposure_curve else Decimal("0"),
            fill_rate=_ratio(Decimal(len(trades)), Decimal(attempted_orders)),
            partial_fill_rate=_ratio(
                Decimal(sum(1 for trade in trades if trade.fill.partial)),
                Decimal(len(trades)),
            ),
            average_slippage=_average(slippages),
            fees=portfolio.fees_paid,
            latency_impact=latency_impact,
            sharpe_approx=_sharpe(returns),
            profit_factor=_profit_factor(wins, losses),
            metadata={
                "attempted_orders": attempted_orders,
                "initial_cash": str(self.config.initial_cash),
                "order_size": str(self.config.order_size),
                "fee_bps": str(self.config.fee_bps),
                "latency_ms": self.config.latency_ms,
            },
        )

    def _risk_allows(self, order: SimulatedOrder, portfolio: PortfolioState) -> bool:
        position = portfolio.position_for(order.asset_id)
        if order.side == "buy" and position.quantity + order.size > self.config.max_position:
            return False
        if portfolio.current_exposure() > self.config.max_market_exposure:
            return False
        return True


def make_order_id() -> str:
    return str(uuid.uuid4())


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= 0:
        return Decimal("0")
    return numerator / denominator


def _average(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal(len(values))


def _max_drawdown(equity_curve: list[Decimal]) -> Decimal:
    peak: Decimal | None = None
    max_dd = Decimal("0")
    for equity in equity_curve:
        peak = equity if peak is None else max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak)
    return max_dd


def _equity_returns(equity_curve: list[Decimal]) -> list[Decimal]:
    returns: list[Decimal] = []
    for previous, current in zip(equity_curve, equity_curve[1:], strict=False):
        if previous != 0:
            returns.append((current - previous) / previous)
    return returns


def _sharpe(returns: list[float]) -> Decimal | None:
    if len(returns) < 2:
        return None
    std = pstdev(returns)
    if std == 0:
        return None
    return Decimal(str(mean(returns) / std))


def _profit_factor(wins: list[Decimal], losses: list[Decimal]) -> Decimal | None:
    gross_win = sum(wins, Decimal("0"))
    gross_loss = abs(sum(losses, Decimal("0")))
    if gross_loss == 0:
        return None
    return gross_win / gross_loss
