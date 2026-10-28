from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from app.core.logging import logger

# Create SQLAlchemy Async Engine
engine_kwargs = {"echo": False}
if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initializes database schema and populates initial Indian market sector and stock records.
    """
    from app.models import (
        User, NewsArticle, NewsAnalysis, NewsEntity,
        Stock, Sector, MarketDataSnapshot, Signal,
        PaperTrade, PredictionResult, DailyReport, Alert,
        SystemLog, ApiUsage, SystemSetting
    )
    from app.models.seed import seed_initial_market_data

    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")

    # Seed core Indian stocks and sectors
    async with AsyncSessionLocal() as session:
        await seed_initial_market_data(session)
