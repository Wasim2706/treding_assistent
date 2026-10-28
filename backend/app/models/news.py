from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Float, Boolean, DateTime, Integer, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now


class NewsArticle(Base, TimestampMixin):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_fingerprint: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1000))
    normalized_url: Mapped[str] = mapped_column(String(1000), index=True)
    source: Mapped[str] = mapped_column(String(100), index=True)
    author: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    language: Mapped[str] = mapped_column(String(10), default="en")
    country: Mapped[str] = mapped_column(String(10), default="IN")
    source_reliability_score: Mapped[int] = mapped_column(Integer, default=70)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    analysis: Mapped[Optional["NewsAnalysis"]] = relationship(
        "NewsAnalysis", back_populates="article", uselist=False, cascade="all, delete-orphan"
    )
    entities: Mapped[list["NewsEntity"]] = relationship(
        "NewsEntity", back_populates="article", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_news_published_source", "published_at", "source"),
    )


class NewsAnalysis(Base, TimestampMixin):
    __tablename__ = "news_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey("news_articles.id"), unique=True)
    summary: Mapped[str] = mapped_column(Text)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    sentiment: Mapped[str] = mapped_column(String(20), default="NEUTRAL")  # BULLISH, BEARISH, NEUTRAL
    impact_score: Mapped[int] = mapped_column(Integer, default=50)  # 0 - 100
    confidence: Mapped[int] = mapped_column(Integer, default=50)    # 0 - 100
    time_horizon: Mapped[str] = mapped_column(String(30), default="INTRADAY")  # INTRADAY, SHORT_TERM, MEDIUM_TERM

    affected_sectors: Mapped[List[str]] = mapped_column(JSON, default=list)
    affected_stocks: Mapped[List[str]] = mapped_column(JSON, default=list)
    affected_indices: Mapped[List[str]] = mapped_column(JSON, default=list)

    reasoning: Mapped[str] = mapped_column(Text)
    risk_factors: Mapped[List[str]] = mapped_column(JSON, default=list)
    confirmed_facts: Mapped[List[str]] = mapped_column(JSON, default=list)
    market_interpretation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    speculation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    article: Mapped["NewsArticle"] = relationship("NewsArticle", back_populates="analysis")

    __table_args__ = (
        Index("idx_analysis_event_impact", "event_type", "impact_score"),
    )


class NewsEntity(Base, TimestampMixin):
    __tablename__ = "news_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey("news_articles.id"), index=True)
    entity_name: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(50))  # STOCK, SECTOR, INDEX, COMMODITY, REGULATOR, THEME
    relevance_score: Mapped[int] = mapped_column(Integer, default=50)

    article: Mapped["NewsArticle"] = relationship("NewsArticle", back_populates="entities")
