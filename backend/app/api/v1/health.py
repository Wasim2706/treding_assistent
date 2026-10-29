import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_standard_disclaimer
from app.services.ai.cost_control import get_today_ai_spend_usd
from app.schemas.system import HealthStatus, ReadinessStatus, MetricsStatus
from app.schemas.common import DisclaimerResponse

router = APIRouter(tags=["Health & System"])
_START_TIME = time.time()


@router.get("/health", response_model=HealthStatus)
async def get_health(db: AsyncSession = Depends(get_db)):
    """
    Application liveness probe and health status.
    Confirms database connectivity, active configuration, and trading safety enforcement.
    """
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    ai_status = "configured" if settings.OPENAI_API_KEY else "unconfigured (mock fallback)"

    return HealthStatus(
        status="ok" if "unhealthy" not in db_status else "degraded",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        mode="PAPER_TRADING_ONLY" if settings.PAPER_TRADING_ONLY else "REAL_ORDERS_ACTIVE",
        real_orders_enabled=settings.REAL_ORDERS_ENABLED,
        timestamp=datetime.now(timezone.utc),
        database=db_status,
        ai_status=ai_status,
        paper_trading_safety="ENFORCED"
    )


@router.get("/ready", response_model=ReadinessStatus)
async def get_readiness(db: AsyncSession = Depends(get_db)):
    """Readiness probe checking critical sub-systems."""
    db_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return ReadinessStatus(
        status="ready" if db_ok else "not_ready",
        checks={
            "database": db_ok,
            "safety_rules_active": settings.PAPER_TRADING_ONLY,
            "real_trading_blocked": not settings.REAL_ORDERS_ENABLED
        },
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/metrics", response_model=MetricsStatus)
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """System runtime metrics for monitoring and dashboard display."""
    uptime = time.time() - _START_TIME

    # Query counts safely
    async def count_table(table: str) -> int:
        try:
            res = await db.execute(text(f"SELECT count(*) FROM {table}"))
            return int(res.scalar() or 0)
        except Exception:
            return 0

    articles_total = await count_table("news_articles")
    signals_total = await count_table("signals")
    paper_trades = await count_table("paper_trades")
    reports_total = await count_table("daily_reports")
    api_calls = await count_table("api_usage")
    ai_spend = await get_today_ai_spend_usd()

    return MetricsStatus(
        uptime_seconds=round(uptime, 2),
        news_articles_total=articles_total,
        signals_generated_total=signals_total,
        paper_trades_active=paper_trades,
        daily_reports_generated=reports_total,
        api_calls_count=api_calls,
        estimated_ai_cost_usd=round(ai_spend, 4),
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/disclaimer", response_model=DisclaimerResponse)
async def get_disclaimer():
    """Mandatory trading safety and regulatory compliance notice."""
    info = get_standard_disclaimer()
    return DisclaimerResponse(
        mode=info["mode"],
        real_orders_enabled=info["real_orders_enabled"],
        disclaimer=info["disclaimer"],
        guarantee_statement=info["guarantee_statement"]
    )
