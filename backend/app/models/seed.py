from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.market import Sector, Stock
from app.models.system import SystemSetting
from app.core.logging import logger

INITIAL_SECTORS = [
    {
        "name": "Banking & Financial Services",
        "description": "Public and private commercial banks and NBFCs",
        "sensitivities": {
            "rbi_rate_cut": "BULLISH",
            "rbi_rate_hike": "BEARISH",
            "gdp_growth_up": "BULLISH",
            "inflation_spike": "NEUTRAL_TO_BEARISH"
        }
    },
    {
        "name": "Information Technology",
        "description": "IT services, SaaS, consulting and enterprise software",
        "sensitivities": {
            "us_markets_up": "BULLISH",
            "us_markets_down": "BEARISH",
            "us_tech_weakness": "BEARISH",
            "inr_depreciation": "BULLISH",
            "inr_appreciation": "BEARISH"
        }
    },
    {
        "name": "Oil, Gas & Energy",
        "description": "Upstream exploration, refining, marketing, and power utilities",
        "sensitivities": {
            "crude_oil_up": "BULLISH_UPSTREAM_BEARISH_DOWNSTREAM",
            "crude_oil_down": "BEARISH_UPSTREAM_BULLISH_DOWNSTREAM",
            "opec_output_cut": "BULLISH"
        }
    },
    {
        "name": "Automobile & Auto Components",
        "description": "Passenger vehicles, commercial vehicles, 2-wheelers and tyres",
        "sensitivities": {
            "crude_oil_up": "BEARISH",
            "crude_oil_down": "BULLISH",
            "rbi_rate_cut": "BULLISH",
            "steel_price_rise": "BEARISH"
        }
    },
    {
        "name": "Paints & Specialty Chemicals",
        "description": "Decorative paints, coatings, and specialty chemical derivatives",
        "sensitivities": {
            "crude_oil_up": "BEARISH",
            "crude_oil_down": "BULLISH"
        }
    },
    {
        "name": "Aviation",
        "description": "Commercial passenger airlines and air logistics",
        "sensitivities": {
            "crude_oil_up": "BEARISH",
            "crude_oil_down": "BULLISH",
            "atf_tax_cut": "BULLISH"
        }
    },
    {
        "name": "Gems, Jewellery & Gold Loans",
        "description": "Gold retailers, ornament makers, and gold collateral NBFCs",
        "sensitivities": {
            "gold_up": "BULLISH",
            "gold_down": "BEARISH",
            "gold_import_duty_cut": "BULLISH"
        }
    },
    {
        "name": "Pharmaceuticals & Healthcare",
        "description": "Generic formulations, APIs, hospitals and diagnostics",
        "sensitivities": {
            "us_fda_approvals": "BULLISH",
            "us_fda_warning_letters": "BEARISH",
            "inr_depreciation": "BULLISH"
        }
    },
    {
        "name": "Fast-Moving Consumer Goods (FMCG)",
        "description": "Household products, packaged food, personal care",
        "sensitivities": {
            "monsoon_normal": "BULLISH",
            "rural_demand_rise": "BULLISH",
            "raw_material_inflation": "BEARISH"
        }
    },
    {
        "name": "Metals & Mining",
        "description": "Steel, aluminum, zinc, copper and mining enterprises",
        "sensitivities": {
            "china_stimulus": "BULLISH",
            "china_slowdown": "BEARISH",
            "global_commodity_rally": "BULLISH"
        }
    },
    {
        "name": "Defence & Aerospace",
        "description": "Defence electronics, shipyards, missile systems",
        "sensitivities": {
            "defence_budget_hike": "BULLISH",
            "make_in_india_order": "BULLISH",
            "geopolitical_tension": "BULLISH"
        }
    }
]

INITIAL_STOCKS = [
    # Banking
    {"symbol": "HDFCBANK.NS", "exchange_ticker": "HDFCBANK", "company_name": "HDFC Bank Ltd", "sector": "Banking & Financial Services", "is_nifty50": True, "is_bank_nifty": True},
    {"symbol": "ICICIBANK.NS", "exchange_ticker": "ICICIBANK", "company_name": "ICICI Bank Ltd", "sector": "Banking & Financial Services", "is_nifty50": True, "is_bank_nifty": True},
    {"symbol": "SBIN.NS", "exchange_ticker": "SBIN", "company_name": "State Bank of India", "sector": "Banking & Financial Services", "is_nifty50": True, "is_bank_nifty": True},
    {"symbol": "KOTAKBANK.NS", "exchange_ticker": "KOTAKBANK", "company_name": "Kotak Mahindra Bank Ltd", "sector": "Banking & Financial Services", "is_nifty50": True, "is_bank_nifty": True},
    {"symbol": "AXISBANK.NS", "exchange_ticker": "AXISBANK", "company_name": "Axis Bank Ltd", "sector": "Banking & Financial Services", "is_nifty50": True, "is_bank_nifty": True},
    {"symbol": "BAJFINANCE.NS", "exchange_ticker": "BAJFINANCE", "company_name": "Bajaj Finance Ltd", "sector": "Banking & Financial Services", "is_nifty50": True, "is_bank_nifty": False},

    # IT
    {"symbol": "TCS.NS", "exchange_ticker": "TCS", "company_name": "Tata Consultancy Services Ltd", "sector": "Information Technology", "is_nifty50": True, "is_bank_nifty": False},
    {"symbol": "INFY.NS", "exchange_ticker": "INFY", "company_name": "Infosys Ltd", "sector": "Information Technology", "is_nifty50": True, "is_bank_nifty": False},
    {"symbol": "HCLTECH.NS", "exchange_ticker": "HCLTECH", "company_name": "HCL Technologies Ltd", "sector": "Information Technology", "is_nifty50": True, "is_bank_nifty": False},
    {"symbol": "WIPRO.NS", "exchange_ticker": "WIPRO", "company_name": "Wipro Ltd", "sector": "Information Technology", "is_nifty50": True, "is_bank_nifty": False},

    # Energy & Oil
    {"symbol": "RELIANCE.NS", "exchange_ticker": "RELIANCE", "company_name": "Reliance Industries Ltd", "sector": "Oil, Gas & Energy", "is_nifty50": True, "is_bank_nifty": False},
    {"symbol": "ONGC.NS", "exchange_ticker": "ONGC", "company_name": "Oil and Natural Gas Corporation Ltd", "sector": "Oil, Gas & Energy", "is_nifty50": True, "is_bank_nifty": False},
    {"symbol": "BPCL.NS", "exchange_ticker": "BPCL", "company_name": "Bharat Petroleum Corporation Ltd", "sector": "Oil, Gas & Energy", "is_nifty50": True, "is_bank_nifty": False},

    # Auto
    {"symbol": "TATAMOTORS.NS", "exchange_ticker": "TATAMOTORS", "company_name": "Tata Motors Passenger Vehicles Ltd", "sector": "Automobile & Auto Components", "is_nifty50": True, "is_bank_nifty": False},
    {"symbol": "MARUTI.NS", "exchange_ticker": "MARUTI", "company_name": "Maruti Suzuki India Ltd", "sector": "Automobile & Auto Components", "is_nifty50": True, "is_bank_nifty": False},
    {"symbol": "M&M.NS", "exchange_ticker": "M&M", "company_name": "Mahindra & Mahindra Ltd", "sector": "Automobile & Auto Components", "is_nifty50": True, "is_bank_nifty": False},

    # Paints & Airlines (Crude oil beneficiaries/victims)
    {"symbol": "ASIANPAINT.NS", "exchange_ticker": "ASIANPAINT", "company_name": "Asian Paints Ltd", "sector": "Paints & Specialty Chemicals", "is_nifty50": True, "is_bank_nifty": False},
    {"symbol": "BERGEPAINT.NS", "exchange_ticker": "BERGEPAINT", "company_name": "Berger Paints India Ltd", "sector": "Paints & Specialty Chemicals", "is_nifty50": False, "is_bank_nifty": False},
    {"symbol": "INDIGO.NS", "exchange_ticker": "INDIGO", "company_name": "InterGlobe Aviation Ltd", "sector": "Aviation", "is_nifty50": False, "is_bank_nifty": False},

    # Jewellery & Gold
    {"symbol": "TITAN.NS", "exchange_ticker": "TITAN", "company_name": "Titan Company Ltd", "sector": "Gems, Jewellery & Gold Loans", "is_nifty50": True, "is_bank_nifty": False},
    {"symbol": "MUTHOOTFIN.NS", "exchange_ticker": "MUTHOOTFIN", "company_name": "Muthoot Finance Ltd", "sector": "Gems, Jewellery & Gold Loans", "is_nifty50": False, "is_bank_nifty": False},

    # Pharma
    {"symbol": "SUNPHARMA.NS", "exchange_ticker": "SUNPHARMA", "company_name": "Sun Pharmaceutical Industries Ltd", "sector": "Pharmaceuticals & Healthcare", "is_nifty50": True, "is_bank_nifty": False},
    {"symbol": "CIPLA.NS", "exchange_ticker": "CIPLA", "company_name": "Cipla Ltd", "sector": "Pharmaceuticals & Healthcare", "is_nifty50": True, "is_bank_nifty": False},

    # FMCG
    {"symbol": "HINDUNILVR.NS", "exchange_ticker": "HINDUNILVR", "company_name": "Hindustan Unilever Ltd", "sector": "Fast-Moving Consumer Goods (FMCG)", "is_nifty50": True, "is_bank_nifty": False},
    {"symbol": "ITC.NS", "exchange_ticker": "ITC", "company_name": "ITC Ltd", "sector": "Fast-Moving Consumer Goods (FMCG)", "is_nifty50": True, "is_bank_nifty": False},

    # Metals
    {"symbol": "TATASTEEL.NS", "exchange_ticker": "TATASTEEL", "company_name": "Tata Steel Ltd", "sector": "Metals & Mining", "is_nifty50": True, "is_bank_nifty": False},
    {"symbol": "HINDALCO.NS", "exchange_ticker": "HINDALCO", "company_name": "Hindalco Industries Ltd", "sector": "Metals & Mining", "is_nifty50": True, "is_bank_nifty": False},

    # Defence
    {"symbol": "HAL.NS", "exchange_ticker": "HAL", "company_name": "Hindustan Aeronautics Ltd", "sector": "Defence & Aerospace", "is_nifty50": False, "is_bank_nifty": False},
    {"symbol": "BEL.NS", "exchange_ticker": "BEL", "company_name": "Bharat Electronics Ltd", "sector": "Defence & Aerospace", "is_nifty50": True, "is_bank_nifty": False}
]


async def seed_initial_market_data(session: AsyncSession) -> None:
    """Seeds baseline Indian sectors and representative stocks if empty."""
    # Check if sectors exist
    existing_sector = await session.execute(select(Sector).limit(1))
    if existing_sector.scalars().first():
        return

    logger.info("Seeding initial Indian market sectors and top stocks...")
    sector_map = {}
    for sec_data in INITIAL_SECTORS:
        sec = Sector(
            name=sec_data["name"],
            description=sec_data["description"],
            sensitivities=sec_data["sensitivities"]
        )
        session.add(sec)
        await session.flush()
        sector_map[sec.name] = sec.id

    for stock_data in INITIAL_STOCKS:
        sector_id = sector_map.get(stock_data["sector"])
        stk = Stock(
            symbol=stock_data["symbol"],
            exchange_ticker=stock_data["exchange_ticker"],
            company_name=stock_data["company_name"],
            sector_id=sector_id,
            is_nifty50=stock_data["is_nifty50"],
            is_bank_nifty=stock_data["is_bank_nifty"],
            is_active=True
        )
        session.add(stk)

    # Seed initial system settings
    default_settings = [
        {"key": "SIGNAL_WEIGHTS", "value": {"news": 0.35, "technical": 0.30, "volume": 0.15, "market": 0.10, "sector": 0.10}, "desc": "Configurable signal scoring weights"},
        {"key": "CONFIDENCE_THRESHOLDS", "value": {"min_trade_confidence": 65, "telegram_alert_impact": 70}, "desc": "Signal and alert thresholds"},
        {"key": "AI_COST_CONTROLS", "value": {"max_articles_cycle": 10, "daily_budget_usd": 5.0}, "desc": "OpenAI rate & cost caps"}
    ]
    for s in default_settings:
        setting = SystemSetting(key=s["key"], value_json=s["value"], description=s["desc"])
        session.add(setting)

    await session.commit()
    logger.info(f"Seeded {len(INITIAL_SECTORS)} sectors, {len(INITIAL_STOCKS)} stocks, and system settings.")
