from fastapi import FastAPI

from polybot.api.router import api_router
from polybot.core.config import get_settings
from polybot.core.logging import configure_logging, get_logger
from polybot.core.paths import ensure_runtime_directories


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(level=settings.log_level, log_format=settings.log_format)
    ensure_runtime_directories(settings.project_root)

    logger = get_logger(__name__)
    logger.info("starting_api", app=settings.app_name, environment=settings.app_env)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.include_router(api_router)
    return app


app = create_app()

