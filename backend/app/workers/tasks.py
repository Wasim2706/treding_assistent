import time
from datetime import datetime, timezone
from typing import Dict, Any
from app.core.logging import logger
from app.core.database import AsyncSessionLocal
from app.models.system import SystemLog


async def run_news_intelligence_cycle() -> Dict[str, Any]:
    """
    Executes the 5-minute news collection, deduplication, classification, and alerting pipeline.
    """
    from app.services.news.engine import news_engine
    return await news_engine.run_cycle()


async def run_signal_generation_cycle() -> Dict[str, Any]:
    """
    Deterministic signal engine combining news score, technical indicators, and sector trends.
    Also updates open paper trading positions against live market prices.
    """
    from app.services.signals.generator import signal_generator
    from app.services.paper_trading.engine import paper_trading_engine

    start_time = time.time()
    logger.info("Executing multi-factor signal synthesis and paper position management...")

    async with AsyncSessionLocal() as db:
        signals = await signal_generator.run_cycle(db)
        position_updates = await paper_trading_engine.update_open_positions(db)

    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(
        f"Signal cycle complete: {len(signals)} signals generated, "
        f"{position_updates.get('open_positions_evaluated', 0)} paper positions tracked in {duration_ms}ms"
    )

    return {
        "status": "success",
        "duration_ms": duration_ms,
        "signals_generated": len(signals),
        "paper_positions_evaluated": position_updates.get("open_positions_evaluated", 0),
        "paper_positions_closed": position_updates.get("closed_trades", 0),
    }


async def run_pre_market_report_generation() -> Dict[str, Any]:
    """
    Synthesizes the Indian market pre-open report before 09:15 NSE market open.
    """
    from app.services.reports.pre_market import pre_market_report_generator

    start_time = time.time()
    logger.info("Executing daily Indian market pre-open intelligence report synthesis...")

    result = await pre_market_report_generator.generate_daily_report()

    duration_ms = round((time.time() - start_time) * 1000, 2)
    result["duration_ms"] = duration_ms
    logger.info(f"Pre-market report completed in {duration_ms}ms (Report #{result.get('report_id')})")
    return result


async def run_prediction_evaluation_cycle() -> Dict[str, Any]:
    """
    Compares past predictions against actual price movement to evaluate calibration and accuracy.
    """
    from app.services.evaluation.service import evaluation_service

    start_time = time.time()
    logger.info("Executing post-market prediction outcome evaluation and calibration cycle...")

    async with AsyncSessionLocal() as db:
        result = await evaluation_service.evaluate_pending_predictions(db, force_all=False)

    duration_ms = round((time.time() - start_time) * 1000, 2)
    result["duration_ms"] = duration_ms
    logger.info(
        f"Prediction evaluation complete: {result.get('evaluated_count', 0)} evaluated, "
        f"{result.get('correct_count', 0)} correct ({result.get('accuracy_pct', 0)}%) in {duration_ms}ms"
    )
    return result
