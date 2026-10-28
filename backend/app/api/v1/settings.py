from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.system import SystemSetting
from app.schemas.system import SystemSettingRead
from app.schemas.signal import SignalWeightsUpdate
from app.schemas.common import APIResponse

router = APIRouter(prefix="/settings", tags=["Engine Settings & Configuration"])


@router.get("", response_model=APIResponse[List[SystemSettingRead]])
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Retrieves configurable weights, thresholds, and limits."""
    res = await db.execute(select(SystemSetting))
    settings_records = res.scalars().all()
    return APIResponse(data=settings_records, message="System settings loaded")


@router.put("/weights", response_model=APIResponse[dict])
async def update_signal_weights(weights: SignalWeightsUpdate, db: AsyncSession = Depends(get_db)):
    """Updates the multi-factor scoring weights (must sum to 1.0)."""
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
