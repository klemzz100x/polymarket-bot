import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from polybot.core.logging import get_logger

T = TypeVar("T")
logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    attempts: int = 3
    initial_delay_seconds: float = 0.5
    max_delay_seconds: float = 5.0
    backoff_multiplier: float = 2.0


async def run_with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    policy: RetryPolicy,
    operation_name: str,
) -> T:
    delay = policy.initial_delay_seconds
    last_error: Exception | None = None
    for attempt in range(1, policy.attempts + 1):
        try:
            return await operation()
        except Exception as exc:
            last_error = exc
            if attempt >= policy.attempts:
                break
            logger.warning(
                "operation_retrying",
                operation=operation_name,
                attempt=attempt,
                next_delay_seconds=delay,
                error=str(exc),
            )
            await asyncio.sleep(delay)
            delay = min(delay * policy.backoff_multiplier, policy.max_delay_seconds)
    assert last_error is not None
    logger.error("operation_retries_exhausted", operation=operation_name, error=str(last_error))
    raise last_error
