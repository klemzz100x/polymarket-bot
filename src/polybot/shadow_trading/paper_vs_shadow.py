from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

from polybot.paper_trading.models import PaperTradingResult
from polybot.shadow_trading.models import ShadowTradingResult


@dataclass(frozen=True, slots=True)
class PaperShadowComparison:
    paper_fill_rate: Decimal
    shadow_fill_probability: Decimal
    paper_average_slippage: Decimal
    shadow_average_slippage: Decimal
    fill_rate_delta: Decimal
    slippage_delta: Decimal
    opportunity_decay: Decimal
    anomalies: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            key: str(value) if isinstance(value, Decimal) else value
            for key, value in asdict(self).items()
        }


def compare_paper_vs_shadow(
    *,
    paper: PaperTradingResult,
    shadow: ShadowTradingResult,
) -> PaperShadowComparison:
    paper_slippage = _paper_average_slippage(paper)
    fill_delta = paper.fill_rate - shadow.fill_probability
    slippage_delta = shadow.average_slippage - paper_slippage
    opportunity_decay = max(fill_delta, Decimal("0")) + max(slippage_delta, Decimal("0"))
    anomalies: list[str] = []
    if fill_delta > Decimal("0.25"):
        anomalies.append("paper simulator appears too optimistic versus shadow fill probability")
    if slippage_delta > Decimal("0.02"):
        anomalies.append("shadow slippage materially exceeds paper slippage")
    if shadow.missed_fill_count > 0:
        anomalies.append("shadow layer detected missed fills")
    return PaperShadowComparison(
        paper_fill_rate=paper.fill_rate,
        shadow_fill_probability=shadow.fill_probability,
        paper_average_slippage=paper_slippage,
        shadow_average_slippage=shadow.average_slippage,
        fill_rate_delta=fill_delta,
        slippage_delta=slippage_delta,
        opportunity_decay=opportunity_decay,
        anomalies=anomalies,
    )


def _paper_average_slippage(paper: PaperTradingResult) -> Decimal:
    if not paper.fills:
        return Decimal("0")
    return sum((abs(fill.slippage) for fill in paper.fills), Decimal("0")) / Decimal(len(paper.fills))
