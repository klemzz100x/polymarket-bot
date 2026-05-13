from decimal import Decimal

from polybot.risk.kill_switch import KillSwitchEvaluation, evaluate_kill_switch
from polybot.shadow_trading.models import ShadowTradingResult


def evaluate_pre_live_kill_switch(
    *,
    shadow: ShadowTradingResult | None = None,
    drawdown: Decimal = Decimal("0"),
    stale_data_count: int = 0,
    db_healthy: bool = True,
    redis_healthy: bool = True,
    api_healthy: bool = True,
    collector_failures: int = 0,
    rejected_order_rate: Decimal = Decimal("0"),
    missing_market_data: bool = False,
) -> KillSwitchEvaluation:
    return evaluate_kill_switch(
        drawdown=drawdown,
        stale_data_count=stale_data_count,
        db_healthy=db_healthy,
        redis_healthy=redis_healthy,
        api_healthy=api_healthy,
        average_slippage=shadow.average_slippage if shadow else Decimal("0"),
        rejected_order_rate=rejected_order_rate,
        collector_failures=collector_failures,
        latency_ms=shadow.average_delay_ms if shadow else Decimal("0"),
        missing_market_data=missing_market_data,
    )
