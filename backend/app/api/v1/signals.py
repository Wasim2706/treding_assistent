from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.signal import Signal
from app.schemas.signal import SignalRead, SignalGenerateRequest
from app.schemas.common import PaginatedResponse, APIResponse

router = APIRouter(prefix="/signals", tags=["Trading Signals Engine"])


@router.get("", response_model=PaginatedResponse[SignalRead])
async def list_signals(
    direction: Optional[str] = Query(None, description="BUY, SELL, WATCH, NO_TRADE"),
    symbol: Optional[str] = Query(None, description="Stock ticker"),
    min_confidence: Optional[int] = Query(None, ge=0, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists deterministic paper-trading decision-support signals.
    Never guarantees outcomes; always includes entry/exit windows and invalidation criteria.
    """
    query = select(Signal).order_by(desc(Signal.created_at))

    if direction:
        query = query.where(Signal.direction == direction.upper())
    if symbol:
        query = query.where(Signal.symbol == symbol.upper())
    if min_confidence:
        query = query.where(Signal.confidence >= min_confidence)

    offset = (page - 1) * page_size
    res = await db.execute(query.offset(offset).limit(page_size))
    signals = res.scalars().all()

    total_res = await db.execute(select(Signal.id))
    total = len(total_res.scalars().all())

    return PaginatedResponse(
        success=True,
        total=total,
        page=page,
        page_size=page_size,
        items=signals,
        disclaimer="DECISION SUPPORT ONLY. NO TRADE is generated when data or technical confirmation is unclear."
    )


@router.get("/top", response_model=APIResponse[List[SignalRead]])
async def get_top_signals(limit: int = Query(5, ge=1, le=20), db: AsyncSession = Depends(get_db)):
    """Returns top ranked high-confidence actionable signals."""
    query = select(Signal).where(
        Signal.direction.in_(["BUY", "SELL"]),
        Signal.status == "PENDING"
    ).order_by(desc(Signal.composite_score)).limit(limit)

    res = await db.execute(query)
    top_signals = res.scalars().all()
    return APIResponse(
        data=top_signals,
        message=f"Retrieved top {len(top_signals)} ranked setups"
    )


@router.post("/generate", response_model=APIResponse[dict])
async def trigger_signal_generation(
    request: SignalGenerateRequest = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers multi-factor signal synthesis combining news sentiment, technicals, and sector matrix.
    """
    from app.workers.tasks import run_signal_generation_cycle
    result = await run_signal_generation_cycle()
    return APIResponse(data=result, message="Signal generation engine executed successfully.")
