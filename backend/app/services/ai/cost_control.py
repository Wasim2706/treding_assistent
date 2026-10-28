from datetime import datetime, timezone, timedelta
from typing import List, Tuple
from sqlalchemy import select, func

from app.core.config import settings
from app.core.logging import logger
from app.core.database import AsyncSessionLocal
from app.models.system import ApiUsage
from app.services.news.models import RawNewsArticle


async def get_today_ai_spend_usd() -> float:
    """Calculates total OpenAI API spending for the current UTC day."""
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(func.sum(ApiUsage.estimated_cost_usd))
                .where(ApiUsage.provider == "OPENAI")
                .where(ApiUsage.created_at >= start_of_day)
            )
            total = res.scalar() or 0.0
            return float(total)
    except Exception as e:
        logger.debug(f"Error querying today's AI spend: {e}")
        return 0.0


async def is_ai_budget_available() -> bool:
    """Checks whether today's spend is below configured daily budget cap."""
    spent = await get_today_ai_spend_usd()
    if spent >= settings.DAILY_AI_BUDGET_USD:
        logger.warning(
            f"Daily AI budget exceeded: ${spent:.3f} >= ${settings.DAILY_AI_BUDGET_USD:.2f}. "
            f"Enforcing deterministic rule-based analysis."
        )
        return False
    return True


def filter_high_value_articles(
    articles: List[RawNewsArticle],
    max_count: int = None
) -> Tuple[List[RawNewsArticle], List[RawNewsArticle]]:
    """
    Cost-control gate (Section 20):
    Separates articles into:
    1. High-value articles deserving OpenAI deep analysis (RBI, Crude, High impact >= 60, or with specific stock tickers)
    2. Lower-priority articles to be processed rule-based without LLM API costs.
    """
    max_count = max_count or settings.MAX_ARTICLES_PER_AI_CYCLE
    high_value = []
    standard_value = []

    # Priority categories that always warrant AI analysis
    priority_categories = {"RBI", "Earnings", "Crude oil", "War/conflict", "Interest rates", "Inflation", "M&A"}

    for article in articles:
        has_priority_category = any(c in priority_categories for c in article.categories)
        has_specific_ticker = len(article.tickers) > 0
        is_high_impact = article.preliminary_impact_score >= 60

        if (has_priority_category or has_specific_ticker or is_high_impact) and article.source_reliability_score >= 70:
            high_value.append(article)
        else:
            standard_value.append(article)

    # Sort high-value articles by preliminary impact descending
    high_value.sort(key=lambda a: a.preliminary_impact_score, reverse=True)

    # If exceeding max cycle cap, move excess to standard_value
    if len(high_value) > max_count:
        excess = high_value[max_count:]
        high_value = high_value[:max_count]
        standard_value.extend(excess)

    logger.info(
        f"Cost control filter: {len(high_value)} articles queued for AI analysis "
        f"(Capped at {max_count}), {len(standard_value)} assigned to rule-based analysis."
    )
    return high_value, standard_value
