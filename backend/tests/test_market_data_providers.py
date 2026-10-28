import pytest
from datetime import datetime, timezone, timedelta

from app.services.market_data.base import (
    get_indian_market_status,
    normalize_ticker,
    clean_ticker,
    IST_OFFSET,
)
from app.services.market_data.mock import MockMarketDataProvider
from app.services.market_data.yahoo import YahooFinanceProvider


def test_symbol_normalization_and_clean():
    assert normalize_ticker("RELIANCE") == "RELIANCE.NS"
    assert normalize_ticker("TCS.NS") == "TCS.NS"
    assert normalize_ticker("^NSEI") == "^NSEI"
    assert normalize_ticker("^NSEBANK") == "^NSEBANK"
    assert normalize_ticker("CL=F") == "CL=F"
    assert normalize_ticker("INR=X") == "INR=X"

    assert clean_ticker("RELIANCE.NS") == "RELIANCE"
    assert clean_ticker("TCS.BO") == "TCS"
    assert clean_ticker("INFY") == "INFY"


def test_indian_market_status_scenarios():
    # Scenario A: Regular trading hours (Tuesday at 11:30 AM IST)
    # 2026-03-10 is Tuesday
    dt_regular = datetime(2026, 3, 10, 11, 30, tzinfo=IST_OFFSET)
    status_reg = get_indian_market_status(dt_regular)
    assert status_reg["is_open"] is True
    assert status_reg["session"] == "REGULAR"
    assert status_reg["trading_day"] is True

    # Scenario B: Pre-open session (Tuesday at 09:05 AM IST)
    dt_pre = datetime(2026, 3, 10, 9, 5, tzinfo=IST_OFFSET)
    status_pre = get_indian_market_status(dt_pre)
    assert status_pre["is_open"] is False
    assert status_pre["session"] == "PRE_OPEN"

    # Scenario C: Post-close session (Tuesday at 15:45 IST)
    dt_post = datetime(2026, 3, 10, 15, 45, tzinfo=IST_OFFSET)
    status_post = get_indian_market_status(dt_post)
    assert status_post["is_open"] is False
    assert status_post["session"] == "POST_CLOSE"

    # Scenario D: After hours closed (Tuesday at 20:00 IST)
    dt_closed = datetime(2026, 3, 10, 20, 0, tzinfo=IST_OFFSET)
    status_closed = get_indian_market_status(dt_closed)
    assert status_closed["is_open"] is False
    assert status_closed["session"] == "CLOSED"

    # Scenario E: Weekend (Sunday at 12:00 IST)
    dt_weekend = datetime(2026, 3, 15, 12, 0, tzinfo=IST_OFFSET)
    status_weekend = get_indian_market_status(dt_weekend)
    assert status_weekend["is_open"] is False
    assert status_weekend["session"] == "CLOSED"
    assert status_weekend["trading_day"] is False
    assert "Weekend" in status_weekend["session_description"]


@pytest.mark.asyncio
async def test_mock_market_data_provider_quote():
    provider = MockMarketDataProvider(seed=123)
    quote = await provider.get_latest_price("RELIANCE")

    assert quote["symbol"] == "RELIANCE"
    assert quote["last_price"] > 2000.0
    assert "change" in quote
    assert "change_pct" in quote
    assert "volume" in quote
    assert quote["volume"] > 0


@pytest.mark.asyncio
async def test_mock_market_data_provider_history():
    provider = MockMarketDataProvider(seed=123)
    df = await provider.get_historical_ohlcv("TCS", period="3mo")

    assert len(df) >= 60
    assert set(["Open", "High", "Low", "Close", "Volume"]).issubset(df.columns)
    assert (df["High"] >= df["Low"]).all()


@pytest.mark.asyncio
async def test_mock_market_data_provider_index_quote():
    provider = MockMarketDataProvider(seed=123)
    nifty = await provider.get_index_quote("^NSEI")

    assert nifty["symbol"] == "^NSEI"
    assert nifty["last_price"] > 20000.0


@pytest.mark.asyncio
async def test_yahoo_finance_provider_graceful_fallback():
    # If ticker does not exist or network fails, YahooFinanceProvider must safely return mock data
    provider = YahooFinanceProvider(timeout_sec=2.0)
    quote = await provider.get_latest_price("NON_EXISTENT_TICKER_XYZ")

    assert "last_price" in quote
    assert quote["last_price"] > 0
