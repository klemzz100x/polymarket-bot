from decimal import Decimal

from polybot.shadow_trading.models import ShadowFill


def average_delay_ms(fills: list[ShadowFill]) -> Decimal:
    if not fills:
        return Decimal("0")
    return sum((Decimal(fill.delay_ms) for fill in fills), Decimal("0")) / Decimal(len(fills))


def latency_anomalies(
    fills: list[ShadowFill],
    *,
    warning_ms: int = 1500,
    critical_ms: int = 5000,
) -> list[str]:
    anomalies: list[str] = []
    if not fills:
        return anomalies
    max_delay = max(fill.delay_ms for fill in fills)
    if max_delay >= critical_ms:
        anomalies.append(f"critical latency spike detected: {max_delay}ms")
    elif max_delay >= warning_ms:
        anomalies.append(f"warning latency spike detected: {max_delay}ms")
    return anomalies
