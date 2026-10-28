from app.services.news.models import RawNewsArticle
from app.services.news.base_provider import AbstractNewsProvider
from app.services.news.registry import news_registry, NewsProviderRegistry
from app.services.news.deduplication import (
    normalize_url,
    compute_article_fingerprint,
    calculate_title_similarity,
    get_source_reliability,
    validate_publication_timestamp,
    DeduplicationPipeline
)
from app.services.news.classification import (
    classify_news_categories,
    extract_affected_tickers,
    estimate_sentiment_and_impact
)
from app.services.news.engine import news_engine, NewsIntelligenceEngine

__all__ = [
    "RawNewsArticle",
    "AbstractNewsProvider",
    "news_registry",
    "NewsProviderRegistry",
    "normalize_url",
    "compute_article_fingerprint",
    "calculate_title_similarity",
    "get_source_reliability",
    "validate_publication_timestamp",
    "DeduplicationPipeline",
    "classify_news_categories",
    "extract_affected_tickers",
    "estimate_sentiment_and_impact",
    "news_engine",
    "NewsIntelligenceEngine",
]
