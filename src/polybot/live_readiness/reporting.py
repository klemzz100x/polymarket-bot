from polybot.live_readiness.readiness_score import LiveReadinessReport
from polybot.resources.markdown import render_frontmatter


def render_live_readiness_report(report: LiveReadinessReport) -> str:
    metadata = {
        "type": "live-readiness-report",
        "status": report.status,
        "score": str(report.live_readiness_score),
        "tags": ["live-readiness", "pre-live", "risk"],
    }
    checks = "\n".join(
        f"- `{check.severity}` `{check.name}` passed=`{check.passed}` score=`{check.score}` {check.message}"
        for check in report.checks
    )
    recommendations = "\n".join(f"- {item}" for item in report.recommendations)
    return f"""{render_frontmatter(metadata)}
# Live Readiness Report

## Executive Summary
- Status: `{report.status}`
- Live readiness score: `{report.live_readiness_score}`
- Execution quality score: `{report.execution_quality_score}`
- Infrastructure health score: `{report.infrastructure_health_score}`
- Strategy stability score: `{report.strategy_stability_score}`
- Kill switch state: `{report.kill_switch_state}`

## Metrics
{checks}

## Anomalies
- Any failed critical check forces readiness to `failed`.

## Problems Detected
{recommendations or "- No blocking problems detected."}

## Strategies Concerned
- See shadow trading and paper trading reports for strategy-level details.

## Recommendations
{recommendations or "- Continue shadow validation. Do not enable live trading yet."}

## Next Actions
- Resolve failed checks.
- Re-run shadow trading.
- Re-run readiness scoring.
- Review kill switch events.

## Links
- [[Shadow Trading]]
- [[Execution Quality]]
- [[Risk Management]]
- [[Paper Trading]]
"""
