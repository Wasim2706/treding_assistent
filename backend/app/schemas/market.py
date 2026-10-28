from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class SectorRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    sensitivities: Dict[str, Any] = {}
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StockRead(BaseModel):
    id: int
    symbol: str
    exchange_ticker: str
    company_name: str
    sector_id: Optional[int] = None
    is_nifty50: bool
    is_bank_nifty: bool
    is_active: bool
    market_cap_tier: str
    sector: Optional[SectorRead] = None
    model_config = ConfigDict(from_attributes=True)


class MarketSnapshotRead(BaseModel):
    id: int
    symbol: str
    last_price: float
    change_pct: float
    open_price: float
    high_price: float
    low_price: float
    prev_close: float
    volume: float
    avg_volume_20: float
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_20: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    atr_14: Optional[float] = None
    vwap: Optional[float] = None
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    gap_pct: Optional[float] = 0.0
    volatility: Optional[float] = 0.0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
