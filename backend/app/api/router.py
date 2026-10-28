from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.news import router as news_router
from app.api.v1.signals import router as signals_router
from app.api.v1.market import router as market_router
from app.api.v1.paper_trading import router as paper_trading_router
from app.api.v1.reports import router as reports_router
from app.api.v1.performance import router as performance_router
from app.api.v1.settings import router as settings_router

api_router = APIRouter()

# Health endpoints are also mounted at top level for Render/K8s
api_router.include_router(health_router, prefix="")
api_router.include_router(news_router)
api_router.include_router(signals_router)
api_router.include_router(market_router)
api_router.include_router(paper_trading_router)
api_router.include_router(reports_router)
api_router.include_router(performance_router)
api_router.include_router(settings_router)
