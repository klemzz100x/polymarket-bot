from decimal import Decimal

from polybot.live_readiness.readiness_checks import check_boolean, check_threshold
from polybot.live_readiness.readiness_score import ReadinessCheckResult


def infrastructure_checks(
    *,
    db_healthy: bool,
    redis_healthy: bool,
    api_healthy: bool,
    collectors_healthy: bool,
    websocket_healthy: bool,
    telegram_ready: bool,
    dashboard_ready: bool,
    obsidian_ready: bool,
    stale_data_count: int,
) -> list[ReadinessCheckResult]:
    return [
        check_boolean("db_healthy", db_healthy, message="Database is not healthy."),
        check_boolean("redis_healthy", redis_healthy, message="Redis is not healthy.", severity="warning"),
        check_boolean("api_healthy", api_healthy, message="API is not healthy."),
        check_boolean("infra_collectors_healthy", collectors_healthy, message="Collectors are not healthy."),
        check_boolean("infra_websocket_healthy", websocket_healthy, message="WebSocket layer is not healthy.", severity="warning"),
        check_boolean("infra_telegram_ready", telegram_ready, message="Telegram alerts are not operational.", severity="warning"),
        check_boolean("infra_dashboard_ready", dashboard_ready, message="Dashboard is not operational.", severity="warning"),
        check_boolean("infra_obsidian_ready", obsidian_ready, message="Obsidian reporting is not operational.", severity="warning"),
        check_threshold(
            "infra_stale_data_absent",
            Decimal(stale_data_count),
            maximum=Decimal("0"),
            message="Stale data detected.",
        ),
    ]
