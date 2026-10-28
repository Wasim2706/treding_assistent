import pytest
from sqlalchemy import select
from app.services.news.engine import NewsIntelligenceEngine
from app.models.news import NewsArticle, NewsAnalysis
from app.core.database import AsyncSessionLocal


@pytest.mark.asyncio
async def test_ai_news_engine_fact_vs_speculation_persistence(db_session):
    engine = NewsIntelligenceEngine(session_factory=AsyncSessionLocal)

    result = await engine.run_cycle(session_factory=AsyncSessionLocal)
    assert result["status"] == "success"

    # Query saved news analysis records
    res = await db_session.execute(select(NewsAnalysis))
    analyses = res.scalars().all()
    assert len(analyses) > 0

    # Verify every analysis has strict confirmed_facts and market_interpretation populated
    for a in analyses:
        assert a.confirmed_facts is not None
        assert isinstance(a.confirmed_facts, list)
        assert len(a.confirmed_facts) > 0
        assert a.market_interpretation is not None
        assert len(a.market_interpretation) > 10
        assert a.sentiment in ["BULLISH", "BEARISH", "NEUTRAL"]
        assert 0 <= a.impact_score <= 100
        assert 0 <= a.confidence <= 100
        assert a.time_horizon in ["INTRADAY", "SHORT_TERM", "MEDIUM_TERM"]
