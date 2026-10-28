from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Float, Boolean, DateTime, Integer, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


class SystemLog(Base, TimestampMixin):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_name: Mapped[str] = mapped_column(String(100), index=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    articles_fetched: Mapped[int] = mapped_column(Integer, default=0)
    articles_filtered: Mapped[int] = mapped_column(Integer, default=0)
    articles_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    signals_generated: Mapped[int] = mapped_column(Integer, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, default=0)
    api_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)


class ApiUsage(Base, TimestampMixin):
    __tablename__ = "api_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)  # OPENAI, FINNHUB, NEWSAPI, etc.
    operation: Mapped[str] = mapped_column(String(80))
    units_consumed: Mapped[int] = mapped_column(Integer, default=1)  # tokens or calls
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)


class SystemSetting(Base, TimestampMixin):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    value_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
