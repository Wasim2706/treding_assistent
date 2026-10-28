import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Computes Simple Moving Average with minimum observations."""
    return series.rolling(window=period, min_periods=max(1, period // 2)).mean()


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Computes Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Computes Relative Strength Index (RSI) using Wilder's smoothed moving average.
    """
    if len(series) < 2:
        return pd.Series([50.0] * len(series), index=series.index)

    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta.where(delta < 0, 0.0))

    # Wilder's Smoothing: alpha = 1 / period
    alpha = 1.0 / period
    avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))

    # When loss is 0 (all gains), RSI is 100; when gain is 0 (all losses), RSI is 0
    fallback = pd.Series(np.where(avg_gain > 0, 100.0, 50.0), index=rsi.index)
    rsi = rsi.fillna(fallback)
    return rsi


def calculate_macd(
    series: pd.Series, 
    fast: int = 12, 
    slow: int = 26, 
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Computes MACD (Moving Average Convergence Divergence).
    Returns (macd_line, signal_line, histogram).
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Computes Average True Range (ATR)."""
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder's smoothing for ATR
    atr = true_range.ewm(alpha=1.0 / period, adjust=False).mean()
    return atr


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Computes Volume Weighted Average Price (VWAP)."""
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
    vol = df["Volume"].fillna(0)
    pv = typical_price * vol
    cum_pv = pv.cumsum()
    cum_vol = vol.cumsum()
    vwap = cum_pv / cum_vol.replace(0, np.nan)
    return vwap.fillna(typical_price)


def calculate_classic_pivots(
    prev_high: float, 
    prev_low: float, 
    prev_close: float
) -> Dict[str, float]:
    """
    Computes Classic Floor Pivot points (P, R1, S1, R2, S2, R3, S3).
    """
    pivot = (prev_high + prev_low + prev_close) / 3.0
    r1 = (2.0 * pivot) - prev_low
    s1 = (2.0 * pivot) - prev_high
    r2 = pivot + (prev_high - prev_low)
    s2 = pivot - (prev_high - prev_low)
    r3 = prev_high + 2.0 * (pivot - prev_low)
    s3 = prev_low - 2.0 * (prev_high - pivot)

    return {
        "pivot": round(pivot, 2),
        "r1": round(r1, 2),
        "s1": round(s1, 2),
        "r2": round(r2, 2),
        "s2": round(s2, 2),
        "r3": round(r3, 2),
        "s3": round(s3, 2),
    }


def calculate_camarilla_pivots(
    prev_high: float, 
    prev_low: float, 
    prev_close: float
) -> Dict[str, float]:
    """
    Computes Camarilla Pivot levels (Breakout R4/S4 and Reversal R3/S3).
    """
    diff = prev_high - prev_low
    r4 = prev_close + diff * 1.1 / 2.0
    r3 = prev_close + diff * 1.1 / 4.0
    s3 = prev_close - diff * 1.1 / 4.0
    s4 = prev_close - diff * 1.1 / 2.0

    return {
        "cam_r4": round(r4, 2),
        "cam_r3": round(r3, 2),
        "cam_s3": round(s3, 2),
        "cam_s4": round(s4, 2),
    }


def calculate_volatility(close_series: pd.Series, window: int = 20) -> float:
    """Computes 20-day annualized historical volatility percentage."""
    if len(close_series) < 3:
        return 0.0
    log_returns = np.log(close_series / close_series.shift(1)).dropna()
    window_slice = log_returns.tail(window)
    if len(window_slice) < 2:
        return 0.0
    daily_vol = window_slice.std()
    annualized_vol = daily_vol * np.sqrt(252) * 100.0
    return round(float(annualized_vol), 2)


def determine_trend_bias(
    last_price: float,
    sma_20: Optional[float],
    sma_50: Optional[float],
    sma_200: Optional[float],
    rsi_14: Optional[float],
    macd_hist: Optional[float]
) -> str:
    """
    Evaluates multi-timeframe alignment across Moving Averages, RSI, and MACD.
    Returns: 'BULLISH', 'BEARISH', or 'NEUTRAL'
    """
    bull_points = 0
    bear_points = 0

    if sma_20 is not None:
        if last_price > sma_20:
            bull_points += 1
        else:
            bear_points += 1

    if sma_50 is not None:
        if last_price > sma_50:
            bull_points += 1
        else:
            bear_points += 1

    if sma_200 is not None:
        if last_price > sma_200:
            bull_points += 1
        else:
            bear_points += 1

    if rsi_14 is not None:
        if rsi_14 >= 55.0:
            bull_points += 1
        elif rsi_14 <= 45.0:
            bear_points += 1

    if macd_hist is not None:
        if macd_hist > 0:
            bull_points += 1
        elif macd_hist < 0:
            bear_points += 1

    if bull_points >= 3 and bear_points <= 1:
        return "BULLISH"
    elif bear_points >= 3 and bull_points <= 1:
        return "BEARISH"
    return "NEUTRAL"


def calculate_all_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Given an OHLCV DataFrame with at least 5 candles, computes all required
    technical indicators and levels matching MarketDataSnapshot.
    """
    if df is None or len(df) == 0:
        return {}

    # Ensure required columns exist
    req = ["Open", "High", "Low", "Close"]
    for col in req:
        if col not in df.columns:
            raise ValueError(f"DataFrame missing required column: {col}")

    if "Volume" not in df.columns:
        df["Volume"] = 100000.0

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    open_p = df["Open"]
    vol = df["Volume"]

    # Current & previous candle values
    last_idx = -1
    prev_idx = -2 if len(df) >= 2 else -1

    last_price = float(close.iloc[last_idx])
    open_price = float(open_p.iloc[last_idx])
    high_price = float(high.iloc[last_idx])
    low_price = float(low.iloc[last_idx])
    current_vol = float(vol.iloc[last_idx])
    prev_close = float(close.iloc[prev_idx])

    # Percentage change
    change = last_price - prev_close
    change_pct = (change / prev_close * 100.0) if prev_close > 0 else 0.0

    # Gap-up / Gap-down percentage
    gap_pct = ((open_price - prev_close) / prev_close * 100.0) if prev_close > 0 else 0.0

    # Moving Averages
    sma_20_series = calculate_sma(close, 20)
    sma_50_series = calculate_sma(close, 50)
    sma_200_series = calculate_sma(close, 200)
    ema_20_series = calculate_ema(close, 20)

    sma_20 = float(sma_20_series.iloc[last_idx]) if not np.isnan(sma_20_series.iloc[last_idx]) else None
    sma_50 = float(sma_50_series.iloc[last_idx]) if not np.isnan(sma_50_series.iloc[last_idx]) else None
    sma_200 = float(sma_200_series.iloc[last_idx]) if not np.isnan(sma_200_series.iloc[last_idx]) else None
    ema_20 = float(ema_20_series.iloc[last_idx]) if not np.isnan(ema_20_series.iloc[last_idx]) else None

    # RSI
    rsi_series = calculate_rsi(close, 14)
    rsi_14 = float(rsi_series.iloc[last_idx]) if not np.isnan(rsi_series.iloc[last_idx]) else 50.0

    # MACD
    macd_line, macd_sig, macd_h = calculate_macd(close, 12, 26, 9)
    macd = float(macd_line.iloc[last_idx]) if not np.isnan(macd_line.iloc[last_idx]) else 0.0
    macd_signal = float(macd_sig.iloc[last_idx]) if not np.isnan(macd_sig.iloc[last_idx]) else 0.0
    macd_hist = float(macd_h.iloc[last_idx]) if not np.isnan(macd_h.iloc[last_idx]) else 0.0

    # ATR
    atr_series = calculate_atr(df, 14)
    atr_14 = float(atr_series.iloc[last_idx]) if not np.isnan(atr_series.iloc[last_idx]) else None

    # VWAP
    vwap_series = calculate_vwap(df)
    vwap = float(vwap_series.iloc[last_idx]) if not np.isnan(vwap_series.iloc[last_idx]) else None

    # Volume Averages
    vol_sma_20 = float(calculate_sma(vol, 20).iloc[last_idx])
    vol_surge_ratio = (current_vol / vol_sma_20) if vol_sma_20 > 0 else 1.0

    # Pivots from previous candle
    ref_high = float(high.iloc[prev_idx])
    ref_low = float(low.iloc[prev_idx])
    ref_close = float(close.iloc[prev_idx])
    classic_pivots = calculate_classic_pivots(ref_high, ref_low, ref_close)
    camarilla_pivots = calculate_camarilla_pivots(ref_high, ref_low, ref_close)

    # Volatility
    volatility = calculate_volatility(close, 20)

    # Trend Bias
    trend_bias = determine_trend_bias(
        last_price=last_price,
        sma_20=sma_20,
        sma_50=sma_50,
        sma_200=sma_200,
        rsi_14=rsi_14,
        macd_hist=macd_hist
    )

    return {
        "last_price": round(last_price, 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "open_price": round(open_price, 2),
        "high_price": round(high_price, 2),
        "low_price": round(low_price, 2),
        "prev_close": round(prev_close, 2),
        "volume": round(current_vol, 0),
        "avg_volume_20": round(vol_sma_20, 0),
        "vol_surge_ratio": round(vol_surge_ratio, 2),
        "sma_20": round(sma_20, 2) if sma_20 is not None else None,
        "sma_50": round(sma_50, 2) if sma_50 is not None else None,
        "sma_200": round(sma_200, 2) if sma_200 is not None else None,
        "ema_20": round(ema_20, 2) if ema_20 is not None else None,
        "rsi_14": round(rsi_14, 2),
        "macd": round(macd, 2),
        "macd_signal": round(macd_signal, 2),
        "macd_hist": round(macd_hist, 2),
        "atr_14": round(atr_14, 2) if atr_14 is not None else None,
        "vwap": round(vwap, 2) if vwap is not None else None,
        "support_level": classic_pivots["s1"],
        "resistance_level": classic_pivots["r1"],
        "pivot_levels": {**classic_pivots, **camarilla_pivots},
        "gap_pct": round(gap_pct, 2),
        "volatility": volatility,
        "trend_bias": trend_bias,
    }
