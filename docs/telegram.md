# Telegram Alerts

Telegram is used only for monitoring and alerting. It does not place orders, change risk settings, or enable live trading.

## Configuration

Put the Telegram values in your local `.env` file:

```bash
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
TELEGRAM_CHAT_ID=<your-chat-id>
TELEGRAM_NOTIFICATIONS=true
```

The application loads these variables through the central settings system in `src/polybot/core/config.py`.

If Telegram is enabled but `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` is missing, the app emits a clear warning in the logs.

## Test

Run:

```bash
PYTHONPATH=src python3 scripts/test_telegram.py
```

Expected message:

```text
✅ Telegram alerts operational
```

## Security

- Keep the real token in `.env`.
- `.env` is ignored by git.
- Do not hardcode the token in Python code.
- Use Telegram only for read-only monitoring and alerting.
