import logging
import sys
from typing import Any

try:
    import structlog
except ImportError:  # pragma: no cover - local smoke tests may run without optional deps.
    structlog = None  # type: ignore[assignment]


class _KeywordLogger:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def debug(self, event: str, **kwargs: Any) -> None:
        self._logger.debug(_format_event(event, kwargs))

    def info(self, event: str, **kwargs: Any) -> None:
        self._logger.info(_format_event(event, kwargs))

    def warning(self, event: str, **kwargs: Any) -> None:
        self._logger.warning(_format_event(event, kwargs))

    def error(self, event: str, **kwargs: Any) -> None:
        self._logger.error(_format_event(event, kwargs))


def configure_logging(level: str = "INFO", log_format: str = "json") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        stream=sys.stdout,
    )
    if structlog is None:
        return

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: Any
    if log_format == "console":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    if structlog is None:
        return _KeywordLogger(logging.getLogger(name))
    return structlog.get_logger(name)


def _format_event(event: str, kwargs: dict[str, Any]) -> str:
    if not kwargs:
        return event
    fields = " ".join(f"{key}={value}" for key, value in kwargs.items())
    return f"{event} {fields}"
