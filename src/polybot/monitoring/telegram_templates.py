from decimal import Decimal

from polybot.live_readiness.readiness_score import LiveReadinessReport
from polybot.risk.kill_switch import KillSwitchEvent
from polybot.shadow_trading.models import ShadowFill


def shadow_fill_impossible(fill: ShadowFill) -> str:
    return "\n".join(
        [
            "Shadow fill impossible",
            f"order_id={fill.order_id}",
            f"asset_id={fill.asset_id}",
            f"requested_size={fill.requested_size}",
            f"reason={fill.reason or 'market conditions did not support the fill'}",
        ]
    )


def excessive_slippage(
    *,
    market_id: str,
    strategy_name: str,
    average_slippage: Decimal,
    threshold: Decimal,
) -> str:
    return "\n".join(
        [
            "Excessive shadow slippage",
            f"market_id={market_id}",
            f"strategy={strategy_name}",
            f"average_slippage={average_slippage}",
            f"threshold={threshold}",
        ]
    )


def readiness_degraded(report: LiveReadinessReport) -> str:
    return "\n".join(
        [
            "Live readiness degraded",
            f"status={report.status}",
            f"score={report.live_readiness_score}",
            f"kill_switch_state={report.kill_switch_state}",
            "No live trading is enabled.",
        ]
    )


def stale_collectors(*, stale_data_count: int, collector_failures: int) -> str:
    return "\n".join(
        [
            "Collector freshness issue",
            f"stale_data_count={stale_data_count}",
            f"collector_failures={collector_failures}",
        ]
    )


def kill_switch_triggered(event: KillSwitchEvent) -> str:
    return "\n".join(
        [
            "Kill switch triggered",
            f"trigger={event.trigger.value}",
            f"severity={event.severity}",
            f"reason={event.reason}",
        ]
    )


def abnormal_latency(*, market_id: str, latency_ms: Decimal, threshold_ms: Decimal) -> str:
    return "\n".join(
        [
            "Abnormal shadow latency",
            f"market_id={market_id}",
            f"latency_ms={latency_ms}",
            f"threshold_ms={threshold_ms}",
        ]
    )


def shadow_vs_paper_mismatch(*, market_id: str, mismatch_reason: str) -> str:
    return "\n".join(
        [
            "Shadow vs paper mismatch",
            f"market_id={market_id}",
            f"reason={mismatch_reason}",
        ]
    )


def live_mode_changed(*, previous_mode: str, next_mode: str) -> str:
    return "\n".join(["Live mode changed", f"previous={previous_mode}", f"next={next_mode}"])


def wallet_desync(*, wallet_address: str, reason: str) -> str:
    return "\n".join(["Wallet desync detected", f"wallet={wallet_address}", f"reason={reason}"])


def risk_gate_blocked_order(*, client_order_id: str, reason: str) -> str:
    return "\n".join(["Risk gate blocked order", f"client_order_id={client_order_id}", f"reason={reason}"])


def rejected_live_order(*, client_order_id: str, reason: str) -> str:
    return "\n".join(["Live order rejected", f"client_order_id={client_order_id}", f"reason={reason}"])


def abnormal_exposure(*, exposure_usd: Decimal, limit_usd: Decimal) -> str:
    return "\n".join(
        [
            "Abnormal exposure",
            f"exposure_usd={exposure_usd}",
            f"limit_usd={limit_usd}",
        ]
    )


def oms_reconciliation_issue(*, severity: str, description: str) -> str:
    return "\n".join(
        [
            "OMS reconciliation issue",
            f"severity={severity}",
            f"description={description}",
        ]
    )
