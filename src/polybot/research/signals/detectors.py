from decimal import Decimal

from polybot.data.schemas import OrderBookSnapshot, Trade
from polybot.research.metrics import compute_orderbook_metrics
from polybot.research.signals.models import ResearchSignal


def detect_research_signals(
    *,
    market_id: str,
    snapshots: list[OrderBookSnapshot],
    trades: list[Trade],
) -> list[ResearchSignal]:
    signals: list[ResearchSignal] = []
    ordered = sorted(snapshots, key=lambda snapshot: snapshot.snapshot_ts)
    for previous, current in zip([None, *ordered[:-1]], ordered, strict=False):
        metrics = compute_orderbook_metrics(current)
        if metrics.spread_pct is not None and metrics.spread_pct >= Decimal("0.10"):
            signals.append(
                ResearchSignal(
                    market_id=market_id,
                    asset_id=current.asset_id,
                    timestamp=current.snapshot_ts,
                    signal_type="wide_spread",
                    severity=_severity(metrics.spread_pct, Decimal("0.20")),
                    confidence=min(Decimal("0.95"), metrics.spread_pct * Decimal("4")),
                    description="Spread is materially wider than normal research threshold.",
                    metrics={
                        "spread_abs": _s(metrics.spread_abs),
                        "spread_pct": _s(metrics.spread_pct),
                        "best_bid": _s(metrics.best_bid),
                        "best_ask": _s(metrics.best_ask),
                    },
                    hypothesis="Wide spread may indicate temporary liquidity gap or passive quoting opportunity.",
                    next_action="Check persistence across multiple snapshots before backtesting passive entry.",
                )
            )

        if metrics.orderbook_imbalance is not None and abs(metrics.orderbook_imbalance) >= Decimal("0.70"):
            direction = "bid-heavy" if metrics.orderbook_imbalance > 0 else "ask-heavy"
            signals.append(
                ResearchSignal(
                    market_id=market_id,
                    asset_id=current.asset_id,
                    timestamp=current.snapshot_ts,
                    signal_type="extreme_orderbook_imbalance",
                    severity=_severity(abs(metrics.orderbook_imbalance), Decimal("0.85")),
                    confidence=min(Decimal("0.90"), abs(metrics.orderbook_imbalance)),
                    description=f"Orderbook depth is extremely imbalanced ({direction}).",
                    metrics={
                        "imbalance": _s(metrics.orderbook_imbalance),
                        "bid_depth": _s(metrics.bid_depth),
                        "ask_depth": _s(metrics.ask_depth),
                    },
                    hypothesis="Imbalance may precede repricing if depth pressure is persistent.",
                    next_action="Backtest whether next snapshots move toward the heavy side.",
                )
            )

        if metrics.total_depth <= Decimal("25") and metrics.spread_pct and metrics.spread_pct >= Decimal("0.05"):
            signals.append(
                ResearchSignal(
                    market_id=market_id,
                    asset_id=current.asset_id,
                    timestamp=current.snapshot_ts,
                    signal_type="liquidity_vacuum",
                    severity="warning",
                    confidence=Decimal("0.65"),
                    description="Low visible depth combined with non-trivial spread.",
                    metrics={
                        "total_depth": _s(metrics.total_depth),
                        "spread_pct": _s(metrics.spread_pct),
                    },
                    hypothesis="Small trades may move the book; fade strategies need conservative sizing.",
                    next_action="Measure slippage and failure rate before treating as opportunity.",
                )
            )

        if previous and previous.best_bid and previous.best_ask and metrics.mid_price:
            previous_metrics = compute_orderbook_metrics(previous)
            if previous_metrics.mid_price:
                jump = abs(metrics.mid_price - previous_metrics.mid_price)
                if jump >= Decimal("0.05"):
                    signals.append(
                        ResearchSignal(
                            market_id=market_id,
                            asset_id=current.asset_id,
                            timestamp=current.snapshot_ts,
                            signal_type="rapid_price_jump",
                            severity=_severity(jump, Decimal("0.10")),
                            confidence=min(Decimal("0.90"), jump * Decimal("8")),
                            description="Mid price moved rapidly between consecutive snapshots.",
                            metrics={
                                "previous_mid": _s(previous_metrics.mid_price),
                                "current_mid": _s(metrics.mid_price),
                                "jump": _s(jump),
                            },
                            hypothesis="Fast repricing may create delayed adjustment in related markets.",
                            next_action="Cross-check with trades and correlated markets.",
                        )
                    )

    signals.extend(_volume_spike_signals(market_id=market_id, trades=trades))
    signals.extend(_stable_wide_spread_signals(market_id=market_id, snapshots=ordered))
    return signals


def _volume_spike_signals(market_id: str, trades: list[Trade]) -> list[ResearchSignal]:
    if len(trades) < 5:
        return []
    sizes = [trade.size for trade in trades]
    average = sum(sizes, Decimal("0")) / Decimal(len(sizes))
    if average <= 0:
        return []
    signals: list[ResearchSignal] = []
    for trade in trades:
        if trade.size >= average * Decimal("5"):
            signals.append(
                ResearchSignal(
                    market_id=market_id,
                    asset_id=trade.asset_id,
                    timestamp=trade.traded_at,
                    signal_type="volume_spike",
                    severity="warning",
                    confidence=Decimal("0.70"),
                    description="Single trade size materially exceeds recent average trade size.",
                    metrics={"trade_size": _s(trade.size), "average_trade_size": _s(average)},
                    hypothesis="Volume spike may signal information arrival or forced execution.",
                    next_action="Inspect price movement before and after spike.",
                )
            )
    return signals


def _stable_wide_spread_signals(
    market_id: str,
    snapshots: list[OrderBookSnapshot],
    window: int = 5,
) -> list[ResearchSignal]:
    signals: list[ResearchSignal] = []
    if len(snapshots) < window:
        return signals
    for index in range(window - 1, len(snapshots)):
        window_snapshots = snapshots[index - window + 1 : index + 1]
        metrics = [compute_orderbook_metrics(snapshot) for snapshot in window_snapshots]
        spreads = [metric.spread_pct for metric in metrics if metric.spread_pct is not None]
        if len(spreads) == window and min(spreads) >= Decimal("0.06"):
            current = window_snapshots[-1]
            signals.append(
                ResearchSignal(
                    market_id=market_id,
                    asset_id=current.asset_id,
                    timestamp=current.snapshot_ts,
                    signal_type="stable_exploitable_spread",
                    severity="info",
                    confidence=Decimal("0.60"),
                    description="Spread stayed above threshold for several consecutive snapshots.",
                    metrics={"window": window, "min_spread_pct": _s(min(spreads))},
                    hypothesis="Persistent spread may be backtestable with passive fill assumptions.",
                    next_action="Run wide-spread mean reversion backtest with latency and partial fills.",
                )
            )
    return signals


def _severity(value: Decimal, high_threshold: Decimal) -> str:
    return "critical" if value >= high_threshold else "warning"


def _s(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None

