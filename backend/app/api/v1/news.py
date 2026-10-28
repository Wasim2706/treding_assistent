from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.news import NewsArticle, NewsAnalysis
from app.schemas.news import NewsArticleRead
from app.schemas.common import PaginatedResponse, APIResponse

router = APIRouter(prefix="/news", tags=["News Intelligence"])


@router.get("", response_model=PaginatedResponse[NewsArticleRead])
async def list_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    event_type: Optional[str] = Query(None, description="Filter by event category"),
    min_impact: Optional[int] = Query(None, ge=0, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves paginated news articles enriched with sentiment, category, and Indian market impact.
    """
    query = select(NewsArticle).options(
        selectinload(NewsArticle.analysis),
        selectinload(NewsArticle.entities)
    ).order_by(desc(NewsArticle.published_at))

    if symbol:
        from app.models.news import NewsEntity
        query = query.join(NewsArticle.entities).where(NewsEntity.entity_name == symbol.upper())
    if event_type:
        query = query.join(NewsArticle.analysis).where(NewsAnalysis.event_type == event_type)
    if min_impact:
        query = query.join(NewsArticle.analysis).where(NewsAnalysis.impact_score >= min_impact)

    # Offset pagination
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    articles = result.scalars().all()

    # Total count
    total_result = await db.execute(select(NewsArticle.id))
    total_count = len(total_result.scalars().all())

    return PaginatedResponse(
        success=True,
        total=total_count,
        page=page,
        page_size=page_size,
        items=articles,
        disclaimer="News sentiment and AI impact scores are algorithmic estimates for paper trading only."
    )


@router.get("/{article_id}", response_model=APIResponse[NewsArticleRead])
async def get_article_detail(article_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch single article with detailed AI fact vs speculation analysis."""
    query = select(NewsArticle).options(
        selectinload(NewsArticle.analysis),
        selectinload(NewsArticle.entities)
    ).where(NewsArticle.id == article_id)

    result = await db.execute(query)
    article = result.scalars().first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    return APIResponse(data=article, message="Article retrieved successfully")


@router.post("/refresh", response_model=APIResponse[dict])
async def trigger_news_refresh():
    """
    Manually triggers the 5-minute news collection and intelligence cycle.
    """
    from app.workers.tasks import run_news_intelligence_cycle
    result = await run_news_intelligence_cycle()
    return APIResponse(data=result, message="News collection and AI processing cycle completed.")
