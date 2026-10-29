from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # General App Configuration
    APP_NAME: str = "Indian Stock Market AI Intelligence & Decision Support"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "dev-insecure-secret-key-change-in-production-12345"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]

    # TRADING SAFETY - STRICTLY ENFORCED
    PAPER_TRADING_ONLY: bool = True
    REAL_ORDERS_ENABLED: bool = False
    REGULATORY_DISCLAIMER: str = (
        "AI Market-Intelligence & Decision-Support System operating strictly in PAPER TRADING / SIGNAL-ONLY mode. "
        "This system does not provide guaranteed returns or investment advice. All financial market trading carries high risk."
    )

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./trading_assistant.db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if not v:
            return "sqlite+aiosqlite:///./trading_assistant.db"
        # Render provides postgres:// which needs postgresql+asyncpg://
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Redis (Optional, Celery/caching fallback)
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Configuration (OpenAI)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    MAX_ARTICLES_PER_AI_CYCLE: int = 10
    DAILY_AI_BUDGET_USD: float = 5.0

    # News Provider APIs
    NEWS_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    ALPHA_VANTAGE_API_KEY: str = ""
    GNEWS_API_KEY: str = ""

    # Market Data API
    MARKET_DATA_API_KEY: str = ""
    MARKET_DATA_PROVIDER: str = "yahoo"  # yahoo, nse, mock

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_ALERTS_ENABLED: bool = False

    # Signal Engine Configurable Weights (Must sum to 1.0)
    WEIGHT_NEWS: float = 0.35
    WEIGHT_TECHNICAL: float = 0.30
    WEIGHT_VOLUME: float = 0.15
    WEIGHT_MARKET: float = 0.10
    WEIGHT_SECTOR: float = 0.10

    # Risk & Thresholds
    MIN_SIGNAL_CONFIDENCE: int = 65  # 0-100 score threshold to issue BUY/SELL
    ALERT_IMPACT_THRESHOLD: int = 70  # Telegram alert trigger
    DEFAULT_RISK_REWARD_TARGET: float = 2.0  # 1:2 R:R minimum

    # Market Schedule (Asia/Kolkata IST)
    TIMEZONE: str = "Asia/Kolkata"
    NEWS_CYCLE_INTERVAL_SECONDS: int = 300  # 5 minutes
    PRE_MARKET_REPORT_TIME: str = "08:30"   # IST
    NSE_MARKET_OPEN: str = "09:15"          # IST
    NSE_MARKET_CLOSE: str = "15:30"         # IST

    # Background Worker Execution Control
    ENABLE_SCHEDULER: bool = True           # Set False when worker is deployed as separate process


settings = Settings()
