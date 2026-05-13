from decimal import Decimal

from polybot.backtesting.results import BacktestResult
from polybot.evaluation.performance import compute_strategy_performance
from polybot.paper_trading.models import PaperTradingResult


def compare_backtest_vs_paper(
    *,
    backtest: BacktestResult,
    paper: PaperTradingResult,
) -> dict[str, str]:
    backtest_perf = compute_strategy_performance(backtest, source="backtest")
    paper_perf = compute_strategy_performance(paper, source="paper")
    return {
        "market_id": paper.market_id,
        "strategy_name": paper.strategy_name,
        "backtest_net_pnl": str(backtest_perf.net_pnl),
        "paper_net_pnl": str(paper_perf.net_pnl),
        "net_pnl_delta": str(backtest_perf.net_pnl - paper_perf.net_pnl),
        "backtest_fill_rate": str(backtest_perf.fill_rate),
        "paper_fill_rate": str(paper_perf.fill_rate),
        "fill_rate_delta": str(backtest_perf.fill_rate - paper_perf.fill_rate),
        "backtest_partial_fill_rate": str(backtest_perf.partial_fill_rate),
        "paper_partial_fill_rate": str(paper_perf.partial_fill_rate),
        "backtest_average_slippage": str(backtest_perf.average_slippage),
        "paper_average_slippage": str(paper_perf.average_slippage),
        "slippage_delta": str(backtest_perf.average_slippage - paper_perf.average_slippage),
        "backtest_max_drawdown": str(backtest_perf.drawdown.max_drawdown),
        "paper_max_drawdown": str(paper_perf.drawdown.max_drawdown),
        "drawdown_delta": str(backtest_perf.drawdown.max_drawdown - paper_perf.drawdown.max_drawdown),
        "backtest_trade_count": str(backtest_perf.trade_count),
        "paper_trade_count": str(paper_perf.trade_count),
        "trade_count_delta": str(Decimal(backtest_perf.trade_count - paper_perf.trade_count)),
    }
