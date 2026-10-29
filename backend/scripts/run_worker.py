"""
Persistent Background Worker Service entrypoint.
Manages the 5-minute news cycle, deterministic signal generation, and market schedules.
"""
import asyncio
import os
import sys

# Ensure backend root is on sys.path
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.core.database import init_db
from app.workers.scheduler import start_scheduler, stop_scheduler
from app.workers.tasks import run_news_intelligence_cycle
from app.core.logging import logger


async def main():
    logger.info("Initializing persistent background worker service...")
    await init_db()
    await start_scheduler()

    # Trigger an immediate news intelligence run on startup
    try:
        logger.info("Executing startup news intelligence cycle...")
        await run_news_intelligence_cycle()
    except Exception as exc:
        logger.warning(f"Initial news cycle warning (non-fatal): {exc}")

    logger.info("Background worker service running. Listening for scheduled triggers...")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Gracefully stopping background worker scheduler...")
        await stop_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
