from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.services.news.models import RawNewsArticle


class AbstractNewsProvider(ABC):
    """
    Modular abstraction for news providers (NewsAPI, Finnhub, GNews, Alpha Vantage, RSS, etc.).
    Prevents vendor lock-in and allows seamless failover.
    """

    def __init__(self, name: str, reliability_score: int = 70):
        self.name = name
        self.reliability_score = reliability_score

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if provider credentials or sources are available."""
        pass

    @abstractmethod
    async def fetch_latest_news(self, limit: int = 25) -> List[RawNewsArticle]:
        """Fetch general financial and market news."""
        pass

    @abstractmethod
    async def fetch_news_by_symbol(self, symbol: str, limit: int = 10) -> List[RawNewsArticle]:
        """Fetch news specifically mentioning an equity symbol/company."""
        pass

    @abstractmethod
    async def fetch_news_by_sector(self, sector: str, limit: int = 10) -> List[RawNewsArticle]:
        """Fetch news related to an industrial sector."""
        pass

    @abstractmethod
    async def fetch_news_by_country(self, country: str = "IN", limit: int = 25) -> List[RawNewsArticle]:
        """Fetch market news specific to a country/exchange."""
        pass

    @abstractmethod
    def normalize_article(self, raw_item: Dict[str, Any]) -> Optional[RawNewsArticle]:
        """Converts vendor-specific raw article payload into canonical RawNewsArticle."""
        pass
