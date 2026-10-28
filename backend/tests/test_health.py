import pytest


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert data["mode"] == "PAPER_TRADING_ONLY"
    assert data["real_orders_enabled"] is False
    assert data["paper_trading_safety"] == "ENFORCED"


@pytest.mark.asyncio
async def test_ready_endpoint(async_client):
    response = await async_client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] is True
    assert data["checks"]["safety_rules_active"] is True


@pytest.mark.asyncio
async def test_metrics_endpoint(async_client):
    response = await async_client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert "news_articles_total" in data
    assert "signals_generated_total" in data


@pytest.mark.asyncio
async def test_disclaimer_endpoint(async_client):
    response = await async_client.get("/disclaimer")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "PAPER_TRADING_ONLY"
    assert "PAPER TRADING" in data["disclaimer"]
    assert "No guaranteed" in data["guarantee_statement"] or "do not guarantee" in data["guarantee_statement"]
