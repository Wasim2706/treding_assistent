from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PaperTradeCreate(BaseModel):
    signal_id: Optional[int] = None
    symbol: str
    direction: str  # BUY, SELL
    quantity: int = Field(gt=0, default=100)
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    target_1: float = Field(gt=0)
    target_2: Optional[float] = None
    notes: Optional[str] = None


class PaperTradeRead(BaseModel):
    id: int
    signal_id: Optional[int] = None
    symbol: str
    direction: str
    quantity: int
    entry_price: float
    current_price: float
    exit_price: Optional[float] = None
    stop_loss: float
    target_1: float
    target_2: Optional[float] = None
    unrealized_pnl: float
    realized_pnl: float
    pnl_percentage: float
    max_adverse_excursion: float
    max_favorable_excursion: float
    status: str
    entered_at: datetime
    exited_at: Optional[datetime] = None
    exit_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PaperTradingMetrics(BaseModel):
    total_trades: int
    open_positions: int
    closed_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    loss_rate_pct: float
    total_realized_pnl: float
    total_unrealized_pnl: float
    profit_factor: float
    average_trade_return_pct: float
    max_drawdown_pct: float
