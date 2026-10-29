"""
Standalone CLI entrypoint for Daily Indian Pre-Market Report generation.
Intended for Render Cron Job execution at 08:30 IST (03:00 UTC) Mon-Fri.
"""
import asyncio
import os
import sys

# Ensure backend root is on sys.path
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.core.database import init_db
from app.workers.tasks import run_pre_market_report_generation
from app.core.logging import logger


async def main():
    logger.info("Triggering standalone Indian Pre-Market Report generation...")
    # Ensure database tables exist
    await init_db()
    result = await run_pre_market_report_generation()
    logger.info(
        f"Pre-Market Report execution finished: Report #{result.get('report_id')}, "
        f"status={result.get('status', 'complete')}"
    )


if __name__ == "__main__":
    asyncio.run(main())
