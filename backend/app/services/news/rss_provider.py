import asyncio
import feedparser
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser

from app.services.news.base_provider import AbstractNewsProvider
from app.services.news.models import RawNewsArticle
from app.services.news.deduplication import (
    normalize_url,
    compute_article_fingerprint,
    get_source_reliability,
    validate_publication_timestamp
)
from app.core.logging import logger

# Active Indian Financial RSS Feeds
INDIAN_RSS_FEEDS = [
    {"source": "Moneycontrol Markets", "url": "https://www.moneycontrol.com/rss/marketreports.xml"},
    {"source": "Moneycontrol Top News", "url": "https://www.moneycontrol.com/rss/MCtopnews.xml"},
    {"source": "Economic Times Markets", "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"},
    {"source": "Economic Times Economy", "url": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms"},
    {"source": "Livemint Markets", "url": "https://www.livemint.com/rss/markets"},
    {"source": "Livemint Companies", "url": "https://www.livemint.com/rss/companies"},
    {"source": "Business Standard", "url": "https://www.business-standard.com/rss/markets-106.rss"},
]

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
}


class RSSNewsProvider(AbstractNewsProvider):
    """
    Scrapes and normalizes high-reliability RSS feeds from premier Indian financial media.
    Does not require third-party API keys and operates with zero subscription costs.
    """

    def __init__(self, feeds: Optional[List[Dict[str, str]]] = None):
        super().__init__(name="Indian Financial RSS Feeds", reliability_score=90)
        self.feeds = feeds or INDIAN_RSS_FEEDS

    @property
    def is_configured(self) -> bool:
        return True  # Public feeds are always accessible

    async def _fetch_single_feed(self, client: httpx.AsyncClient, feed_meta: Dict[str, str]) -> List[RawNewsArticle]:
        feed_source = feed_meta["source"]
        feed_url = feed_meta["url"]
        articles = []

        try:
            resp = await client.get(feed_url, headers=DEFAULT_HEADERS, timeout=8.0)
            if resp.status_code != 200:
                logger.warning(f"RSS feed {feed_source} returned status {resp.status_code}")
                return []

            parsed = feedparser.parse(resp.text)
            for entry in parsed.entries[:15]:
                item_dict = {
                    "title": getattr(entry, "title", ""),
                    "description": getattr(entry, "summary", "") or getattr(entry, "description", ""),
                    "url": getattr(entry, "link", ""),
                    "source": feed_source,
                    "author": getattr(entry, "author", None),
                    "published": getattr(entry, "published", None) or getattr(entry, "updated", None),
                }
                normalized = self.normalize_article(item_dict)
                if normalized:
                    articles.append(normalized)
        except Exception as exc:
            logger.debug(f"Failed fetching RSS feed {feed_source}: {str(exc)}")

        return articles

    async def fetch_latest_news(self, limit: int = 50) -> List[RawNewsArticle]:
        """Fetches latest articles across all configured Indian financial RSS feeds concurrently."""
        all_articles: List[RawNewsArticle] = []

        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = [self._fetch_single_feed(client, feed) for feed in self.feeds]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in results:
                if isinstance(res, list):
                    all_articles.extend(res)

        # Sort by published_at descending
        all_articles.sort(key=lambda a: a.published_at, reverse=True)
        return all_articles[:limit]

    async def fetch_news_by_symbol(self, symbol: str, limit: int = 10) -> List[RawNewsArticle]:
        latest = await self.fetch_latest_news(limit=60)
        sym_clean = symbol.upper().replace(".NS", "")
        return [a for a in latest if sym_clean in a.title.upper() or sym_clean in (a.description or "").upper()][:limit]

    async def fetch_news_by_sector(self, sector: str, limit: int = 10) -> List[RawNewsArticle]:
        latest = await self.fetch_latest_news(limit=60)
        sec_clean = sector.lower()
        return [a for a in latest if sec_clean in a.title.lower() or sec_clean in (a.description or "").lower()][:limit]

    async def fetch_news_by_country(self, country: str = "IN", limit: int = 25) -> List[RawNewsArticle]:
        return await self.fetch_latest_news(limit=limit)

    def normalize_article(self, raw_item: Dict[str, Any]) -> Optional[RawNewsArticle]:
        title = raw_item.get("title", "").strip()
        url = raw_item.get("url", "").strip()
        if not title or not url:
            return None

        # Clean description HTML tags
        desc = raw_item.get("description", "")
        if desc:
            import re
            desc = re.sub(r"<[^>]+>", "", desc).strip()

        # Parse publication timestamp
        pub_raw = raw_item.get("published")
        pub_time = datetime.now(timezone.utc)
        if pub_raw:
            try:
                parsed_dt = date_parser.parse(pub_raw)
                if parsed_dt.tzinfo is None:
                    parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                pub_time = parsed_dt
            except Exception:
                pass

        # Validate timestamp
        if not validate_publication_timestamp(pub_time):
            return None

        norm_url = normalize_url(url)
        source = raw_item.get("source", "RSS Feed")
        reliability = get_source_reliability(source)
        fingerprint = compute_article_fingerprint(title, desc)

        return RawNewsArticle(
            article_id=fingerprint[:16],
            title=title,
            description=desc,
            url=url,
            normalized_url=norm_url,
            source=source,
            author=raw_item.get("author"),
            published_at=pub_time,
            language="en",
            country="IN",
            source_reliability_score=reliability,
            fingerprint=fingerprint
        )
