from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Float, Boolean, DateTime, Integer, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now


class Signal(Base, TimestampMixin):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(30), index=True)
    direction: Mapped[str] = mapped_column(String(20), index=True)  # BUY, SELL, WATCH, NO_TRADE

    entry_zone: Mapped[str] = mapped_column(String(100))
    entry_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_reward: Mapped[str] = mapped_column(String(30), default="1:2.0")

    entry_time_window: Mapped[str] = mapped_column(String(150))
    exit_time_window: Mapped[str] = mapped_column(String(150))

    confidence: Mapped[int] = mapped_column(Integer, default=50)

    # Component Scores
    news_score: Mapped[float] = mapped_column(Float, default=0.0)
    technical_score: Mapped[float] = mapped_column(Float, default=0.0)
    volume_score: Mapped[float] = mapped_column(Float, default=0.0)
    market_score: Mapped[float] = mapped_column(Float, default=0.0)
    sector_score: Mapped[float] = mapped_column(Float, default=0.0)
    composite_score: Mapped[float] = mapped_column(Float, default=0.0)

    reasoning: Mapped[str] = mapped_column(Text)
    invalidated_if: Mapped[str] = mapped_column(Text)
    technical_confirmation: Mapped[str] = mapped_column(Text)
    news_sources: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(String(30), default="PENDING")  # PENDING, TRIGGERED, EXPIRED, CLOSED
    is_paper_traded: Mapped[bool] = mapped_column(Boolean, default=False)

    paper_trades: Mapped[list["PaperTrade"]] = relationship("PaperTrade", back_populates="signal")

    __table_args__ = (
        Index("idx_signal_symbol_dir_created", "symbol", "direction", "created_at"),
    )
