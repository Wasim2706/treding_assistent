import asyncio
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import select, desc

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.news import NewsArticle, NewsAnalysis
from app.models.signal import Signal
from app.models.paper_trading import PaperTrade
from app.models.report import DailyReport
from app.services.market_data.service import market_data_service
from app.services.paper_trading.engine import paper_trading_engine
from app.services.telegram.formatter import (
    format_welcome_message,
    format_help_message,
    format_market_status_message,
    format_news_item,
    format_signal_alert,
    format_paper_positions_summary,
    format_pre_market_report_message,
)

logger = logging.getLogger(__name__)


class TelegramBotService:
    """
    Asynchronous Telegram Bot Service providing interactive market commands,
    threshold-gated breaking catalyst alerts, and high-conviction signal dispatch.
    
    Operates safely in mock/disabled mode if TELEGRAM_BOT_TOKEN is not configured.
    """

    def __init__(self, bot_token: Optional[str] = None, default_chat_id: Optional[str] = None):
        self.token = bot_token if bot_token is not None else settings.TELEGRAM_BOT_TOKEN
        self.default_chat_id = default_chat_id if default_chat_id is not None else settings.TELEGRAM_CHAT_ID
        self.is_enabled = bool(self.token and len(self.token.strip()) > 5)

        self._bot = None
        if self.is_enabled:
            try:
                import telegram
                self._bot = telegram.Bot(token=self.token)
                logger.info("[TelegramBot] Initialized telegram Bot client successfully.")
            except Exception as e:
                logger.warning(f"[TelegramBot] Failed to initialize telegram client: {e}. Running in disabled mode.")
                self.is_enabled = False
        else:
            logger.info("[TelegramBot] No bot token provided. Telegram service operating in mock/logging mode.")

    async def send_message(
        self, 
        text: str, 
        chat_id: Optional[str] = None, 
        parse_mode: str = "Markdown"
    ) -> bool:
        """Sends a message to the specified chat or default broadcast channel."""
        target_chat = chat_id or self.default_chat_id
        if not target_chat:
            logger.debug(f"[TelegramBot] No chat_id provided. Mock output:\n{text}")
            return True

        if not self.is_enabled or not self._bot:
            logger.info(f"[TelegramBot (Mock)] Message to {target_chat}:\n{text}")
            return True

        try:
            await self._bot.send_message(
                chat_id=target_chat,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=False
            )
            return True
        except Exception as e:
            logger.error(f"[TelegramBot] Error sending message to {target_chat}: {e}")
            # Try plain text fallback if markdown parsing failed
            try:
                await self._bot.send_message(chat_id=target_chat, text=text, parse_mode=None)
                return True
            except Exception:
                return False

    async def handle_start(self, chat_id: Optional[str] = None) -> str:
        msg = format_welcome_message()
        if chat_id:
            await self.send_message(msg, chat_id=chat_id)
        return msg

    async def handle_help(self, chat_id: Optional[str] = None) -> str:
        msg = format_help_message()
        if chat_id:
            await self.send_message(msg, chat_id=chat_id)
        return msg

    async def handle_status(self, chat_id: Optional[str] = None) -> str:
        status_dict = await market_data_service.get_market_status()
        overview = await market_data_service.get_market_overview()
        msg = format_market_status_message(status_dict, overview)
        if chat_id:
            await self.send_message(msg, chat_id=chat_id)
        return msg

    async def handle_news(self, chat_id: Optional[str] = None, limit: int = 5) -> List[str]:
        messages = []
        async with AsyncSessionLocal() as db:
            query = (
                select(NewsArticle, NewsAnalysis)
                .outerjoin(NewsAnalysis, NewsArticle.id == NewsAnalysis.article_id)
                .order_by(desc(NewsArticle.published_at))
                .limit(limit)
            )
            res = await db.execute(query)
            articles = res.all()

            if not articles:
                no_news = "📰 *No recent news items logged yet.*"
                if chat_id:
                    await self.send_message(no_news, chat_id=chat_id)
                return [no_news]

            for art, ana in articles:
                item_msg = format_news_item(art, ana)
                messages.append(item_msg)
                if chat_id:
                    await self.send_message(item_msg, chat_id=chat_id)

        return messages

    async def handle_top(self, chat_id: Optional[str] = None) -> str:
        async with AsyncSessionLocal() as db:
            # Query top signals first
            sig_query = (
                select(Signal)
                .where(Signal.direction.in_(["BUY", "SELL"]))
                .order_by(desc(Signal.composite_score))
                .limit(3)
            )
            sig_res = await db.execute(sig_query)
            top_sigs = sig_res.scalars().all()

            if top_sigs:
                header = "🔥 *TOP HIGH-CONVICTION TRADE SETUPS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                items = [format_signal_alert(s) for s in top_sigs]
                full_msg = header + "\n\n".join(items)
            else:
                full_msg = "🔥 *Top Setups:*\nNo high-conviction BUY/SELL signals currently active. Watchlist mode engaged."

            if chat_id:
                await self.send_message(full_msg, chat_id=chat_id)
            return full_msg

    async def handle_signals(self, chat_id: Optional[str] = None, limit: int = 5) -> str:
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Signal).order_by(desc(Signal.created_at)).limit(limit))
            signals = res.scalars().all()

            if not signals:
                msg = "📡 *Active Signals:* None currently generated. Run /status to check engine."
            else:
                header = f"📡 *Latest Multi-Factor Signals ({len(signals)}):*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                items = [format_signal_alert(s) for s in signals]
                msg = header + "\n\n".join(items)

            if chat_id:
                await self.send_message(msg, chat_id=chat_id)
            return msg

    async def handle_watchlist(self, chat_id: Optional[str] = None) -> str:
        async with AsyncSessionLocal() as db:
            buy_res = await db.execute(select(Signal).where(Signal.direction == "BUY").limit(5))
            buys = buy_res.scalars().all()

            notrade_res = await db.execute(select(Signal).where(Signal.direction == "NO_TRADE").limit(5))
            no_trades = notrade_res.scalars().all()

            msg = "📋 *INDIAN MARKET WATCHLISTS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            msg += "🟢 *Confirmed High-Probability Setups:*\n"
            if buys:
                for b in buys:
                    msg += f"• *{b.symbol}*: Entry `{b.entry_zone}` | Target `₹{b.target_1}` | SL `₹{b.stop_loss}`\n"
            else:
                msg += "• No active confirmed setups.\n"

            msg += "\n🚫 *No-Trade Blocked Watchlist:*\n"
            if no_trades:
                for n in no_trades:
                    msg += f"• *{n.symbol}*: Conflict detected (Score: {n.composite_score}/100)\n"
            else:
                msg += "• No severe technical conflicts logged.\n"

            msg += "\n⚠️ _Paper trading & algorithmic support only._"

            if chat_id:
                await self.send_message(msg, chat_id=chat_id)
            return msg

    async def handle_performance(self, chat_id: Optional[str] = None) -> str:
        async with AsyncSessionLocal() as db:
            metrics = await paper_trading_engine.get_metrics(db)
            pos_res = await db.execute(select(PaperTrade).where(PaperTrade.status == "OPEN"))
            positions = pos_res.scalars().all()

            msg = format_paper_positions_summary(positions, metrics)
            if chat_id:
                await self.send_message(msg, chat_id=chat_id)
            return msg

    async def handle_papertrade(self, chat_id: Optional[str] = None) -> str:
        return await self.handle_performance(chat_id)

    async def handle_report(self, chat_id: Optional[str] = None) -> str:
        async with AsyncSessionLocal() as db:
            res = await db.execute(
                select(DailyReport)
                .where(DailyReport.report_type == "PRE_MARKET")
                .order_by(desc(DailyReport.created_at))
                .limit(1)
            )
            report = res.scalars().first()

            if not report:
                msg = "📑 *Daily Pre-Market Report:*\nNo report generated yet today. The pre-market report generates automatically at 08:30 IST or via `/report` trigger."
            else:
                msg = format_pre_market_report_message(report)

            if chat_id:
                await self.send_message(msg, chat_id=chat_id)
            return msg

    async def broadcast_breaking_news(self, article: Any, analysis: Any) -> bool:
        """Threshold-gated breaking catalyst alert (impact >= 70)."""
        impact = getattr(analysis, "impact_score", 0)
        if impact < settings.ALERT_IMPACT_THRESHOLD:
            return False

        msg = f"🚨 *BREAKING HIGH-IMPACT MARKET CATALYST*\n\n" + format_news_item(article, analysis)
        return await self.send_message(msg)

    async def broadcast_signal(self, signal: Any) -> bool:
        """Threshold-gated signal broadcast (conviction >= 70)."""
        if getattr(signal, "composite_score", 0) < 70.0 or getattr(signal, "direction", "") not in ("BUY", "SELL"):
            return False

        msg = format_signal_alert(signal)
        return await self.send_message(msg)

    async def broadcast_pre_market_report(self, report: Any) -> bool:
        """Dispatches formatted Indian market pre-open report to the broadcast channel."""
        msg = format_pre_market_report_message(report)
        return await self.send_message(msg)


telegram_bot_service = TelegramBotService()
