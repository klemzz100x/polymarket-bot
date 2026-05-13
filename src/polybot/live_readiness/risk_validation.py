from decimal import Decimal

from polybot.live_readiness.readiness_checks import check_threshold
from polybot.live_readiness.readiness_score import ReadinessCheckResult


def risk_checks(
    *,
    drawdown: Decimal = Decimal("0"),
    exposure: Decimal = Decimal("0"),
    rejected_rate: Decimal = Decimal("0"),
    max_drawdown: Decimal = Decimal("0.20"),
    max_exposure: Decimal = Decimal("250"),
    max_rejected_rate: Decimal = Decimal("0.50"),
) -> list[ReadinessCheckResult]:
    return [
        check_threshold("paper_drawdown", drawdown, maximum=max_drawdown, message="Paper drawdown exceeds readiness limit."),
        check_threshold("paper_exposure", exposure, maximum=max_exposure, message="Paper exposure exceeds readiness limit."),
        check_threshold("strategy_rejected_shadow_orders", rejected_rate, maximum=max_rejected_rate, message="Rejected shadow order rate is too high.", severity="warning"),
    ]
