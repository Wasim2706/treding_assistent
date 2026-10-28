from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.paper_trading import PaperTrade
from app.models.signal import Signal
from app.schemas.paper_trading import PaperTradingMetrics
from app.services.market_data.service import market_data_service
from app.services.market_data.base import get_current_ist_time, clean_ticker


class PaperTradingEngine:
    """
    Virtual Paper Trading Engine operating strictly in simulation mode.
    NO REAL TRADES ARE EVER EXECUTED.
    
    Features:
    - 2% Capital Risk Position Sizing
    - Automated Target 1, Target 2, and Stop Loss Detection
    - Breakeven Trailing Stop when Target 1 is achieved
    - Maximum Adverse Excursion (MAE) and Maximum Favorable Excursion (MFE) tracking
    - EOD 15:15 IST Auto-Squareoff for intraday risk management
    """

    DEFAULT_PORTFOLIO_CAPITAL: float = 1_000_000.0  # ₹10 Lakhs Virtual Starting Capital
    MAX_CAPITAL_RISK_PCT: float = 0.02              # 2.0% Maximum Risk per Trade

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        portfolio_balance: float = DEFAULT_PORTFOLIO_CAPITAL
    ) -> int:
        """
        Calculates position quantity so maximum loss at stop_loss <= 2% of portfolio balance.
        """
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share <= 0:
            return 100

        max_risk_rupees = portfolio_balance * self.MAX_CAPITAL_RISK_PCT
        calculated_qty = int(max_risk_rupees / risk_per_share)
        return max(1, min(calculated_qty, 5000))

    async def open_position_from_signal(
        self,
        signal_id: int,
        db: AsyncSession,
        portfolio_balance: float = DEFAULT_PORTFOLIO_CAPITAL
    ) -> PaperTrade:
        """Opens a virtual position based on a generated Signal."""
        sig = await db.get(Signal, signal_id)
        if not sig:
            raise ValueError(f"Signal ID {signal_id} not found.")

        if sig.direction not in ("BUY", "SELL"):
            raise ValueError(f"Cannot execute paper trade for non-directional signal ({sig.direction}).")

        if not sig.entry_price or not sig.stop_loss or not sig.target_1:
            raise ValueError("Signal lacks entry, stop-loss, or target levels.")

        symbol = clean_ticker(sig.symbol)
        qty = self.calculate_position_size(sig.entry_price, sig.stop_loss, portfolio_balance)

        paper_trade = PaperTrade(
            signal_id=sig.id,
            symbol=symbol,
            direction=sig.direction,
            quantity=qty,
            entry_price=sig.entry_price,
            current_price=sig.entry_price,
            stop_loss=sig.stop_loss,
            target_1=sig.target_1,
            target_2=sig.target_2,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            pnl_percentage=0.0,
            max_adverse_excursion=0.0,
            max_favorable_excursion=0.0,
            status="OPEN",
            notes=f"Auto-opened from Signal #{sig.id} ({sig.direction} {symbol})"
        )

        sig.is_paper_traded = True
        sig.status = "TRIGGERED"

        db.add(paper_trade)
        await db.commit()
        await db.refresh(paper_trade)
        return paper_trade

    async def open_manual_trade(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        target_1: float,
        target_2: Optional[float],
        quantity: Optional[int],
        notes: Optional[str],
        db: AsyncSession,
        portfolio_balance: float = DEFAULT_PORTFOLIO_CAPITAL
    ) -> PaperTrade:
        """Opens a virtual trade entered manually by user."""
        clean = clean_ticker(symbol)
        dir_clean = direction.upper()
        if dir_clean not in ("BUY", "SELL"):
            raise ValueError("Direction must be BUY or SELL.")

        qty = quantity or self.calculate_position_size(entry_price, stop_loss, portfolio_balance)

        paper_trade = PaperTrade(
            symbol=clean,
            direction=dir_clean,
            quantity=qty,
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss=stop_loss,
            target_1=target_1,
            target_2=target_2,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            pnl_percentage=0.0,
            max_adverse_excursion=0.0,
            max_favorable_excursion=0.0,
            status="OPEN",
            notes=notes or f"Manual virtual trade: {dir_clean} {clean}"
        )

        db.add(paper_trade)
        await db.commit()
        await db.refresh(paper_trade)
        return paper_trade

    async def update_open_positions(
        self,
        db: AsyncSession,
        force_eod_squareoff: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates all OPEN paper trades against current market prices.
        Applies:
        - Target 1 / Target 2 hit detection
        - Stop Loss hit detection
        - Trailing stop movement to breakeven when Target 1 is hit
        - MAE & MFE tracking
        - 15:15 IST EOD auto square-off
        """
        res = await db.execute(select(PaperTrade).where(PaperTrade.status == "OPEN"))
        open_positions = res.scalars().all()

        ist_now = get_current_ist_time()
        is_eod_cutoff = force_eod_squareoff or (ist_now.hour == 15 and ist_now.minute >= 15)

        updated_count = 0
        closed_count = 0

        for trade in open_positions:
            try:
                quote = await market_data_service.get_quote(trade.symbol)
                curr_price = quote.get("last_price", trade.entry_price)
                trade.current_price = curr_price

                # Calculate P&L and %
                if trade.direction == "BUY":
                    unrealized = (curr_price - trade.entry_price) * trade.quantity
                    pnl_pct = ((curr_price - trade.entry_price) / trade.entry_price) * 100.0
                else:  # SELL
                    unrealized = (trade.entry_price - curr_price) * trade.quantity
                    pnl_pct = ((trade.entry_price - curr_price) / trade.entry_price) * 100.0

                trade.unrealized_pnl = round(unrealized, 2)
                trade.pnl_percentage = round(pnl_pct, 2)

                # MFE: Highest profit percentage achieved
                if pnl_pct > trade.max_favorable_excursion:
                    trade.max_favorable_excursion = round(pnl_pct, 2)

                # MAE: Deepest drawdown percentage experienced (negative number)
                if pnl_pct < trade.max_adverse_excursion:
                    trade.max_adverse_excursion = round(pnl_pct, 2)

                # 1. Stop Loss Hit Check
                is_sl_hit = False
                if trade.direction == "BUY" and curr_price <= trade.stop_loss:
                    is_sl_hit = True
                elif trade.direction == "SELL" and curr_price >= trade.stop_loss:
                    is_sl_hit = True

                if is_sl_hit:
                    await self._close_trade_internal(
                        trade=trade,
                        exit_price=trade.stop_loss,
                        status="STOPPED_OUT",
                        reason="STOP_LOSS_HIT"
                    )
                    closed_count += 1
                    continue

                # 2. Target 2 Hit Check (Full Profit Target)
                if trade.target_2:
                    is_t2_hit = False
                    if trade.direction == "BUY" and curr_price >= trade.target_2:
                        is_t2_hit = True
                    elif trade.direction == "SELL" and curr_price <= trade.target_2:
                        is_t2_hit = True

                    if is_t2_hit:
                        await self._close_trade_internal(
                            trade=trade,
                            exit_price=trade.target_2,
                            status="TARGET_REACHED",
                            reason="TARGET_2_HIT"
                        )
                        closed_count += 1
                        continue

                # 3. Target 1 Hit Check (Move Stop Loss to Breakeven)
                is_t1_hit = False
                if trade.direction == "BUY" and curr_price >= trade.target_1:
                    is_t1_hit = True
                elif trade.direction == "SELL" and curr_price <= trade.target_1:
                    is_t1_hit = True

                if is_t1_hit:
                    # Protect profit by trailing stop loss to entry price (breakeven)
                    if trade.direction == "BUY" and trade.stop_loss < trade.entry_price:
                        trade.stop_loss = trade.entry_price
                        trade.notes = (trade.notes or "") + " [Target 1 hit: Stop moved to Break-even]"
                    elif trade.direction == "SELL" and trade.stop_loss > trade.entry_price:
                        trade.stop_loss = trade.entry_price
                        trade.notes = (trade.notes or "") + " [Target 1 hit: Stop moved to Break-even]"

                # 4. EOD Cutoff (15:15 IST)
                if is_eod_cutoff:
                    await self._close_trade_internal(
                        trade=trade,
                        exit_price=curr_price,
                        status="CLOSED",
                        reason="EOD_SQUAREOFF"
                    )
                    closed_count += 1
                    continue

                updated_count += 1

            except Exception as e:
                pass

        await db.commit()
        return {
            "open_positions_evaluated": len(open_positions),
            "updated_active": updated_count,
            "closed_trades": closed_count
        }

    async def _close_trade_internal(
        self,
        trade: PaperTrade,
        exit_price: float,
        status: str,
        reason: str
    ) -> None:
        """Internal helper to finalize trade metrics."""
        trade.exit_price = exit_price
        trade.current_price = exit_price
        trade.status = status
        trade.exit_reason = reason
        trade.exited_at = datetime.now(timezone.utc)

        if trade.direction == "BUY":
            realized = (exit_price - trade.entry_price) * trade.quantity
            pnl_pct = ((exit_price - trade.entry_price) / trade.entry_price) * 100.0
        else:  # SELL
            realized = (trade.entry_price - exit_price) * trade.quantity
            pnl_pct = ((trade.entry_price - exit_price) / trade.entry_price) * 100.0

        trade.realized_pnl = round(realized, 2)
        trade.unrealized_pnl = 0.0
        trade.pnl_percentage = round(pnl_pct, 2)

    async def close_position_manually(
        self,
        trade_id: int,
        db: AsyncSession,
        exit_price: Optional[float] = None,
        reason: str = "MANUAL_EXIT"
    ) -> PaperTrade:
        """Manually closes an open paper trade."""
        trade = await db.get(PaperTrade, trade_id)
        if not trade:
            raise ValueError(f"Paper trade {trade_id} not found.")

        if trade.status != "OPEN":
            raise ValueError(f"Paper trade {trade_id} is already closed ({trade.status}).")

        if exit_price is None:
            quote = await market_data_service.get_quote(trade.symbol)
            exit_price = quote.get("last_price", trade.entry_price)

        await self._close_trade_internal(
            trade=trade,
            exit_price=exit_price,
            status="CLOSED",
            reason=reason
        )
        await db.commit()
        await db.refresh(trade)
        return trade

    async def get_metrics(self, db: AsyncSession) -> PaperTradingMetrics:
        """Calculates portfolio performance metrics across all paper trades."""
        res = await db.execute(select(PaperTrade))
        all_trades = res.scalars().all()

        total = len(all_trades)
        open_positions = sum(1 for t in all_trades if t.status == "OPEN")
        closed_trades = sum(1 for t in all_trades if t.status != "OPEN")

        winning_trades = sum(1 for t in all_trades if t.status != "OPEN" and t.realized_pnl > 0)
        losing_trades = sum(1 for t in all_trades if t.status != "OPEN" and t.realized_pnl < 0)

        win_rate = (winning_trades / closed_trades * 100.0) if closed_trades > 0 else 0.0
        loss_rate = (losing_trades / closed_trades * 100.0) if closed_trades > 0 else 0.0

        total_realized = sum(t.realized_pnl for t in all_trades if t.status != "OPEN")
        total_unrealized = sum(t.unrealized_pnl for t in all_trades if t.status == "OPEN")

        gross_profit = sum(t.realized_pnl for t in all_trades if t.status != "OPEN" and t.realized_pnl > 0)
        gross_loss = abs(sum(t.realized_pnl for t in all_trades if t.status != "OPEN" and t.realized_pnl < 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)

        closed_pnl_pcts = [t.pnl_percentage for t in all_trades if t.status != "OPEN"]
        avg_return = (sum(closed_pnl_pcts) / len(closed_pnl_pcts)) if closed_pnl_pcts else 0.0

        # Calculate max drawdown percentage from closed trades
        running_equity = 1_000_000.0
        peak = running_equity
        max_dd = 0.0
        for t in all_trades:
            if t.status != "OPEN":
                running_equity += t.realized_pnl
                if running_equity > peak:
                    peak = running_equity
                dd = ((peak - running_equity) / peak) * 100.0 if peak > 0 else 0.0
                if dd > max_dd:
                    max_dd = dd

        return PaperTradingMetrics(
            total_trades=total,
            open_positions=open_positions,
            closed_trades=closed_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate_pct=round(win_rate, 2),
            loss_rate_pct=round(loss_rate, 2),
            total_realized_pnl=round(total_realized, 2),
            total_unrealized_pnl=round(total_unrealized, 2),
            profit_factor=round(profit_factor, 2),
            average_trade_return_pct=round(avg_return, 2),
            max_drawdown_pct=round(max_dd, 2)
        )


paper_trading_engine = PaperTradingEngine()
