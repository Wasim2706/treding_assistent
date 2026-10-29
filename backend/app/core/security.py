import secrets
from typing import Optional
from fastapi import HTTPException, Security, Request, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.logging import logger

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER_AUTH = HTTPBearer(auto_error=False)

# Strictly forbidden phrases that violate algorithmic trading safety rules
FORBIDDEN_SAFETY_PHRASES = [
    "guaranteed profit",
    "guaranteed prediction",
    "100% accurate",
    "100% win",
    "risk-free trade",
    "sure shot",
    "jackpot call"
]


def contains_forbidden_phrase(text: str) -> Optional[str]:
    """Returns the forbidden phrase if found in the text, else None."""
    if not text:
        return None
    lower = text.lower()
    for phrase in FORBIDDEN_SAFETY_PHRASES:
        if phrase in lower:
            return phrase
    return None


def validate_safety_text(text: str) -> str:
    """
    Ensures no generated text or AI output makes prohibited guarantee claims.
    Raises ValueError if a prohibited phrase is detected.
    """
    detected = contains_forbidden_phrase(text)
    if detected:
        raise ValueError(f"Trading safety violation: Prohibited phrase '{detected}' detected.")
    return text


def sanitize_safety_text(text: str) -> str:
    """
    Defensive sanitizer: replaces any prohibited guarantee phrase with a compliant disclaimer notice.
    """
    if not text:
        return text
    result = text
    for phrase in FORBIDDEN_SAFETY_PHRASES:
        if phrase in result.lower():
            # Case-insensitive replacement
            import re
            result = re.sub(re.escape(phrase), "[NON-GUARANTEED PROBABILISTIC ESTIMATE]", result, flags=re.IGNORECASE)
    return result


def get_standard_disclaimer() -> dict:
    """Returns standardized regulatory and paper-trading disclaimer."""
    return {
        "mode": "PAPER_TRADING_ONLY" if settings.PAPER_TRADING_ONLY else "REAL_ORDERS_ACTIVE",
        "real_orders_enabled": settings.REAL_ORDERS_ENABLED,
        "disclaimer": settings.REGULATORY_DISCLAIMER,
        "guarantee_statement": "Past performance and model predictions do not guarantee future market returns."
    }


def is_auth_required() -> bool:
    """Determines whether API key authentication must be enforced for mutating actions."""
    return (
        settings.REQUIRE_AUTH_FOR_MUTATIONS
        or settings.ENVIRONMENT == "production"
        or bool(settings.ADMIN_API_KEY and len(settings.ADMIN_API_KEY) > 0)
    )


async def verify_api_key(
    request: Request,
    api_key_header: Optional[str] = Security(API_KEY_HEADER),
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(BEARER_AUTH)
) -> bool:
    """
    Authentication dependency for protected mutating endpoints.
    Extracts key from 'X-API-Key' header or 'Authorization: Bearer <key>'.
    Enforced in production, when ADMIN_API_KEY is configured, or when REQUIRE_AUTH_FOR_MUTATIONS=True.
    """
    if not is_auth_required():
        # Open in development mode if no key configured
        return True

    # Extract token from header or bearer
    token = api_key_header
    if not token and bearer_creds:
        token = bearer_creds.credentials

    if not token:
        logger.warning(f"Unauthorized mutation attempt on {request.method} {request.url.path} (missing credentials)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide valid 'X-API-Key' header or 'Authorization: Bearer <key>'."
        )

    # Validate against configured admin key or secret key
    valid_keys = []
    if settings.ADMIN_API_KEY:
        valid_keys.append(settings.ADMIN_API_KEY)
    if settings.SECRET_KEY and settings.SECRET_KEY != "dev-insecure-secret-key-change-in-production-12345":
        valid_keys.append(settings.SECRET_KEY)
    elif not valid_keys:
        # Fallback to SECRET_KEY even in dev if auth is required
        valid_keys.append(settings.SECRET_KEY)

    token_bytes = token.encode("utf-8")
    is_valid = any(
        secrets.compare_digest(token_bytes, k.encode("utf-8"))
        for k in valid_keys
    )

    if not is_valid:
        logger.warning(f"Unauthorized mutation attempt on {request.method} {request.url.path} (invalid API key)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key credentials."
        )

    return True
