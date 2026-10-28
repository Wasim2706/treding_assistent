from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.market_data.confirmation import TechnicalConfirmationGate, TechnicalConfirmationResult


class ScoreBreakdown(BaseModel):
    news_score: float = Field(ge=0.0, le=100.0)
    technical_score: float = Field(ge=0.0, le=100.0)
    volume_score: float = Field(ge=0.0, le=100.0)
    market_score: float = Field(ge=0.0, le=100.0)
    sector_score: float = Field(ge=0.0, le=100.0)
    composite_score: float = Field(ge=0.0, le=100.0)
    direction: str  # BUY, SELL, WATCH, NO_TRADE
    confidence: int = Field(ge=0, le=100)
    technical_confirmation: TechnicalConfirmationResult
    reasons: List[str]
    invalidation_rules: List[str]


class MultiFactorScorer:
    """
    Deterministic multi-factor scoring engine combining:
    1. News sentiment & impact (35%)
    2. Technical indicator confirmation (30%)
    3. Volume surge & momentum (15%)
    4. NIFTY 50 / market trend (10%)
    5. Sector trend & macro sensitivity (10%)
    """

    def __init__(
        self,
        weight_news: float = 0.35,
        weight_technical: float = 0.30,
        weight_volume: float = 0.15,
        weight_market: float = 0.10,
        weight_sector: float = 0.10
    ):
        self.w_news = weight_news
        self.w_tech = weight_technical
        self.w_vol = weight_volume
        self.w_mkt = weight_market
        self.w_sec = weight_sector

    def compute_volume_score(self, vol_surge_ratio: float, gap_pct: float) -> float:
        """
        Scores volume & momentum (0 - 100).
        1.0x surge = 50 pts, 1.5x = 75 pts, >= 2.0x = 90-100 pts.
        """
        surge = max(0.0, vol_surge_ratio)
        if surge < 0.6:
            base_score = 30.0
        elif surge < 1.0:
            base_score = 45.0
        elif surge < 1.4:
            base_score = 65.0
        elif surge < 2.0:
            base_score = 80.0
        else:
            base_score = 95.0

        # Momentum bonus if gap aligns
        gap_bonus = min(10.0, abs(gap_pct) * 3.0)
        return min(100.0, max(0.0, base_score + (gap_bonus if surge >= 1.0 else 0.0)))

    def compute_market_score(self, nifty_quote: Optional[Dict[str, Any]], target_direction: str) -> float:
        """
        Scores broader Indian market alignment with target direction.
        """
        if not nifty_quote:
            return 50.0  # Neutral baseline if market quote unavailable

        change_pct = nifty_quote.get("change_pct", 0.0) or 0.0
        if target_direction == "BUY":
            if change_pct >= 0.8:
                return 90.0
            elif change_pct >= 0.2:
                return 75.0
            elif change_pct >= -0.2:
                return 55.0
            elif change_pct >= -0.8:
                return 35.0
            else:
                return 20.0
        elif target_direction == "SELL":
            if change_pct <= -0.8:
                return 90.0
            elif change_pct <= -0.2:
                return 75.0
            elif change_pct <= 0.2:
                return 55.0
            elif change_pct <= 0.8:
                return 35.0
            else:
                return 20.0
        return 50.0

    def compute_sector_score(
        self, 
        sector_sensitivities: Optional[Dict[str, Any]], 
        macro_factors: Optional[Dict[str, Any]],
        target_direction: str
    ) -> float:
        """
        Scores sector macro alignment against current macro drivers (e.g. Crude oil, Gold, USD/INR).
        """
        if not sector_sensitivities or not macro_factors:
            return 55.0  # Neutral baseline

        score = 50.0
        crude_pct = macro_factors.get("crude_oil_pct", 0.0) or 0.0

        # Crude oil sensitivity evaluation
        crude_impact = sector_sensitivities.get("crude_oil_up")
        if crude_impact:
            if crude_pct > 1.5:  # Crude oil spiking
                if crude_impact == "BEARISH" and target_direction == "BUY":
                    score -= 20.0
                elif crude_impact == "BULLISH" and target_direction == "BUY":
                    score += 20.0
                elif crude_impact == "BEARISH" and target_direction == "SELL":
                    score += 20.0
            elif crude_pct < -1.5:  # Crude oil dropping
                if crude_impact == "BEARISH" and target_direction == "BUY":
                    score += 20.0  # Falling crude benefits paint/auto/aviation
                elif crude_impact == "BULLISH" and target_direction == "BUY":
                    score -= 20.0

        return min(100.0, max(0.0, score))

    def evaluate(
        self,
        symbol: str,
        news_sentiment: str,
        news_impact: float,
        news_confidence: float,
        market_data: Optional[Dict[str, Any]],
        nifty_quote: Optional[Dict[str, Any]] = None,
        sector_sensitivities: Optional[Dict[str, Any]] = None,
        macro_factors: Optional[Dict[str, Any]] = None
    ) -> ScoreBreakdown:
        sentiment = (news_sentiment or "NEUTRAL").upper()
        target_direction = "BUY" if sentiment == "BULLISH" else ("SELL" if sentiment == "BEARISH" else "WATCH")

        # 1. Technical Confirmation Gate
        tech_confirm = TechnicalConfirmationGate.evaluate(
            symbol=symbol,
            news_sentiment=sentiment,
            news_impact=news_impact,
            market_data=market_data
        )

        # 2. News Component Score
        if sentiment in ("BULLISH", "BEARISH"):
            # Scaled by impact and confidence
            news_score = round(news_impact * 0.6 + news_confidence * 0.4, 1)
        else:
            news_score = 40.0

        # 3. Technical Component Score
        technical_score = round(tech_confirm.technical_score, 1)

        # 4. Volume / Momentum Component Score
        vol_surge = market_data.get("vol_surge_ratio", 1.0) if market_data else 1.0
        gap_pct = market_data.get("gap_pct", 0.0) if market_data else 0.0
        volume_score = round(self.compute_volume_score(vol_surge, gap_pct), 1)

        # 5. Market Trend Component Score
        market_score = round(self.compute_market_score(nifty_quote, target_direction), 1)

        # 6. Sector Trend Component Score
        sector_score = round(self.compute_sector_score(sector_sensitivities, macro_factors, target_direction), 1)

        # Composite Score Calculation
        composite = (
            self.w_news * news_score +
            self.w_tech * technical_score +
            self.w_vol * volume_score +
            self.w_mkt * market_score +
            self.w_sec * sector_score
        )
        composite = round(min(100.0, max(0.0, composite)), 1)

        # Determine Final Direction & Recommendation
        reasons: List[str] = list(tech_confirm.reasons)
        invalidation_rules: List[str] = list(tech_confirm.conflicts)

        if tech_confirm.status == "INSUFFICIENT_DATA":
            direction = "NO_TRADE"
            confidence = 10
        elif tech_confirm.status == "CONFLICTING":
            direction = "NO_TRADE"
            confidence = 20
            reasons.append("Signals Conflict: News narrative contradicted by primary technical price action.")
        elif composite >= 70.0 and tech_confirm.is_confirmed:
            direction = target_direction
            confidence = int(composite)
            reasons.append(f"Multi-factor composite score ({composite:.1f}/100) satisfies high-conviction threshold.")
        elif composite >= 50.0:
            direction = "WATCH"
            confidence = int(composite)
            reasons.append(f"Moderate conviction ({composite:.1f}/100) or awaiting clearer technical breakout.")
        else:
            direction = "NO_TRADE"
            confidence = int(composite)
            reasons.append(f"Sub-threshold score ({composite:.1f}/100). Fails risk-reward confirmation criteria.")

        return ScoreBreakdown(
            news_score=news_score,
            technical_score=technical_score,
            volume_score=volume_score,
            market_score=market_score,
            sector_score=sector_score,
            composite_score=composite,
            direction=direction,
            confidence=confidence,
            technical_confirmation=tech_confirm,
            reasons=reasons,
            invalidation_rules=invalidation_rules
        )
