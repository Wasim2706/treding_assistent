import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.market import Stock, MarketDataSnapshot
from app.services.market_data.base import (
    AbstractMarketDataProvider,
    clean_ticker,
    get_indian_market_status,
)
from app.services.market_data.mock import MockMarketDataProvider
from app.services.market_data.yahoo import YahooFinanceProvider
from app.services.market_data.indicators import calculate_all_indicators

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Central orchestration service for Indian stock market data, caching,
    technical indicators computation, and database snapshot synchronization.
    """

    def __init__(
        self, 
        primary_provider: Optional[AbstractMarketDataProvider] = None,
        quote_ttl_sec: int = 60,
        indicator_ttl_sec: int = 300
    ):
        from app.core.config import settings
        if primary_provider is not None:
            self._provider = primary_provider
        elif getattr(settings, "ENVIRONMENT", "") == "testing":
            self._provider = MockMarketDataProvider()
        else:
            self._provider = YahooFinanceProvider()

        self._mock_provider = MockMarketDataProvider()
        self._quote_ttl = timedelta(seconds=quote_ttl_sec)
        self._indicator_ttl = timedelta(seconds=indicator_ttl_sec)

        # In-memory TTL caches: { symbol: (timestamp, data) }
        self._quote_cache: Dict[str, tuple[datetime, Dict[str, Any]]] = {}
        self._indicator_cache: Dict[str, tuple[datetime, Dict[str, Any]]] = {}

    def set_mock_price(self, symbol: str, price: float) -> None:
        """Sets price in mock provider and clears cache (useful for testing)."""
        clean = clean_ticker(symbol)
        self._quote_cache.pop(clean, None)
        if hasattr(self._provider, "set_price"):
            self._provider.set_price(clean, price)
        if hasattr(self._mock_provider, "set_price"):
            self._mock_provider.set_price(clean, price)

    async def get_market_status(self) -> Dict[str, Any]:
        """Returns the current trading session status for NSE/BSE."""
        return get_indian_market_status()

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Retrieves real-time/delayed quote with 60s TTL caching."""
        clean = clean_ticker(symbol)
        now = datetime.now(timezone.utc)

        if clean in self._quote_cache:
            ts, cached = self._quote_cache[clean]
            if now - ts < self._quote_ttl:
                return cached

        try:
            quote = await self._provider.get_latest_price(clean)
        except Exception as e:
            logger.warning(f"[MarketDataService] Provider failed for quote {clean}: {e}. Using mock fallback.")
            quote = await self._mock_provider.get_latest_price(clean)

        self._quote_cache[clean] = (now, quote)
        return quote

    async def get_indicators(self, symbol: str) -> Dict[str, Any]:
        """Retrieves computed technical indicators with 5m TTL caching."""
        clean = clean_ticker(symbol)
        now = datetime.now(timezone.utc)

        if clean in self._indicator_cache:
            ts, cached = self._indicator_cache[clean]
            if now - ts < self._indicator_ttl:
                return cached

        try:
            df = await self._provider.get_historical_ohlcv(clean, period="3mo", interval="1d")
        except Exception as e:
            logger.warning(f"[MarketDataService] History fetch failed for {clean}: {e}. Using mock.")
            df = await self._mock_provider.get_historical_ohlcv(clean, period="3mo", interval="1d")

        indicators = calculate_all_indicators(df)
        indicators["symbol"] = clean
        self._indicator_cache[clean] = (now, indicators)
        return indicators

    async def get_or_create_snapshot(
        self, 
        symbol: str, 
        db: AsyncSession
    ) -> MarketDataSnapshot:
        """
        Computes the latest technical indicators for a symbol and persists
        the record into the market_data table.
        """
        clean = clean_ticker(symbol)
        indicators = await self.get_indicators(clean)

        snapshot = MarketDataSnapshot(
            symbol=clean,
            last_price=indicators.get("last_price", 0.0),
            change_pct=indicators.get("change_pct", 0.0),
            open_price=indicators.get("open_price", 0.0),
            high_price=indicators.get("high_price", 0.0),
            low_price=indicators.get("low_price", 0.0),
            prev_close=indicators.get("prev_close", 0.0),
            volume=indicators.get("volume", 0.0),
            avg_volume_20=indicators.get("avg_volume_20", 0.0),
            sma_20=indicators.get("sma_20"),
            sma_50=indicators.get("sma_50"),
            sma_200=indicators.get("sma_200"),
            ema_20=indicators.get("ema_20"),
            rsi_14=indicators.get("rsi_14"),
            macd=indicators.get("macd"),
            macd_signal=indicators.get("macd_signal"),
            macd_hist=indicators.get("macd_hist"),
            atr_14=indicators.get("atr_14"),
            vwap=indicators.get("vwap"),
            support_level=indicators.get("support_level"),
            resistance_level=indicators.get("resistance_level"),
            gap_pct=indicators.get("gap_pct", 0.0),
            volatility=indicators.get("volatility", 0.0),
        )

        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)
        return snapshot

    async def get_market_overview(self) -> Dict[str, Any]:
        """
        Gathers real-time quotes for primary macro indices & commodities:
        NIFTY 50, BANK NIFTY, Crude Oil, Gold, and USD/INR.
        """
        indices_to_fetch = {
            "nifty50": "^NSEI",
            "bank_nifty": "^NSEBANK",
            "crude_oil": "CL=F",
            "gold": "GC=F",
            "usd_inr": "INR=X"
        }

        tasks = [self._provider.get_index_quote(ticker) for ticker in indices_to_fetch.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        overview: Dict[str, Any] = {
            "session": get_indian_market_status(),
            "benchmarks": {}
        }

        for (name, ticker), res in zip(indices_to_fetch.items(), results):
            if isinstance(res, Exception):
                logger.warning(f"Index fetch failed for {ticker}: {res}")
                overview["benchmarks"][name] = await self._mock_provider.get_index_quote(ticker)
            else:
                overview["benchmarks"][name] = res

        return overview

    async def get_global_market_cues(self) -> Dict[str, Any]:
        """
        Gathers comprehensive overnight global cues:
        US markets, European indices, Asian cues, Commodities, Yields, and Currencies.
        Calculates aggregate overnight directional bias for the Indian pre-open session.
        """
        cues_map = {
            # US Indices
            "dow_jones": "^DJI",
            "sp500": "^GSPC",
            "nasdaq": "NQ=F",
            # European Indices
            "ftse100": "^FTSE",
            "dax": "^GDAXI",
            # Asian & Offshore Cues
            "gift_nifty": "GIFTI.NS",
            "nikkei225": "^N225",
            "hang_seng": "^HSI",
            # Commodities
            "crude_wti": "CL=F",
            "crude_brent": "BZ=F",
            "gold": "GC=F",
            # Macro / FX
            "us_10y_yield": "^TNX",
            "usd_inr": "INR=X",
        }

        tasks = [self._provider.get_index_quote(ticker) for ticker in cues_map.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        instruments: Dict[str, Dict[str, Any]] = {}
        for (name, ticker), res in zip(cues_map.items(), results):
            if isinstance(res, Exception):
                quote = await self._mock_provider.get_index_quote(ticker)
            else:
                quote = res
            if isinstance(quote, dict) and "timestamp" in quote and isinstance(quote["timestamp"], datetime):
                quote = {**quote, "timestamp": quote["timestamp"].isoformat()}
            instruments[name] = quote

        # Calculate US aggregate momentum
        us_changes = [
            instruments.get(k, {}).get("change_pct", 0.0)
            for k in ["dow_jones", "sp500", "nasdaq"]
        ]
        avg_us = sum(us_changes) / len(us_changes) if us_changes else 0.0

        # GIFT Nifty cue
        gift_change = instruments.get("gift_nifty", {}).get("change_pct", 0.0)

        # Crude oil cue (Crude rise is bearish for India, crude fall is bullish)
        crude_change = instruments.get("crude_wti", {}).get("change_pct", 0.0)

        # Directional sentiment determination
        score = 0
        if avg_us > 0.3:
            score += 1
        elif avg_us < -0.3:
            score -= 1

        if gift_change > 0.2:
            score += 1
        elif gift_change < -0.2:
            score -= 1

        # Crude oil inverse relationship for Indian economy
        if crude_change > 2.0:
            score -= 1
        elif crude_change < -2.0:
            score += 1

        if score >= 1:
            sentiment = "BULLISH"
        elif score <= -1:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"

        narrative_parts = []
        if avg_us > 0.2:
            narrative_parts.append(f"Wall Street closed positive (Avg {avg_us:+.2f}%)")
        elif avg_us < -0.2:
            narrative_parts.append(f"Wall Street closed weaker (Avg {avg_us:+.2f}%)")
        else:
            narrative_parts.append(f"US indices showed a flat-to-mixed closing ({avg_us:+.2f}%)")

        if gift_change > 0.15:
            narrative_parts.append(f"GIFT Nifty indicates a positive gap opening ({gift_change:+.2f}%)")
        elif gift_change < -0.15:
            narrative_parts.append(f"GIFT Nifty points toward a cautious/negative opening ({gift_change:+.2f}%)")
        else:
            narrative_parts.append("GIFT Nifty signals a flat open")

        if abs(crude_change) >= 1.5:
            direction_str = "spiked" if crude_change > 0 else "cooled down"
            narrative_parts.append(f"Crude oil {direction_str} by {crude_change:+.2f}%")

        summary_narrative = ". ".join(narrative_parts) + "."

        return {
            "sentiment": sentiment,
            "avg_us_change_pct": round(avg_us, 2),
            "gift_nifty_change_pct": round(gift_change, 2),
            "crude_change_pct": round(crude_change, 2),
            "instruments": instruments,
            "summary_narrative": summary_narrative,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def refresh_all_snapshots(self, db: AsyncSession, limit: int = 30) -> int:
        """
        Refreshes technical snapshots for tracked stocks in the database.
        """
        query = select(Stock).where(Stock.is_active == True).limit(limit)
        res = await db.execute(query)
        stocks = res.scalars().all()

        count = 0
        for stock in stocks:
            try:
                await self.get_or_create_snapshot(stock.symbol, db)
                count += 1
            except Exception as e:
                logger.error(f"Failed to refresh snapshot for {stock.symbol}: {e}")

        return count


# Global singleton instance
market_data_service = MarketDataService()
