from decimal import Decimal

from polybot.shadow_trading.models import ShadowFill


def average_slippage(fills: list[ShadowFill]) -> Decimal:
    executable = [abs(fill.slippage_abs) for fill in fills if fill.fill_possible]
    if not executable:
        return Decimal("0")
    return sum(executable, Decimal("0")) / Decimal(len(executable))


def fill_probability(fills: list[ShadowFill]) -> Decimal:
    if not fills:
        return Decimal("0")
    return sum((fill.fill_probability for fill in fills), Decimal("0")) / Decimal(len(fills))


def count_missed_fills(fills: list[ShadowFill]) -> int:
    return sum(1 for fill in fills if not fill.fill_possible)


def count_impossible_fills(fills: list[ShadowFill]) -> int:
    return sum(
        1
        for fill in fills
        if fill.fill_possible
        and (
            fill.average_price is None
            or fill.average_price <= 0
            or fill.average_price >= 1
            or fill.filled_size > fill.requested_size
        )
    )
