import pytest
from app.services.market_data.confirmation import TechnicalConfirmationGate


def test_confirmation_insufficient_data():
    # Empty market data
    res = TechnicalConfirmationGate.evaluate(
        symbol="RELIANCE",
        news_sentiment="BULLISH",
        news_impact=80.0,
        market_data=None
    )
    assert res.is_confirmed is False
    assert res.status == "INSUFFICIENT_DATA"
    assert res.recommendation == "NO_TRADE"
    assert len(res.conflicts) > 0


def test_confirmation_neutral_news():
    market_snapshot = {
        "last_price": 2950.0,
        "sma_20": 2900.0,
        "rsi_14": 55.0,
        "macd_hist": 2.5
    }
    res = TechnicalConfirmationGate.evaluate(
        symbol="RELIANCE",
        news_sentiment="NEUTRAL",
        news_impact=40.0,
        market_data=market_snapshot
    )
    assert res.is_confirmed is False
    assert res.status == "NEUTRAL_MARKET"
    assert res.recommendation == "WATCH"


def test_confirmation_bullish_aligned():
    # Bullish news + strong technical uptrend
    market_snapshot = {
        "last_price": 3050.0,
        "sma_20": 2980.0,
        "sma_50": 2900.0,
        "rsi_14": 62.0,
        "macd_hist": 4.5,
        "vol_surge_ratio": 1.4,
        "support_level": 2950.0,
        "resistance_level": 3100.0
    }
    res = TechnicalConfirmationGate.evaluate(
        symbol="RELIANCE",
        news_sentiment="BULLISH",
        news_impact=85.0,
        market_data=market_snapshot
    )
    assert res.is_confirmed is True
    assert res.status == "CONFIRMED"
    assert res.recommendation == "ALLOW_SIGNAL"
    assert res.technical_score >= 60.0
    assert len(res.reasons) >= 3


def test_confirmation_bullish_conflict_bearish_breakdown():
    # Positive news, BUT stock is breaking down hard below 20 SMA, RSI weak, MACD negative
    market_snapshot = {
        "last_price": 2780.0,
        "sma_20": 2950.0,
        "sma_50": 3000.0,
        "rsi_14": 34.0,
        "macd_hist": -7.2,
        "vol_surge_ratio": 0.8,
        "support_level": 2850.0,  # price breached support
        "resistance_level": 3000.0
    }
    res = TechnicalConfirmationGate.evaluate(
        symbol="RELIANCE",
        news_sentiment="BULLISH",
        news_impact=85.0,
        market_data=market_snapshot
    )
    assert res.is_confirmed is False
    assert res.status == "CONFLICTING"
    assert res.recommendation == "NO_TRADE"
    assert len(res.conflicts) >= 2


def test_confirmation_bearish_aligned():
    # Bearish news + downward technical momentum
    market_snapshot = {
        "last_price": 1620.0,
        "sma_20": 1680.0,
        "sma_50": 1720.0,
        "rsi_14": 41.0,
        "macd_hist": -3.8,
        "vol_surge_ratio": 1.3,
        "support_level": 1590.0,
        "resistance_level": 1670.0
    }
    res = TechnicalConfirmationGate.evaluate(
        symbol="HDFCBANK",
        news_sentiment="BEARISH",
        news_impact=75.0,
        market_data=market_snapshot
    )
    assert res.is_confirmed is True
    assert res.status == "CONFIRMED"
    assert res.recommendation == "ALLOW_SIGNAL"
    assert res.technical_score >= 60.0


def test_confirmation_bearish_conflict_bullish_breakout():
    # Negative news, BUT stock is surging above 20 SMA, RSI 68, MACD positive
    market_snapshot = {
        "last_price": 1750.0,
        "sma_20": 1680.0,
        "sma_50": 1650.0,
        "rsi_14": 68.0,
        "macd_hist": 5.0,
        "vol_surge_ratio": 1.5,
        "support_level": 1660.0,
        "resistance_level": 1720.0  # price breached above resistance
    }
    res = TechnicalConfirmationGate.evaluate(
        symbol="HDFCBANK",
        news_sentiment="BEARISH",
        news_impact=80.0,
        market_data=market_snapshot
    )
    assert res.is_confirmed is False
    assert res.status == "CONFLICTING"
    assert res.recommendation == "NO_TRADE"
    assert len(res.conflicts) >= 2
