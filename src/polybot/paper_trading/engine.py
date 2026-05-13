from decimal import Decimal
from pathlib import Path
import uuid

from polybot.backtesting.engine import BacktestStrategy
from polybot.backtesting.execution_simulator import ExecutionSimulator
from polybot.backtesting.fee_model import FeeModel
from polybot.backtesting.latency_model import LatencyModel
from polybot.backtesting.portfolio import PortfolioState
from polybot.backtesting.results import BacktestConfig, BacktestTrade, SimulatedOrder
from polybot.backtesting.slippage_model import SlippageModel
from polybot.data.schemas import OrderBookSnapshot, Trade
from polybot.paper_trading.ledger import JsonlPaperLedger
from polybot.paper_trading.models import (
    PaperTradingConfig,
    PaperTradingEvent,
    PaperTradingOrderDecision,
    PaperTradingResult,
    now_utc,
)
from polybot.paper_trading.risk import PaperRiskManager
from polybot.paper_trading.signal_policy import SignalDrivenPaperPolicy
from polybot.research.inefficiencies import scan_inefficiencies
from polybot.research.metrics import compute_orderbook_metrics
from polybot.research.signals import ResearchSignal


class PaperTradingEngine:
    def __init__(
        self,
        config: PaperTradingConfig,
        *,
        strategy: BacktestStrategy | None = None,
        signal_policy: SignalDrivenPaperPolicy | None = None,
    ) -> None:
        self.config = config
        self.run_id = config.run_id or str(uuid.uuid4())
        self.strategy = strategy
        self.signal_policy = signal_policy or SignalDrivenPaperPolicy()
        self.risk = PaperRiskManager(config)
        self.simulator = ExecutionSimulator(
            fee_model=FeeModel(config.fee_bps),
            latency_model=LatencyModel(config.latency_ms),
            slippage_model=SlippageModel(),
        )

    def run(
        self,
        *,
        snapshots: list[OrderBookSnapshot],
        trades: list[Trade] | None = None,
    ) -> PaperTradingResult:
        started_at = now_utc()
        ordered = sorted(snapshots, key=lambda snapshot: snapshot.snapshot_ts)
        trades = sorted(trades or [], key=lambda trade: trade.traded_at)
        portfolio = PortfolioState(cash=self.config.initial_cash)
        events: list[PaperTradingEvent] = []
        fills = []
        backtest_trades: list[BacktestTrade] = []
        all_signals: list[ResearchSignal] = []
        attempted_orders = 0
        rejected_orders = 0

        self._event(events, "paper_run_started", started_at, {"config": self.config})

        for index, snapshot in enumerate(ordered):
            metric = compute_orderbook_metrics(snapshot)
            if metric.mid_price is not None:
                portfolio.mark({snapshot.asset_id: metric.mid_price})

            window = _snapshot_window(ordered, index=index, limit=self.config.signal_window)
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
            all_signals.extend(current_signals)
            for signal in current_signals:
                self._event(events, "research_signal", signal.timestamp, signal.to_dict())

            decisions = self._decisions(snapshot=snapshot, signals=current_signals, portfolio=portfolio)
            for decision in decisions:
                attempted_orders += 1
                risk = self.risk.validate_order(decision.order, portfolio)
                if not risk.allowed:
                    rejected_orders += 1
                    self._event(
                        events,
                        "paper_order_rejected",
                        snapshot.snapshot_ts,
                        {
                            "order": decision.order,
                            "source": decision.source,
                            "reason": risk.reason,
                        },
                    )
                    continue

                self._event(
                    events,
                    "paper_order_created",
                    snapshot.snapshot_ts,
                    {
                        "order": decision.order,
                        "source": decision.source,
                        "signal_type": decision.signal_type,
                        "reason": decision.reason,
                    },
                )
                fill = self.simulator.execute(decision.order, ordered[index:])
                if fill.filled_size <= 0:
                    self._event(
                        events,
                        "paper_order_unfilled",
                        fill.filled_at,
                        {"order": decision.order, "fill": fill},
                    )
                    continue
                gross_pnl = portfolio.apply_fill(fill)
                net_pnl = gross_pnl - fill.fees
                fills.append(fill)
                backtest_trade = BacktestTrade(
                    order=decision.order,
                    fill=fill,
                    gross_pnl=gross_pnl,
                    net_pnl=net_pnl,
                )
                backtest_trades.append(backtest_trade)
                self._event(
                    events,
                    "paper_fill",
                    fill.filled_at,
                    {"order": decision.order, "fill": fill, "net_pnl": net_pnl},
                )

        latest_marks = {}
        for snapshot in ordered:
            metric = compute_orderbook_metrics(snapshot)
            if metric.mid_price is not None:
                latest_marks[snapshot.asset_id] = metric.mid_price
        final_equity = portfolio.mark(latest_marks) if latest_marks else portfolio.cash
        result = PaperTradingResult(
            run_id=self.run_id,
            market_id=self.config.market_id,
            strategy_name=self.config.strategy_name,
            started_at=started_at,
            finished_at=now_utc(),
            snapshot_count=len(ordered),
            signal_count=len(all_signals),
            attempted_orders=attempted_orders,
            filled_orders=len(fills),
            rejected_orders=rejected_orders,
            fills=fills,
            trades=backtest_trades,
            signals=all_signals,
            events=events,
            final_cash=portfolio.cash,
            final_equity=final_equity,
            net_pnl=final_equity - self.config.initial_cash,
            fees=portfolio.fees_paid,
            max_exposure=max(portfolio.exposure_curve) if portfolio.exposure_curve else Decimal("0"),
            fill_rate=_ratio(Decimal(len(fills)), Decimal(attempted_orders)),
            partial_fill_rate=_ratio(
                Decimal(sum(1 for fill in fills if fill.partial)),
                Decimal(len(fills)),
            ),
            metadata={"decision_mode": self.config.decision_mode},
        )

        self._event(
            events,
            "paper_run_finished",
            result.finished_at,
            {
                "run_id": result.run_id,
                "net_pnl": result.net_pnl,
                "final_equity": result.final_equity,
                "filled_orders": result.filled_orders,
                "rejected_orders": result.rejected_orders,
            },
        )
        self._write_ledger(events)
        return result

    def _decisions(
        self,
        *,
        snapshot: OrderBookSnapshot,
        signals: list[ResearchSignal],
        portfolio: PortfolioState,
    ) -> list[PaperTradingOrderDecision]:
        decisions: list[PaperTradingOrderDecision] = []
        mode = self.config.decision_mode.lower()
        if mode in {"strategy", "hybrid"} and self.strategy is not None:
            strategy_config = BacktestConfig(
                strategy_name=self.config.strategy_name,
                market_id=self.config.market_id,
                initial_cash=self.config.initial_cash,
                order_size=self.config.order_size,
                max_position=self.config.max_position,
                max_market_exposure=self.config.max_market_exposure,
                fee_bps=self.config.fee_bps,
                latency_ms=self.config.latency_ms,
            )
            for order in self.strategy.on_snapshot(
                snapshot=snapshot,
                portfolio=portfolio,
                config=strategy_config,
            ):
                decisions.append(
                    PaperTradingOrderDecision(
                        order=order,
                        source="research_strategy",
                        reason=order.reason,
                    )
                )
        if mode in {"signals", "hybrid"}:
            decisions.extend(
                self.signal_policy.decide(
                    snapshot=snapshot,
                    signals=signals,
                    portfolio=portfolio,
                    config=self.config,
                )
            )
        return _dedupe_decisions(decisions)

    def _event(
        self,
        events: list[PaperTradingEvent],
        event_type: str,
        timestamp,
        payload: dict,
    ) -> None:
        events.append(
            PaperTradingEvent(
                run_id=self.run_id,
                event_type=event_type,
                timestamp=timestamp,
                payload=payload,
            )
        )

    def _write_ledger(self, events: list[PaperTradingEvent]) -> None:
        if not self.config.ledger_path:
            return
        JsonlPaperLedger(Path(self.config.ledger_path)).append_many(events)


def _snapshot_window(
    snapshots: list[OrderBookSnapshot],
    *,
    index: int,
    limit: int,
) -> list[OrderBookSnapshot]:
    start = max(0, index - limit + 1)
    return snapshots[start : index + 1]


def _dedupe_decisions(decisions: list[PaperTradingOrderDecision]) -> list[PaperTradingOrderDecision]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[PaperTradingOrderDecision] = []
    for decision in decisions:
        key = (decision.order.asset_id, decision.order.side, decision.order.reason)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(decision)
    return deduped


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= 0:
        return Decimal("0")
    return numerator / denominator
