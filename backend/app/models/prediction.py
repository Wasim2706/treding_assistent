from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Boolean, DateTime, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now


class PredictionResult(Base, TimestampMixin):
    __tablename__ = "prediction_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_id: Mapped[int] = mapped_column(Integer, ForeignKey("signals.id"), index=True)
    paper_trade_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("paper_trades.id"), nullable=True)

    symbol: Mapped[str] = mapped_column(String(30), index=True)
    predicted_direction: Mapped[str] = mapped_column(String(20))  # BUY, SELL, WATCH
    predicted_confidence: Mapped[int] = mapped_column(Integer)
    price_at_prediction: Mapped[float] = mapped_column(Float)

    evaluation_horizon: Mapped[str] = mapped_column(String(30), default="INTRADAY")  # INTRADAY, 1_DAY, 3_DAY
    evaluation_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    actual_price_at_eval: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_price_change_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_direction: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # BULLISH, BEARISH, FLAT

    is_direction_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_evaluated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    evaluation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    paper_trade: Mapped[Optional["PaperTrade"]] = relationship("PaperTrade", back_populates="prediction_result")

    __table_args__ = (
        Index("idx_prediction_symbol_eval", "symbol", "is_evaluated"),
    )
