from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class NewsAnalysisBase(BaseModel):
    summary: str
    event_type: str
    sentiment: str  # BULLISH, BEARISH, NEUTRAL
    impact_score: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    time_horizon: str  # INTRADAY, SHORT_TERM, MEDIUM_TERM
    affected_sectors: List[str] = []
    affected_stocks: List[str] = []
    affected_indices: List[str] = []
    reasoning: str
    risk_factors: List[str] = []
    confirmed_facts: List[str] = []
    market_interpretation: Optional[str] = None
    speculation: Optional[str] = None


class NewsAnalysisRead(NewsAnalysisBase):
    id: int
    article_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class NewsEntityRead(BaseModel):
    id: int
    entity_name: str
    entity_type: str
    relevance_score: int
    model_config = ConfigDict(from_attributes=True)


class NewsArticleBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    source: str
    author: Optional[str] = None
    published_at: datetime
    language: str = "en"
    country: str = "IN"
    source_reliability_score: int = 70


class NewsArticleRead(NewsArticleBase):
    id: int
    article_fingerprint: str
    normalized_url: str
    fetched_at: datetime
    is_processed: bool
    is_alert_sent: bool
    analysis: Optional[NewsAnalysisRead] = None
    entities: List[NewsEntityRead] = []
    model_config = ConfigDict(from_attributes=True)
