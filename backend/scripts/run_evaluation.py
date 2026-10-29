"""
Standalone CLI entrypoint for Post-Market Prediction Evaluation cycle.
Intended for Render Cron Job execution at 16:00 IST (10:30 UTC) Mon-Fri.
"""
import asyncio
import os
import sys

# Ensure backend root is on sys.path
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.core.database import init_db
from app.workers.tasks import run_prediction_evaluation_cycle
from app.core.logging import logger


async def main():
    logger.info("Triggering standalone Post-Market Prediction Evaluation...")
    # Ensure database tables exist
    await init_db()
    result = await run_prediction_evaluation_cycle()
    logger.info(
        f"Prediction Evaluation finished: {result.get('evaluated_count', 0)} evaluated, "
        f"{result.get('correct_count', 0)} correct ({result.get('accuracy_pct', 0)}%)."
    )


if __name__ == "__main__":
    asyncio.run(main())
