import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import logger
from app.core.database import AsyncSessionLocal
from app.models.news import NewsArticle, NewsAnalysis, NewsEntity
from app.models.report import Alert
from app.models.system import SystemLog
from app.services.news.models import RawNewsArticle
from app.services.news.registry import news_registry
from app.services.news.deduplication import DeduplicationPipeline
from app.services.news.classification import (
    classify_news_categories,
    extract_affected_tickers,
    estimate_sentiment_and_impact
)


class NewsIntelligenceEngine:
    """
    Executes the 5-Minute News Intelligence Pipeline:
    FETCH -> NORMALIZE -> DEDUPLICATE -> CLASSIFY -> ENTITY EXTRACTION -> MARKET IMPACT -> STORE -> ALERT IF IMPORTANT
    """

    def __init__(self, session_factory=None):
        self.session_factory = session_factory or AsyncSessionLocal
        self.deduplicator = DeduplicationPipeline()

    async def _load_existing_fingerprints(self, session: AsyncSession) -> None:
        """Loads recent article fingerprints and URLs to prevent re-processing across worker restarts."""
        res = await session.execute(
            select(NewsArticle.normalized_url, NewsArticle.article_fingerprint, NewsArticle.title)
            .order_by(NewsArticle.published_at.desc())
            .limit(500)
        )
        rows = res.all()
        urls = {r[0] for r in rows if r[0]}
        fps = {r[1] for r in rows if r[1]}
        titles = [r[2] for r in rows if r[2]]
        self.deduplicator.load_existing_state(urls, fps, titles)

    async def run_cycle(self, session_factory=None) -> Dict[str, Any]:
        """Runs a complete 5-minute news collection, processing, and storage cycle."""
        start_time = time.time()
        logger.info("Executing 5-minute news engine cycle...")

        fetched_count = 0
        filtered_count = 0
        stored_count = 0
        alerts_count = 0
        errors_count = 0

        factory = session_factory or self.session_factory
        async with factory() as session:
            try:
                # 1. Warm deduplicator with historical DB state
                await self._load_existing_fingerprints(session)

                # 2. FETCH: Multi-provider concurrent aggregation
                raw_articles: List[RawNewsArticle] = await news_registry.fetch_aggregated_news(limit_per_provider=25)
                fetched_count = len(raw_articles)
                logger.info(f"Fetched {fetched_count} raw articles across all providers.")

                # 3. NORMALIZE & DEDUPLICATE
                unique_articles: List[RawNewsArticle] = []
                for article in raw_articles:
                    if self.deduplicator.is_duplicate(article):
                        filtered_count += 1
                        continue
                    self.deduplicator.register(article)
                    unique_articles.append(article)

                logger.info(f"Deduplication completed: {len(unique_articles)} novel articles retained, {filtered_count} duplicates rejected.")

                # 4. CLASSIFY & SCORE & STORE
                for article in unique_articles:
                    # Classify categories
                    categories = classify_news_categories(article.title, article.description or "")
                    article.categories = categories

                    # Extract affected Indian stocks
                    tickers = extract_affected_tickers(article.title, article.description or "")
                    article.tickers = tickers

                    # Estimate preliminary sentiment and impact
                    sentiment, impact = estimate_sentiment_and_impact(
                        article.title,
                        article.description or "",
                        categories=categories,
                        reliability_score=article.source_reliability_score
                    )
                    article.sentiment = sentiment
                    article.preliminary_impact_score = impact

                    # Primary event type
                    primary_event = categories[0] if categories else "General"

                    # Check if high impact alert should be triggered
                    should_alert = (
                        impact >= settings.ALERT_IMPACT_THRESHOLD
                        and article.source_reliability_score >= 75
                        and (len(tickers) > 0 or "RBI" in categories or "Crude oil" in categories or "War/conflict" in categories)
                    )

                    # Persist NewsArticle
                    db_article = NewsArticle(
                        article_fingerprint=article.fingerprint,
                        title=article.title,
                        description=article.description,
                        content=article.content,
                        url=article.url,
                        normalized_url=article.normalized_url,
                        source=article.source,
                        author=article.author,
                        published_at=article.published_at,
                        language=article.language,
                        country=article.country,
                        source_reliability_score=article.source_reliability_score,
                        is_processed=True,
                        is_alert_sent=should_alert
                    )
                    session.add(db_article)
                    await session.flush()

                    # Persist NewsAnalysis
                    affected_indices = ["NIFTY 50"] if any(c in categories for c in ["RBI", "Interest rates", "Crude oil", "GDP"]) else []
                    if "Banking" in categories or "RBI" in categories:
                        affected_indices.append("BANK NIFTY")

                    analysis = NewsAnalysis(
                        article_id=db_article.id,
                        summary=article.description or article.title,
                        event_type=primary_event,
                        sentiment=sentiment,
                        impact_score=impact,
                        confidence=article.source_reliability_score,
                        time_horizon="INTRADAY" if impact >= 75 else "SHORT_TERM",
                        affected_sectors=article.sectors,
                        affected_stocks=tickers,
                        affected_indices=affected_indices,
                        reasoning=f"Categorized under {primary_event} with {sentiment} market bias. Mentioned tickers: {', '.join(tickers) if tickers else 'Broad Market'}.",
                        confirmed_facts=[article.title],
                        market_interpretation=f"Potential {sentiment.lower()} reaction across relevant Indian equities.",
                        risk_factors=["Broader index volatility", "Market gap-open risk"]
                    )
                    session.add(analysis)

                    # Persist NewsEntities
                    for ticker in tickers:
                        ent = NewsEntity(
                            article_id=db_article.id,
                            entity_name=ticker,
                            entity_type="STOCK",
                            relevance_score=85
                        )
                        session.add(ent)

                    for cat in categories:
                        ent = NewsEntity(
                            article_id=db_article.id,
                            entity_name=cat,
                            entity_type="THEME",
                            relevance_score=75
                        )
                        session.add(ent)

                    # Trigger alert if threshold met
                    if should_alert:
                        alerts_count += 1
                        alert_msg = f"[{sentiment}] {article.title} (Impact: {impact}/100)"
                        alert_record = Alert(
                            title=f"Breaking Market Intelligence: {primary_event}",
                            message=alert_msg,
                            alert_type="HIGH_IMPACT_NEWS",
                            impact_score=impact,
                            channel="WEB_DASHBOARD",
                            is_sent=True,
                            metadata_json={
                                "article_id": db_article.id,
                                "source": article.source,
                                "tickers": tickers,
                                "url": article.url
                            }
                        )
                        session.add(alert_record)

                    stored_count += 1

                await session.commit()

            except Exception as exc:
                errors_count += 1
                await session.rollback()
                logger.error(f"Error in news intelligence engine cycle: {str(exc)}", exc_info=True)

            # Record system log entry
            duration_ms = round((time.time() - start_time) * 1000, 2)
            log_entry = SystemLog(
                job_name="5min_news_engine_cycle",
                duration_ms=duration_ms,
                articles_fetched=fetched_count,
                articles_filtered=filtered_count,
                articles_analyzed=stored_count,
                signals_generated=0,
                errors_count=errors_count,
                details={
                    "stored_count": stored_count,
                    "alerts_generated": alerts_count,
                    "pipeline_status": "success" if errors_count == 0 else "error"
                }
            )
            session.add(log_entry)
            await session.commit()

        logger.info(
            f"News engine cycle complete: {stored_count} stored, {filtered_count} duplicates filtered, "
            f"{alerts_count} alerts raised in {duration_ms}ms (Errors: {errors_count})."
        )

        return {
            "status": "success" if errors_count == 0 else "error",
            "duration_ms": duration_ms,
            "articles_fetched": fetched_count,
            "duplicates_filtered": filtered_count,
            "articles_stored": stored_count,
            "alerts_generated": alerts_count,
            "errors": errors_count
        }


# Singleton engine
news_engine = NewsIntelligenceEngine()
