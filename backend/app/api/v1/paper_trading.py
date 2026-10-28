from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.paper_trading import PaperTrade
from app.models.signal import Signal
from app.schemas.paper_trading import PaperTradeCreate, PaperTradeRead, PaperTradingMetrics
from app.schemas.common import APIResponse, PaginatedResponse

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
    res = await db.execute(select(PaperTrade))
    all_trades = res.scalars().all()

    total = len(all_trades)
    open_p = sum(1 for t in all_trades if t.status == "OPEN")
    closed = sum(1 for t in all_trades if t.status != "OPEN")
    winning = sum(1 for t in all_trades if t.realized_pnl > 0)
    losing = sum(1 for t in all_trades if t.realized_pnl < 0)

    win_rate = (winning / closed * 100) if closed > 0 else 0.0
    loss_rate = (losing / closed * 100) if closed > 0 else 0.0
    total_realized = sum(t.realized_pnl for t in all_trades)
    total_unrealized = sum(t.unrealized_pnl for t in all_trades if t.status == "OPEN")

    gross_profit = sum(t.realized_pnl for t in all_trades if t.realized_pnl > 0)
    gross_loss = abs(sum(t.realized_pnl for t in all_trades if t.realized_pnl < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)

    avg_return = (sum(t.pnl_percentage for t in all_trades if t.status != "OPEN") / closed) if closed > 0 else 0.0

    metrics = PaperTradingMetrics(
        total_trades=total,
        open_positions=open_p,
        closed_trades=closed,
        winning_trades=winning,
        losing_trades=losing,
        win_rate_pct=round(win_rate, 2),
        loss_rate_pct=round(loss_rate, 2),
        total_realized_pnl=round(total_realized, 2),
        total_unrealized_pnl=round(total_unrealized, 2),
        profit_factor=round(profit_factor, 2),
        average_trade_return_pct=round(avg_return, 2),
        max_drawdown_pct=0.0
    )
    return APIResponse(data=metrics, message="Calculated paper trading performance metrics")


@router.post("/open", response_model=APIResponse[PaperTradeRead])
async def open_virtual_trade(trade: PaperTradeCreate, db: AsyncSession = Depends(get_db)):
    """Opens a virtual position in Paper Trading mode."""
    new_trade = PaperTrade(
        signal_id=trade.signal_id,
        symbol=trade.symbol.upper(),
        direction=trade.direction.upper(),
        quantity=trade.quantity,
        entry_price=trade.entry_price,
        current_price=trade.entry_price,
        stop_loss=trade.stop_loss,
        target_1=trade.target_1,
        target_2=trade.target_2,
        status="OPEN",
        notes=trade.notes
    )
    db.add(new_trade)
    await db.commit()
    await db.refresh(new_trade)
    return APIResponse(data=new_trade, message="Virtual paper position opened.")
