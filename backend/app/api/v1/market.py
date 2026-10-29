from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.market import Stock, Sector, MarketDataSnapshot
from app.schemas.market import StockRead, SectorRead, MarketSnapshotRead
from app.schemas.common import APIResponse
from app.services.market_data.service import market_data_service
from app.services.market_data.base import get_indian_market_status, clean_ticker

router = APIRouter(prefix="/market", tags=["Market Data & Indices"])


@router.get("/status", response_model=APIResponse[Dict[str, Any]])
async def get_market_session_status():
    """Returns current Indian stock market (NSE/BSE) trading session and hours."""
    status = await market_data_service.get_market_status()
    return APIResponse(data=status, message="Market session status")


@router.get("/overview", response_model=APIResponse[Dict[str, Any]])
async def get_market_overview():
    """Returns live quotes for major Indian benchmarks (NIFTY 50, Bank NIFTY, Crude, Gold, USD/INR)."""
    overview = await market_data_service.get_market_overview()
    return APIResponse(data=overview, message="Major index and commodity overview")


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


@router.get("/quote/{symbol}", response_model=APIResponse[Dict[str, Any]])
async def get_quote(symbol: str):
    """Retrieves live or cached price quote for a symbol."""
    quote = await market_data_service.get_quote(symbol)
    return APIResponse(data=quote, message=f"Quote for {clean_ticker(symbol)}")


@router.get("/indicators/{symbol}", response_model=APIResponse[Dict[str, Any]])
async def get_technical_indicators(symbol: str):
    """Retrieves full technical indicators (SMA, EMA, RSI, MACD, ATR, Pivots) for a symbol."""
    indicators = await market_data_service.get_indicators(symbol)
    return APIResponse(data=indicators, message=f"Technical indicators for {clean_ticker(symbol)}")


@router.get("/snapshots/{symbol}", response_model=APIResponse[Optional[MarketSnapshotRead]])
async def get_latest_market_snapshot(symbol: str, db: AsyncSession = Depends(get_db)):
    """Retrieves latest OHLCV and technical indicators from database for symbol."""
    clean = clean_ticker(symbol)
    res = await db.execute(
        select(MarketDataSnapshot)
        .where(MarketDataSnapshot.symbol == clean)
        .order_by(desc(MarketDataSnapshot.created_at))
        .limit(1)
    )
    snapshot = res.scalars().first()

    # If no snapshot in DB yet, compute and persist one automatically
    if snapshot is None:
        try:
            snapshot = await market_data_service.get_or_create_snapshot(clean, db)
        except Exception:
            pass

    return APIResponse(data=snapshot, message=f"Market snapshot for {clean}")


@router.post("/snapshot/{symbol}", response_model=APIResponse[MarketSnapshotRead], dependencies=[Depends(verify_api_key)])
async def create_market_snapshot(symbol: str, db: AsyncSession = Depends(get_db)):
    """Triggers an on-demand market data fetch and technical calculation, saving snapshot to DB."""
    clean = clean_ticker(symbol)
    snapshot = await market_data_service.get_or_create_snapshot(clean, db)
    return APIResponse(data=snapshot, message=f"Market snapshot refreshed and stored for {clean}")


@router.post("/refresh-all", response_model=APIResponse[Dict[str, Any]], dependencies=[Depends(verify_api_key)])
async def refresh_all_snapshots(db: AsyncSession = Depends(get_db)):
    """Refreshes market data and technical indicators for all active stocks."""
    count = await market_data_service.refresh_all_snapshots(db)
    return APIResponse(data={"refreshed_count": count}, message=f"Successfully refreshed {count} market snapshots")
