from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from app.services.news.base_provider import AbstractNewsProvider
from app.services.news.models import RawNewsArticle
from app.services.news.deduplication import normalize_url, compute_article_fingerprint

MOCK_INDIAN_MARKET_NEWS = [
    {
        "title": "RBI MPC Meeting: Repo rate held steady at 6.5%, growth projection pegged at 7.2%",
        "description": "The Reserve Bank of India Monetary Policy Committee voted unanimously to maintain the benchmark repo rate at 6.50%, noting inflation moderation while maintaining economic growth focus.",
        "url": "https://www.moneycontrol.com/news/economy/rbi-mpc-decision-repo-rate-held-steady-12345.html",
        "source": "Moneycontrol Markets",
        "author": "Banking Bureau",
        "hours_ago": 1,
        "tickers": ["HDFCBANK", "SBIN", "ICICIBANK"],
        "sectors": ["Banking & Financial Services"],
        "categories": ["RBI", "Interest rates", "Banking"]
    },
    {
        "title": "Brent crude oil jumps 3.8% to $88/bbl on Middle East supply disruption fears",
        "description": "Global crude benchmarks surged as tensions in the Middle East sparked fresh supply disruption concerns. Higher crude is expected to pressure oil marketing companies and paint manufacturers.",
        "url": "https://economictimes.indiatimes.com/markets/commodities/brent-crude-surges-supply-fears/articleshow/98765432.cms",
        "source": "Economic Times Markets",
        "author": "Commodity Desk",
        "hours_ago": 2,
        "tickers": ["ONGC", "BPCL", "ASIANPAINT", "INDIGO"],
        "sectors": ["Oil, Gas & Energy", "Paints & Specialty Chemicals", "Aviation"],
        "categories": ["Crude oil", "Geopolitical", "Energy"]
    },
    {
        "title": "TCS bags $1.2 billion digital transformation deal from European enterprise",
        "description": "Tata Consultancy Services announced a multi-year digital modernization deal with a major European logistics conglomerate, boosting constant currency revenue visibility.",
        "url": "https://www.livemint.com/companies/news/tcs-bags-mega-deal-europe-11698765432.html",
        "source": "Livemint Companies",
        "author": "Tech Correspondent",
        "hours_ago": 3,
        "tickers": ["TCS", "INFY"],
        "sectors": ["Information Technology"],
        "categories": ["Corporate announcement", "IT", "Technology"]
    },
    {
        "title": "Tata Motors registers 12% rise in quarterly domestic vehicle dispatch numbers",
        "description": "Tata Motors reported a solid 12% year-on-year increase in total domestic dispatches driven by festive EV demand and commercial fleet replacement cycles.",
        "url": "https://www.business-standard.com/markets/news/tata-motors-auto-dispatch-q-numbers-123.html",
        "source": "Business Standard",
        "author": "Auto Desk",
        "hours_ago": 4,
        "tickers": ["TATAMOTORS", "MARUTI"],
        "sectors": ["Automobile & Auto Components"],
        "categories": ["Earnings", "Auto"]
    },
    {
        "title": "Titan Company reports 22% surge in festive jewellery sales following duty rationalization",
        "description": "Titan posted robust consumer demand across Tanishq and Mia retail stores, benefiting from reduced gold import duties and strong marriage season footfalls.",
        "url": "https://www.moneycontrol.com/news/business/titan-reports-22-percent-jewellery-growth-1234.html",
        "source": "Moneycontrol Markets",
        "author": "Retail Bureau",
        "hours_ago": 5,
        "tickers": ["TITAN", "MUTHOOTFIN"],
        "sectors": ["Gems, Jewellery & Gold Loans"],
        "categories": ["Earnings", "Gold", "FMCG"]
    },
    {
        "title": "Ministry of Defence clears capital acquisition of advanced fighter aircraft systems for ₹45,000 crore",
        "description": "The Defence Acquisition Council chaired by Raksha Mantri granted Acceptance of Necessity for critical indigenous defence systems to be manufactured by HAL and BEL.",
        "url": "https://economictimes.indiatimes.com/news/defence/dac-clears-major-procurement-hal-bel/articleshow/99887766.cms",
        "source": "Economic Times Economy",
        "author": "Defence Bureau",
        "hours_ago": 6,
        "tickers": ["HAL", "BEL"],
        "sectors": ["Defence & Aerospace"],
        "categories": ["Government policy", "Defence"]
    }
]


class MockNewsProvider(AbstractNewsProvider):
    """
    High-fidelity synthetic news provider for testing, offline verification,
    and fallback operation when public networks or third-party quotas are constrained.
    """

    def __init__(self):
        super().__init__(name="Mock Indian Financial Feed", reliability_score=92)

    @property
    def is_configured(self) -> bool:
        return True

    async def fetch_latest_news(self, limit: int = 10) -> List[RawNewsArticle]:
        articles = []
        for item in MOCK_INDIAN_MARKET_NEWS[:limit]:
            norm = self.normalize_article(item)
            if norm:
                articles.append(norm)
        return articles

    async def fetch_news_by_symbol(self, symbol: str, limit: int = 5) -> List[RawNewsArticle]:
        latest = await self.fetch_latest_news(limit=20)
        clean = symbol.upper().replace(".NS", "")
        return [a for a in latest if clean in a.tickers or clean in a.title][:limit]

    async def fetch_news_by_sector(self, sector: str, limit: int = 5) -> List[RawNewsArticle]:
        latest = await self.fetch_latest_news(limit=20)
        return [a for a in latest if sector in a.sectors][:limit]

    async def fetch_news_by_country(self, country: str = "IN", limit: int = 10) -> List[RawNewsArticle]:
        return await self.fetch_latest_news(limit=limit)

    def normalize_article(self, raw_item: Dict[str, Any]) -> Optional[RawNewsArticle]:
        title = raw_item["title"]
        desc = raw_item["description"]
        url = raw_item["url"]
        norm_url = normalize_url(url)
        hours_ago = raw_item.get("hours_ago", 1)
        pub_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        fingerprint = compute_article_fingerprint(title, desc)

        return RawNewsArticle(
            article_id=fingerprint[:16],
            title=title,
            description=desc,
            url=url,
            normalized_url=norm_url,
            source=raw_item["source"],
            author=raw_item.get("author"),
            published_at=pub_time,
            language="en",
            country="IN",
            tickers=raw_item.get("tickers", []),
            sectors=raw_item.get("sectors", []),
            categories=raw_item.get("categories", []),
            source_reliability_score=self.reliability_score,
            fingerprint=fingerprint
        )
