import uuid
from decimal import Decimal

from polybot.backtesting.portfolio import PortfolioState
from polybot.backtesting.results import SimulatedFill
from polybot.data.schemas import OrderBookSnapshot, Trade
from polybot.paper_trading.models import PaperTradingConfig
from polybot.paper_trading.risk import PaperRiskManager
from polybot.paper_trading.signal_policy import SignalDrivenPaperPolicy
from polybot.research.inefficiencies import scan_inefficiencies
from polybot.shadow_trading.execution_analysis import compare_execution
from polybot.shadow_trading.fill_analysis import (
    average_slippage,
    count_impossible_fills,
    count_missed_fills,
    fill_probability,
)
from polybot.shadow_trading.latency_analysis import average_delay_ms, latency_anomalies
from polybot.shadow_trading.market_reality import build_market_reality_snapshot
from polybot.shadow_trading.models import (
    ShadowDecision,
    ShadowFill,
    ShadowOrder,
    ShadowTradingResult,
    now_utc,
)
from polybot.shadow_trading.order_simulator import simulate_shadow_fill


class ShadowTradingEngine:
    def __init__(
        self,
        config: PaperTradingConfig,
        *,
        signal_policy: SignalDrivenPaperPolicy | None = None,
    ) -> None:
        self.config = config
        self.run_id = config.run_id or str(uuid.uuid4())
        self.signal_policy = signal_policy or SignalDrivenPaperPolicy()
        self.risk = PaperRiskManager(config)

    def run(
        self,
        *,
        snapshots: list[OrderBookSnapshot],
        trades: list[Trade] | None = None,
    ) -> ShadowTradingResult:
        started_at = now_utc()
        ordered = sorted(snapshots, key=lambda item: item.snapshot_ts)
        trades = sorted(trades or [], key=lambda item: item.traded_at)
        portfolio = PortfolioState(cash=self.config.initial_cash)
        decisions: list[ShadowDecision] = []
        fills = []
        comparisons = []
        reality_snapshots = [build_market_reality_snapshot(item) for item in ordered]
        signal_count = 0

        for index, snapshot in enumerate(ordered):
            window = ordered[max(0, index - self.config.signal_window + 1) : index + 1]
            trade_window = [
                trade for trade in trades if trade.traded_at <= snapshot.snapshot_ts
            ][-self.config.signal_window :]
            report = scan_inefficiencies(
                market_id=self.config.market_id,
                snapshots=window,
                trades=trade_window,
            )
            current_signals = [
                signal
                for signal in report.signals
                if signal.timestamp == snapshot.snapshot_ts and signal.asset_id == snapshot.asset_id
            ]
            signal_count += len(current_signals)
            for decision in self.signal_policy.decide(
                snapshot=snapshot,
                signals=current_signals,
                portfolio=portfolio,
                config=self.config,
            ):
                risk = self.risk.validate_order(decision.order, portfolio)
                shadow_order = ShadowOrder(
                    order_id=decision.order.order_id,
                    market_id=decision.order.market_id,
                    asset_id=decision.order.asset_id,
                    side=decision.order.side,
                    size=decision.order.size,
                    created_at=decision.order.created_at,
                    order_type=decision.order.order_type,
                    limit_price=decision.order.limit_price,
                    source=decision.source,
                    signal_type=decision.signal_type,
                    reason=decision.reason,
                )
                shadow_decision = ShadowDecision(
                    decision_id=str(uuid.uuid4()),
                    market_id=self.config.market_id,
                    asset_id=snapshot.asset_id,
                    timestamp=snapshot.snapshot_ts,
                    action=decision.order.side,
                    order=shadow_order,
                    signal_type=decision.signal_type,
                    confidence=_signal_confidence(current_signals, decision.signal_type),
                    status="risk_rejected" if not risk.allowed else "created",
                    reason=risk.reason if not risk.allowed else decision.reason,
                )
                decisions.append(shadow_decision)
                if not risk.allowed:
                    continue
                fill = simulate_shadow_fill(
                    shadow_order,
                    ordered[index:],
                    latency_ms=self.config.latency_ms,
                )
                fills.append(fill)
                if fill.fill_possible:
                    portfolio.apply_fill(_to_portfolio_fill(fill, self.config.fee_bps))
                reality = next(
                    (
                        item
                        for item in reality_snapshots
                        if item.asset_id == fill.asset_id and item.snapshot_ts == fill.observed_at
                    ),
                    None,
                )
                comparisons.append(
                    compare_execution(decision=shadow_decision, fill=fill, reality=reality)
                )

        anomalies = [
            *latency_anomalies(fills),
            *_execution_anomalies(fills),
        ]
        finished_at = now_utc()
        return ShadowTradingResult(
            run_id=self.run_id,
            market_id=self.config.market_id,
            strategy_name=self.config.strategy_name,
            started_at=started_at,
            finished_at=finished_at,
            snapshot_count=len(ordered),
            signal_count=signal_count,
            decision_count=len(decisions),
            theoretical_fill_count=sum(1 for fill in fills if fill.fill_possible),
            missed_fill_count=count_missed_fills(fills),
            impossible_fill_count=count_impossible_fills(fills),
            average_slippage=average_slippage(fills),
            average_delay_ms=average_delay_ms(fills),
            fill_probability=fill_probability(fills),
            decisions=decisions,
            fills=fills,
            comparisons=comparisons,
            market_snapshots=reality_snapshots[-1000:],
            anomalies=anomalies,
            metadata={"decision_mode": "signals", "latency_ms": self.config.latency_ms},
        )


def _signal_confidence(signals, signal_type: str | None) -> Decimal | None:
    for signal in signals:
        if signal.signal_type == signal_type:
            return signal.confidence
    return None


def _execution_anomalies(fills) -> list[str]:
    anomalies: list[str] = []
    if any(not fill.fill_possible for fill in fills):
        anomalies.append("shadow fill impossible for at least one theoretical order")
    if any(abs(fill.slippage_abs) > Decimal("0.03") for fill in fills):
        anomalies.append("excessive slippage detected in shadow fills")
    return anomalies


def _to_portfolio_fill(fill: ShadowFill, fee_bps: Decimal) -> SimulatedFill:
    notional = (
        fill.filled_size * fill.average_price
        if fill.average_price is not None
        else Decimal("0")
    )
    fees = notional * (fee_bps / Decimal("10000"))
    return SimulatedFill(
        order_id=fill.order_id,
        asset_id=fill.asset_id,
        side=fill.side,
        requested_size=fill.requested_size,
        filled_size=fill.filled_size,
        average_price=fill.average_price,
        fees=fees,
        slippage=fill.slippage_abs,
        filled_at=fill.observed_at,
        partial=fill.partial,
        latency_ms=fill.delay_ms,
    )
