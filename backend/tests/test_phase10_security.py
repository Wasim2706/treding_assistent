import pytest
import time
from httpx import AsyncClient, ASGITransport
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import (
    validate_safety_text,
    sanitize_safety_text,
    contains_forbidden_phrase,
    verify_api_key,
    is_auth_required,
    FORBIDDEN_SAFETY_PHRASES
)
from app.core.rate_limit import InMemoryRateLimiter, RateLimitMiddleware
from app.services.ai.cost_control import get_today_ai_spend_usd, is_ai_budget_available
from app.models.system import ApiUsage
from app.main import app


# ------------------------------------------------------------------------------
# 1. Trading Safety & Anti-Guarantee Rules
# ------------------------------------------------------------------------------

def test_forbidden_phrases_detection():
    """Validates that all forbidden guarantee phrases are detected accurately."""
    for phrase in FORBIDDEN_SAFETY_PHRASES:
        text = f"This setup offers a {phrase} for intraday traders."
        assert contains_forbidden_phrase(text) is not None
        with pytest.raises(ValueError, match="Trading safety violation"):
            validate_safety_text(text)


def test_sanitize_safety_text():
    """Ensures safety sanitizer replaces prohibited phrases with compliant disclaimer."""
    unsafe = "This system generates guaranteed profit and 100% accurate signals."
    safe = sanitize_safety_text(unsafe)
    assert "guaranteed profit" not in safe.lower()
    assert "100% accurate" not in safe.lower()
    assert "[NON-GUARANTEED PROBABILISTIC ESTIMATE]" in safe


def test_compliant_text_passes_safety():
    """Compliant probabilistic trading texts pass validation without errors."""
    compliant = "RELIANCE setup indicates a favorable 1:2 risk-to-reward ratio based on breakout above 50 SMA."
    assert validate_safety_text(compliant) == compliant


# ------------------------------------------------------------------------------
# 2. Authentication & API Key Verification
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auth_not_required_in_dev_without_key(monkeypatch):
    """In development without ADMIN_API_KEY, authentication is optional."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "REQUIRE_AUTH_FOR_MUTATIONS", False)
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "")
    assert is_auth_required() is False


@pytest.mark.asyncio
async def test_auth_required_in_production(monkeypatch):
    """In production, authentication is strictly required."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert is_auth_required() is True


@pytest.mark.asyncio
async def test_verify_api_key_valid_header(monkeypatch):
    """Providing the correct ADMIN_API_KEY succeeds."""
    monkeypatch.setattr(settings, "REQUIRE_AUTH_FOR_MUTATIONS", True)
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "test-secret-key-999")

    class MockRequest:
        method = "POST"
        url = type("Url", (), {"path": "/api/v1/news/refresh"})()

    result = await verify_api_key(
        request=MockRequest(),
        api_key_header="test-secret-key-999",
        bearer_creds=None
    )
    assert result is True


@pytest.mark.asyncio
async def test_verify_api_key_valid_bearer(monkeypatch):
    """Providing the correct Bearer token succeeds."""
    from fastapi.security import HTTPAuthorizationCredentials

    monkeypatch.setattr(settings, "REQUIRE_AUTH_FOR_MUTATIONS", True)
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "bearer-token-secret-123")

    class MockRequest:
        method = "POST"
        url = type("Url", (), {"path": "/api/v1/news/refresh"})()

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bearer-token-secret-123")
    result = await verify_api_key(
        request=MockRequest(),
        api_key_header=None,
        bearer_creds=creds
    )
    assert result is True


@pytest.mark.asyncio
async def test_verify_api_key_invalid_raises_401(monkeypatch):
    """Invalid API key raises HTTP 401 Unauthorized."""
    monkeypatch.setattr(settings, "REQUIRE_AUTH_FOR_MUTATIONS", True)
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "test-secret-key-999")

    class MockRequest:
        method = "POST"
        url = type("Url", (), {"path": "/api/v1/news/refresh"})()

    with pytest.raises(HTTPException) as exc:
        await verify_api_key(
            request=MockRequest(),
            api_key_header="wrong-key",
            bearer_creds=None
        )
    assert exc.value.status_code == 401


# ------------------------------------------------------------------------------
# 3. Rate Limiter Unit Tests
# ------------------------------------------------------------------------------

def test_rate_limiter_sliding_window():
    """Tests the in-memory sliding window rate limiter."""
    limiter = InMemoryRateLimiter()
    now = time.time()

    # Allow up to 3 requests
    allowed, rem, _ = limiter.check_rate_limit("1.2.3.4", limit=3, current_time=now)
    assert allowed is True
    assert rem == 2

    allowed, rem, _ = limiter.check_rate_limit("1.2.3.4", limit=3, current_time=now + 1)
    assert allowed is True
    assert rem == 1

    allowed, rem, _ = limiter.check_rate_limit("1.2.3.4", limit=3, current_time=now + 2)
    assert allowed is True
    assert rem == 0

    # 4th request should be blocked
    allowed, rem, retry_after = limiter.check_rate_limit("1.2.3.4", limit=3, current_time=now + 3)
    assert allowed is False
    assert rem == 0
    assert retry_after > 0

    # After 61 seconds, window slides and requests are permitted again
    allowed, rem, _ = limiter.check_rate_limit("1.2.3.4", limit=3, current_time=now + 62)
    assert allowed is True


# ------------------------------------------------------------------------------
# 4. AI Cost Control & Daily Budget Cap
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ai_cost_control_budget(db_session, monkeypatch):
    """Tests daily budget check against ApiUsage records."""
    monkeypatch.setattr(settings, "DAILY_AI_BUDGET_USD", 5.0)

    # Current spend should be within budget
    available = await is_ai_budget_available()
    assert available is True

    # Insert a record exceeding the daily budget
    expensive_call = ApiUsage(
        provider="OPENAI",
        operation="chat_completions_gpt-4o-mini",
        units_consumed=50000000,
        estimated_cost_usd=6.50
    )
    db_session.add(expensive_call)
    await db_session.commit()

    # When budget exceeded, is_ai_budget_available returns False
    spend = await get_today_ai_spend_usd()
    assert spend >= 6.50

    available_after = await is_ai_budget_available()
    assert available_after is False


# ------------------------------------------------------------------------------
# 5. Protected Endpoints HTTP Integration Tests
# ------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_protected_endpoint_rejects_without_auth(monkeypatch):
    """Protected mutation endpoint returns 401 when REQUIRE_AUTH_FOR_MUTATIONS is enabled."""
    monkeypatch.setattr(settings, "REQUIRE_AUTH_FOR_MUTATIONS", True)
    monkeypatch.setattr(settings, "ADMIN_API_KEY", "super-admin-key-777")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Calling without header should return 401
        res = await client.post("/api/v1/news/refresh")
        assert res.status_code == 401

        # Calling with invalid header returns 401
        res = await client.post("/api/v1/news/refresh", headers={"X-API-Key": "wrong"})
        assert res.status_code == 401

        # Calling with valid header succeeds or executes
        # (It will proceed past auth, returning 200 or successful APIResponse)
        res = await client.post("/api/v1/news/refresh", headers={"X-API-Key": "super-admin-key-777"})
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_security_status_endpoint():
    """GET /api/v1/settings/security returns comprehensive security posture."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/settings/security")
        assert res.status_code == 200
        data = res.json()["data"]
        assert "auth_required" in data
        assert "rate_limit_enabled" in data
        assert "daily_ai_budget_usd" in data
        assert "ai_spend_today_usd" in data
        assert "trading_mode" in data
        assert data["trading_mode"] == "PAPER_TRADING_ONLY"


@pytest.mark.asyncio
async def test_security_headers_present():
    """Verifies that security and anti-guarantee headers are set on all responses."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert res.headers.get("X-Frame-Options") == "DENY"
        assert res.headers.get("X-Trading-Mode") == "PAPER_TRADING_ONLY"
        assert res.headers.get("X-Trading-Safety") == "ENFORCED_NON_GUARANTEED"
