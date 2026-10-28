import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.market_data.service import market_data_service
from app.models.market import MarketDataSnapshot


@pytest.mark.asyncio
async def test_market_service_quote_and_caching():
    quote1 = await market_data_service.get_quote("RELIANCE")
    assert quote1["symbol"] == "RELIANCE"
    assert quote1["last_price"] > 0

    # Second call should be served from cache
    quote2 = await market_data_service.get_quote("RELIANCE")
    assert quote2["last_price"] == quote1["last_price"]


@pytest.mark.asyncio
async def test_market_service_indicators():
    indicators = await market_data_service.get_indicators("TCS")
    assert indicators["symbol"] == "TCS"
    assert "rsi_14" in indicators
    assert "macd" in indicators
    assert "sma_20" in indicators
    assert "trend_bias" in indicators


@pytest.mark.asyncio
async def test_market_service_get_or_create_snapshot(db_session: AsyncSession):
    snapshot = await market_data_service.get_or_create_snapshot("HDFCBANK", db_session)
    assert isinstance(snapshot, MarketDataSnapshot)
    assert snapshot.symbol == "HDFCBANK"
    assert snapshot.last_price > 0
    assert snapshot.rsi_14 is not None


@pytest.mark.asyncio
async def test_market_service_overview():
    overview = await market_data_service.get_market_overview()
    assert "session" in overview
    assert "benchmarks" in overview
    benchmarks = overview["benchmarks"]
    assert "nifty50" in benchmarks
    assert "bank_nifty" in benchmarks
    assert "crude_oil" in benchmarks


@pytest.mark.asyncio
async def test_market_api_status(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/market/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "session" in data["data"]
    assert "current_ist" in data["data"]


@pytest.mark.asyncio
async def test_market_api_overview(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/market/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "benchmarks" in data["data"]


@pytest.mark.asyncio
async def test_market_api_quote(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/market/quote/INFY")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["symbol"] == "INFY"
    assert data["data"]["last_price"] > 0


@pytest.mark.asyncio
async def test_market_api_indicators(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/market/indicators/INFY")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "rsi_14" in data["data"]
    assert "macd" in data["data"]


@pytest.mark.asyncio
async def test_market_api_snapshot_post(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/market/snapshot/SBIN")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["symbol"] == "SBIN"
    assert data["data"]["last_price"] > 0
