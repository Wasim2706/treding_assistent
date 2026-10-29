import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.models.report import DailyReport, Alert
from app.services.reports.pre_market import pre_market_report_generator
from app.services.telegram.bot import telegram_bot_service
from app.services.telegram.formatter import format_pre_market_report_message
from app.core.security import validate_safety_text


@pytest.mark.asyncio
async def test_gather_global_cues():
    cues = await pre_market_report_generator.gather_global_cues()
    assert "sentiment" in cues
    assert cues["sentiment"] in ("BULLISH", "BEARISH", "NEUTRAL")
    assert "instruments" in cues
    assert "dow_jones" in cues["instruments"]
    assert "sp500" in cues["instruments"]
    assert "gift_nifty" in cues["instruments"]
    assert "crude_wti" in cues["instruments"]
    assert "usd_inr" in cues["instruments"]
    assert len(cues["summary_narrative"]) > 10


@pytest.mark.asyncio
async def test_calculate_index_outlook():
    mock_cues = {
        "sentiment": "BULLISH",
        "gift_nifty_change_pct": 0.45,
        "crude_change_pct": -0.8,
    }
    nifty_out, bank_out = await pre_market_report_generator.calculate_index_outlook(mock_cues)

    # NIFTY 50 checks
    assert nifty_out["symbol"] == "NIFTY 50"
    assert nifty_out["last_price"] > 0
    assert nifty_out["support_1"] < nifty_out["pivot"] < nifty_out["resistance_1"]
    assert nifty_out["sentiment"] in ("BULLISH", "BEARISH", "RANGEBOUND_NEUTRAL")
    assert "Positive Gap" in nifty_out["expected_open"]
    assert len(nifty_out["levels"]) > 5

    # BANK NIFTY checks
    assert bank_out["symbol"] == "BANK NIFTY"
    assert bank_out["last_price"] > 0
    assert bank_out["support_1"] < bank_out["pivot"] < bank_out["resistance_1"]
    assert bank_out["sentiment"] in ("BULLISH", "BEARISH", "RANGEBOUND_NEUTRAL")


def test_calculate_sector_bias():
    mock_cues_bullish_tech = {
        "crude_change_pct": -2.5,
        "instruments": {"nasdaq": {"change_pct": 1.2}}
    }
    bias = pre_market_report_generator.calculate_sector_bias(mock_cues_bullish_tech, [])
    assert any("Information Technology" in s for s in bias["outperforming_candidates"])
    assert any("Paints" in s for s in bias["outperforming_candidates"])

    mock_cues_high_oil = {
        "crude_change_pct": 3.5,
        "instruments": {"nasdaq": {"change_pct": -1.0}}
    }
    bias_oil = pre_market_report_generator.calculate_sector_bias(mock_cues_high_oil, [])
    assert any("Information Technology" in s for s in bias_oil["headwind_candidates"])
    assert any("Paints" in s for s in bias_oil["headwind_candidates"])
    assert any("Upstream Oil" in s for s in bias_oil["outperforming_candidates"])


@pytest.mark.asyncio
async def test_gather_watchlists(db_session):
    top_watch, no_trade_watch = await pre_market_report_generator.gather_watchlists(db_session)

    # Top Watchlist checks (3-5 stocks)
    assert 3 <= len(top_watch) <= 5
    for item in top_watch:
        assert item["direction"] in ("BUY", "SELL")
        assert item["entry_price"] > 0
        assert item["stop_loss"] is not None
        assert item["target_1"] is not None
        assert "1:" in item["risk_reward"]
        assert len(item["symbol"]) > 0

    # No-Trade Watchlist checks (2-4 stocks)
    assert 2 <= len(no_trade_watch) <= 4
    for item in no_trade_watch:
        assert len(item["symbol"]) > 0
        assert len(item["reason"]) > 10
        assert "technical_rule_triggered" in item


def test_synthesize_risk_warnings():
    warnings = pre_market_report_generator.synthesize_risk_warnings()
    assert len(warnings) >= 4
    # Must mention opening volatility window
    assert any("09:15" in w and "09:30" in w for w in warnings)
    # Must mention 15:15 intraday square off
    assert any("15:15" in w for w in warnings)
    # Must mention 2% capital risk
    assert any("2%" in w for w in warnings)


def test_build_markdown_report_and_safety():
    report_md = pre_market_report_generator.build_markdown_report(
        report_date="2026-10-29",
        global_cues={
            "sentiment": "BULLISH",
            "summary_narrative": "Global markets closed on a firm note overnight.",
            "instruments": {
                "dow_jones": {"last_price": 42500, "change_pct": 0.4},
                "sp500": {"last_price": 5820, "change_pct": 0.5},
                "nasdaq": {"last_price": 20400, "change_pct": 0.8},
                "gift_nifty": {"last_price": 24950, "change_pct": 0.4},
                "crude_wti": {"last_price": 78.4, "change_pct": -0.5},
                "usd_inr": {"last_price": 84.1, "change_pct": -0.05},
            }
        },
        catalysts=[
            {
                "headline": "US Tech Megacaps Post Strong Quarterly Numbers",
                "summary": "Enterprise cloud and AI spending sustained above consensus targets.",
                "source": "Reuters",
                "sentiment": "BULLISH",
                "impact_score": 82,
                "confirmed_facts": ["Revenue grew 14% YoY across leading hyperscalers."],
                "market_interpretation": ["Positive demand environment for Tier-1 Indian IT exporters."],
                "speculation": ["Speculation around accelerated GenAI consulting budgets."],
                "affected_sectors": ["Information Technology"],
                "affected_stocks": ["TCS", "INFY"],
            }
        ],
        nifty_outlook={
            "sentiment": "BULLISH",
            "last_price": 24850,
            "expected_open": "Positive Gap (+80 pts)",
            "pivot": 24820,
            "support_1": 24750,
            "support_2": 24680,
            "resistance_1": 24920,
            "resistance_2": 25000,
            "rsi": 58.2,
            "trend_bias": "BULLISH",
        },
        bank_nifty_outlook={
            "sentiment": "BULLISH",
            "last_price": 52400,
            "pivot": 52350,
            "support_1": 52100,
            "support_2": 51800,
            "resistance_1": 52700,
            "resistance_2": 53000,
        },
        sector_bias={
            "outperforming_candidates": ["Information Technology", "Banking & Financial Services"],
            "headwind_candidates": [],
            "neutral_candidates": ["FMCG", "Auto"],
        },
        top_watchlist=[
            {
                "symbol": "INFY",
                "direction": "BUY",
                "entry_zone": "₹1835 - ₹1845",
                "target_1": 1890,
                "target_2": 1930,
                "stop_loss": 1810,
                "risk_reward": "1:2.3",
                "confidence": 80,
                "catalyst_rationale": "Bullish US Tech cues and positive RSI divergence.",
                "technical_confirmation": "CONFIRMED",
            }
        ],
        no_trade_watchlist=[
            {
                "symbol": "ASIANPAINT",
                "composite_score": 45.0,
                "technical_rule_triggered": "Overhead 200 SMA Resistance",
                "reason": "Trading directly into descending long-term resistance band.",
            }
        ],
        risk_warnings=[
            "Avoid order placement in opening 09:15-09:30 volatility window.",
            "Square off all intraday paper positions before 15:15 IST.",
        ]
    )

    # Verify all 6 core sections exist
    assert "## 1. Global Overnight Summary" in report_md
    assert "## 2. Top Global & Domestic Catalysts" in report_md
    assert "## 3. Indian Market Outlook" in report_md
    assert "## 4. Top High-Conviction Stock Watchlist" in report_md
    assert "## 5. 'No-Trade' Watchlist" in report_md
    assert "## 6. Actionable Risk Warnings" in report_md

    # Epistemic integrity check
    assert "Confirmed Facts" in report_md
    assert "Market Interpretation" in report_md
    assert "Speculation" in report_md

    # Safety check: passes anti-guarantee validator
    validate_safety_text(report_md)


@pytest.mark.asyncio
async def test_generate_daily_report_persistence(db_session):
    result = await pre_market_report_generator.generate_daily_report(db_session)
    assert result["status"] == "success"
    assert "report_id" in result
    assert result["top_watchlist_count"] >= 3
    assert result["no_trade_watchlist_count"] >= 2

    # Query database
    rep_res = await db_session.execute(
        select(DailyReport).where(DailyReport.id == result["report_id"])
    )
    report = rep_res.scalars().first()
    assert report is not None
    assert report.report_type == "PRE_MARKET"
    assert report.is_published is True
    assert len(report.markdown_content) > 500

    # Check alert was created
    alert_res = await db_session.execute(
        select(Alert).where(Alert.alert_type == "PRE_MARKET")
    )
    alerts = alert_res.scalars().all()
    assert len(alerts) > 0


@pytest.mark.asyncio
async def test_telegram_pre_market_report_formatting(db_session):
    # Generate report
    result = await pre_market_report_generator.generate_daily_report(db_session)
    rep_res = await db_session.execute(
        select(DailyReport).where(DailyReport.id == result["report_id"])
    )
    report = rep_res.scalars().first()

    # Test formatter
    msg = format_pre_market_report_message(report)
    assert "PRE-MARKET REPORT" in msg
    assert "NIFTY 50" in msg
    assert "BANK NIFTY" in msg
    assert "Pivots:" in msg
    assert "Top High-Conviction Setups:" in msg
    assert "No-Trade Blocked Stocks:" in msg
    assert "Actionable Risk Warnings:" in msg

    # Test broadcast
    sent = await telegram_bot_service.broadcast_pre_market_report(report)
    assert sent is True

    # Test handle_report command
    cmd_msg = await telegram_bot_service.handle_report()
    assert "PRE-MARKET REPORT" in cmd_msg


@pytest.mark.asyncio
async def test_reports_api_endpoints(db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trigger report generation
        gen_resp = await client.post("/api/v1/reports/pre-market/generate")
        assert gen_resp.status_code == 200
        gen_data = gen_resp.json()
        assert gen_data["success"] is True
        assert gen_data["data"]["status"] == "success"

        # Fetch latest pre-market report
        latest_resp = await client.get("/api/v1/reports/pre-market/latest")
        assert latest_resp.status_code == 200
        latest_data = latest_resp.json()
        assert latest_data["success"] is True
        report = latest_data["data"]
        assert report is not None
        assert report["report_type"] == "PRE_MARKET"
        assert len(report["top_watchlist"]) >= 3
        assert len(report["no_trade_watchlist"]) >= 2
        assert len(report["markdown_content"]) > 200

        # List reports
        list_resp = await client.get("/api/v1/reports?page=1&page_size=5")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["success"] is True
        assert len(list_data["items"]) >= 1

        # List alerts
        alerts_resp = await client.get("/api/v1/reports/alerts?limit=10")
        assert alerts_resp.status_code == 200
        alerts_data = alerts_resp.json()
        assert alerts_data["success"] is True
        assert len(alerts_data["data"]) >= 1
