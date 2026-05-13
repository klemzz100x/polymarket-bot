from polybot.core.compat import StrEnum


class LiveExecutionMode(StrEnum):
    DISABLED = "DISABLED"
    READ_ONLY = "READ_ONLY"
    SHADOW = "SHADOW"
    MICRO_LIVE = "MICRO_LIVE"


def parse_live_execution_mode(value: str | LiveExecutionMode | None) -> LiveExecutionMode:
    if isinstance(value, LiveExecutionMode):
        return value
    if value is None:
        return LiveExecutionMode.DISABLED
    try:
        return LiveExecutionMode(value.upper())
    except ValueError:
        return LiveExecutionMode.DISABLED


def mode_allows_wallet_sync(mode: LiveExecutionMode) -> bool:
    return mode in {
        LiveExecutionMode.READ_ONLY,
        LiveExecutionMode.SHADOW,
        LiveExecutionMode.MICRO_LIVE,
    }


def mode_allows_order_preparation(mode: LiveExecutionMode) -> bool:
    return mode in {LiveExecutionMode.SHADOW, LiveExecutionMode.MICRO_LIVE}


def mode_allows_order_submission(mode: LiveExecutionMode) -> bool:
    return mode == LiveExecutionMode.MICRO_LIVE
