from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RawNewsArticle(BaseModel):
    article_id: str
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    normalized_url: str
    source: str
    author: Optional[str] = None
    published_at: datetime
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: str = "en"
    country: str = "IN"
    tickers: List[str] = Field(default_factory=list)
    sectors: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    source_reliability_score: int = 70
    fingerprint: str = ""
    preliminary_impact_score: int = 50
    sentiment: str = "NEUTRAL"
    metadata: Dict[str, Any] = Field(default_factory=dict)
