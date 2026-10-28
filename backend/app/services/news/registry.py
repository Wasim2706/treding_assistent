import asyncio
from typing import List, Dict, Type, Optional
from app.services.news.base_provider import AbstractNewsProvider
from app.services.news.models import RawNewsArticle
from app.services.news.rss_provider import RSSNewsProvider
from app.services.news.newsapi_provider import NewsAPIProvider
from app.services.news.mock_provider import MockNewsProvider
from app.core.config import settings
from app.core.logging import logger


class NewsProviderRegistry:
    """
    Modular manager and orchestrator for news providers.
    Supports concurrent multi-provider aggregation, failover, and dynamic registration.
    """

    def __init__(self):
        self.providers: Dict[str, AbstractNewsProvider] = {}
        self._initialize_default_providers()

    def register(self, provider: AbstractNewsProvider) -> None:
        """Registers a news provider."""
        self.providers[provider.name] = provider
        logger.info(f"Registered news provider: {provider.name} (Configured: {provider.is_configured})")

    def _initialize_default_providers(self) -> None:
        """Initializes standard suite of news providers."""
        # 1. Public Indian Financial RSS Provider (Always active)
        self.register(RSSNewsProvider())

        # 2. NewsAPI.org Provider (Active when API key provided)
        if settings.NEWS_API_KEY:
            self.register(NewsAPIProvider())

        # 3. High-fidelity Mock Provider (Used as reliable fallback or in test mode)
        self.register(MockNewsProvider())

    def get_configured_providers(self) -> List[AbstractNewsProvider]:
        """Returns list of active, configured news providers."""
        return [p for p in self.providers.values() if p.is_configured]

    async def fetch_aggregated_news(self, limit_per_provider: int = 25) -> List[RawNewsArticle]:
        """
        Queries all configured news providers concurrently.
        Safely isolates failures so a failing provider does not crash the pipeline.
        """
        active_providers = self.get_configured_providers()
        if not active_providers:
            logger.warning("No news providers configured! Using MockNewsProvider fallback.")
            active_providers = [MockNewsProvider()]

        tasks = [p.fetch_latest_news(limit=limit_per_provider) for p in active_providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        aggregated: List[RawNewsArticle] = []
        for provider, res in zip(active_providers, results):
            if isinstance(res, Exception):
                logger.error(f"Provider '{provider.name}' failed with error: {str(res)}")
            elif isinstance(res, list):
                logger.info(f"Provider '{provider.name}' returned {len(res)} articles.")
                aggregated.extend(res)

        return aggregated


# Singleton registry instance
news_registry = NewsProviderRegistry()
