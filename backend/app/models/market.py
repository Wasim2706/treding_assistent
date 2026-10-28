from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Float, Boolean, DateTime, Integer, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now


class Sector(Base, TimestampMixin):
    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Configurable matrix: e.g., {"crude_oil_up": "BEARISH", "rbi_rate_cut": "BULLISH", "us_tech_down": "BEARISH"}
    sensitivities: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    stocks: Mapped[list["Stock"]] = relationship("Stock", back_populates="sector")


class Stock(Base, TimestampMixin):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(30), unique=True, index=True)  # e.g. RELIANCE.NS or RELIANCE
    exchange_ticker: Mapped[str] = mapped_column(String(30), index=True)      # e.g. RELIANCE
    company_name: Mapped[str] = mapped_column(String(200))
    sector_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sectors.id"), nullable=True)
    is_nifty50: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bank_nifty: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    market_cap_tier: Mapped[str] = mapped_column(String(20), default="LARGE_CAP")

    sector: Mapped[Optional["Sector"]] = relationship("Sector", back_populates="stocks")
    market_snapshots: Mapped[list["MarketDataSnapshot"]] = relationship("MarketDataSnapshot", back_populates="stock")

    __table_args__ = (
        Index("idx_stock_symbol_active", "symbol", "is_active"),
    )


class MarketDataSnapshot(Base, TimestampMixin):
    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(30), ForeignKey("stocks.symbol"), index=True)
    last_price: Mapped[float] = mapped_column(Float, default=0.0)
    change_pct: Mapped[float] = mapped_column(Float, default=0.0)
    open_price: Mapped[float] = mapped_column(Float, default=0.0)
    high_price: Mapped[float] = mapped_column(Float, default=0.0)
    low_price: Mapped[float] = mapped_column(Float, default=0.0)
    prev_close: Mapped[float] = mapped_column(Float, default=0.0)
    volume: Mapped[float] = mapped_column(Float, default=0.0)
    avg_volume_20: Mapped[float] = mapped_column(Float, default=0.0)

    # Technical Indicators
    sma_20: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sma_50: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sma_200: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ema_20: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rsi_14: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    macd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    macd_signal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    macd_hist: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    atr_14: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vwap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    support_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resistance_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gap_pct: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    volatility: Mapped[Optional[float]] = mapped_column(Float, default=0.0)

    stock: Mapped["Stock"] = relationship("Stock", back_populates="market_snapshots")

    __table_args__ = (
        Index("idx_market_symbol_created", "symbol", "created_at"),
    )
