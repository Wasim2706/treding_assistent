import pytest
from datetime import datetime, timezone
from app.services.ai.client import OpenAIAnalyzer
from app.services.news.models import RawNewsArticle


@pytest.mark.asyncio
async def test_openai_analyzer_deterministic_fallback():
    # Force unconfigured analyzer to test resilient fallback
    analyzer = OpenAIAnalyzer(api_key="")
    assert analyzer.is_configured is False

    article = RawNewsArticle(
        article_id="test1",
        title="Brent crude surges 4.2% on escalating Red Sea shipping disruptions",
        description="Crude prices jumped as tankers were rerouted, driving up shipping and insurance premiums.",
        url="https://economictimes.com/crude-jump",
        normalized_url="https://economictimes.com/crude-jump",
        source="Economic Times Markets",
        published_at=datetime.now(timezone.utc),
        source_reliability_score=90,
        fingerprint="fp1234567890abcdef"
    )

    analysis = await analyzer.analyze_article(article)
    assert analysis is not None
    assert analysis.event_type in ["Crude oil", "Geopolitical"]
    assert analysis.sentiment in ["BULLISH", "BEARISH", "NEUTRAL"]
    assert analysis.impact_score >= 70
    assert "Oil, Gas & Energy" in analysis.affected_sectors
    assert len(analysis.confirmed_facts) > 0
    assert analysis.market_interpretation != ""


@pytest.mark.asyncio
async def test_openai_analyzer_caching():
    analyzer = OpenAIAnalyzer(api_key="")

    article = RawNewsArticle(
        article_id="test2",
        title="TCS announces large enterprise cloud deal with European retailer",
        description="Deal size estimated at $750 million over 5 years.",
        url="https://livemint.com/tcs-deal",
        normalized_url="https://livemint.com/tcs-deal",
        source="Livemint Companies",
        published_at=datetime.now(timezone.utc),
        source_reliability_score=88,
        fingerprint="fp_tcs_unique_123"
    )

    # First run fills cache
    analysis1 = await analyzer.analyze_article(article)
    assert article.fingerprint in analyzer._cache

    # Second run retrieves from cache
    analysis2 = await analyzer.analyze_article(article)
    assert analysis1 == analysis2


@pytest.mark.asyncio
async def test_api_cost_calculation():
    analyzer = OpenAIAnalyzer(api_key="")
    # For 1,000 prompt tokens ($0.15/1M) + 500 completion tokens ($0.60/1M)
    # 1000 * 0.00000015 = 0.00015
    # 500 * 0.00000060 = 0.00030
    # Total = 0.00045 USD
    cost = await analyzer._record_api_usage(1000, 500)
    assert round(cost, 6) == 0.00045
