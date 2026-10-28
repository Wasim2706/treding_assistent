from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TechnicalConfirmationResult(BaseModel):
    symbol: str
    news_sentiment: str
    is_confirmed: bool
    status: str  # "CONFIRMED", "CONFLICTING", "WEAK_CONFIRMATION", "INSUFFICIENT_DATA", "NEUTRAL_MARKET"
    technical_score: float = Field(ge=0.0, le=100.0)  # 0 to 100
    recommendation: str  # "ALLOW_SIGNAL", "WATCH", "NO_TRADE"
    reasons: List[str]
    conflicts: List[str]


class TechnicalConfirmationGate:
    """
    Enforces the primary risk constraint:
    'Never generate a trading signal using news alone. Require confirmation from market data.'
    'If news and market data conflict, default to NO TRADE.'
    """

    @staticmethod
    def evaluate(
        symbol: str,
        news_sentiment: str,
        news_impact: float,
        market_data: Optional[Dict[str, Any]]
    ) -> TechnicalConfirmationResult:
        sentiment = (news_sentiment or "NEUTRAL").upper()

        # 1. Check for complete market data
        if not market_data:
            return TechnicalConfirmationResult(
                symbol=symbol,
                news_sentiment=sentiment,
                is_confirmed=False,
                status="INSUFFICIENT_DATA",
                technical_score=0.0,
                recommendation="NO_TRADE",
                reasons=["No market data snapshot available for symbol."],
                conflicts=["Market data is completely missing. Execution safety prevents unconfirmed signals."]
            )

        last_price = market_data.get("last_price", 0.0) or 0.0
        sma_20 = market_data.get("sma_20")
        sma_50 = market_data.get("sma_50")
        sma_200 = market_data.get("sma_200")
        rsi_14 = market_data.get("rsi_14")
        macd_hist = market_data.get("macd_hist")
        support_level = market_data.get("support_level")
        resistance_level = market_data.get("resistance_level")
        vol_surge_ratio = market_data.get("vol_surge_ratio", 1.0) or 1.0

        if last_price <= 0.0 or rsi_14 is None:
            return TechnicalConfirmationResult(
                symbol=symbol,
                news_sentiment=sentiment,
                is_confirmed=False,
                status="INSUFFICIENT_DATA",
                technical_score=0.0,
                recommendation="NO_TRADE",
                reasons=["Essential price or RSI indicator data is missing."],
                conflicts=["Incomplete technical snapshot."]
            )

        # 2. Check for Neutral or sub-threshold news impact
        if sentiment == "NEUTRAL" or news_impact < 25.0:
            return TechnicalConfirmationResult(
                symbol=symbol,
                news_sentiment=sentiment,
                is_confirmed=False,
                status="NEUTRAL_MARKET",
                technical_score=50.0,
                recommendation="WATCH",
                reasons=[f"News sentiment is {sentiment} with impact {news_impact:.1f}. No directional bias to confirm."],
                conflicts=[]
            )

        reasons: List[str] = []
        conflicts: List[str] = []
        score = 0.0

        # 3. Evaluate Bullish News against Technicals
        if sentiment == "BULLISH":
            # Criteria A: Price trend vs 20 SMA
            if sma_20 is not None:
                if last_price >= sma_20:
                    score += 25.0
                    reasons.append(f"Price (₹{last_price:.1f}) is above 20 SMA (₹{sma_20:.1f}), confirming short-term uptrend.")
                else:
                    conflicts.append(f"Price (₹{last_price:.1f}) is below 20 SMA (₹{sma_20:.1f}). Downtrend contradicts bullish news.")

            # Criteria B: Price trend vs 50 SMA
            if sma_50 is not None:
                if last_price >= sma_50:
                    score += 15.0
                    reasons.append(f"Price is above 50 SMA (₹{sma_50:.1f}).")
                else:
                    conflicts.append(f"Price is below intermediate 50 SMA (₹{sma_50:.1f}).")

            # Criteria C: RSI momentum zone
            if 48.0 <= rsi_14 <= 72.0:
                score += 25.0
                reasons.append(f"RSI-14 ({rsi_14:.1f}) is in healthy bullish momentum zone (48-72).")
            elif rsi_14 > 75.0:
                score += 5.0
                conflicts.append(f"RSI-14 ({rsi_14:.1f}) indicates severe overbought conditions. High risk of mean-reversion.")
            elif rsi_14 < 40.0:
                conflicts.append(f"RSI-14 ({rsi_14:.1f}) reflects weak bearish momentum despite positive news.")
            else:
                score += 10.0
                reasons.append(f"RSI-14 ({rsi_14:.1f}) is neutral.")

            # Criteria D: MACD momentum
            if macd_hist is not None:
                if macd_hist > 0:
                    score += 20.0
                    reasons.append(f"MACD histogram ({macd_hist:+.2f}) is positive, showing buyer dominance.")
                else:
                    conflicts.append(f"MACD histogram ({macd_hist:+.2f}) is negative, indicating selling pressure.")

            # Criteria E: Volume confirmation
            if vol_surge_ratio >= 1.2:
                score += 15.0
                reasons.append(f"Volume surge ratio ({vol_surge_ratio:.2f}x) confirms institutional interest.")
            else:
                score += 5.0

            # Decisive conflict check: If breaking down below support
            if support_level is not None and last_price < support_level * 0.995:
                conflicts.append(f"Price has breached primary support level (₹{support_level:.1f}). Major structural conflict.")

        # 4. Evaluate Bearish News against Technicals
        elif sentiment == "BEARISH":
            # Criteria A: Price trend vs 20 SMA
            if sma_20 is not None:
                if last_price <= sma_20:
                    score += 25.0
                    reasons.append(f"Price (₹{last_price:.1f}) is below 20 SMA (₹{sma_20:.1f}), confirming downward trajectory.")
                else:
                    conflicts.append(f"Price (₹{last_price:.1f}) is above 20 SMA (₹{sma_20:.1f}). Strength contradicts bearish news.")

            # Criteria B: Price trend vs 50 SMA
            if sma_50 is not None:
                if last_price <= sma_50:
                    score += 15.0
                    reasons.append(f"Price is below 50 SMA (₹{sma_50:.1f}).")
                else:
                    conflicts.append(f"Price is above intermediate 50 SMA (₹{sma_50:.1f}).")

            # Criteria C: RSI momentum zone
            if 28.0 <= rsi_14 <= 52.0:
                score += 25.0
                reasons.append(f"RSI-14 ({rsi_14:.1f}) confirms bearish momentum zone (28-52).")
            elif rsi_14 < 25.0:
                score += 5.0
                conflicts.append(f"RSI-14 ({rsi_14:.1f}) is deeply oversold. High short squeeze risk.")
            elif rsi_14 > 60.0:
                conflicts.append(f"RSI-14 ({rsi_14:.1f}) is bullish, resisting negative sentiment.")
            else:
                score += 10.0
                reasons.append(f"RSI-14 ({rsi_14:.1f}) is neutral.")

            # Criteria D: MACD momentum
            if macd_hist is not None:
                if macd_hist < 0:
                    score += 20.0
                    reasons.append(f"MACD histogram ({macd_hist:+.2f}) is negative, confirming downward momentum.")
                else:
                    conflicts.append(f"MACD histogram ({macd_hist:+.2f}) is positive, showing buyer resistance.")

            # Criteria E: Volume confirmation
            if vol_surge_ratio >= 1.2:
                score += 15.0
                reasons.append(f"High volume ({vol_surge_ratio:.2f}x) validates selling pressure.")
            else:
                score += 5.0

            # Decisive conflict check: If breaking out above resistance
            if resistance_level is not None and last_price > resistance_level * 1.005:
                conflicts.append(f"Price has breached primary resistance (₹{resistance_level:.1f}). Technical breakout contradicts bearish news.")

        # 5. Final Synthesis and Recommendation
        score = min(100.0, max(0.0, score))

        # Strict conflict threshold: If there are 2 or more serious technical conflicts, default to NO TRADE
        if len(conflicts) >= 2 or (sentiment == "BULLISH" and last_price < (sma_20 or last_price) and rsi_14 < 42):
            return TechnicalConfirmationResult(
                symbol=symbol,
                news_sentiment=sentiment,
                is_confirmed=False,
                status="CONFLICTING",
                technical_score=score,
                recommendation="NO_TRADE",
                reasons=reasons,
                conflicts=conflicts
            )

        if score >= 60.0:
            return TechnicalConfirmationResult(
                symbol=symbol,
                news_sentiment=sentiment,
                is_confirmed=True,
                status="CONFIRMED",
                technical_score=score,
                recommendation="ALLOW_SIGNAL",
                reasons=reasons,
                conflicts=conflicts
            )
        else:
            return TechnicalConfirmationResult(
                symbol=symbol,
                news_sentiment=sentiment,
                is_confirmed=False,
                status="WEAK_CONFIRMATION",
                technical_score=score,
                recommendation="WATCH",
                reasons=reasons,
                conflicts=conflicts
            )
