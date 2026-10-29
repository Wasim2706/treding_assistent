import time
from typing import Dict, List
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import logger


class InMemoryRateLimiter:
    """
    Sliding window in-memory rate limiter per client IP.
    Separates general read limits and intensive mutation limits.
    """

    def __init__(self):
        # Maps client_ip -> list of epoch timestamps
        self._requests: Dict[str, List[float]] = {}
        self._last_cleanup: float = time.time()

    def _cleanup_old_entries(self, current_time: float):
        """Evicts expired timestamps and empty IP keys to prevent memory growth."""
        if current_time - self._last_cleanup < 60.0:
            return

        window_start = current_time - 60.0
        keys_to_delete = []

        for ip, timestamps in self._requests.items():
            valid_ts = [t for t in timestamps if t > window_start]
            if valid_ts:
                self._requests[ip] = valid_ts
            else:
                keys_to_delete.append(ip)

        for ip in keys_to_delete:
            self._requests.pop(ip, None)

        self._last_cleanup = current_time

    def check_rate_limit(self, client_ip: str, limit: int, current_time: float) -> tuple[bool, int, int]:
        """
        Returns (is_allowed, remaining_requests, retry_after_seconds).
        """
        self._cleanup_old_entries(current_time)

        window_start = current_time - 60.0
        history = self._requests.get(client_ip, [])
        # Keep only timestamps in the current 60s sliding window
        recent = [t for t in history if t > window_start]

        if len(recent) >= limit:
            oldest = recent[0]
            retry_after = max(1, int(60.0 - (current_time - oldest)))
            self._requests[client_ip] = recent
            return False, 0, retry_after

        recent.append(current_time)
        self._requests[client_ip] = recent
        remaining = max(0, limit - len(recent))
        return True, remaining, 0

    def reset(self):
        """Clears all tracking data (useful for test resets)."""
        self._requests.clear()


limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware enforcing sliding-window rate limits per client IP.
    """

    EXEMPT_PATHS = {
        "/health",
        "/ready",
        "/metrics",
        "/disclaimer",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico"
    }

    async def dispatch(self, request: Request, call_next):
        # 1. Skip if rate limiting is disabled or during automated testing
        if not settings.RATE_LIMIT_ENABLED or settings.ENVIRONMENT == "testing":
            return await call_next(request)

        # 2. Skip exempt monitoring / documentation paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # 3. Determine client IP (considering reverse proxy X-Forwarded-For)
        client_ip = "127.0.0.1"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        elif request.client and request.client.host:
            client_ip = request.client.host

        # 4. Determine rate limit for the operation type
        is_mutation = request.method in {"POST", "PUT", "DELETE", "PATCH"}
        limit = (
            settings.RATE_LIMIT_MUTATION_PER_MINUTE
            if is_mutation
            else settings.RATE_LIMIT_PER_MINUTE
        )

        now = time.time()
        allowed, remaining, retry_after = limiter.check_rate_limit(
            client_ip=f"{client_ip}:{'mutation' if is_mutation else 'read'}",
            limit=limit,
            current_time=now
        )

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {request.method} {request.url.path} "
                f"(Limit: {limit} req/min). Retry-After: {retry_after}s"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + retry_after)),
                },
                content={
                    "success": False,
                    "message": "Rate limit exceeded. Too many requests.",
                    "detail": f"Client exceeded rate limit of {limit} requests per minute for this endpoint type.",
                    "retry_after_seconds": retry_after,
                    "disclaimer": settings.REGULATORY_DISCLAIMER
                }
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
