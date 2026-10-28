from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class AIArticleAnalysis(BaseModel):
    """
    Strict machine-readable response format from OpenAI API.
    Enforces separation between confirmed facts, market interpretation, and speculation.
    """
    summary: str = Field(
        ...,
        description="Executive 1-2 sentence summary of the news development."
    )
    event_type: str = Field(
        ...,
        description="Primary category (e.g. Earnings, RBI, Crude oil, Geopolitical, IT, Banking, etc.)"
    )
    sentiment: Literal["BULLISH", "BEARISH", "NEUTRAL"] = Field(
        ...,
        description="Overall market bias for Indian equities."
    )
    impact_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Estimated potential market impact score (0 to 100)."
    )
    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score in the analysis (0 to 100)."
    )
    time_horizon: Literal["INTRADAY", "SHORT_TERM", "MEDIUM_TERM"] = Field(
        ...,
        description="Expected time horizon of impact."
    )
    affected_sectors: List[str] = Field(
        default_factory=list,
        description="Indian market sectors affected (e.g. Banking, IT, Paints, Auto, Oil & Gas)."
    )
    affected_stocks: List[str] = Field(
        default_factory=list,
        description="Indian stock exchange tickers likely affected (e.g. RELIANCE, TCS, HDFCBANK, ASIANPAINT)."
    )
    affected_indices: List[str] = Field(
        default_factory=list,
        description="Indices affected (e.g. NIFTY 50, BANK NIFTY, NIFTY IT)."
    )
    reasoning: str = Field(
        ...,
        description="Logical rationale explaining the market impact and sector transmission mechanism."
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Potential catalyst invalidators, macro counter-trends, or headline risks."
    )

    # MANDATORY FACT VS SPECULATION SEPARATION
    confirmed_facts: List[str] = Field(
        default_factory=list,
        description="Verified historical or explicitly confirmed facts stated in the source article."
    )
    market_interpretation: str = Field(
        ...,
        description="Economic and fundamental interpretation of how the facts relate to Indian market trends."
    )
    speculation: Optional[str] = Field(
        default=None,
        description="Any rumors, anonymous source claims, or speculative analyst forecasts, clearly segregated."
    )

    model_config = ConfigDict(from_attributes=True)
