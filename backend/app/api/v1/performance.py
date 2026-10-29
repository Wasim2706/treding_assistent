from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.prediction import PredictionResult
from app.schemas.system import PredictionEvaluationRead
from app.schemas.common import APIResponse, PaginatedResponse

router = APIRouter(prefix="/performance", tags=["Prediction Evaluation & Accuracy"])


@router.get("/predictions", response_model=PaginatedResponse[PredictionEvaluationRead])
async def list_prediction_evaluations(
    symbol: Optional[str] = Query(None),
    evaluated_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists prediction records and compares predicted direction vs actual subsequent price movement.
    Provides verifiable algorithmic calibration.
    """
    query = select(PredictionResult).order_by(desc(PredictionResult.created_at))

    if symbol:
        query = query.where(PredictionResult.symbol == symbol.upper())
    if evaluated_only:
        query = query.where(PredictionResult.is_evaluated == True)

    offset = (page - 1) * page_size
    res = await db.execute(query.offset(offset).limit(page_size))
    predictions = res.scalars().all()

    total_res = await db.execute(select(PredictionResult.id))
    total = len(total_res.scalars().all())

    return PaginatedResponse(
        success=True,
        total=total,
        page=page,
        page_size=page_size,
        items=predictions,
        disclaimer="Prediction evaluation is conducted to measure model calibration. No guarantee of future performance."
    )


@router.get("/summary", response_model=APIResponse[dict])
async def get_prediction_summary(db: AsyncSession = Depends(get_db)):
    """Summary metrics: Directional accuracy, precision, Brier calibration score, and sector breakdown."""
    from app.services.evaluation.service import evaluation_service
    summary = await evaluation_service.get_performance_summary(db)
    return APIResponse(
        data=summary,
        message="Prediction evaluation and calibration metrics computed successfully."
    )


@router.post("/evaluate", response_model=APIResponse[dict], dependencies=[Depends(verify_api_key)])
async def trigger_prediction_evaluation(
    force_all: bool = Query(False, description="Evaluate all pending predictions regardless of due timestamp"),
    db: AsyncSession = Depends(get_db)
):
    """Triggers verification of pending predictions against actual market quotes."""
    from app.services.evaluation.service import evaluation_service
    result = await evaluation_service.evaluate_pending_predictions(db, force_all=force_all)
    return APIResponse(data=result, message="Prediction evaluation cycle executed successfully.")


@router.post("/backtest", response_model=APIResponse[dict], dependencies=[Depends(verify_api_key)])
async def trigger_historical_backtest(
    symbols: Optional[str] = Query(None, description="Comma-separated stock symbols to backtest"),
    period_days: int = Query(60, ge=10, le=365, description="Lookback window in days"),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes a strategy backtest across historical candles with rolling indicator windows
    and zero look-ahead bias.
    """
    from app.services.evaluation.service import evaluation_service
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else None
    result = await evaluation_service.run_historical_backtest(db, symbols=symbol_list, period_days=period_days)
    return APIResponse(data=result, message="Historical backtesting simulation completed successfully.")
