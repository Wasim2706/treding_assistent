import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser

from app.core.config import settings
from app.services.news.base_provider import AbstractNewsProvider
from app.services.news.models import RawNewsArticle
from app.services.news.deduplication import (
    normalize_url,
    compute_article_fingerprint,
    get_source_reliability,
    validate_publication_timestamp
)
from app.core.logging import logger


class NewsAPIProvider(AbstractNewsProvider):
    """NewsAPI.org provider for Indian business headlines and global financial events."""

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="NewsAPI", reliability_score=80)
        self.api_key = api_key or settings.NEWS_API_KEY

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    async def fetch_latest_news(self, limit: int = 25) -> List[RawNewsArticle]:
        if not self.is_configured:
            return []

        articles: List[RawNewsArticle] = []
        url = f"{self.BASE_URL}/top-headlines"
        params = {
            "country": "in",
            "category": "business",
            "pageSize": min(limit, 50),
            "apiKey": self.api_key
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("articles", []):
                        norm = self.normalize_article(item)
                        if norm:
                            articles.append(norm)
                else:
                    logger.warning(f"NewsAPI error status: {resp.status_code}")
        except Exception as exc:
            logger.error(f"NewsAPI fetch exception: {str(exc)}")

        return articles

    async def fetch_news_by_symbol(self, symbol: str, limit: int = 10) -> List[RawNewsArticle]:
        if not self.is_configured:
            return []
        sym_clean = symbol.upper().replace(".NS", "")
        url = f"{self.BASE_URL}/everything"
        params = {
            "q": f'"{sym_clean}" AND (NSE OR BSE OR stock OR earnings)',
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": limit,
            "apiKey": self.api_key
        }
        articles = []
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    for item in resp.json().get("articles", []):
                        norm = self.normalize_article(item)
                        if norm:
                            articles.append(norm)
        except Exception as e:
            logger.error(f"NewsAPI symbol query error: {str(e)}")
        return articles

    async def fetch_news_by_sector(self, sector: str, limit: int = 10) -> List[RawNewsArticle]:
        if not self.is_configured:
            return []
        url = f"{self.BASE_URL}/everything"
        params = {
            "q": f'"{sector}" AND India AND (market OR stocks)',
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": limit,
            "apiKey": self.api_key
        }
        articles = []
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    for item in resp.json().get("articles", []):
                        norm = self.normalize_article(item)
                        if norm:
                            articles.append(norm)
        except Exception as e:
            logger.error(f"NewsAPI sector query error: {str(e)}")
        return articles

    async def fetch_news_by_country(self, country: str = "IN", limit: int = 25) -> List[RawNewsArticle]:
        return await self.fetch_latest_news(limit=limit)

    def normalize_article(self, raw_item: Dict[str, Any]) -> Optional[RawNewsArticle]:
        title = raw_item.get("title", "").strip()
        url = raw_item.get("url", "").strip()
        if not title or not url or title == "[Removed]":
            return None

        desc = raw_item.get("description", "")
        pub_raw = raw_item.get("publishedAt")
        pub_time = datetime.now(timezone.utc)
        if pub_raw:
            try:
                parsed_dt = date_parser.parse(pub_raw)
                if parsed_dt.tzinfo is None:
                    parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                pub_time = parsed_dt
            except Exception:
                pass

        if not validate_publication_timestamp(pub_time):
            return None

        source_info = raw_item.get("source", {})
        source_name = source_info.get("name", "NewsAPI") if isinstance(source_info, dict) else "NewsAPI"
        reliability = get_source_reliability(source_name)
        norm_url = normalize_url(url)
        fingerprint = compute_article_fingerprint(title, desc)

        return RawNewsArticle(
            article_id=fingerprint[:16],
            title=title,
            description=desc,
            content=raw_item.get("content"),
            url=url,
            normalized_url=norm_url,
            source=source_name,
            author=raw_item.get("author"),
            published_at=pub_time,
            language="en",
            country="IN",
            source_reliability_score=reliability,
            fingerprint=fingerprint
        )
