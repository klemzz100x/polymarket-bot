from dataclasses import dataclass
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from polybot.core.config import Settings
from polybot.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TelegramSendResult:
    success: bool
    status_code: int | None = None
    response_body: str = ""
    error: str = ""


def send_telegram_message(
    *,
    settings: Settings,
    text: str,
    parse_mode: str | None = None,
    timeout_seconds: float = 10.0,
) -> TelegramSendResult:
    if not settings.telegram_enabled or not settings.telegram_notifications:
        return TelegramSendResult(success=False, error="Telegram notifications are disabled.")
    if not settings.telegram_bot_token:
        logger.warning("telegram_send_skipped_missing_token")
        return TelegramSendResult(success=False, error="TELEGRAM_BOT_TOKEN is missing.")
    if not settings.telegram_chat_id:
        logger.warning("telegram_send_skipped_missing_chat_id")
        return TelegramSendResult(success=False, error="TELEGRAM_CHAT_ID is missing.")

    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "disable_web_page_preview": "true",
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    request = Request(
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
        data=urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            body = response.read().decode("utf-8")
            success = 200 <= response.status < 300
            if success:
                logger.info("telegram_message_sent", chat_id=settings.telegram_chat_id)
            else:
                logger.warning("telegram_message_failed", status_code=response.status, body=body)
            return TelegramSendResult(
                success=success,
                status_code=response.status,
                response_body=body,
            )
    except Exception as exc:
        error = _sanitize_error(str(exc), token=settings.telegram_bot_token)
        logger.error("telegram_message_error", error=error)
        return TelegramSendResult(success=False, error=error)


def parse_telegram_response(result: TelegramSendResult) -> dict[str, object]:
    if not result.response_body:
        return {}
    try:
        parsed = json.loads(result.response_body)
    except json.JSONDecodeError:
        return {"raw": result.response_body}
    return parsed if isinstance(parsed, dict) else {"raw": parsed}


def _sanitize_error(error: str, *, token: str) -> str:
    if not token:
        return error
    return error.replace(token, "<telegram-bot-token>")
