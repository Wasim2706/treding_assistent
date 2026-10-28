import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app.services.market_data.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_atr,
    calculate_vwap,
    calculate_classic_pivots,
    calculate_camarilla_pivots,
    calculate_volatility,
    determine_trend_bias,
    calculate_all_indicators,
)


@pytest.fixture
def sample_ohlcv_df():
    """Generates 50 daily candles of synthetic OHLCV data."""
    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(50)]
    np.random.seed(42)
    base = 1000.0
    returns = np.random.normal(0.001, 0.015, 50)
    prices = base * np.exp(np.cumsum(returns))

    data = []
    for dt, close_p in zip(dates, prices):
        open_p = close_p * np.random.uniform(0.99, 1.01)
        high_p = max(open_p, close_p) * np.random.uniform(1.002, 1.015)
        low_p = min(open_p, close_p) * np.random.uniform(0.985, 0.998)
        vol = np.random.uniform(500000, 2000000)
        data.append({
            "Date": dt,
            "Open": open_p,
            "High": high_p,
            "Low": low_p,
            "Close": close_p,
            "Volume": vol
        })

    df = pd.DataFrame(data)
    df = df.set_index("Date")
    return df


def test_calculate_sma(sample_ohlcv_df):
    sma20 = calculate_sma(sample_ohlcv_df["Close"], 20)
    assert len(sma20) == len(sample_ohlcv_df)
    # The 20th item should equal the arithmetic mean of the first 20 items
    expected_20 = sample_ohlcv_df["Close"].iloc[0:20].mean()
    assert abs(sma20.iloc[19] - expected_20) < 1e-4


def test_calculate_ema(sample_ohlcv_df):
    ema20 = calculate_ema(sample_ohlcv_df["Close"], 20)
    assert len(ema20) == len(sample_ohlcv_df)
    assert not ema20.isna().any()


def test_calculate_rsi_bounds(sample_ohlcv_df):
    rsi = calculate_rsi(sample_ohlcv_df["Close"], 14)
    assert len(rsi) == len(sample_ohlcv_df)
    valid_rsi = rsi.dropna()
    assert (valid_rsi >= 0.0).all()
    assert (valid_rsi <= 100.0).all()


def test_calculate_rsi_extreme_uptrend():
    # Monotonically increasing prices -> RSI should approach 100
    prices = pd.Series([100.0 + i * 5.0 for i in range(30)])
    rsi = calculate_rsi(prices, 14)
    assert rsi.iloc[-1] > 90.0


def test_calculate_rsi_extreme_downtrend():
    # Monotonically decreasing prices -> RSI should approach 0
    prices = pd.Series([200.0 - i * 5.0 for i in range(30)])
    rsi = calculate_rsi(prices, 14)
    assert rsi.iloc[-1] < 10.0


def test_calculate_macd(sample_ohlcv_df):
    macd, signal, hist = calculate_macd(sample_ohlcv_df["Close"], 12, 26, 9)
    assert len(macd) == len(sample_ohlcv_df)
    assert len(signal) == len(sample_ohlcv_df)
    assert len(hist) == len(sample_ohlcv_df)
    # Check identity: hist = macd - signal
    np.testing.assert_allclose(hist, macd - signal, rtol=1e-5)


def test_calculate_atr(sample_ohlcv_df):
    atr = calculate_atr(sample_ohlcv_df, 14)
    assert len(atr) == len(sample_ohlcv_df)
    assert (atr > 0.0).all()


def test_calculate_vwap(sample_ohlcv_df):
    vwap = calculate_vwap(sample_ohlcv_df)
    assert len(vwap) == len(sample_ohlcv_df)
    assert not vwap.isna().any()
    # VWAP should lie within reasonable price range
    assert (vwap > sample_ohlcv_df["Low"].min() * 0.9).all()
    assert (vwap < sample_ohlcv_df["High"].max() * 1.1).all()


def test_classic_pivot_points():
    h = 3000.0
    l = 2900.0
    c = 2950.0
    pivots = calculate_classic_pivots(h, l, c)

    expected_p = (h + l + c) / 3.0  # 2950.0
    assert pivots["pivot"] == round(expected_p, 2)
    assert pivots["r1"] == round(2.0 * expected_p - l, 2)  # 3000.0
    assert pivots["s1"] == round(2.0 * expected_p - h, 2)  # 2900.0
    assert pivots["r2"] > pivots["r1"]
    assert pivots["s2"] < pivots["s1"]


def test_camarilla_pivot_points():
    h = 3000.0
    l = 2900.0
    c = 2950.0
    cam = calculate_camarilla_pivots(h, l, c)
    assert cam["cam_r4"] > cam["cam_r3"]
    assert cam["cam_s4"] < cam["cam_s3"]


def test_calculate_volatility(sample_ohlcv_df):
    vol = calculate_volatility(sample_ohlcv_df["Close"], 20)
    assert isinstance(vol, float)
    assert vol > 0.0
    assert vol < 150.0  # Reasonable annualized equity volatility range


def test_determine_trend_bias():
    # Strong bullish scenario
    bias_bull = determine_trend_bias(
        last_price=3000.0,
        sma_20=2900.0,
        sma_50=2800.0,
        sma_200=2700.0,
        rsi_14=65.0,
        macd_hist=5.2
    )
    assert bias_bull == "BULLISH"

    # Strong bearish scenario
    bias_bear = determine_trend_bias(
        last_price=2600.0,
        sma_20=2750.0,
        sma_50=2850.0,
        sma_200=2950.0,
        rsi_14=35.0,
        macd_hist=-8.5
    )
    assert bias_bear == "BEARISH"

    # Mixed / Neutral scenario
    bias_neutral = determine_trend_bias(
        last_price=2800.0,
        sma_20=2810.0,
        sma_50=2790.0,
        sma_200=2800.0,
        rsi_14=49.0,
        macd_hist=0.1
    )
    assert bias_neutral == "NEUTRAL"


def test_calculate_all_indicators_integration(sample_ohlcv_df):
    res = calculate_all_indicators(sample_ohlcv_df)

    expected_keys = [
        "last_price", "change", "change_pct", "open_price", "high_price",
        "low_price", "prev_close", "volume", "avg_volume_20", "sma_20",
        "sma_50", "rsi_14", "macd", "macd_signal", "macd_hist",
        "atr_14", "vwap", "support_level", "resistance_level",
        "gap_pct", "volatility", "trend_bias"
    ]
    for key in expected_keys:
        assert key in res, f"Missing key in indicators: {key}"
        assert res[key] is not None
