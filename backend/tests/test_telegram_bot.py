import pytest
from app.services.telegram.bot import TelegramBotService


@pytest.mark.asyncio
async def test_telegram_bot_disabled_mode():
    bot = TelegramBotService(bot_token="")
    assert bot.is_enabled is False
    res = await bot.send_message("Test message")
    assert res is True


@pytest.mark.asyncio
async def test_telegram_command_handlers():
    bot = TelegramBotService(bot_token="")

    start_msg = await bot.handle_start()
    assert "Indian Stock Market" in start_msg
    assert "/status" in start_msg

    help_msg = await bot.handle_help()
    assert "/signals" in help_msg

    status_msg = await bot.handle_status()
    assert "Indian Stock Market Status" in status_msg

    news_msgs = await bot.handle_news(limit=3)
    assert isinstance(news_msgs, list)
    assert len(news_msgs) > 0

    top_msg = await bot.handle_top()
    assert "top" in top_msg.lower()

    signals_msg = await bot.handle_signals()
    assert "Signals" in signals_msg

    watchlist_msg = await bot.handle_watchlist()
    assert "WATCHLISTS" in watchlist_msg

    perf_msg = await bot.handle_performance()
    assert "Paper-Trading Portfolio" in perf_msg

    rep_msg = await bot.handle_report()
    assert "Report" in rep_msg


@pytest.mark.asyncio
async def test_telegram_broadcast_breaking_news_threshold():
    bot = TelegramBotService(bot_token="")

    class DummyArticle:
        title = "RBI Unexpected 50bps Repo Rate Cut"
        source = "Livemint"
        url = "https://livemint.com/rbi"

    class HighImpactAnalysis:
        impact_score = 85
        sentiment = "BULLISH"
        summary = "RBI cuts policy rate by 50bps to stimulate manufacturing."
        confirmed_facts = ["Repo rate reduced to 6.0%"]
        affected_stocks = ["HDFCBANK", "ICICIBANK"]
        affected_sectors = ["Banking & Financial Services"]

    class LowImpactAnalysis:
        impact_score = 45
        sentiment = "NEUTRAL"
        summary = "Minor board appointment."
        confirmed_facts = []
        affected_stocks = []
        affected_sectors = []

    # High impact (>= 70) should broadcast
    res_high = await bot.broadcast_breaking_news(DummyArticle(), HighImpactAnalysis())
    assert res_high is True

    # Low impact (< 70) should NOT broadcast
    res_low = await bot.broadcast_breaking_news(DummyArticle(), LowImpactAnalysis())
    assert res_low is False


@pytest.mark.asyncio
async def test_telegram_broadcast_signal_threshold():
    bot = TelegramBotService(bot_token="")

    class HighConvictionSignal:
        direction = "BUY"
        symbol = "RELIANCE"
        composite_score = 82.0
        confidence = 85
        entry_zone = "₹2940 - ₹2960"
        entry_price = 2950.0
        stop_loss = 2890.0
        target_1 = 3040.0
        target_2 = 3120.0
        risk_reward = "1:2.8"
        entry_time_window = "Post-09:30"
        exit_time_window = "15:15"
        reasoning = "Test setup"
        invalidated_if = "Breach"

    class LowConvictionSignal:
        direction = "WATCH"
        symbol = "INFY"
        composite_score = 55.0
        confidence = 55

    res_high = await bot.broadcast_signal(HighConvictionSignal())
    assert res_high is True

    res_low = await bot.broadcast_signal(LowConvictionSignal())
    assert res_low is False
