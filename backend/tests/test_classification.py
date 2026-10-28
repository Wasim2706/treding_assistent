from app.services.news.classification import (
    classify_news_categories,
    extract_affected_tickers,
    estimate_sentiment_and_impact
)


def test_classify_news_categories():
    rbi_title = "RBI MPC Announcement: Governor Shaktikanta Das keeps repo rate steady"
    categories = classify_news_categories(rbi_title)
    assert "RBI" in categories
    assert "Interest rates" in categories

    crude_title = "Brent crude rallies 3.5% as Red Sea tension intensifies"
    categories_crude = classify_news_categories(crude_title)
    assert "Crude oil" in categories_crude
    assert "Geopolitical" in categories_crude

    earnings_title = "Tata Motors Q4 net profit jumps 45% YoY to ₹9,920 crore"
    categories_earnings = classify_news_categories(earnings_title)
    assert "Earnings" in categories_earnings
    assert "Auto" in categories_earnings


def test_extract_affected_tickers():
    title = "Reliance Retail expands quick commerce as TCS deal wins accelerate"
    tickers = extract_affected_tickers(title)
    assert "RELIANCE" in tickers
    assert "TCS" in tickers

    bank_title = "HDFC Bank and ICICI Bank lead rally in Bank Nifty"
    bank_tickers = extract_affected_tickers(bank_title)
    assert "HDFCBANK" in bank_tickers
    assert "ICICIBANK" in bank_tickers


def test_estimate_sentiment_and_impact():
    # Bullish scenario
    bull_title = "Titan surges 5% as festive jewellery demand jumps to record high"
    sentiment, impact = estimate_sentiment_and_impact(bull_title, categories=["Earnings", "Gold"])
    assert sentiment == "BULLISH"
    assert impact >= 75  # High-impact category + bullish intensity

    # Bearish scenario
    bear_title = "Asian Paints plunges 4% as crude oil price spike compresses operating margins"
    sentiment_bear, impact_bear = estimate_sentiment_and_impact(bear_title, categories=["Crude oil"])
    assert sentiment_bear == "BEARISH"
    assert impact_bear >= 75

    # Neutral scenario
    neutral_title = "SEBI issues consultation paper regarding derivative trading frameworks"
    sentiment_neutral, impact_neutral = estimate_sentiment_and_impact(neutral_title, categories=["SEBI"])
    assert sentiment_neutral == "NEUTRAL"
