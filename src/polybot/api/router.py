from fastapi import APIRouter

from polybot.api.routes import (
    automation,
    evaluation,
    health,
    live_execution,
    metrics,
    paper_trading,
    pre_live,
    research,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(metrics.router)
api_router.include_router(automation.router, prefix="/automation", tags=["automation"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(research.router, tags=["research"])
api_router.include_router(paper_trading.router)
api_router.include_router(evaluation.router)
api_router.include_router(pre_live.router)
api_router.include_router(live_execution.router)
