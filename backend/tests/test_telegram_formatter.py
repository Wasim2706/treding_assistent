import pytest
from app.services.telegram.formatter import (
    escape_markdown,
    get_sentiment_emoji,
    format_welcome_message,
    format_help_message,
    format_market_status_message,
    format_news_item,
    format_signal_alert,
    format_paper_positions_summary,
)
from app.core.security import FORBIDDEN_SAFETY_PHRASES


def test_escape_markdown():
    raw = "TCS_NSE *High* [Risk] `Price`"
    escaped = escape_markdown(raw)
    assert "\\_" in escaped
    assert "\\*" in escaped
    assert "\\[" in escaped
    assert "\\`" in escaped


def test_sentiment_emojis():
    assert get_sentiment_emoji("BULLISH") == "🟢"
    assert get_sentiment_emoji("BEARISH") == "🔴"
    assert get_sentiment_emoji("NEUTRAL") == "🟡"
    assert get_sentiment_emoji("UNKNOWN") == "🟡"


def test_welcome_message_content_and_safety():
    msg = format_welcome_message()
    assert "/status" in msg
    assert "/signals" in msg
    assert "/papertrade" in msg
    assert "PAPER TRADING" in msg

    # Anti-guarantee check
    for phrase in FORBIDDEN_SAFETY_PHRASES:
        assert phrase not in msg.lower()


def test_help_message_content():
    msg = format_help_message()
    assert "/status" in msg
    assert "/news" in msg
    assert "/top" in msg
    assert "/watchlist" in msg
    assert "/performance" in msg


def test_market_status_formatting():
    status = {
        "session": "REGULAR",
        "is_open": True,
        "session_description": "Trading Open",
        "current_ist": "2026-10-28 11:30:00 IST",
        "next_session": "Market Closes at 15:30 IST"
    }
    overview = {
        "benchmarks": {
            "nifty50": {"last_price": 24850.0, "change_pct": 0.65},
            "bank_nifty": {"last_price": 52400.0, "change_pct": -0.20},
            "crude_oil": {"last_price": 78.4, "change_pct": 1.1},
            "usd_inr": {"last_price": 84.1, "change_pct": 0.05}
        }
    }
    msg = format_market_status_message(status, overview)
    assert "🟢 OPEN" in msg
    assert "24850" in msg
    assert "NIFTY 50" in msg


def test_signal_alert_formatting():
    class DummySignal:
        direction = "BUY"
        symbol = "RELIANCE"
        entry_zone = "₹2940 - ₹2960"
        entry_price = 2950.0
        stop_loss = 2890.0
        target_1 = 3040.0
        target_2 = 3120.0
        risk_reward = "1:2.8"
        composite_score = 82.0
        confidence = 85
        entry_time_window = "Post-09:30 IST"
        exit_time_window = "15:15 IST"
        reasoning = "Strong catalyst alignment and 20 SMA breakout."
        invalidated_if = "15m close below ₹2890"

    msg = format_signal_alert(DummySignal())
    assert "BUY RELIANCE" in msg
    assert "₹2890" in msg
    assert "₹3040" in msg
    assert "1:2.8" in msg
    assert "PAPER TRADING / DECISION SUPPORT ONLY" in msg


def test_paper_positions_formatting():
    class DummyPosition:
        symbol = "TCS"
        direction = "BUY"
        quantity = 50
        entry_price = 3900.0
        current_price = 3950.0
        unrealized_pnl = 2500.0
        pnl_percentage = 1.28
        stop_loss = 3820.0
        target_1 = 4020.0

    class DummyMetrics:
        total_realized_pnl = 15000.0
        total_unrealized_pnl = 2500.0
        win_rate_pct = 68.5
        profit_factor = 2.45

    msg = format_paper_positions_summary([DummyPosition()], DummyMetrics())
    assert "TCS" in msg
    assert "₹+15,000.00" in msg
    assert "68.5%" in msg
    assert "₹+2,500.00" in msg
