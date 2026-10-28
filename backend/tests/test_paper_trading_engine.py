import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.signal import Signal
from app.models.paper_trading import PaperTrade
from app.services.paper_trading.engine import PaperTradingEngine, paper_trading_engine
from app.services.market_data.service import market_data_service


def test_position_sizing_two_percent_risk():
    engine = PaperTradingEngine()
    capital = 1_000_000.0  # ₹10 Lakhs
    entry = 3000.0
    stop_loss = 2950.0      # Risk per share = ₹50
    # 2% of 10L = 20,000 -> 20,000 / 50 = 400 shares
    qty = engine.calculate_position_size(entry, stop_loss, capital)
    assert qty == 400


@pytest.mark.asyncio
async def test_open_position_from_signal(db_session: AsyncSession):
    # Create test signal
    sig = Signal(
        symbol="TCS",
        direction="BUY",
        entry_zone="₹3900 - ₹3920",
        entry_price=3900.0,
        stop_loss=3820.0,
        target_1=4020.0,
        target_2=4100.0,
        risk_reward="1:2.5",
        entry_time_window="09:30-11:30",
        exit_time_window="15:15",
        confidence=80,
        news_score=80.0,
        technical_score=80.0,
        volume_score=75.0,
        market_score=70.0,
        sector_score=70.0,
        composite_score=76.0,
        reasoning="Test signal setup",
        invalidated_if="Breach of stop loss",
        technical_confirmation="Confirmed",
        status="PENDING",
        is_paper_traded=False
    )
    db_session.add(sig)
    await db_session.commit()
    await db_session.refresh(sig)

    trade = await paper_trading_engine.open_position_from_signal(sig.id, db_session)

    assert isinstance(trade, PaperTrade)
    assert trade.symbol == "TCS"
    assert trade.direction == "BUY"
    assert trade.entry_price == 3900.0
    assert trade.stop_loss == 3820.0
    assert trade.status == "OPEN"
    assert trade.quantity > 0

    # Signal status should be updated
    await db_session.refresh(sig)
    assert sig.is_paper_traded is True
    assert sig.status == "TRIGGERED"


@pytest.mark.asyncio
async def test_trailing_stop_on_target_1_hit(db_session: AsyncSession):
    # Create trade with entry=2000, SL=1960, T1=2060, T2=2100
    trade = PaperTrade(
        symbol="INFY",
        direction="BUY",
        quantity=100,
        entry_price=2000.0,
        current_price=2000.0,
        stop_loss=1960.0,
        target_1=2060.0,
        target_2=2100.0,
        status="OPEN"
    )
    db_session.add(trade)
    await db_session.commit()
    await db_session.refresh(trade)

    # Mock market price to hit Target 1 (2070.0)
    market_data_service.set_mock_price("INFY", 2070.0)

    update_res = await paper_trading_engine.update_open_positions(db_session)
    await db_session.refresh(trade)

    # Position should still be OPEN, but stop_loss moved to entry_price (2000.0)
    assert trade.status == "OPEN"
    assert trade.stop_loss == 2000.0
    assert trade.max_favorable_excursion > 0
    # Reset mock price to baseline
    market_data_service.set_mock_price("INFY", 1840.0)


@pytest.mark.asyncio
async def test_stop_loss_hit(db_session: AsyncSession):
    # Create trade with entry=2000, SL=1960
    trade = PaperTrade(
        symbol="SBIN",
        direction="BUY",
        quantity=200,
        entry_price=800.0,
        current_price=800.0,
        stop_loss=785.0,
        target_1=825.0,
        status="OPEN"
    )
    db_session.add(trade)
    await db_session.commit()
    await db_session.refresh(trade)

    # Mock market price dropping below Stop Loss (780.0)
    market_data_service.set_mock_price("SBIN", 780.0)

    update_res = await paper_trading_engine.update_open_positions(db_session)
    await db_session.refresh(trade)

    assert trade.status == "STOPPED_OUT"
    assert trade.exit_reason == "STOP_LOSS_HIT"
    assert trade.realized_pnl < 0
    assert trade.exited_at is not None
    # Reset mock price to baseline
    market_data_service.set_mock_price("SBIN", 820.0)


@pytest.mark.asyncio
async def test_eod_squareoff(db_session: AsyncSession):
    trade = PaperTrade(
        symbol="LT",
        direction="BUY",
        quantity=50,
        entry_price=3500.0,
        current_price=3520.0,
        stop_loss=3450.0,
        target_1=3600.0,
        status="OPEN"
    )
    db_session.add(trade)
    await db_session.commit()

    # Force EOD square-off
    await paper_trading_engine.update_open_positions(db_session, force_eod_squareoff=True)
    await db_session.refresh(trade)

    assert trade.status == "CLOSED"
    assert trade.exit_reason == "EOD_SQUAREOFF"


@pytest.mark.asyncio
async def test_portfolio_metrics_calculation(db_session: AsyncSession):
    metrics = await paper_trading_engine.get_metrics(db_session)
    assert metrics.total_trades >= 0
    assert 0.0 <= metrics.win_rate_pct <= 100.0
    assert metrics.profit_factor >= 0.0
