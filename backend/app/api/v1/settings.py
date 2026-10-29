from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_api_key, is_auth_required
from app.models.system import SystemSetting
from app.schemas.system import SystemSettingRead
from app.schemas.signal import SignalWeightsUpdate
from app.schemas.common import APIResponse
from app.services.ai.cost_control import get_today_ai_spend_usd, is_ai_budget_available

router = APIRouter(prefix="/settings", tags=["Engine Settings & Configuration"])


@router.get("", response_model=APIResponse[List[SystemSettingRead]])
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Retrieves configurable weights, thresholds, and limits."""
    res = await db.execute(select(SystemSetting))
    settings_records = res.scalars().all()
    return APIResponse(data=settings_records, message="System settings loaded")


@router.get("/security", response_model=APIResponse[Dict[str, Any]])
async def get_security_and_budget_status():
    """
    Returns API security status, rate limit policies, and real-time AI budget consumption.
    """
    ai_spend = await get_today_ai_spend_usd()
    budget_ok = await is_ai_budget_available()

    return APIResponse(
        data={
            "auth_required": is_auth_required(),
            "admin_key_configured": bool(settings.ADMIN_API_KEY),
            "environment": settings.ENVIRONMENT,
            "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
            "rate_limit_read_per_min": settings.RATE_LIMIT_PER_MINUTE,
            "rate_limit_mutation_per_min": settings.RATE_LIMIT_MUTATION_PER_MINUTE,
            "daily_ai_budget_usd": settings.DAILY_AI_BUDGET_USD,
            "ai_spend_today_usd": round(ai_spend, 4),
            "ai_budget_available": budget_ok,
            "trading_mode": "PAPER_TRADING_ONLY" if settings.PAPER_TRADING_ONLY else "REAL_ORDERS",
            "real_orders_enabled": settings.REAL_ORDERS_ENABLED,
            "safety_enforcement": "ENFORCED"
        },
        message="Retrieved security and budget status"
    )


@router.put("/weights", response_model=APIResponse[dict], dependencies=[Depends(verify_api_key)])
async def update_signal_weights(weights: SignalWeightsUpdate, db: AsyncSession = Depends(get_db)):
    """Updates the multi-factor scoring weights (must sum to 1.0). Requires authentication."""
    total = round(weights.weight_news + weights.weight_technical + weights.weight_volume + weights.weight_market + weights.weight_sector, 4)
    if total != 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signal weights must sum exactly to 1.0 (current sum: {total})"
        )

    res = await db.execute(select(SystemSetting).where(SystemSetting.key == "SIGNAL_WEIGHTS"))
    setting = res.scalars().first()
    new_weights = {
        "news": weights.weight_news,
        "technical": weights.weight_technical,
        "volume": weights.weight_volume,
        "market": weights.weight_market,
        "sector": weights.weight_sector
    }
    if setting:
        setting.value_json = new_weights
    else:
        setting = SystemSetting(key="SIGNAL_WEIGHTS", value_json=new_weights, description="Signal weights")
        db.add(setting)

    await db.commit()
    return APIResponse(data=new_weights, message="Signal weights updated successfully")
