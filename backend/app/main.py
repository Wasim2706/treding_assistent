import os
import sys
import time

# Ensure backend root is on sys.path regardless of execution working directory
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.core.database import init_db
from app.api.router import api_router
from app.workers.scheduler import start_scheduler, stop_scheduler


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Trading-Mode"] = "PAPER_TRADING_ONLY"
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = round((time.time() - start_time) * 1000, 2)
            response.headers["X-Process-Time-Ms"] = str(process_time)
            if request.url.path not in ["/health", "/ready", "/metrics"]:
                logger.info(f"{request.method} {request.url.path} - {response.status_code} ({process_time}ms)")
            return response
        except Exception as exc:
            process_time = round((time.time() - start_time) * 1000, 2)
            logger.error(f"Unhandled error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "message": "An internal server error occurred.",
                    "detail": str(exc) if settings.DEBUG else "Internal processing error",
                    "disclaimer": settings.REGULATORY_DISCLAIMER
                }
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info("Initializing Indian Market AI Intelligence Application...")
    logger.info(f"Operating Mode: PAPER_TRADING_ONLY = {settings.PAPER_TRADING_ONLY}")

    # 1. Initialize DB and Seed Data
    await init_db()

    # 2. Start Background Scheduler (in web worker mode)
    if settings.ENVIRONMENT != "testing":
        await start_scheduler()

    yield

    logger.info("Gracefully shutting down services...")
    await stop_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AI-Powered Indian Stock Market News Intelligence & Deterministic Trading Decision-Support API.\n\n"
            "**IMPORTANT TRADING SAFETY NOTICE**:\n"
            "This application operates strictly in **PAPER TRADING / SIGNAL-ONLY mode**.\n"
            "It does NOT place real market orders. Predictions are probabilistic and carry NO guarantees."
        ),
        lifespan=lifespan
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security & Logging Middlewares
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Mount API Routers
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # Also mount root health checks for Render / Kubernetes
    from app.api.v1.health import router as root_health_router
    app.include_router(root_health_router, prefix="")

    return app


app = create_app()
