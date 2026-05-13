from decimal import Decimal

from polybot.live_readiness.readiness_score import ReadinessCheckResult


def check_boolean(name: str, passed: bool, *, message: str, severity: str = "critical") -> ReadinessCheckResult:
    return ReadinessCheckResult(
        name=name,
        passed=passed,
        score=Decimal("100") if passed else Decimal("0"),
        severity=severity,
        message="ok" if passed else message,
    )


def check_threshold(
    name: str,
    value: Decimal,
    *,
    maximum: Decimal,
    message: str,
    severity: str = "critical",
) -> ReadinessCheckResult:
    passed = value <= maximum
    score = Decimal("100") if passed else max(Decimal("0"), Decimal("100") - ((value - maximum) * Decimal("100")))
    return ReadinessCheckResult(
        name=name,
        passed=passed,
        score=score,
        severity=severity,
        message="ok" if passed else message,
        metadata={"value": str(value), "maximum": str(maximum)},
    )
