from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SignalRead(BaseModel):
    id: int
    symbol: str
    direction: str  # BUY, SELL, WATCH, NO_TRADE
    entry_zone: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_1: Optional[float] = None
    target_2: Optional[float] = None
    risk_reward: str
    entry_time_window: str
    exit_time_window: str
    confidence: int
    news_score: float
    technical_score: float
    volume_score: float
    market_score: float
    sector_score: float
    composite_score: float
    reasoning: str
    invalidated_if: str
    technical_confirmation: str
    news_sources: List[Dict[str, Any]] = []
    status: str
    is_paper_traded: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SignalWeightsUpdate(BaseModel):
    weight_news: float = Field(ge=0.0, le=1.0)
    weight_technical: float = Field(ge=0.0, le=1.0)
    weight_volume: float = Field(ge=0.0, le=1.0)
    weight_market: float = Field(ge=0.0, le=1.0)
    weight_sector: float = Field(ge=0.0, le=1.0)


class SignalGenerateRequest(BaseModel):
    symbols: Optional[List[str]] = None
    min_confidence: Optional[int] = 60
