from decimal import Decimal

from polybot.live_readiness.readiness_checks import check_threshold
from polybot.live_readiness.readiness_score import ReadinessCheckResult
from polybot.shadow_trading.models import ShadowTradingResult


def execution_quality_checks(
    shadow: ShadowTradingResult | None,
    *,
    max_slippage: Decimal = Decimal("0.05"),
    max_delay_ms: Decimal = Decimal("5000"),
) -> list[ReadinessCheckResult]:
    if shadow is None:
        return [
            ReadinessCheckResult(
                name="shadow_result_available",
                passed=False,
                score=Decimal("0"),
                severity="critical",
                message="No shadow trading result available.",
            )
        ]
    return [
        ReadinessCheckResult(
            name="shadow_market_data_available",
            passed=shadow.snapshot_count > 0,
            score=Decimal("100") if shadow.snapshot_count > 0 else Decimal("0"),
            severity="critical",
            message="ok" if shadow.snapshot_count > 0 else "No orderbook snapshots were available.",
            metadata={"snapshot_count": shadow.snapshot_count},
        ),
        ReadinessCheckResult(
            name="shadow_decision_flow_active",
            passed=shadow.decision_count > 0,
            score=Decimal("100") if shadow.decision_count > 0 else Decimal("50"),
            severity="warning",
            message="ok" if shadow.decision_count > 0 else "No shadow decisions were generated.",
            metadata={"decision_count": shadow.decision_count},
        ),
        check_threshold(
            "execution_shadow_slippage",
            shadow.average_slippage,
            maximum=max_slippage,
            message="Shadow slippage is too high.",
        ),
        check_threshold(
            "execution_shadow_latency",
            shadow.average_delay_ms,
            maximum=max_delay_ms,
            message="Shadow execution delay is too high.",
        ),
        ReadinessCheckResult(
            name="shadow_fill_realism",
            passed=shadow.impossible_fill_count == 0,
            score=Decimal("100") if shadow.impossible_fill_count == 0 else Decimal("0"),
            severity="critical",
            message="ok" if shadow.impossible_fill_count == 0 else "Impossible fills detected in shadow layer.",
            metadata={"impossible_fill_count": shadow.impossible_fill_count},
        ),
    ]
