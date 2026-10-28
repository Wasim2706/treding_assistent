import pytest


@pytest.mark.asyncio
async def test_get_stocks_api(async_client):
    response = await async_client.get("/api/v1/market/stocks")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 20


@pytest.mark.asyncio
async def test_get_sectors_api(async_client):
    response = await async_client.get("/api/v1/market/sectors")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 10
    # Check sector sensitivity matrix
    banking = next((s for s in data["data"] if "Banking" in s["name"]), None)
    assert banking is not None
    assert "rbi_rate_cut" in banking["sensitivities"]


@pytest.mark.asyncio
async def test_news_endpoint_pagination(async_client):
    response = await async_client.get("/api/v1/news?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_signals_endpoint(async_client):
    response = await async_client.get("/api/v1/signals")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_paper_trading_metrics(async_client):
    response = await async_client.get("/api/v1/paper-trading/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "win_rate_pct" in data["data"]
    assert "profit_factor" in data["data"]


@pytest.mark.asyncio
async def test_settings_weights_update(async_client):
    # Valid weights totaling 1.0
    payload = {
        "weight_news": 0.30,
        "weight_technical": 0.35,
        "weight_volume": 0.15,
        "weight_market": 0.10,
        "weight_sector": 0.10
    }
    response = await async_client.put("/api/v1/settings/weights", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["technical"] == 0.35

    # Invalid weights totaling != 1.0 must fail with 400
    bad_payload = {
        "weight_news": 0.50,
        "weight_technical": 0.50,
        "weight_volume": 0.50,
        "weight_market": 0.10,
        "weight_sector": 0.10
    }
    bad_resp = await async_client.put("/api/v1/settings/weights", json=bad_payload)
    assert bad_resp.status_code == 400


@pytest.mark.asyncio
async def test_trigger_news_refresh_api(async_client):
    response = await async_client.post("/api/v1/news/refresh")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "articles_fetched" in data["data"]
    assert "articles_stored" in data["data"]
