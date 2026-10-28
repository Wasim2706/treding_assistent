from typing import Dict, Any, List, Optional
from datetime import datetime


def escape_markdown(text: str) -> str:
    """Escapes special markdown characters for Telegram MarkdownV2 / V1."""
    if not text:
        return ""
    # Standard replacement for common special characters in V1 / clean text
    return text.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")


def get_sentiment_emoji(sentiment: str) -> str:
    s = (sentiment or "").upper()
    if s == "BULLISH":
        return "🟢"
    elif s == "BEARISH":
        return "🔴"
    else:
        return "🟡"


def format_welcome_message() -> str:
    return (
        "🤖 *Indian Stock Market AI Intelligence Bot*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Real-time Indian market intelligence, news analysis, technical confirmations, and paper-trading signals.\n\n"
        "⚡ *Quick Commands:*\n"
        "• /status — Indian market hours (IST) & session state\n"
        "• /news — Latest 5 summarized Indian market catalysts\n"
        "• /top — Top high-impact catalysts & trade setups\n"
        "• /signals — Active multi-factor trading signals\n"
        "• /watchlist — High-probability vs. No-Trade lists\n"
        "• /performance — Paper-trading win rate, P&L & metrics\n"
        "• /papertrade — Open virtual positions & P&L\n"
        "• /report — Daily Pre-Market Indian intelligence report\n"
        "• /help — Detailed usage & command guide\n\n"
        "⚠️ *Regulatory Disclaimer:*\n"
        "_This system operates in STRICT PAPER TRADING / SIGNAL-ONLY mode. "
        "Outputs are for quantitative decision-support only. No guaranteed returns. "
        "Not SEBI registered financial advice._"
    )


def format_help_message() -> str:
    return (
        "📖 *Command Reference Guide*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "• `/status` : Check NSE/BSE session (Pre-open, Regular, Closed), IST clock, and active worker status.\n"
        "• `/news` : View recent filtered Indian financial news with AI fact vs. speculation separation.\n"
        "• `/top` : Instant snapshot of highest-impact catalysts (Impact ≥ 70/100).\n"
        "• `/signals` : Multi-factor signals (News 35%, Tech 30%, Vol 15%, Market 10%, Sector 10%).\n"
        "• `/watchlist` : Active watchlists with technical pivot levels (Classic & Camarilla).\n"
        "• `/performance` : Verified paper-trading win rate, profit factor, and directional accuracy.\n"
        "• `/papertrade` : Inspect open virtual positions, trailing stop status, and simulated P&L.\n"
        "• `/report` : Read the latest pre-market Indian market outlook report.\n\n"
        "⚠️ _All trades are virtual simulations (0% real capital)._"
    )


def format_market_status_message(status: Dict[str, Any], overview: Optional[Dict[str, Any]] = None) -> str:
    session = status.get("session", "CLOSED")
    is_open = status.get("is_open", False)
    badge = "🟢 OPEN" if is_open else ("🟡 PRE-OPEN" if session == "PRE_OPEN" else "⚪ CLOSED")
    desc = status.get("session_description", "")
    ist = status.get("current_ist", "")
    next_s = status.get("next_session", "")

    msg = (
        f"🇮🇳 *Indian Stock Market Status: {badge}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Session:* {desc}\n"
        f"• *IST Time:* `{ist}`\n"
        f"• *Next Phase:* {next_s}\n"
    )

    if overview and "benchmarks" in overview:
        bm = overview["benchmarks"]
        nifty = bm.get("nifty50", {})
        bank = bm.get("bank_nifty", {})
        crude = bm.get("crude_oil", {})
        inr = bm.get("usd_inr", {})

        msg += (
            f"\n📊 *Major Benchmarks:*\n"
            f"• NIFTY 50: `₹{nifty.get('last_price', '--')}` ({nifty.get('change_pct', 0):+.2f}%)\n"
            f"• BANK NIFTY: `₹{bank.get('last_price', '--')}` ({bank.get('change_pct', 0):+.2f}%)\n"
            f"• Crude Oil: `${crude.get('last_price', '--')}` ({crude.get('change_pct', 0):+.2f}%)\n"
            f"• USD / INR: `₹{inr.get('last_price', '--')}` ({inr.get('change_pct', 0):+.2f}%)\n"
        )

    msg += "\n⚠️ _Paper-trading & decision-support only._"
    return msg


def format_news_item(article: Any, analysis: Optional[Any] = None) -> str:
    title = getattr(article, "title", "")
    source = getattr(article, "source", "Financial News")
    url = getattr(article, "url", "")

    if analysis:
        sentiment = getattr(analysis, "sentiment", "NEUTRAL")
        emoji = get_sentiment_emoji(sentiment)
        impact = getattr(analysis, "impact_score", 50)
        summary = getattr(analysis, "summary", "")
        facts = getattr(analysis, "confirmed_facts", []) or []
        stocks = getattr(analysis, "affected_stocks", []) or []
        sectors = getattr(analysis, "affected_sectors", []) or []

        tickers_str = ", ".join(stocks) if stocks else "General Market"
        sectors_str = ", ".join(sectors) if sectors else "Macro"

        msg = (
            f"{emoji} *{sentiment} CATALYST (Impact: {impact}/100)*\n"
            f"📰 *{title}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Source:* {source}\n"
            f"• *Affected Tickers:* `{tickers_str}`\n"
            f"• *Sector:* {sectors_str}\n\n"
            f"📝 *Summary:* {summary}\n"
        )

        if facts:
            msg += f"✅ *Confirmed Fact:* {facts[0]}\n"

        if url:
            msg += f"\n🔗 [Read Full Article]({url})\n"
    else:
        msg = (
            f"📰 *{title}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Source:* {source}\n"
            f"🔗 [Read Source]({url})\n"
        )

    msg += "\n⚠️ _Decision-support intelligence only._"
    return msg


def format_signal_alert(signal: Any) -> str:
    direction = getattr(signal, "direction", "WATCH")
    symbol = getattr(signal, "symbol", "")
    emoji = get_sentiment_emoji("BULLISH" if direction == "BUY" else ("BEARISH" if direction == "SELL" else "NEUTRAL"))

    entry_zone = getattr(signal, "entry_zone", "")
    entry_p = getattr(signal, "entry_price", None)
    sl = getattr(signal, "stop_loss", None)
    t1 = getattr(signal, "target_1", None)
    t2 = getattr(signal, "target_2", None)
    rr = getattr(signal, "risk_reward", "1:2.0")
    score = getattr(signal, "composite_score", 0.0)
    conf = getattr(signal, "confidence", 50)
    entry_w = getattr(signal, "entry_time_window", "")
    exit_w = getattr(signal, "exit_time_window", "")
    reasons = getattr(signal, "reasoning", "")
    invalid_if = getattr(signal, "invalidated_if", "")

    msg = (
        f"{emoji} *NEW TRADING SIGNAL: {direction} {symbol}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Conviction Score:* `{score}/100` (Confidence: {conf}%)\n"
        f"⚖️ *Risk / Reward:* `{rr}`\n\n"
        f"📍 *Trade Setup Levels:*\n"
        f"• Entry Zone: `{entry_zone}` (Current: ₹{entry_p})\n"
        f"• Stop Loss: `₹{sl}`\n"
        f"• Target 1: `₹{t1}`\n"
        f"• Target 2: `₹{t2}`\n\n"
        f"⏰ *Execution Windows:*\n"
        f"• Entry: {entry_w}\n"
        f"• Exit: {exit_w}\n\n"
        f"🔍 *Technical & Catalyst Rationale:*\n"
        f"{reasons}\n\n"
        f"🚫 *Invalidation Rule:*\n"
        f"{invalid_if}\n\n"
        f"⚠️ *PAPER TRADING / DECISION SUPPORT ONLY. NOT FINANCIAL ADVICE.*"
    )
    return msg


def format_paper_positions_summary(positions: List[Any], metrics: Optional[Any] = None) -> str:
    msg = (
        "💼 *Simulated Paper-Trading Portfolio*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    if metrics:
        total_pnl = getattr(metrics, "total_realized_pnl", 0.0)
        unrealized = getattr(metrics, "total_unrealized_pnl", 0.0)
        win_rate = getattr(metrics, "win_rate_pct", 0.0)
        p_factor = getattr(metrics, "profit_factor", 1.0)

        pnl_color = "+" if total_pnl >= 0 else ""
        msg += (
            f"• *Realized P&L:* `₹{pnl_color}{total_pnl:,.2f}`\n"
            f"• *Unrealized P&L:* `₹{unrealized:+,.2f}`\n"
            f"• *Win Rate:* `{win_rate:.1f}%` | *Profit Factor:* `{p_factor:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
        )

    if not positions:
        msg += "No open virtual positions at this time.\n"
    else:
        msg += f"📋 *Active Positions ({len(positions)}):*\n\n"
        for p in positions:
            sym = getattr(p, "symbol", "")
            direction = getattr(p, "direction", "BUY")
            qty = getattr(p, "quantity", 0)
            entry = getattr(p, "entry_price", 0.0)
            curr = getattr(p, "current_price", entry)
            unreal = getattr(p, "unrealized_pnl", 0.0)
            pnl_pct = getattr(p, "pnl_percentage", 0.0)
            sl = getattr(p, "stop_loss", 0.0)
            t1 = getattr(p, "target_1", 0.0)

            emoji = "🟢" if unreal >= 0 else "🔴"
            msg += (
                f"{emoji} *{direction} {sym}* ({qty} qty)\n"
                f"  Entry: `₹{entry}` | Current: `₹{curr}`\n"
                f"  P&L: `₹{unreal:+,.2f}` ({pnl_pct:+.2f}%)\n"
                f"  SL: `₹{sl}` | T1: `₹{t1}`\n\n"
            )

    msg += "⚠️ _Simulated virtual portfolio. Zero real capital deployed._"
    return msg
