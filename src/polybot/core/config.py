import logging
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "local"
    app_name: str = "polymarket-bot"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    log_format: str = "json"

    project_root: Path = Path(".")
    resources_dir: Path = Path("resources")
    obsidian_vault_dir: Path = Path("obsidian-vault")
    external_agents_dir: Path = Path("external-agents")

    database_url: str = "postgresql+asyncpg://polymarket:change-me@localhost:5432/polymarket"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"

    polymarket_gamma_api_url: str = "https://gamma-api.polymarket.com"
    polymarket_data_api_url: str = "https://data-api.polymarket.com"
    polymarket_clob_api_url: str = "https://clob.polymarket.com"
    polymarket_ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws"
    polymarket_http_timeout_seconds: float = 20.0
    polymarket_markets_page_limit: int = 100
    polymarket_default_orderbook_interval_seconds: int = 5

    polybot_automation_secret: str = Field(default="", alias="POLYBOT_AUTOMATION_SECRET")
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_notifications: bool = False
    live_trading_enabled: bool = False
    live_execution_mode: str = "DISABLED"
    max_order_size_usd: float = 1.0
    max_daily_loss_usd: float = 5.0
    max_open_positions: int = 2
    kill_switch_enabled: bool = True
    require_manual_confirmation: bool = True
    polymarket_private_key: str = ""
    polymarket_funder_address: str = ""
    polymarket_api_key: str = ""
    polymarket_api_secret: str = ""
    polymarket_api_passphrase: str = ""

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    validate_runtime_settings(settings)
    return settings


def validate_runtime_settings(settings: Settings) -> None:
    logger = logging.getLogger(__name__)
    if settings.telegram_enabled and not settings.telegram_bot_token:
        logger.warning("Telegram is enabled but TELEGRAM_BOT_TOKEN is missing.")
    if settings.telegram_enabled and not settings.telegram_chat_id:
        logger.warning("Telegram is enabled but TELEGRAM_CHAT_ID is missing.")
    if settings.live_trading_enabled:
        logger.warning("LIVE_TRADING_ENABLED is true. Ensure readiness, kill switch, and risk gates are proven.")
    if settings.live_execution_mode.upper() == "MICRO_LIVE" and not settings.live_trading_enabled:
        logger.warning("LIVE_EXECUTION_MODE is MICRO_LIVE but LIVE_TRADING_ENABLED is false.")
    if settings.live_trading_enabled and settings.require_manual_confirmation:
        logger.warning("Live trading is enabled but manual confirmation is still required.")
