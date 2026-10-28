from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from app.services.market_data.base import (
    AbstractMarketDataProvider,
    clean_ticker,
    normalize_ticker,
    get_indian_market_status,
)

BASE_PRICES: Dict[str, float] = {
    # NIFTY 50 Core
    "RELIANCE": 2950.0,
    "TCS": 3950.0,
    "HDFCBANK": 1680.0,
    "INFY": 1840.0,
    "ICICIBANK": 1245.0,
    "SBIN": 820.0,
    "BHARTIARTL": 1650.0,
    "TATAMOTORS": 980.0,
    "ITC": 490.0,
    "LT": 3650.0,
    "MARUTI": 12200.0,
    "SUNPHARMA": 1720.0,
    "TITAN": 3450.0,
    "KOTAKBANK": 1780.0,
    "HINDUNILVR": 2750.0,
    "BAJFINANCE": 7150.0,
    "ASIANPAINT": 2920.0,
    "AXISBANK": 1190.0,
    "NTPC": 410.0,
    "ONGC": 315.0,
    "POWERGRID": 330.0,
    "TATASTEEL": 155.0,
    "JSWSTEEL": 960.0,
    "COALINDIA": 505.0,
    "ADANIENT": 3050.0,
    "ADANIPORTS": 1410.0,
    # Defense & PSU
    "HAL": 4650.0,
    "BEL": 295.0,
    "BHEL": 275.0,
    # Benchmarks & Indices
    "^NSEI": 24850.0,
    "^NSEBANK": 52400.0,
    "CL=F": 78.40,
    "GC=F": 2680.0,
    "INR=X": 84.10,
}


class MockMarketDataProvider(AbstractMarketDataProvider):
    """
    Deterministic & realistic market data provider for Indian equities & indices.
    Used for local testing, offline simulation, and safety fallback.
    """

    def __init__(self, seed: Optional[int] = 42):
        self._seed = seed
        self._base_prices = BASE_PRICES.copy()
        self._overrides: Dict[str, float] = {}

    @property
    def name(self) -> str:
        return "mock_market_data"

    def set_price(self, symbol: str, price: float) -> None:
        """Helper to override price for controlled test scenarios."""
        clean = clean_ticker(symbol)
        self._overrides[clean] = price
        self._base_prices[clean] = price

    async def get_latest_price(self, symbol: str) -> Dict[str, Any]:
        clean = clean_ticker(symbol)
        if clean in self._overrides:
            exact_price = self._overrides[clean]
            prev_close = self._base_prices.get(clean, exact_price)
            change = round(exact_price - prev_close, 2)
            change_pct = round((change / prev_close) * 100.0, 2) if prev_close > 0 else 0.0
            return {
                "symbol": clean,
                "ticker": normalize_ticker(symbol),
                "last_price": exact_price,
                "change": change,
                "change_pct": change_pct,
                "open_price": exact_price,
                "high_price": exact_price,
                "low_price": exact_price,
                "prev_close": prev_close,
                "volume": 1000000,
                "timestamp": datetime.now(timezone.utc),
            }

        base = self._base_prices.get(clean, 1000.0)

        # Minor variance for realistic simulation (+- 0.8%)
        rng = np.random.RandomState(hash(clean) % 2**32)
        drift = rng.uniform(-0.008, 0.012)
        last_price = round(base * (1.0 + drift), 2)
        prev_close = base
        change = round(last_price - prev_close, 2)
        change_pct = round((change / prev_close) * 100.0, 2)

        open_price = round(prev_close * (1.0 + rng.uniform(-0.004, 0.004)), 2)
        high_price = max(open_price, last_price, round(open_price * 1.008, 2))
        low_price = min(open_price, last_price, round(open_price * 0.992, 2))
        volume = int(rng.uniform(500000, 3500000))

        return {
            "symbol": clean,
            "ticker": normalize_ticker(symbol),
            "last_price": last_price,
            "change": change,
            "change_pct": change_pct,
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "prev_close": prev_close,
            "volume": volume,
            "timestamp": datetime.now(timezone.utc),
        }

    async def get_historical_ohlcv(
        self, 
        symbol: str, 
        period: str = "3mo", 
        interval: str = "1d"
    ) -> pd.DataFrame:
        clean = clean_ticker(symbol)
        base_price = self._base_prices.get(clean, 1000.0)

        # Number of daily candles based on period
        num_candles = 90
        if "1mo" in period:
            num_candles = 30
        elif "6mo" in period:
            num_candles = 130
        elif "1y" in period:
            num_candles = 250

        # Deterministic generation using symbol hash
        rng = np.random.RandomState(abs(hash(clean)) % (2**31))

        # Generate daily dates (excluding weekends)
        end_date = datetime.now(timezone.utc)
        dates = []
        current = end_date
        while len(dates) < num_candles:
            if current.weekday() < 5:  # Weekday
                dates.append(current)
            current -= timedelta(days=1)
        dates.reverse()

        # Generate geometric Brownian motion for price path
        daily_volatility = 0.014  # ~22% annualized vol
        daily_drift = 0.0004       # slight upward drift
        shocks = rng.normal(daily_drift, daily_volatility, num_candles)
        price_path = base_price * np.exp(np.cumsum(shocks))

        # Normalize so the last price lands near base_price
        correction_factor = base_price / price_path[-1]
        price_path = price_path * correction_factor

        data = []
        for i, dt in enumerate(dates):
            close_p = price_path[i]
            prev_p = price_path[i - 1] if i > 0 else close_p
            candle_vol = rng.uniform(0.004, 0.015)
            open_p = prev_p * (1.0 + rng.uniform(-0.003, 0.003))
            high_p = max(open_p, close_p) * (1.0 + candle_vol)
            low_p = min(open_p, close_p) * (1.0 - candle_vol)
            vol = rng.uniform(400000, 4500000)

            data.append({
                "Date": dt,
                "Open": round(float(open_p), 2),
                "High": round(float(high_p), 2),
                "Low": round(float(low_p), 2),
                "Close": round(float(close_p), 2),
                "Volume": round(float(vol), 0),
            })

        df = pd.DataFrame(data)
        df = df.set_index("Date")
        return df

    async def get_index_quote(self, index_symbol: str) -> Dict[str, Any]:
        symbol = index_symbol.strip()
        base = self._base_prices.get(symbol, 24000.0)

        rng = np.random.RandomState(abs(hash(symbol)) % (2**31))
        drift = rng.uniform(-0.006, 0.008)
        last_price = round(base * (1.0 + drift), 2)
        change = round(last_price - base, 2)
        change_pct = round((change / base) * 100.0, 2)

        return {
            "symbol": symbol,
            "last_price": last_price,
            "change": change,
            "change_pct": change_pct,
            "timestamp": datetime.now(timezone.utc),
        }
