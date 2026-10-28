from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.models.signal import Signal
from app.models.market import Stock, Sector, MarketDataSnapshot
from app.models.news import NewsArticle, NewsAnalysis
from app.core.security import validate_safety_text
from app.services.signals.scoring import MultiFactorScorer, ScoreBreakdown
from app.services.market_data.service import market_data_service
from app.services.market_data.base import clean_ticker, get_indian_market_status


class SignalGenerator:
    """
    Synthesizes multi-factor signals for Indian equities.
    Calculates dynamic entry zones, ATR-based stop-losses, and multi-tier targets.
    Enforces strict risk:reward (minimum 1:1.5) and epistemic safety constraints.
    """

    def __init__(self, scorer: Optional[MultiFactorScorer] = None):
        self.scorer = scorer or MultiFactorScorer()

    def calculate_levels(
        self,
        last_price: float,
        direction: str,
        atr_14: Optional[float],
        support_level: Optional[float],
        resistance_level: Optional[float]
    ) -> Dict[str, Any]:
        """Calculates dynamic entry zone, stop loss, and targets using ATR buffer."""
        buffer = atr_14 if (atr_14 is not None and atr_14 > 0) else (last_price * 0.012)
        buffer = max(buffer, last_price * 0.005)  # minimum 0.5% buffer

        if direction == "BUY":
            entry_low = round(last_price * 0.997, 2)
            entry_high = round(last_price * 1.003, 2)
            entry_zone = f"₹{entry_low} - ₹{entry_high}"

            sl_candidate = last_price - (1.5 * buffer)
            if support_level and support_level < last_price:
                sl = round(min(sl_candidate, support_level * 0.998), 2)
            else:
                sl = round(sl_candidate, 2)

            risk = last_price - sl
            t1 = round(last_price + (1.5 * risk), 2)
            t2 = round(last_price + (2.5 * risk), 2)
            rr_ratio = f"1:{round((t2 - last_price) / risk, 1)}" if risk > 0 else "1:2.0"

        elif direction == "SELL":
            entry_low = round(last_price * 0.997, 2)
            entry_high = round(last_price * 1.003, 2)
            entry_zone = f"₹{entry_low} - ₹{entry_high}"

            sl_candidate = last_price + (1.5 * buffer)
            if resistance_level and resistance_level > last_price:
                sl = round(max(sl_candidate, resistance_level * 1.002), 2)
            else:
                sl = round(sl_candidate, 2)

            risk = sl - last_price
            t1 = round(last_price - (1.5 * risk), 2)
            t2 = round(last_price - (2.5 * risk), 2)
            rr_ratio = f"1:{round((last_price - t2) / risk, 1)}" if risk > 0 else "1:2.0"

        else:  # WATCH or NO_TRADE
            entry_zone = f"₹{round(last_price * 0.99, 2)} - ₹{round(last_price * 1.01, 2)}"
            sl = None
            t1 = None
            t2 = None
            rr_ratio = "N/A"

        return {
            "entry_zone": entry_zone,
            "entry_price": round(last_price, 2),
            "stop_loss": sl,
            "target_1": t1,
            "target_2": t2,
            "risk_reward": rr_ratio,
        }

    async def generate_signal_for_stock(
        self,
        stock: Stock,
        db: AsyncSession,
        nifty_quote: Optional[Dict[str, Any]] = None,
        macro_factors: Optional[Dict[str, Any]] = None
    ) -> Optional[Signal]:
        symbol = clean_ticker(stock.symbol)

        # 1. Fetch latest technical indicators
        indicators = await market_data_service.get_indicators(symbol)
        last_price = indicators.get("last_price", 0.0)
        if last_price <= 0:
            return None

        # 2. Fetch latest news analysis for this stock safely
        news_query = (
            select(NewsAnalysis, NewsArticle)
            .join(NewsArticle, NewsAnalysis.article_id == NewsArticle.id)
            .order_by(desc(NewsArticle.published_at))
            .limit(15)
        )
        news_res = await db.execute(news_query)
        all_recent = news_res.all()

        recent_analyses = [
            (analysis, article) for analysis, article in all_recent
            if analysis.affected_stocks and symbol in analysis.affected_stocks
        ]

        news_sentiment = "NEUTRAL"
        news_impact = 40.0
        news_confidence = 50.0
        news_sources = []
        catalyst_summary = ""

        if recent_analyses:
            top_analysis, top_article = recent_analyses[0]
            news_sentiment = top_analysis.sentiment
            news_impact = float(top_analysis.impact_score)
            news_confidence = float(top_analysis.confidence)
            catalyst_summary = top_analysis.summary
            for analysis, article in recent_analyses[:3]:
                news_sources.append({
                    "title": article.title,
                    "source": article.source,
                    "sentiment": analysis.sentiment,
                    "impact_score": analysis.impact_score,
                    "url": article.url
                })
        else:
            trend = indicators.get("trend_bias", "NEUTRAL")
            news_sentiment = trend
            news_impact = 50.0
            catalyst_summary = f"Technical setup identified based on {trend} indicator alignment."

        # 3. Sector sensitivities (safe against un-awaited async lazy loading)
        sector_sensitivities = {}
        if stock.sector_id:
            sec = await db.get(Sector, stock.sector_id)
            if sec and sec.sensitivities:
                sector_sensitivities = sec.sensitivities

        # 4. Multi-Factor Evaluation
        score_breakdown: ScoreBreakdown = self.scorer.evaluate(
            symbol=symbol,
            news_sentiment=news_sentiment,
            news_impact=news_impact,
            news_confidence=news_confidence,
            market_data=indicators,
            nifty_quote=nifty_quote,
            sector_sensitivities=sector_sensitivities,
            macro_factors=macro_factors
        )

        direction = score_breakdown.direction

        # 5. Compute dynamic price levels
        levels = self.calculate_levels(
            last_price=last_price,
            direction=direction,
            atr_14=indicators.get("atr_14"),
            support_level=indicators.get("support_level"),
            resistance_level=indicators.get("resistance_level")
        )

        # 6. Session execution windows
        entry_window = "Post-09:30 IST buffer (Avoid 09:15-09:30 opening volatility)"
        exit_window = "Intraday exit by 15:15 IST or Stop Loss hit"

        # 7. Construct invalidation and reasoning text
        reasons_text = "; ".join(score_breakdown.reasons) if score_breakdown.reasons else "Deterministic criteria evaluated."
        invalidated_text = (
            f"Invalidated if price breaches ₹{levels['stop_loss']} or if high-impact macroeconomic reversal occurs."
            if levels["stop_loss"] else "Invalidated on technical trend breakdown."
        )
        confirmation_text = f"Status: {score_breakdown.technical_confirmation.status}. Score: {score_breakdown.technical_score:.1f}/100."

        reasons_text = validate_safety_text(reasons_text)
        invalidated_text = validate_safety_text(invalidated_text)

        signal = Signal(
            symbol=symbol,
            direction=direction,
            entry_zone=levels["entry_zone"],
            entry_price=levels["entry_price"],
            stop_loss=levels["stop_loss"],
            target_1=levels["target_1"],
            target_2=levels["target_2"],
            risk_reward=levels["risk_reward"],
            entry_time_window=entry_window,
            exit_time_window=exit_window,
            confidence=score_breakdown.confidence,
            news_score=score_breakdown.news_score,
            technical_score=score_breakdown.technical_score,
            volume_score=score_breakdown.volume_score,
            market_score=score_breakdown.market_score,
            sector_score=score_breakdown.sector_score,
            composite_score=score_breakdown.composite_score,
            reasoning=f"{catalyst_summary} {reasons_text}".strip(),
            invalidated_if=invalidated_text,
            technical_confirmation=confirmation_text,
            news_sources=news_sources,
            status="PENDING",
            is_paper_traded=False
        )

        db.add(signal)
        await db.commit()
        await db.refresh(signal)
        return signal

    async def run_cycle(self, db: AsyncSession, limit: int = 20) -> List[Signal]:
        """Runs signal evaluation cycle across tracked Indian equities."""
        overview = await market_data_service.get_market_overview()
        nifty_quote = overview.get("benchmarks", {}).get("nifty50")
        crude_quote = overview.get("benchmarks", {}).get("crude_oil")

        macro_factors = {
            "crude_oil_pct": crude_quote.get("change_pct", 0.0) if crude_quote else 0.0
        }

        stocks_res = await db.execute(
            select(Stock).options(selectinload(Stock.sector)).where(Stock.is_active == True).limit(limit)
        )
        stocks = stocks_res.scalars().all()

        signals = []
        for stock in stocks:
            try:
                sig = await self.generate_signal_for_stock(
                    stock=stock,
                    db=db,
                    nifty_quote=nifty_quote,
                    macro_factors=macro_factors
                )
                if sig is not None:
                    signals.append(sig)
            except Exception as e:
                pass

        return signals


signal_generator = SignalGenerator()
