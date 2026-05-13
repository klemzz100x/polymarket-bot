from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from polybot.paper_trading.models import PaperTradingResult


@dataclass(frozen=True, slots=True)
class PaperEquitySnapshot:
    run_id: str
    market_id: str
    strategy_name: str
    snapshot_ts: datetime
    equity: Decimal
    cash: Decimal
    net_pnl: Decimal
    exposure: Decimal
    positions: dict[str, str] = field(default_factory=dict)
    source: str = "paper_trading"

    def to_dict(self) -> dict[str, Any]:
        return _json_ready(asdict(self))


def build_equity_snapshots(result: PaperTradingResult) -> list[PaperEquitySnapshot]:
    initial_equity = result.final_equity - result.net_pnl
    current_equity = initial_equity
    positions: dict[str, Decimal] = {}
    snapshots: list[PaperEquitySnapshot] = [
        PaperEquitySnapshot(
            run_id=result.run_id,
            market_id=result.market_id,
            strategy_name=result.strategy_name,
            snapshot_ts=result.started_at,
            equity=initial_equity,
            cash=initial_equity,
            net_pnl=Decimal("0"),
            exposure=Decimal("0"),
            positions={},
        )
    ]

    for trade in sorted(result.trades, key=lambda item: item.fill.filled_at):
        fill = trade.fill
        signed_qty = fill.filled_size if fill.side == "buy" else -fill.filled_size
        positions[fill.asset_id] = positions.get(fill.asset_id, Decimal("0")) + signed_qty
        current_equity += trade.net_pnl
        notional = (
            fill.filled_size * fill.average_price
            if fill.average_price is not None
            else Decimal("0")
        )
        exposure = sum(abs(quantity) for quantity in positions.values())
        snapshots.append(
            PaperEquitySnapshot(
                run_id=result.run_id,
                market_id=result.market_id,
                strategy_name=result.strategy_name,
                snapshot_ts=fill.filled_at,
                equity=current_equity,
                cash=current_equity - notional,
                net_pnl=current_equity - initial_equity,
                exposure=exposure,
                positions={asset_id: str(quantity) for asset_id, quantity in positions.items()},
            )
        )

    snapshots.append(
        PaperEquitySnapshot(
            run_id=result.run_id,
            market_id=result.market_id,
            strategy_name=result.strategy_name,
            snapshot_ts=result.finished_at,
            equity=result.final_equity,
            cash=result.final_cash,
            net_pnl=result.net_pnl,
            exposure=result.max_exposure,
            positions={asset_id: str(quantity) for asset_id, quantity in positions.items()},
            source="paper_trading_final",
        )
    )
    return snapshots


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
