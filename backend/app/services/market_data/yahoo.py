import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pandas as pd

from app.services.market_data.base import (
    AbstractMarketDataProvider,
    normalize_ticker,
    clean_ticker,
)
from app.services.market_data.mock import MockMarketDataProvider

logger = logging.getLogger(__name__)


class YahooFinanceProvider(AbstractMarketDataProvider):
    """
    Market data provider using yfinance with asynchronous thread execution,
    strict timeouts, column normalization, and automatic Mock fallback.
    """

    def __init__(self, timeout_sec: float = 8.0):
        self._timeout_sec = timeout_sec
        self._fallback = MockMarketDataProvider()

    @property
    def name(self) -> str:
        return "yahoo_finance"

    def _sync_fetch_ticker_quote(self, yf_symbol: str) -> Dict[str, Any]:
        """Synchronous fetch executed in worker thread."""
        import yfinance as yf
        ticker = yf.Ticker(yf_symbol)
        fast_info = getattr(ticker, "fast_info", None)

        if fast_info is not None:
            last_price = float(getattr(fast_info, "last_price", 0.0) or 0.0)
            prev_close = float(getattr(fast_info, "previous_close", 0.0) or 0.0)
            open_price = float(getattr(fast_info, "open", 0.0) or last_price)
            high_price = float(getattr(fast_info, "day_high", 0.0) or last_price)
            low_price = float(getattr(fast_info, "day_low", 0.0) or last_price)
            volume = float(getattr(fast_info, "last_volume", 0.0) or 0.0)

            if last_price > 0:
                change = last_price - prev_close if prev_close > 0 else 0.0
                change_pct = (change / prev_close * 100.0) if prev_close > 0 else 0.0
                return {
                    "symbol": clean_ticker(yf_symbol),
                    "ticker": yf_symbol,
                    "last_price": round(last_price, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "open_price": round(open_price, 2),
                    "high_price": round(high_price, 2),
                    "low_price": round(low_price, 2),
                    "prev_close": round(prev_close, 2),
                    "volume": round(volume, 0),
                    "timestamp": datetime.now(timezone.utc),
                }

        # Fallback to 1-day history if fast_info missing
        hist = ticker.history(period="2d", interval="1d")
        if not hist.empty:
            last_candle = hist.iloc[-1]
            prev_candle = hist.iloc[-2] if len(hist) > 1 else last_candle
            last_price = float(last_candle["Close"])
            prev_close = float(prev_candle["Close"])
            change = last_price - prev_close
            change_pct = (change / prev_close * 100.0) if prev_close > 0 else 0.0

            return {
                "symbol": clean_ticker(yf_symbol),
                "ticker": yf_symbol,
                "last_price": round(last_price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "open_price": round(float(last_candle["Open"]), 2),
                "high_price": round(float(last_candle["High"]), 2),
                "low_price": round(float(last_candle["Low"]), 2),
                "prev_close": round(prev_close, 2),
                "volume": round(float(last_candle["Volume"]), 0),
                "timestamp": datetime.now(timezone.utc),
            }

        raise ValueError(f"No price data available from Yahoo Finance for {yf_symbol}")

    def _sync_fetch_history(self, yf_symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Synchronous history fetch executed in worker thread."""
        import yfinance as yf
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            raise ValueError(f"Empty historical dataframe returned for {yf_symbol}")

        # Flatten multi-level columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        # Ensure required columns
        req = ["Open", "High", "Low", "Close", "Volume"]
        for col in req:
            if col not in df.columns:
                raise ValueError(f"Missing column {col} in Yahoo Finance history for {yf_symbol}")

        return df[req].copy()

    async def get_latest_price(self, symbol: str) -> Dict[str, Any]:
        yf_symbol = normalize_ticker(symbol)
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._sync_fetch_ticker_quote, yf_symbol),
                timeout=self._timeout_sec
            )
        except Exception as e:
            logger.warning(
                f"[YahooFinanceProvider] Failed to fetch quote for {yf_symbol} ({str(e)}), falling back to mock provider"
            )
            return await self._fallback.get_latest_price(symbol)

    async def get_historical_ohlcv(
        self, 
        symbol: str, 
        period: str = "3mo", 
        interval: str = "1d"
    ) -> pd.DataFrame:
        yf_symbol = normalize_ticker(symbol)
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._sync_fetch_history, yf_symbol, period, interval),
                timeout=self._timeout_sec
            )
        except Exception as e:
            logger.warning(
                f"[YahooFinanceProvider] Failed to fetch history for {yf_symbol} ({str(e)}), falling back to mock provider"
            )
            return await self._fallback.get_historical_ohlcv(symbol, period=period, interval=interval)

    async def get_index_quote(self, index_symbol: str) -> Dict[str, Any]:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._sync_fetch_ticker_quote, index_symbol),
                timeout=self._timeout_sec
            )
        except Exception as e:
            logger.warning(
                f"[YahooFinanceProvider] Failed to fetch index {index_symbol} ({str(e)}), falling back to mock provider"
            )
            return await self._fallback.get_index_quote(index_symbol)
