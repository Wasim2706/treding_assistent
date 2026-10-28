import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.market import Stock
from app.models.signal import Signal
from app.services.signals.generator import SignalGenerator
from app.core.security import validate_safety_text, FORBIDDEN_SAFETY_PHRASES


def test_signal_levels_calculation_buy():
    generator = SignalGenerator()
    levels = generator.calculate_levels(
        last_price=3000.0,
        direction="BUY",
        atr_14=40.0,
        support_level=2950.0,
        resistance_level=3100.0
    )

    assert "₹" in levels["entry_zone"]
    assert levels["entry_price"] == 3000.0
    assert levels["stop_loss"] < 3000.0
    assert levels["target_1"] > 3000.0
    assert levels["target_2"] > levels["target_1"]
    assert "1:" in levels["risk_reward"]


def test_signal_levels_calculation_sell():
    generator = SignalGenerator()
    levels = generator.calculate_levels(
        last_price=1600.0,
        direction="SELL",
        atr_14=25.0,
        support_level=1550.0,
        resistance_level=1650.0
    )

    assert levels["entry_price"] == 1600.0
    assert levels["stop_loss"] > 1600.0
    assert levels["target_1"] < 1600.0
    assert levels["target_2"] < levels["target_1"]


@pytest.mark.asyncio
async def test_signal_generation_for_stock(db_session: AsyncSession):
    generator = SignalGenerator()
    res = await db_session.execute(
        select(Stock).where((Stock.symbol == "RELIANCE.NS") | (Stock.exchange_ticker == "RELIANCE"))
    )
    stock = res.scalars().first()
    assert stock is not None

    signal = await generator.generate_signal_for_stock(
        stock=stock,
        db=db_session
    )

    assert isinstance(signal, Signal)
    assert signal.symbol == "RELIANCE"
    assert signal.direction in ("BUY", "SELL", "WATCH", "NO_TRADE")
    assert signal.composite_score >= 0.0
    assert signal.status == "PENDING"
    assert not signal.is_paper_traded

    # Verify trading safety: no prohibited phrases in reasoning or invalidation
    for phrase in FORBIDDEN_SAFETY_PHRASES:
        assert phrase not in signal.reasoning.lower()
        assert phrase not in signal.invalidated_if.lower()
