from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.report import DailyReport, Alert
from app.schemas.report import DailyReportRead, AlertRead
from app.schemas.common import APIResponse, PaginatedResponse

router = APIRouter(prefix="/reports", tags=["Pre-Market & Daily Reports"])


@router.get("/pre-market/latest", response_model=APIResponse[Optional[DailyReportRead]])
async def get_latest_pre_market_report(db: AsyncSession = Depends(get_db)):
    """Retrieves the latest Indian stock market pre-open report."""
    res = await db.execute(
        select(DailyReport)
        .where(DailyReport.report_type == "PRE_MARKET")
        .order_by(desc(DailyReport.created_at))
        .limit(1)
    )
    report = res.scalars().first()
    return APIResponse(data=report, message="Latest pre-market intelligence report")


@router.get("", response_model=PaginatedResponse[DailyReportRead])
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Lists historical reports."""
    offset = (page - 1) * page_size
    res = await db.execute(
        select(DailyReport).order_by(desc(DailyReport.created_at)).offset(offset).limit(page_size)
    )
    reports = res.scalars().all()

    total_res = await db.execute(select(DailyReport.id))
    total = len(total_res.scalars().all())

    return PaginatedResponse(
        success=True,
        total=total,
        page=page,
        page_size=page_size,
        items=reports,
        disclaimer="Pre-market reports are algorithmic overviews and do not constitute investment advice."
    )


@router.get("/alerts", response_model=APIResponse[List[AlertRead]])
async def list_recent_alerts(limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """Lists recent high-impact news and signal alerts."""
    res = await db.execute(select(Alert).order_by(desc(Alert.created_at)).limit(limit))
    alerts = res.scalars().all()
    return APIResponse(data=alerts, message=f"Retrieved {len(alerts)} alerts")


@router.post("/pre-market/generate", response_model=APIResponse[dict], dependencies=[Depends(verify_api_key)])
async def trigger_pre_market_report():
    """Triggers generation of the Indian market pre-open report."""
    from app.workers.tasks import run_pre_market_report_generation
    result = await run_pre_market_report_generation()
    return APIResponse(data=result, message="Pre-market report generated successfully.")
