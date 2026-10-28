import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from app.core.config import settings
from app.core.logging import logger
from app.workers.tasks import (
    run_news_intelligence_cycle,
    run_signal_generation_cycle,
    run_pre_market_report_generation,
    run_prediction_evaluation_cycle
)

scheduler = AsyncIOScheduler()


def setup_scheduler() -> AsyncIOScheduler:
    """Configures scheduled recurring jobs."""
    # 1. 5-minute news collection and intelligence cycle
    scheduler.add_job(
        run_news_intelligence_cycle,
        trigger=IntervalTrigger(seconds=settings.NEWS_CYCLE_INTERVAL_SECONDS),
        id="news_cycle_5m",
        name="5-Minute News Intelligence Cycle",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )

    # 2. Daily Pre-market Indian stock market report at 08:30 IST (03:00 UTC) Mon-Fri
    scheduler.add_job(
        run_pre_market_report_generation,
        trigger=CronTrigger(day_of_week="mon-fri", hour=3, minute=0, timezone="UTC"),
        id="pre_market_report_daily",
        name="Daily Pre-Market Indian Report (08:30 IST)",
        replace_existing=True,
        max_instances=1
    )

    # 3. Post-market prediction evaluation cycle at 16:00 IST (10:30 UTC) Mon-Fri
    scheduler.add_job(
        run_prediction_evaluation_cycle,
        trigger=CronTrigger(day_of_week="mon-fri", hour=10, minute=30, timezone="UTC"),
        id="prediction_eval_daily",
        name="Daily Prediction Evaluation (16:00 IST)",
        replace_existing=True,
        max_instances=1
    )

    logger.info("Configured scheduled jobs: 5-minute news cycle, 08:30 IST pre-market report, 16:00 IST evaluation.")
    return scheduler


async def start_scheduler() -> None:
    """Starts the background scheduler."""
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()
        logger.info("Background AsyncIOScheduler started successfully.")


async def stop_scheduler() -> None:
    """Stops the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background AsyncIOScheduler stopped.")


if __name__ == "__main__":
    # Standalone worker runner for Render Worker Service
    async def run_standalone_worker():
        logger.info("Starting standalone persistent background worker...")
        await start_scheduler()
        # Trigger initial run
        await run_news_intelligence_cycle()
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, SystemExit):
            await stop_scheduler()

    asyncio.run(run_standalone_worker())
