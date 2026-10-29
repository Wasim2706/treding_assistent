from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.paper_trading import PaperTrade
from app.schemas.paper_trading import PaperTradeCreate, PaperTradeRead, PaperTradingMetrics
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.paper_trading.engine import paper_trading_engine

router = APIRouter(prefix="/paper-trading", tags=["Paper Trading Simulation"])


@router.get("/positions", response_model=APIResponse[List[PaperTradeRead]])
async def list_open_positions(db: AsyncSession = Depends(get_db)):
    """Lists currently open virtual paper trading positions."""
    res = await db.execute(
        select(PaperTrade).where(PaperTrade.status == "OPEN").order_by(desc(PaperTrade.entered_at))
    )
    positions = res.scalars().all()
    return APIResponse(data=positions, message=f"{len(positions)} open paper positions")


@router.get("/trades", response_model=PaginatedResponse[PaperTradeRead])
async def list_all_trades(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Lists historical and active paper trades."""
    query = select(PaperTrade).order_by(desc(PaperTrade.created_at))
    if status_filter:
        query = query.where(PaperTrade.status == status_filter.upper())

    offset = (page - 1) * page_size
    res = await db.execute(query.offset(offset).limit(page_size))
    trades = res.scalars().all()

    total_res = await db.execute(select(PaperTrade.id))
    total = len(total_res.scalars().all())

    return PaginatedResponse(
        success=True,
        total=total,
        page=page,
        page_size=page_size,
        items=trades,
        disclaimer="SIMULATED PAPER TRADING. No real capital is ever deployed."
    )


@router.get("/metrics", response_model=APIResponse[PaperTradingMetrics])
async def get_paper_metrics(db: AsyncSession = Depends(get_db)):
    """Calculates win rate, profit factor, drawdown, and P&L across paper trades."""
    metrics = await paper_trading_engine.get_metrics(db)
    return APIResponse(data=metrics, message="Calculated paper trading performance metrics")


@router.post("/open", response_model=APIResponse[PaperTradeRead], dependencies=[Depends(verify_api_key)])
async def open_virtual_trade(trade: PaperTradeCreate, db: AsyncSession = Depends(get_db)):
    """Opens a virtual position in Paper Trading mode."""
    new_trade = await paper_trading_engine.open_manual_trade(
        symbol=trade.symbol,
        direction=trade.direction,
        entry_price=trade.entry_price,
        stop_loss=trade.stop_loss,
        target_1=trade.target_1,
        target_2=trade.target_2,
        quantity=trade.quantity,
        notes=trade.notes,
        db=db
    )
    return APIResponse(data=new_trade, message="Virtual paper position opened.")


@router.post("/execute-signal/{signal_id}", response_model=APIResponse[PaperTradeRead], dependencies=[Depends(verify_api_key)])
async def execute_signal_as_paper_trade(signal_id: int, db: AsyncSession = Depends(get_db)):
    """Automatically sizes and opens a virtual paper position from an actionable Signal."""
    try:
        trade = await paper_trading_engine.open_position_from_signal(signal_id=signal_id, db=db)
        return APIResponse(data=trade, message=f"Virtual trade executed for Signal #{signal_id}")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/close/{trade_id}", response_model=APIResponse[PaperTradeRead], dependencies=[Depends(verify_api_key)])
async def close_paper_trade(
    trade_id: int,
    exit_price: Optional[float] = Query(None),
    reason: str = Query("MANUAL_EXIT"),
    db: AsyncSession = Depends(get_db)
):
    """Manually closes an active virtual trade."""
    try:
        closed = await paper_trading_engine.close_position_manually(
            trade_id=trade_id,
            db=db,
            exit_price=exit_price,
            reason=reason
        )
        return APIResponse(data=closed, message=f"Virtual position #{trade_id} closed successfully.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/update-positions", response_model=APIResponse[dict], dependencies=[Depends(verify_api_key)])
async def update_active_positions(
    force_eod: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Refreshes open positions against market prices, checking T1, T2, SL, and trailing stops."""
    result = await paper_trading_engine.update_open_positions(db=db, force_eod_squareoff=force_eod)
    return APIResponse(data=result, message="Open paper positions evaluated against market prices.")
