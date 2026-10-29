import pytest
from sqlalchemy import select
from app.services.news.engine import NewsIntelligenceEngine
from app.models.news import NewsArticle, NewsAnalysis, NewsEntity
from app.models.report import Alert
from app.core.database import AsyncSessionLocal


@pytest.mark.asyncio
async def test_news_engine_cycle_and_persistence(db_session):
    engine = NewsIntelligenceEngine(session_factory=AsyncSessionLocal)

    # 1. Run collection cycle
    result = await engine.run_cycle(session_factory=AsyncSessionLocal)
    assert result["status"] == "success"
    assert result["errors"] == 0

    # Verify articles exist in database (either from this cycle or prior API refresh test)
    res = await db_session.execute(select(NewsArticle))
    articles = res.scalars().all()
    assert len(articles) > 0

    # Verify news analysis and sentiment persistence
    res_analysis = await db_session.execute(select(NewsAnalysis))
    analyses = res_analysis.scalars().all()
    assert len(analyses) > 0
    assert any(a.sentiment in ["BULLISH", "BEARISH", "NEUTRAL"] for a in analyses)

    # Verify news entities extraction persistence
    res_entities = await db_session.execute(select(NewsEntity))
    entities = res_entities.scalars().all()
    assert len(entities) > 0
    stock_entities = [e.entity_name for e in entities if e.entity_type == "STOCK"]
    assert len(stock_entities) > 0

    # Verify alerts table received high impact alerts
    res_alerts = await db_session.execute(
        select(Alert).where(Alert.alert_type == "HIGH_IMPACT_NEWS")
    )
    alerts = res_alerts.scalars().all()
    assert len(alerts) > 0
    assert all(a.impact_score >= 70 for a in alerts)


@pytest.mark.asyncio
async def test_news_engine_deduplication_on_subsequent_cycle(db_session):
    engine = NewsIntelligenceEngine(session_factory=AsyncSessionLocal)

    # First cycle
    res1 = await engine.run_cycle(session_factory=AsyncSessionLocal)
    stored_first = res1["articles_stored"]

    # Second immediate cycle should filter out duplicate stories
    res2 = await engine.run_cycle(session_factory=AsyncSessionLocal)
    assert res2["duplicates_filtered"] >= stored_first
    assert res2["articles_stored"] == 0
