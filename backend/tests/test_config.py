import pytest
from app.core.config import Settings
from app.core.security import validate_safety_text, get_standard_disclaimer


def test_settings_defaults():
    s = Settings()
    assert s.PAPER_TRADING_ONLY is True
    assert s.REAL_ORDERS_ENABLED is False
    assert "PAPER TRADING" in s.REGULATORY_DISCLAIMER
    assert s.MIN_SIGNAL_CONFIDENCE == 65
    assert round(s.WEIGHT_NEWS + s.WEIGHT_TECHNICAL + s.WEIGHT_VOLUME + s.WEIGHT_MARKET + s.WEIGHT_SECTOR, 4) == 1.0


def test_database_url_assembly():
    # Should replace postgres:// with postgresql+asyncpg://
    s = Settings(DATABASE_URL="postgres://user:pass@host/db")
    assert s.DATABASE_URL == "postgresql+asyncpg://user:pass@host/db"


def test_safety_phrase_validation():
    # Compliant text should pass
    safe_text = "NIFTY outlook is mildly bullish based on technical confirmation above 24,500."
    assert validate_safety_text(safe_text) == safe_text

    # Prohibited guarantee claims must raise ValueError
    with pytest.raises(ValueError):
        validate_safety_text("This stock is a guaranteed profit trade!")

    with pytest.raises(ValueError):
        validate_safety_text("Our AI provides 100% accurate signals.")

    with pytest.raises(ValueError):
        validate_safety_text("Buy this risk-free trade now.")


def test_standard_disclaimer():
    disc = get_standard_disclaimer()
    assert disc["mode"] == "PAPER_TRADING_ONLY"
    assert disc["real_orders_enabled"] is False
    assert "PAPER TRADING" in disc["disclaimer"]
