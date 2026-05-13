from decimal import Decimal
from typing import Any, Protocol

from polybot.backtesting.results import BacktestResult, BacktestTrade, SimulatedFill
from polybot.evaluation.models import DrawdownMetrics, StrategyPerformance
from polybot.paper_trading.models import PaperTradingResult


class ResultLike(Protocol):
    market_id: str
    trades: list[BacktestTrade]
    fills: list[SimulatedFill]


def compute_strategy_performance(
    result: BacktestResult | PaperTradingResult,
    *,
    source: str,
) -> StrategyPerformance:
    trades = list(result.trades)
    fills = list(_result_fills(result))
    net_pnls = [trade.net_pnl for trade in trades]
    wins = [pnl for pnl in net_pnls if pnl > 0]
    losses = [pnl for pnl in net_pnls if pnl < 0]
    attempted_orders = _attempted_orders(result)
    filled_orders = len(fills)
    rejected_orders = int(getattr(result, "rejected_orders", 0))
    initial_equity = _initial_equity(result)
    equity_curve = equity_curve_from_trades(trades, initial_equity=initial_equity)

    return StrategyPerformance(
        strategy_name=_strategy_name(result),
        market_id=result.market_id,
        source=source,
        gross_pnl=_gross_pnl(result),
        net_pnl=result.net_pnl,
        trade_count=len(trades),
        attempted_orders=attempted_orders,
        filled_orders=filled_orders,
        rejected_trades=rejected_orders,
        win_rate=_ratio(Decimal(len(wins)), Decimal(len(trades))),
        average_win=_average(wins),
        average_loss=_average(losses),
        average_exposure=Decimal(str(getattr(result, "average_exposure", Decimal("0")))),
        max_exposure=Decimal(str(getattr(result, "max_exposure", Decimal("0")))),
        fill_rate=_fill_rate(result, filled_orders=filled_orders, attempted_orders=attempted_orders),
        partial_fill_rate=_partial_fill_rate(result, fills),
        average_slippage=_average([abs(fill.slippage) for fill in fills]),
        fees=Decimal(str(getattr(result, "fees", Decimal("0")))),
        latency_impact=_latency_impact(result, fills),
        signal_hit_rate=_signal_hit_rate(result),
        profit_factor=_profit_factor(wins, losses),
        drawdown=compute_drawdown(equity_curve),
    )


def equity_curve_from_trades(
    trades: list[BacktestTrade],
    *,
    initial_equity: Decimal = Decimal("0"),
) -> list[Decimal]:
    curve = [initial_equity]
    current = initial_equity
    for trade in trades:
        current += trade.net_pnl
        curve.append(current)
    return curve


def compute_drawdown(equity_curve: list[Decimal]) -> DrawdownMetrics:
    if not equity_curve:
        return DrawdownMetrics(
            max_drawdown=Decimal("0"),
            max_drawdown_abs=Decimal("0"),
            peak_equity=Decimal("0"),
            trough_equity=Decimal("0"),
            recovery_equity=None,
        )

    peak = equity_curve[0]
    peak_for_max = peak
    trough_for_max = peak
    trough_index_for_max = 0
    max_drawdown = Decimal("0")
    max_drawdown_abs = Decimal("0")

    for index, equity in enumerate(equity_curve):
        if equity > peak:
            peak = equity
        drawdown_abs = peak - equity
        drawdown = _ratio(drawdown_abs, peak) if peak > 0 else Decimal("0")
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            max_drawdown_abs = drawdown_abs
            peak_for_max = peak
            trough_for_max = equity
            trough_index_for_max = index

    recovery_equity = next(
        (
            equity
            for equity in equity_curve[trough_index_for_max + 1 :]
            if max_drawdown_abs > 0 and equity >= peak_for_max
        ),
        None,
    )
    return DrawdownMetrics(
        max_drawdown=max_drawdown,
        max_drawdown_abs=max_drawdown_abs,
        peak_equity=peak_for_max,
        trough_equity=trough_for_max,
        recovery_equity=recovery_equity,
    )


def _result_fills(result: BacktestResult | PaperTradingResult) -> list[SimulatedFill]:
    fills = getattr(result, "fills", None)
    if fills is not None:
        return list(fills)
    return [trade.fill for trade in result.trades]


def _strategy_name(result: BacktestResult | PaperTradingResult) -> str:
    return str(getattr(result, "strategy_name", getattr(result, "strategy_id", "unknown")))


def _gross_pnl(result: BacktestResult | PaperTradingResult) -> Decimal:
    gross = getattr(result, "gross_pnl", None)
    if gross is not None:
        return Decimal(str(gross))
    return Decimal(str(result.net_pnl)) + Decimal(str(getattr(result, "fees", Decimal("0"))))


def _attempted_orders(result: BacktestResult | PaperTradingResult) -> int:
    attempted = getattr(result, "attempted_orders", None)
    if attempted is not None:
        return int(attempted)
    metadata: dict[str, Any] = getattr(result, "metadata", {})
    if "attempted_orders" in metadata:
        return int(metadata["attempted_orders"])
    fill_rate = Decimal(str(getattr(result, "fill_rate", Decimal("0"))))
    filled_orders = len(_result_fills(result))
    if fill_rate > 0:
        return int((Decimal(filled_orders) / fill_rate).to_integral_value())
    return filled_orders


def _initial_equity(result: BacktestResult | PaperTradingResult) -> Decimal:
    final_equity = getattr(result, "final_equity", None)
    if final_equity is not None:
        return Decimal(str(final_equity)) - Decimal(str(result.net_pnl))
    metadata: dict[str, Any] = getattr(result, "metadata", {})
    if "initial_cash" in metadata:
        return Decimal(str(metadata["initial_cash"]))
    return Decimal("0")


def _fill_rate(
    result: BacktestResult | PaperTradingResult,
    *,
    filled_orders: int,
    attempted_orders: int,
) -> Decimal:
    fill_rate = getattr(result, "fill_rate", None)
    if fill_rate is not None:
        return Decimal(str(fill_rate))
    return _ratio(Decimal(filled_orders), Decimal(attempted_orders))


def _partial_fill_rate(
    result: BacktestResult | PaperTradingResult,
    fills: list[SimulatedFill],
) -> Decimal:
    partial_fill_rate = getattr(result, "partial_fill_rate", None)
    if partial_fill_rate is not None:
        return Decimal(str(partial_fill_rate))
    return _ratio(Decimal(sum(1 for fill in fills if fill.partial)), Decimal(len(fills)))


def _latency_impact(
    result: BacktestResult | PaperTradingResult,
    fills: list[SimulatedFill],
) -> Decimal:
    latency_impact = getattr(result, "latency_impact", None)
    if latency_impact is not None:
        return Decimal(str(latency_impact))
    return sum((abs(fill.slippage * fill.filled_size) for fill in fills), Decimal("0"))


def _signal_hit_rate(result: BacktestResult | PaperTradingResult) -> Decimal | None:
    signal_count = getattr(result, "signal_count", None)
    filled_orders = getattr(result, "filled_orders", None)
    if signal_count is None or filled_orders is None:
        return None
    return _ratio(Decimal(filled_orders), Decimal(signal_count))


def _profit_factor(wins: list[Decimal], losses: list[Decimal]) -> Decimal | None:
    gross_win = sum(wins, Decimal("0"))
    gross_loss = abs(sum(losses, Decimal("0")))
    if gross_loss == 0:
        return None
    return gross_win / gross_loss


def _average(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal(len(values))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= 0:
        return Decimal("0")
    return numerator / denominator
