import pytest
from app.services.signals.scoring import MultiFactorScorer, ScoreBreakdown


def test_scorer_default_weights():
    scorer = MultiFactorScorer()
    assert round(scorer.w_news + scorer.w_tech + scorer.w_vol + scorer.w_mkt + scorer.w_sec, 4) == 1.0


def test_scorer_volume_scoring():
    scorer = MultiFactorScorer()
    # Below average volume
    low_vol = scorer.compute_volume_score(vol_surge_ratio=0.5, gap_pct=0.0)
    assert low_vol == 30.0

    # Normal volume
    norm_vol = scorer.compute_volume_score(vol_surge_ratio=1.0, gap_pct=0.0)
    assert norm_vol == 65.0

    # Institutional surge
    high_vol = scorer.compute_volume_score(vol_surge_ratio=2.2, gap_pct=1.0)
    assert high_vol >= 95.0


def test_scorer_market_alignment():
    scorer = MultiFactorScorer()

    # NIFTY rallying (+1.2%) aligns with BUY
    nifty_up = {"change_pct": 1.2}
    buy_mkt = scorer.compute_market_score(nifty_up, "BUY")
    assert buy_mkt == 90.0

    # NIFTY rallying contradicts SELL
    sell_mkt = scorer.compute_market_score(nifty_up, "SELL")
    assert sell_mkt == 20.0

    # NIFTY falling (-1.0%) aligns with SELL
    nifty_down = {"change_pct": -1.0}
    sell_mkt_down = scorer.compute_market_score(nifty_down, "SELL")
    assert sell_mkt_down == 90.0


def test_scorer_sector_sensitivity_crude():
    scorer = MultiFactorScorer()
    # Auto sector is negatively impacted by rising crude
    auto_sensitivities = {"crude_oil_up": "BEARISH"}

    # Crude spikes +3.0%
    crude_spike = {"crude_oil_pct": 3.0}
    score_buy = scorer.compute_sector_score(auto_sensitivities, crude_spike, "BUY")
    assert score_buy < 50.0  # Penalized because crude up is bad for Auto

    score_sell = scorer.compute_sector_score(auto_sensitivities, crude_spike, "SELL")
    assert score_sell > 50.0  # Rewarded for shorting Auto during crude spike


def test_scorer_high_conviction_buy():
    scorer = MultiFactorScorer()
    market_snapshot = {
        "last_price": 2950.0,
        "sma_20": 2880.0,
        "sma_50": 2800.0,
        "rsi_14": 62.0,
        "macd_hist": 5.0,
        "vol_surge_ratio": 1.6,
        "gap_pct": 0.5,
        "support_level": 2850.0,
        "resistance_level": 3050.0
    }
    nifty_quote = {"change_pct": 0.6}

    result = scorer.evaluate(
        symbol="RELIANCE",
        news_sentiment="BULLISH",
        news_impact=85.0,
        news_confidence=90.0,
        market_data=market_snapshot,
        nifty_quote=nifty_quote
    )

    assert result.direction == "BUY"
    assert result.composite_score >= 70.0
    assert result.technical_confirmation.is_confirmed is True


def test_scorer_conflict_defaults_to_no_trade():
    scorer = MultiFactorScorer()
    # Bullish news, but market data shows severe technical breakdown
    market_snapshot = {
        "last_price": 2700.0,
        "sma_20": 2900.0,
        "sma_50": 2950.0,
        "rsi_14": 32.0,
        "macd_hist": -8.0,
        "vol_surge_ratio": 0.8,
        "gap_pct": -1.2,
        "support_level": 2800.0,  # Below support
        "resistance_level": 3000.0
    }

    result = scorer.evaluate(
        symbol="RELIANCE",
        news_sentiment="BULLISH",
        news_impact=90.0,
        news_confidence=85.0,
        market_data=market_snapshot
    )

    # SAFETY RULE: Contradiction must strictly result in NO_TRADE
    assert result.direction == "NO_TRADE"
    assert result.technical_confirmation.status == "CONFLICTING"
    assert result.confidence < 50
