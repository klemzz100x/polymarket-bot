from dataclasses import asdict, dataclass, field
from datetime import datetime
from polybot.core.compat import UTC
from decimal import Decimal
import json
from typing import Any


@dataclass(frozen=True, slots=True)
class ReadinessCheckResult:
    name: str
    passed: bool
    score: Decimal
    severity: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LiveReadinessReport:
    report_id: str
    generated_at: datetime
    status: str
    live_readiness_score: Decimal
    execution_quality_score: Decimal
    infrastructure_health_score: Decimal
    strategy_stability_score: Decimal
    checks: list[ReadinessCheckResult]
    kill_switch_state: str
    recommendations: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def score_from_checks(
    *,
    report_id: str,
    checks: list[ReadinessCheckResult],
    kill_switch_state: str,
    metadata: dict[str, Any] | None = None,
) -> LiveReadinessReport:
    execution = _average(
        [check.score for check in checks if check.name.startswith("execution_") or check.name.startswith("shadow_")]
    )
    infrastructure = _average(
        [check.score for check in checks if check.name.startswith("infra_") or check.name in {"db_healthy", "redis_healthy", "api_healthy"}]
    )
    strategy = _average(
        [check.score for check in checks if check.name.startswith("strategy_") or check.name.startswith("paper_")]
    )
    if execution == 0 and infrastructure == 0 and strategy == 0:
        live_score = _average([check.score for check in checks])
    else:
        live_score = (execution * Decimal("0.40")) + (infrastructure * Decimal("0.35")) + (strategy * Decimal("0.25"))
    failed = [check for check in checks if not check.passed and check.severity == "critical"]
    status = "failed" if failed or kill_switch_state == "triggered" else ("degraded" if any(not check.passed for check in checks) else "ready")
    return LiveReadinessReport(
        report_id=report_id,
        generated_at=datetime.now(UTC),
        status=status,
        live_readiness_score=live_score,
        execution_quality_score=execution,
        infrastructure_health_score=infrastructure,
        strategy_stability_score=strategy,
        checks=checks,
        kill_switch_state=kill_switch_state,
        recommendations=_recommendations(checks, status),
        metadata=metadata or {},
    )


def _recommendations(checks: list[ReadinessCheckResult], status: str) -> list[str]:
    if status == "ready":
        return ["Continue shadow validation; do not enable live trading yet."]
    return [f"Fix {check.name}: {check.message}" for check in checks if not check.passed]


def _average(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal(len(values))


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
