import os
import sys
import pytest
import pytest_asyncio

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure testing environment before importing app modules
TEST_DB_FILE = os.path.join(os.path.dirname(__file__), "test_trading.db")
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
os.environ["PAPER_TRADING_ONLY"] = "true"

from httpx import AsyncClient, ASGITransport
import app.models  # Ensures all ORM models are registered
from app.core.database import Base, get_db, engine, AsyncSessionLocal
from app.models.seed import seed_initial_market_data
from app.main import create_app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed baseline market data
    async with AsyncSessionLocal() as session:
        await seed_initial_market_data(session)

    yield

    # Clean up test DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client():
    app = create_app()

    async def override_get_db():
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
