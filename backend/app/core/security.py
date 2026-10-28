from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

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


def validate_safety_text(text: str) -> str:
    """
    Ensures no generated text or AI output makes prohibited guarantee claims.
    Raises ValueError or cleanses if detected.
    """
    lower = text.lower()
    for phrase in FORBIDDEN_SAFETY_PHRASES:
        if phrase in lower:
            raise ValueError(f"Trading safety violation: Prohibited phrase '{phrase}' detected.")
    return text


def get_standard_disclaimer() -> dict:
    """Returns standardized regulatory and paper-trading disclaimer."""
    return {
        "mode": "PAPER_TRADING_ONLY" if settings.PAPER_TRADING_ONLY else "REAL_ORDERS_ACTIVE",
        "real_orders_enabled": settings.REAL_ORDERS_ENABLED,
        "disclaimer": settings.REGULATORY_DISCLAIMER,
        "guarantee_statement": "Past performance and model predictions do not guarantee future market returns."
    }


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> bool:
    """
    Optional API key check for protected mutating endpoints.
    In development mode or when no secret key is enforced, allows open access.
    """
    if settings.ENVIRONMENT == "production":
        expected_key = settings.SECRET_KEY
        if not api_key or api_key != expected_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-API-Key authentication header."
            )
    return True
