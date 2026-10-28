import re
from typing import List, Dict, Tuple, Set
from app.services.news.models import RawNewsArticle

# Section 5 Classification Keyword Rules
CATEGORY_PATTERNS = {
    "RBI": [r"\brbi\b", r"reserve bank of india", r"repo rate", r"monetary policy committee", r"\bmpc\b"],
    "SEBI": [r"\bsebi\b", r"securities and exchange board of india", r"market regulator", r"insider trading"],
    "Earnings": [r"\bq[1-4]\b", r"quarterly profit", r"net profit", r"revenue jumps", r"pat surges", r"earnings", r"q4 results", r"ebitda", r"financial results"],
    "Corporate announcement": [r"board meeting", r"dividend", r"bonus issue", r"stock split", r"buyback", r"capex", r"management change"],
    "M&A": [r"merger", r"acquisition", r"acquires", r"buys stake", r"takeover", r"joint venture", r"deal signed"],
    "Regulatory": [r"regulatory penalty", r"compliance", r"cci probe", r"investigation", r"licence revoked", r"fine imposed"],
    "Government policy": [r"cabinet approves", r"ministry of finance", r"budget", r"pli scheme", r"tax exemption", r"gst council", r"customs duty"],
    "Interest rates": [r"rate hike", r"rate cut", r"repo rate", r"policy rate", r"interest rate", r"lending rate", r"yield curve", r"bond yield", r"basis points", r"\bbps\b", r"fed rate"],
    "Inflation": [r"\bcpi\b", r"\bwpi\b", r"inflation", r"retail inflation", r"wholesale price", r"price pressures"],
    "GDP": [r"\bgdp\b", r"economic growth", r"growth forecast", r"gross domestic product", r"imf forecast"],
    "Employment": [r"unemployment", r"hiring", r"layoffs", r"job market", r"payroll"],
    "Geopolitical": [r"geopolitical tension", r"sanctions", r"treaty", r"trade dispute", r"strait of hormuz", r"red sea"],
    "War/conflict": [r"\bwar\b", r"missile strike", r"military conflict", r"airstrike", r"hostilities", r"ceasefire"],
    "Crude oil": [r"brent crude", r"crude oil", r"wti", r"opec", r"petrol price", r"diesel price", r"fuel price"],
    "Gold": [r"gold price", r"bullion", r"precious metals", r"silver price", r"mcx gold"],
    "Currency": [r"usd/inr", r"rupee falls", r"rupee gains", r"dollar index", r"dxy", r"forex reserves"],
    "US markets": [r"wall street", r"s&p 500", r"nasdaq", r"dow jones", r"us futures"],
    "China": [r"china stimulus", r"chinese market", r"beijing", r"pboc", r"shanghai composite"],
    "Europe": [r"ecb", r"european markets", r"dax", r"ftse", r"eurozone"],
    "Technology": [r"artificial intelligence", r"\bai\b", r"cloud computing", r"semiconductor", r"chips"],
    "Banking": [r"bank", r"nbfc", r"loan growth", r"npa", r"bad loans", r"credit growth", r"deposit growth"],
    "IT": [r"it services", r"it sector", r"tech spend", r"constant currency", r"deal wins", r"attrition"],
    "Pharma": [r"pharma", r"drug approval", r"us fda", r"form 483", r"warning letter", r"clinical trial"],
    "Auto": [r"automobile", r"car sales", r"ev sales", r"commercial vehicles", r"two wheeler", r"tractor sales", r"auto\b", r"automakers?", r"vehicles?", r"tata motors", r"maruti"],
    "FMCG": [r"fmcg", r"consumer goods", r"rural demand", r"urban consumption", r"staples"],
    "Energy": [r"power generation", r"solar energy", r"renewable energy", r"grid", r"thermal power", r"lng"],
    "Infrastructure": [r"highway", r"railway order", r"ports", r"expressway", r"metro project", r"construction"],
    "Defence": [r"defence order", r"ministry of defence", r"fighter jet", r"navy", r"missile", r"make in india defence"],
    "Telecom": [r"telecom", r"5g rollout", r"arpu", r"spectrum auction", r"telecom subscriber"],
}

# Ticker Extraction Mapping
INDIAN_TICKER_PATTERNS = {
    "RELIANCE": [r"\breliance\b", r"ril", r"jio", r"reliance retail"],
    "TCS": [r"\btcs\b", r"tata consultancy"],
    "INFY": [r"\binfosys\b", r"\binfy\b"],
    "HDFCBANK": [r"hdfc bank", r"\bhdfc\b"],
    "ICICIBANK": [r"icici bank", r"\bicici\b"],
    "SBIN": [r"state bank of india", r"\bsbi\b"],
    "KOTAKBANK": [r"kotak mahindra", r"kotak bank"],
    "AXISBANK": [r"axis bank"],
    "BAJFINANCE": [r"bajaj finance", r"bajaj finserv"],
    "TATAMOTORS": [r"tata motors", r"jlr", r"jaguar land rover"],
    "MARUTI": [r"maruti suzuki", r"\bmaruti\b"],
    "M&M": [r"mahindra & mahindra", r"\bm&m\b"],
    "ASIANPAINT": [r"asian paints"],
    "BERGEPAINT": [r"berger paints"],
    "INDIGO": [r"interglobe aviation", r"\bindigo\b"],
    "TITAN": [r"titan company", r"\btitan\b", r"tanishq"],
    "MUTHOOTFIN": [r"muthoot finance"],
    "SUNPHARMA": [r"sun pharma", r"sun pharmaceutical"],
    "CIPLA": [r"\bcipla\b"],
    "HINDUNILVR": [r"hindustan unilever", r"\bhul\b"],
    "ITC": [r"\bitc\b"],
    "TATASTEEL": [r"tata steel"],
    "HINDALCO": [r"hindalco"],
    "ONGC": [r"\bongc\b", r"oil and natural gas corp"],
    "BPCL": [r"\bbpcl\b", r"bharat petroleum"],
    "HAL": [r"hindustan aeronautics", r"\bhal\b"],
    "BEL": [r"bharat electronics", r"\bbel\b"],
    "HCLTECH": [r"hcl tech", r"hcl technologies"],
    "WIPRO": [r"\bwipro\b"]
}

# Sentiment Lexicon
BULLISH_KEYWORDS = [
    "surge", "surges", "jump", "jumps", "rally", "rallies", "growth", "record high",
    "profit jumps", "order win", "upgrade", "rate cut", "strong demand", "beat estimates",
    "expansion", "boost", "outperform", "dividend hike", "positive outlook"
]

BEARISH_KEYWORDS = [
    "fall", "falls", "plunge", "slump", "drop", "drops", "loss", "crash", "decline",
    "rate hike", "downgrade", "penalty", "probe", "warning letter", "inflation spikes",
    "misses estimates", "selloff", "weak guidance", "layoffs", "escalation", "strike"
]


def classify_news_categories(title: str, description: str = "") -> List[str]:
    """Identifies all matching market event categories."""
    text = f"{title} {description}".lower()
    categories = []
    for category, patterns in CATEGORY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                categories.append(category)
                break
    return categories if categories else ["Other"]


def extract_affected_tickers(title: str, description: str = "") -> List[str]:
    """Identifies specific Indian stock tickers referenced in news."""
    text = f"{title} {description}".lower()
    matched_tickers = []
    for ticker, patterns in INDIAN_TICKER_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                matched_tickers.append(ticker)
                break
    return matched_tickers


def estimate_sentiment_and_impact(
    title: str,
    description: str = "",
    categories: List[str] = None,
    reliability_score: int = 70
) -> Tuple[str, int]:
    """
    Computes preliminary sentiment (BULLISH/BEARISH/NEUTRAL) and an impact score (0-100)
    using deterministic financial keyword analysis.
    This acts as the pre-filter gate before invoking OpenAI in Phase 3.
    """
    text = f"{title} {description}".lower()
    categories = categories or []

    bullish_count = sum(1 for kw in BULLISH_KEYWORDS if kw in text)
    bearish_count = sum(1 for kw in BEARISH_KEYWORDS if kw in text)

    # Sentiment determination
    if bullish_count > bearish_count:
        sentiment = "BULLISH"
    elif bearish_count > bullish_count:
        sentiment = "BEARISH"
    else:
        sentiment = "NEUTRAL"

    # Base impact score from event category importance
    base_impact = 45
    high_impact_categories = {"RBI", "Earnings", "Crude oil", "War/conflict", "Interest rates", "Inflation", "M&A"}
    medium_impact_categories = {"Government policy", "SEBI", "Banking", "US markets", "Defence", "Currency"}

    for cat in categories:
        if cat in high_impact_categories:
            base_impact = max(base_impact, 75)
        elif cat in medium_impact_categories:
            base_impact = max(base_impact, 60)

    # Intensity modifier
    keyword_intensity = (bullish_count + bearish_count) * 4
    calculated_impact = base_impact + min(keyword_intensity, 20)

    # Reliability dampener
    if reliability_score < 70:
        calculated_impact = int(calculated_impact * 0.85)

    final_impact = max(10, min(95, calculated_impact))
    return sentiment, final_impact
