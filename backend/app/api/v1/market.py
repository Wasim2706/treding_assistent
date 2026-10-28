from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.market import Stock, Sector, MarketDataSnapshot
from app.schemas.market import StockRead, SectorRead, MarketSnapshotRead
from app.schemas.common import APIResponse

router = APIRouter(prefix="/market", tags=["Market Data & Indices"])


@router.get("/stocks", response_model=APIResponse[List[StockRead]])
async def list_stocks(
    sector: Optional[str] = Query(None),
    nifty50_only: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Lists tracked Indian equities."""
    query = select(Stock).options(selectinload(Stock.sector)).where(Stock.is_active == True)
    if nifty50_only:
        query = query.where(Stock.is_nifty50 == True)
    res = await db.execute(query)
    stocks = res.scalars().all()
    return APIResponse(data=stocks, message=f"Retrieved {len(stocks)} stocks")


@router.get("/sectors", response_model=APIResponse[List[SectorRead]])
async def list_sectors(db: AsyncSession = Depends(get_db)):
    """Lists Indian market sectors and their macro sensitivity impact matrix."""
    res = await db.execute(select(Sector))
    sectors = res.scalars().all()
    return APIResponse(data=sectors, message="Indian market sector sensitivity matrix loaded")


@router.get("/snapshots/{symbol}", response_model=APIResponse[Optional[MarketSnapshotRead]])
async def get_latest_market_snapshot(symbol: str, db: AsyncSession = Depends(get_db)):
    """Retrieves latest OHLCV and technical indicators for symbol."""
    res = await db.execute(
        select(MarketDataSnapshot)
        .where(MarketDataSnapshot.symbol == symbol.upper())
        .order_by(desc(MarketDataSnapshot.created_at))
        .limit(1)
    )
    snapshot = res.scalars().first()
    return APIResponse(data=snapshot, message=f"Market snapshot for {symbol}")
