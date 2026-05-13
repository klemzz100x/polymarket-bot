#!/usr/bin/env python
from __future__ import annotations

import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def main() -> int:
    load_dotenv(Path(".env"))

    enabled = env_bool("TELEGRAM_ENABLED")
    notifications = env_bool("TELEGRAM_NOTIFICATIONS")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not enabled or not notifications:
        print("Telegram notifications are disabled.")
        return 1
    if not token:
        print("Telegram test failed: TELEGRAM_BOT_TOKEN is missing.")
        return 1
    if not chat_id:
        print("Telegram test failed: TELEGRAM_CHAT_ID is missing.")
        return 1

    request = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=urlencode(
            {
                "chat_id": chat_id,
                "text": "✅ Telegram alerts operational",
                "disable_web_page_preview": "true",
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310
            body = response.read().decode("utf-8")
            if 200 <= response.status < 300:
                print("Telegram test message sent successfully.")
                return 0
            print(f"Telegram test failed: HTTP {response.status} {sanitize(body, token)}")
            return 1
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        print(f"Telegram test failed: HTTP {exc.code} {sanitize(body, token)}")
        return 1
    except URLError as exc:
        print(f"Telegram test failed: network error: {exc.reason}")
        return 1


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_bool(name: str) -> bool:
    return os.getenv(name, "").lower() in {"1", "true", "yes", "y", "on"}


def sanitize(text: str, token: str) -> str:
    return text.replace(token, "<telegram-bot-token>") if token else text


if __name__ == "__main__":
    raise SystemExit(main())
