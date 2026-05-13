from polybot.backtesting.engine import BacktestStrategy
from polybot.strategies.research.v1 import (
    LiquidityVacuumFade,
    OrderbookImbalanceMomentum,
    WideSpreadMeanReversion,
)


def get_research_strategy(name: str) -> BacktestStrategy:
    normalized = name.strip().lower().replace("_", "-")
    if normalized in {"wide-spread-mean-reversion", "wide-spread"}:
        return WideSpreadMeanReversion()
    if normalized in {"orderbook-imbalance-momentum", "imbalance-momentum"}:
        return OrderbookImbalanceMomentum()
    if normalized in {"liquidity-vacuum-fade", "liquidity-vacuum"}:
        return LiquidityVacuumFade()
    raise ValueError(f"Unknown research strategy: {name}")

