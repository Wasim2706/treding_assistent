import pytest
from pydantic import ValidationError
from app.services.ai.schemas import AIArticleAnalysis


def test_ai_article_analysis_valid_schema():
    analysis = AIArticleAnalysis(
        summary="RBI keeps benchmark repo rate unchanged at 6.50% citing sustained domestic momentum.",
        event_type="RBI",
        sentiment="NEUTRAL",
        impact_score=80,
        confidence=90,
        time_horizon="SHORT_TERM",
        affected_sectors=["Banking & Financial Services", "Automobile & Auto Components"],
        affected_stocks=["HDFCBANK", "SBIN", "TATAMOTORS"],
        affected_indices=["NIFTY 50", "BANK NIFTY"],
        reasoning="Neutral interest rate stance ensures stable net interest margins for commercial banks.",
        risk_factors=["Sticky food inflation", "Global rate divergence"],
        confirmed_facts=["RBI MPC voted to maintain benchmark repo rate at 6.50%."],
        market_interpretation="Stability in lending rates supports ongoing retail credit and mortgage demand.",
        speculation="Some market participants anticipate a 25 bps rate cut in Q4."
    )

    assert analysis.impact_score == 80
    assert analysis.sentiment == "NEUTRAL"
    assert len(analysis.confirmed_facts) == 1
    assert "HDFCBANK" in analysis.affected_stocks
    assert analysis.speculation is not None


def test_ai_article_analysis_boundary_validation():
    # Impact score > 100 must fail
    with pytest.raises(ValidationError):
        AIArticleAnalysis(
            summary="Invalid score test",
            event_type="General",
            sentiment="BULLISH",
            impact_score=150,  # Invalid
            confidence=80,
            time_horizon="INTRADAY",
            reasoning="Rationale",
            market_interpretation="Deduction"
        )

    # Invalid sentiment enum must fail
    with pytest.raises(ValidationError):
        AIArticleAnalysis(
            summary="Invalid sentiment test",
            event_type="General",
            sentiment="VERY_BULLISH",  # Invalid
            impact_score=70,
            confidence=80,
            time_horizon="INTRADAY",
            reasoning="Rationale",
            market_interpretation="Deduction"
        )
