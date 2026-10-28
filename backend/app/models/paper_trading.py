from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now


class PaperTrade(Base, TimestampMixin):
    __tablename__ = "paper_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("signals.id"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(30), index=True)
    direction: Mapped[str] = mapped_column(String(10))  # BUY, SELL
    quantity: Mapped[int] = mapped_column(Integer, default=100)

    entry_price: Mapped[float] = mapped_column(Float)
    current_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    stop_loss: Mapped[float] = mapped_column(Float)
    target_1: Mapped[float] = mapped_column(Float)
    target_2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    pnl_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    max_adverse_excursion: Mapped[float] = mapped_column(Float, default=0.0)   # MAE
    max_favorable_excursion: Mapped[float] = mapped_column(Float, default=0.0) # MFE

    status: Mapped[str] = mapped_column(String(30), default="OPEN", index=True)  # OPEN, CLOSED, STOPPED_OUT, TARGET_REACHED
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    exited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    exit_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    signal: Mapped[Optional["Signal"]] = relationship("Signal", back_populates="paper_trades")
    prediction_result: Mapped[Optional["PredictionResult"]] = relationship("PredictionResult", back_populates="paper_trade", uselist=False)

    __table_args__ = (
        Index("idx_papertrade_symbol_status", "symbol", "status"),
    )
