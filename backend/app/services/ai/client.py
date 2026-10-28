import json
import asyncio
from typing import Optional, Dict, List, Any
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import logger
from app.core.security import validate_safety_text
from app.core.database import AsyncSessionLocal
from app.models.system import ApiUsage
from app.services.news.models import RawNewsArticle
from app.services.ai.schemas import AIArticleAnalysis
from app.services.ai.prompts import AI_SYSTEM_PROMPT, build_analysis_user_prompt
from app.services.news.classification import (
    classify_news_categories,
    extract_affected_tickers,
    estimate_sentiment_and_impact
)


class OpenAIAnalyzer:
    """
    OpenAI-powered Market Intelligence Analysis Engine.
    Uses structured outputs, strict fact-vs-speculation segregation, token cost tracking,
    and automatic deterministic fallback on API outage or missing credentials.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self._cache: Dict[str, AIArticleAnalysis] = {}
        self._client: Optional[AsyncOpenAI] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None and self.is_configured:
            self._client = AsyncOpenAI(api_key=self.api_key, timeout=15.0)
        return self._client

    async def _record_api_usage(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculates estimated cost for gpt-4o-mini and logs to api_usage table."""
        # gpt-4o-mini pricing: $0.15 / 1M prompt, $0.60 / 1M completion
        cost = (prompt_tokens * 0.15 / 1_000_000) + (completion_tokens * 0.60 / 1_000_000)
        total_tokens = prompt_tokens + completion_tokens

        try:
            async with AsyncSessionLocal() as session:
                record = ApiUsage(
                    provider="OPENAI",
                    operation=f"chat_completions_{self.model}",
                    units_consumed=total_tokens,
                    estimated_cost_usd=round(cost, 6)
                )
                session.add(record)
                await session.commit()
        except Exception as e:
            logger.debug(f"Failed to record API usage metric: {e}")

        return cost

    def _generate_deterministic_analysis(self, article: RawNewsArticle) -> AIArticleAnalysis:
        """
        High-fidelity deterministic fallback analyzer.
        Invoked when OpenAI API is unconfigured, rate-limited, or offline.
        Ensures the intelligence engine continues operating seamlessly (Section 19: Reliability).
        """
        categories = article.categories or classify_news_categories(article.title, article.description or "")
        tickers = article.tickers or extract_affected_tickers(article.title, article.description or "")
        sentiment, impact = estimate_sentiment_and_impact(
            article.title,
            article.description or "",
            categories=categories,
            reliability_score=article.source_reliability_score
        )

        primary_event = categories[0] if categories else "General Market"

        affected_sectors = article.sectors
        if not affected_sectors:
            if "Banking" in categories or "RBI" in categories:
                affected_sectors = ["Banking & Financial Services"]
            elif "IT" in categories or "Technology" in categories:
                affected_sectors = ["Information Technology"]
            elif "Crude oil" in categories or "Energy" in categories:
                affected_sectors = ["Oil, Gas & Energy", "Paints & Specialty Chemicals"]
            elif "Auto" in categories:
                affected_sectors = ["Automobile & Auto Components"]
            elif "Gold" in categories:
                affected_sectors = ["Gems, Jewellery & Gold Loans"]
            elif "Defence" in categories:
                affected_sectors = ["Defence & Aerospace"]
            else:
                affected_sectors = ["Diversified"]

        affected_indices = ["NIFTY 50"] if any(c in categories for c in ["RBI", "Interest rates", "Crude oil", "GDP"]) else []
        if "Banking" in categories or "RBI" in categories:
            affected_indices.append("BANK NIFTY")

        summary = article.description[:200] if article.description else article.title
        reasoning = (
            f"Event classified under {primary_event} with {sentiment} market bias for Indian equities. "
            f"Observed impact score {impact}/100 from {article.source}."
        )

        return AIArticleAnalysis(
            summary=summary,
            event_type=primary_event,
            sentiment=sentiment,  # type: ignore
            impact_score=impact,
            confidence=article.source_reliability_score,
            time_horizon="INTRADAY" if impact >= 75 else "SHORT_TERM",
            affected_sectors=affected_sectors,
            affected_stocks=tickers,
            affected_indices=affected_indices,
            reasoning=reasoning,
            risk_factors=["Headline risk", "Market volatility", "Global macro divergence"],
            confirmed_facts=[article.title],
            market_interpretation=f"Algorithmic synthesis expects {sentiment.lower()} sector transmission across {', '.join(affected_sectors)}.",
            speculation=None
        )

    async def analyze_article(self, article: RawNewsArticle) -> AIArticleAnalysis:
        """
        Analyzes a single news article with OpenAI structured outputs.
        Utilizes caching, safety rule validation, and fallback handling.
        """
        # 1. Check in-memory cache
        if article.fingerprint in self._cache:
            logger.debug(f"AI Cache Hit for fingerprint {article.fingerprint[:12]}")
            return self._cache[article.fingerprint]

        # 2. Check credentials; if missing, use resilient fallback
        if not self.is_configured:
            result = self._generate_deterministic_analysis(article)
            self._cache[article.fingerprint] = result
            return result

        # 3. Call OpenAI Structured API with retries
        client = self._get_client()
        user_prompt = build_analysis_user_prompt(
            article.title,
            article.description or "",
            article.source,
            article.source_reliability_score
        )

        for attempt in range(2):
            try:
                response = await client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": AI_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format=AIArticleAnalysis,
                    temperature=0.1
                )

                parsed_result: AIArticleAnalysis = response.choices[0].message.parsed
                if response.usage:
                    await self._record_api_usage(
                        response.usage.prompt_tokens,
                        response.usage.completion_tokens
                    )

                # Validate safety rules (No guarantee claims)
                validate_safety_text(parsed_result.summary)
                validate_safety_text(parsed_result.reasoning)
                validate_safety_text(parsed_result.market_interpretation)

                # Store in cache
                self._cache[article.fingerprint] = parsed_result
                return parsed_result

            except Exception as exc:
                logger.warning(f"OpenAI call attempt {attempt + 1} failed: {exc}. Retrying...")
                await asyncio.sleep(1.0)

        # Fallback if both attempts fail
        logger.warning(f"Falling back to deterministic intelligence analyzer for '{article.title[:40]}...'")
        fallback_result = self._generate_deterministic_analysis(article)
        self._cache[article.fingerprint] = fallback_result
        return fallback_result

    async def batch_analyze(
        self,
        articles: List[RawNewsArticle],
        concurrency_limit: int = 3
    ) -> Dict[str, AIArticleAnalysis]:
        """Analyzes a batch of news articles concurrently with throttled concurrency."""
        semaphore = asyncio.Semaphore(concurrency_limit)
        results: Dict[str, AIArticleAnalysis] = {}

        async def _bounded_analyze(art: RawNewsArticle):
            async with semaphore:
                res = await self.analyze_article(art)
                results[art.fingerprint] = res

        tasks = [_bounded_analyze(a) for a in articles]
        await asyncio.gather(*tasks, return_exceptions=True)
        return results


# Global singleton analyzer
ai_analyzer = OpenAIAnalyzer()
