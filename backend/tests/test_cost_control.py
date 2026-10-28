import pytest
from datetime import datetime, timezone
from app.services.news.models import RawNewsArticle
from app.services.ai.cost_control import filter_high_value_articles, is_ai_budget_available


def test_filter_high_value_articles():
    high_impact_article = RawNewsArticle(
        article_id="art_high",
        title="RBI MPC hikes repo rate by 25 bps to rein in inflationary pressure",
        description="RBI monetary action.",
        url="https://moneycontrol.com/rbi-hike",
        normalized_url="https://moneycontrol.com/rbi-hike",
        source="Moneycontrol Markets",
        published_at=datetime.now(timezone.utc),
        source_reliability_score=90,
        preliminary_impact_score=85,
        categories=["RBI", "Interest rates"],
        fingerprint="fp_rbi"
    )

    ticker_article = RawNewsArticle(
        article_id="art_ticker",
        title="Reliance Industries commissions new solar giga-factory in Jamnagar",
        description="Reliance clean energy expansion.",
        url="https://economictimes.com/ril-solar",
        normalized_url="https://economictimes.com/ril-solar",
        source="Economic Times Markets",
        published_at=datetime.now(timezone.utc),
        source_reliability_score=88,
        preliminary_impact_score=65,
        tickers=["RELIANCE"],
        categories=["Energy"],
        fingerprint="fp_ril"
    )

    low_impact_filler = RawNewsArticle(
        article_id="art_low",
        title="Local trade body organizes annual retail business networking seminar in Pune",
        description="General networking conference.",
        url="https://someblog.com/seminar",
        normalized_url="https://someblog.com/seminar",
        source="Local Blog",
        published_at=datetime.now(timezone.utc),
        source_reliability_score=60,
        preliminary_impact_score=35,
        categories=["Other"],
        fingerprint="fp_low"
    )

    articles = [high_impact_article, ticker_article, low_impact_filler]
    high_value, standard_value = filter_high_value_articles(articles, max_count=5)

    # RBI and Reliance articles must be prioritized for AI analysis
    assert high_impact_article in high_value
    assert ticker_article in high_value

    # Low impact blog filler must be diverted to standard rule-based processing
    assert low_impact_filler in standard_value
    assert len(high_value) == 2


def test_filter_high_value_articles_capping():
    # Verify strict cycle cap enforcement (Section 20)
    batch = []
    for i in range(15):
        art = RawNewsArticle(
            article_id=f"art_{i}",
            title=f"Quarterly earnings announcement {i} with strong growth",
            url=f"https://example.com/{i}",
            normalized_url=f"https://example.com/{i}",
            source="Reuters",
            published_at=datetime.now(timezone.utc),
            source_reliability_score=90,
            preliminary_impact_score=75,
            categories=["Earnings"],
            fingerprint=f"fp_{i}"
        )
        batch.append(art)

    high_val, std_val = filter_high_value_articles(batch, max_count=10)
    # Must be capped exactly at 10
    assert len(high_val) == 10
    # Remaining 5 pushed to standard processing
    assert len(std_val) == 5


@pytest.mark.asyncio
async def test_is_ai_budget_available(db_session):
    available = await is_ai_budget_available()
    assert isinstance(available, bool)
    assert available is True  # In fresh test DB, spend is 0, so budget is available
