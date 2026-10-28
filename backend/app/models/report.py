from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Boolean, DateTime, Integer, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now


class DailyReport(Base, TimestampMixin):
    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[str] = mapped_column(String(20), index=True)  # YYYY-MM-DD
    report_type: Mapped[str] = mapped_column(String(30), default="PRE_MARKET")
    title: Mapped[str] = mapped_column(String(250))

    global_overnight_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    top_global_events: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    nifty_outlook: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    bank_nifty_outlook: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    top_watchlist: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    no_trade_watchlist: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    risk_warnings: Mapped[List[str]] = mapped_column(JSON, default=list)

    markdown_content: Mapped[str] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("idx_daily_report_date_type", "report_date", "report_type"),
    )


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    alert_type: Mapped[str] = mapped_column(String(50), index=True)  # HIGH_IMPACT_NEWS, SIGNAL_TRIGGER, PRE_MARKET
    impact_score: Mapped[int] = mapped_column(Integer, default=50)
    channel: Mapped[str] = mapped_column(String(30), default="WEB_DASHBOARD")  # TELEGRAM, WEB_DASHBOARD
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
