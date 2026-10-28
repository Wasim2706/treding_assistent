import pytest
from sqlalchemy import select
from app.models.market import Stock, Sector
from app.models.signal import Signal
from app.models.paper_trading import PaperTrade
from app.models.system import SystemSetting


@pytest.mark.asyncio
async def test_seeded_sectors_and_stocks(db_session):
    # Verify sectors were seeded
    sectors_res = await db_session.execute(select(Sector))
    sectors = sectors_res.scalars().all()
    assert len(sectors) >= 10

    sector_names = [s.name for s in sectors]
    assert "Banking & Financial Services" in sector_names
    assert "Information Technology" in sector_names
    assert "Oil, Gas & Energy" in sector_names

    # Verify stocks were seeded
    stocks_res = await db_session.execute(select(Stock))
    stocks = stocks_res.scalars().all()
    assert len(stocks) >= 20

    tickers = [s.exchange_ticker for s in stocks]
    assert "RELIANCE" in tickers
    assert "TCS" in tickers
    assert "HDFCBANK" in tickers


@pytest.mark.asyncio
async def test_signal_and_paper_trade_creation(db_session):
    # Insert a test decision-support signal
    sig = Signal(
        symbol="RELIANCE.NS",
        direction="BUY",
        entry_zone="₹2920 - ₹2935",
        entry_price=2925.0,
        stop_loss=2890.0,
        target_1=2990.0,
        target_2=3040.0,
        risk_reward="1:2.0",
        entry_time_window="After 09:30 IST upon technical confirmation",
        exit_time_window="Before 15:15 IST",
        confidence=74,
        news_score=80.0,
        technical_score=70.0,
        volume_score=75.0,
        market_score=68.0,
        sector_score=72.0,
        composite_score=73.5,
        reasoning="Strong earnings outlook combined with breakout above 50 SMA.",
        invalidated_if="Falls below 2890 or broader market faces severe weakness.",
        technical_confirmation="RSI at 59, 20 EMA crossing above 50 SMA on 15m chart",
        status="PENDING"
    )
    db_session.add(sig)
    await db_session.commit()
    await db_session.refresh(sig)
    assert sig.id is not None

    # Create associated paper trade
    trade = PaperTrade(
        signal_id=sig.id,
        symbol="RELIANCE.NS",
        direction="BUY",
        quantity=50,
        entry_price=2925.0,
        current_price=2925.0,
        stop_loss=2890.0,
        target_1=2990.0,
        status="OPEN"
    )
    db_session.add(trade)
    await db_session.commit()
    await db_session.refresh(trade)
    assert trade.id is not None
    assert trade.status == "OPEN"
