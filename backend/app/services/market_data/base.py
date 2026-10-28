from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
import pandas as pd

# IST Timezone: UTC + 5:30
IST_OFFSET = timezone(timedelta(hours=5, minutes=30))


def get_current_ist_time() -> datetime:
    """Returns the current datetime in Indian Standard Time (IST)."""
    return datetime.now(timezone.utc).astimezone(IST_OFFSET)


def get_indian_market_status(current_dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Calculates Indian stock market (NSE/BSE) trading session status.
    Market Hours (IST):
    - Mon-Fri 09:00 - 09:15: PRE_OPEN
    - Mon-Fri 09:15 - 15:30: REGULAR (Trading Open)
    - Mon-Fri 15:30 - 16:00: POST_CLOSE
    - Mon-Fri 16:00 - 09:00: CLOSED (After Hours)
    - Saturday / Sunday: CLOSED (Weekend)
    """
    now = current_dt or get_current_ist_time()
    weekday = now.weekday()  # Monday = 0, Sunday = 6
    hour = now.hour
    minute = now.minute
    total_minutes = hour * 60 + minute

    pre_open_start = 9 * 60         # 09:00
    regular_start = 9 * 60 + 15     # 09:15
    regular_end = 15 * 60 + 30      # 15:30
    post_close_end = 16 * 60        # 16:00

    ist_str = now.strftime("%Y-%m-%d %H:%M:%S IST")

    if weekday in (5, 6):
        return {
            "is_open": False,
            "session": "CLOSED",
            "session_description": "Market Closed (Weekend)",
            "current_ist": ist_str,
            "trading_day": False,
            "next_session": "Monday 09:00 IST (Pre-Open)"
        }

    if total_minutes < pre_open_start:
        return {
            "is_open": False,
            "session": "CLOSED",
            "session_description": "Pre-Market / Overnight",
            "current_ist": ist_str,
            "trading_day": True,
            "next_session": f"Today 09:00 IST (Pre-Open in {pre_open_start - total_minutes}m)"
        }
    elif pre_open_start <= total_minutes < regular_start:
        return {
            "is_open": False,
            "session": "PRE_OPEN",
            "session_description": "NSE Pre-Open Order Discovery",
            "current_ist": ist_str,
            "trading_day": True,
            "next_session": f"Regular Trading Opens at 09:15 IST (in {regular_start - total_minutes}m)"
        }
    elif regular_start <= total_minutes < regular_end:
        # Determine intraday sub-phase
        sub_phase = "Normal Session"
        if total_minutes < regular_start + 15:
            sub_phase = "Opening Volatility (09:15-09:30)"
        elif total_minutes >= regular_end - 15:
            sub_phase = "Closing Roll-over (15:15-15:30)"

        return {
            "is_open": True,
            "session": "REGULAR",
            "session_description": f"Trading Open ({sub_phase})",
            "current_ist": ist_str,
            "trading_day": True,
            "next_session": f"Market Closes at 15:30 IST (in {regular_end - total_minutes}m)"
        }
    elif regular_end <= total_minutes < post_close_end:
        return {
            "is_open": False,
            "session": "POST_CLOSE",
            "session_description": "Post-Market Order Matching / Reporting",
            "current_ist": ist_str,
            "trading_day": True,
            "next_session": "Session ending at 16:00 IST"
        }
    else:
        return {
            "is_open": False,
            "session": "CLOSED",
            "session_description": "Market Closed (After Hours)",
            "current_ist": ist_str,
            "trading_day": True,
            "next_session": "Next Trading Day 09:00 IST"
        }


def normalize_ticker(symbol: str) -> str:
    """
    Appends .NS to Indian stock symbols for Yahoo Finance compatibility
    while preserving indices and commodity futures symbols.
    """
    symbol = symbol.strip().upper()
    if (
        symbol.startswith("^") or 
        symbol.endswith(".NS") or 
        symbol.endswith(".BO") or 
        "=F" in symbol or 
        "=X" in symbol
    ):
        return symbol
    return f"{symbol}.NS"


def clean_ticker(symbol: str) -> str:
    """Removes exchange suffix (.NS or .BO) to return pure equity ticker."""
    s = symbol.strip().upper()
    if s.endswith(".NS"):
        return s[:-3]
    if s.endswith(".BO"):
        return s[:-3]
    return s


class AbstractMarketDataProvider(ABC):
    """Abstract interface for market data ingestion."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def get_latest_price(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieves real-time/delayed quote for a ticker.
        Returns dict:
        {
            "symbol": str,
            "last_price": float,
            "change": float,
            "change_pct": float,
            "open_price": float,
            "high_price": float,
            "low_price": float,
            "prev_close": float,
            "volume": float,
            "timestamp": datetime
        }
        """
        pass

    @abstractmethod
    async def get_historical_ohlcv(
        self, 
        symbol: str, 
        period: str = "3mo", 
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Retrieves historical OHLCV candles as a pandas DataFrame.
        Columns required: ['Open', 'High', 'Low', 'Close', 'Volume']
        Index: DatetimeIndex
        """
        pass

    @abstractmethod
    async def get_index_quote(self, index_symbol: str) -> Dict[str, Any]:
        """
        Retrieves market index or macro benchmark quote
        (e.g., ^NSEI, ^NSEBANK, CL=F, GC=F, INR=X).
        """
        pass

    async def get_market_status(self) -> Dict[str, Any]:
        """Returns standard Indian market session status."""
        return get_indian_market_status()
