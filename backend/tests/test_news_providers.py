import pytest
from app.services.news.mock_provider import MockNewsProvider
from app.services.news.rss_provider import RSSNewsProvider
from app.services.news.registry import NewsProviderRegistry


@pytest.mark.asyncio
async def test_mock_news_provider():
    provider = MockNewsProvider()
    assert provider.is_configured is True
    assert provider.name == "Mock Indian Financial Feed"

    articles = await provider.fetch_latest_news(limit=5)
    assert len(articles) > 0
    assert articles[0].country == "IN"
    assert articles[0].fingerprint != ""
    assert articles[0].source_reliability_score >= 85

    # Filter by symbol
    tcs_news = await provider.fetch_news_by_symbol("TCS")
    assert any("TCS" in a.tickers for a in tcs_news)


@pytest.mark.asyncio
async def test_rss_news_provider_interface():
    provider = RSSNewsProvider()
    assert provider.is_configured is True
    assert len(provider.feeds) >= 5

    # Test article normalization logic
    sample_entry = {
        "title": "Nifty 50 approaches new milestone above 25,200",
        "description": "<p>Indian markets extended gains on Wednesday.</p>",
        "url": "https://www.moneycontrol.com/news/markets/sample-1.html?utm_source=rss",
        "source": "Moneycontrol Markets",
        "published": "Wed, 28 Oct 2026 09:30:00 +0530",
    }
    normalized = provider.normalize_article(sample_entry)
    assert normalized is not None
    assert normalized.title == "Nifty 50 approaches new milestone above 25,200"
    assert "utm_source" not in normalized.normalized_url
    assert "<p>" not in (normalized.description or "")


@pytest.mark.asyncio
async def test_news_provider_registry():
    registry = NewsProviderRegistry()
    assert len(registry.providers) >= 2

    # Query active providers
    configured = registry.get_configured_providers()
    assert len(configured) >= 1

    # Aggregated fetch
    news = await registry.fetch_aggregated_news(limit_per_provider=5)
    assert len(news) > 0
    assert all(a.fingerprint != "" for a in news)
