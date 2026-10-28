import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal


@pytest.mark.asyncio
async def test_signals_list_and_top_endpoints(async_client: AsyncClient, db_session: AsyncSession):
    # Seed a high-conviction signal
    sig = Signal(
        symbol="RELIANCE",
        direction="BUY",
        entry_zone="₹2940 - ₹2960",
        entry_price=2950.0,
        stop_loss=2890.0,
        target_1=3040.0,
        target_2=3120.0,
        risk_reward="1:2.8",
        entry_time_window="09:30-11:30 IST",
        exit_time_window="15:15 IST",
        confidence=85,
        news_score=85.0,
        technical_score=80.0,
        volume_score=75.0,
        market_score=80.0,
        sector_score=80.0,
        composite_score=81.0,
        reasoning="High conviction test setup",
        invalidated_if="Below stop loss",
        technical_confirmation="Confirmed",
        status="PENDING",
        is_paper_traded=False
    )
    db_session.add(sig)
    await db_session.commit()

    # List signals
    resp = await async_client.get("/api/v1/signals")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["items"]) >= 1

    # Top signals
    top_resp = await async_client.get("/api/v1/signals/top")
    assert top_resp.status_code == 200
    top_data = top_resp.json()
    assert top_data["success"] is True
    assert len(top_data["data"]) >= 1
    assert top_data["data"][0]["composite_score"] >= 70.0


@pytest.mark.asyncio
async def test_signals_generate_endpoint(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/signals/generate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "signals_generated" in data["data"]


@pytest.mark.asyncio
async def test_paper_trading_api_flow(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Open manual paper trade
    open_payload = {
        "symbol": "HDFCBANK",
        "direction": "BUY",
        "quantity": 100,
        "entry_price": 1680.0,
        "stop_loss": 1600.0,
        "target_1": 1750.0,
        "target_2": 1800.0,
        "notes": "API test virtual trade"
    }
    open_resp = await async_client.post("/api/v1/paper-trading/open", json=open_payload)
    assert open_resp.status_code == 200
    trade_data = open_resp.json()["data"]
    trade_id = trade_data["id"]
    assert trade_data["symbol"] == "HDFCBANK"
    assert trade_data["status"] == "OPEN"

    # 2. List positions
    pos_resp = await async_client.get("/api/v1/paper-trading/positions")
    assert pos_resp.status_code == 200
    assert any(p["id"] == trade_id for p in pos_resp.json()["data"])

    # 3. Update positions
    upd_resp = await async_client.post("/api/v1/paper-trading/update-positions")
    assert upd_resp.status_code == 200
    assert upd_resp.json()["success"] is True

    # 4. Close trade
    close_resp = await async_client.post(f"/api/v1/paper-trading/close/{trade_id}?exit_price=1690.0&reason=MANUAL_EXIT")
    assert close_resp.status_code == 200
    closed_data = close_resp.json()["data"]
    assert closed_data["status"] == "CLOSED"
    assert closed_data["realized_pnl"] == 1000.0  # (1690 - 1680) * 100

    # 5. Check metrics
    metrics_resp = await async_client.get("/api/v1/paper-trading/metrics")
    assert metrics_resp.status_code == 200
    m = metrics_resp.json()["data"]
    assert m["total_trades"] >= 1
    assert m["closed_trades"] >= 1
    assert m["winning_trades"] >= 1
    assert m["win_rate_pct"] > 0.0


@pytest.mark.asyncio
async def test_paper_trading_execute_signal_endpoint(async_client: AsyncClient, db_session: AsyncSession):
    # Create an actionable BUY signal
    sig = Signal(
        symbol="INFY",
        direction="BUY",
        entry_zone="₹1800 - ₹1820",
        entry_price=1810.0,
        stop_loss=1770.0,
        target_1=1870.0,
        target_2=1920.0,
        risk_reward="1:2.75",
        entry_time_window="09:30-11:30 IST",
        exit_time_window="15:15 IST",
        confidence=82,
        news_score=80.0,
        technical_score=82.0,
        volume_score=70.0,
        market_score=80.0,
        sector_score=80.0,
        composite_score=78.4,
        reasoning="Test actionable signal for auto-execution",
        invalidated_if="Below stop loss",
        technical_confirmation="Confirmed",
        status="PENDING",
        is_paper_traded=False
    )
    db_session.add(sig)
    await db_session.commit()
    await db_session.refresh(sig)

    resp = await async_client.post(f"/api/v1/paper-trading/execute-signal/{sig.id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["signal_id"] == sig.id
    assert data["symbol"] == "INFY"
    assert data["status"] == "OPEN"
    assert data["quantity"] > 0
