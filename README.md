# AI-Powered Indian Stock Market Intelligence & Trading Decision Support

[![Mode](https://img.shields.io/badge/Mode-PAPER%20TRADING%20%2F%20SIGNAL%20ONLY-emerald)](#important-trading-safety-rules)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.13-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14%20(App%20Router)-black)](https://nextjs.org)

> **IMPORTANT TRADING SAFETY NOTICE**  
> This application operates strictly in **PAPER TRADING / SIGNAL-ONLY mode**. It does **NOT** place real trades automatically. Real order execution is permanently disabled by system architecture. Predictions and signals are probabilistic algorithmic estimates for educational decision-support only. The system **NEVER** claims guaranteed returns or 100% accuracy.

---

## Architecture Overview

```mermaid
flowchart TD
    subgraph DataCollection [5-Minute News & Market Cycle]
        A[News Providers: NewsAPI / Finnhub / RSS] --> B[Deduplication & Article Fingerprinting]
        B --> C[OpenAI Structured Analysis & Classification]
        C --> D[Indian Market Sector Sensitivity Matrix]
    end

    subgraph TechnicalConfirmation [Market Data Engine]
        M[NSE / Yahoo Finance Market Feeds] --> T[Indicators: 20/50/200 SMA, 20 EMA, RSI, MACD, ATR, VWAP]
    end

    subgraph DecisionSupportEngine [Deterministic Multi-Factor Signal Engine]
        D --> S[Weighted Signal Scoring]
        T --> S
        S -->|Weights: News 35%, Tech 30%, Vol 15%, Market 10%, Sector 10%| E{Confidence >= 65% & Confirmation?}
        E -->|Yes| SIG[BUY / SELL / WATCH Signal + Trading Window]
        E -->|Conflict / Insufficient Data| NT[NO TRADE Safe Default]
    end

    subgraph OutputChannels [Distribution & Tracking]
        SIG --> PT[Paper Trading Simulation: P&L, MAE, MFE]
        SIG --> DB[(PostgreSQL Database)]
        SIG --> TG[Telegram Alert Bot]
        SIG --> DASH[Next.js Responsive Dashboard]
        DB --> EVAL[Prediction Calibration & Accuracy Evaluation]
    end
```

---

## Complete Project File Tree

```
Trading Asistent/
├── .env.example                       # Complete environment variable template
├── .env                               # Local active environment configuration
├── docker-compose.yml                 # Local multi-container orchestration
├── render.yaml                        # Production Render Blueprint configuration
├── README.md                          # Documentation and run instructions
├── docker/
│   ├── Dockerfile.backend             # FastAPI production image
│   ├── Dockerfile.worker              # Background worker image
│   └── Dockerfile.frontend            # Next.js multi-stage build image
├── backend/
│   ├── requirements.txt               # Pinned Python dependencies
│   ├── run.py                         # Local backend execution script
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app factory, CORS, security middlewares
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic v2 BaseSettings & validation
│   │   │   ├── database.py            # SQLAlchemy 2.0 async engine & session
│   │   │   ├── logging.py             # Structured logging formatter
│   │   │   └── security.py            # Safety checks & prohibited phrase guards
│   │   ├── models/
│   │   │   ├── base.py                # Base declarative & timestamp mixins
│   │   │   ├── market.py              # Stock, Sector, MarketDataSnapshot
│   │   │   ├── news.py                # NewsArticle, NewsAnalysis, NewsEntity
│   │   │   ├── signal.py              # Signal with multi-factor breakdown
│   │   │   ├── paper_trading.py       # PaperTrade simulation tracking
│   │   │   ├── prediction.py          # PredictionResult evaluation records
│   │   │   ├── report.py              # DailyReport and Alert
│   │   │   ├── system.py              # SystemLog, ApiUsage, SystemSetting, User
│   │   │   └── seed.py                # Indian sectors & NIFTY 50 seed data
│   │   ├── schemas/
│   │   │   ├── common.py              # APIResponse, PaginatedResponse, Disclaimer
│   │   │   ├── news.py                # News schemas with Pydantic v2 ConfigDict
│   │   │   ├── market.py              # Stock & Sector read schemas
│   │   │   ├── signal.py              # Signal read & weight update schemas
│   │   │   ├── paper_trading.py       # Paper trade & metrics schemas
│   │   │   ├── report.py              # Daily report read schemas
│   │   │   └── system.py              # HealthStatus, ReadinessStatus, Metrics
│   │   ├── api/
│   │   │   ├── router.py              # Master API router
│   │   │   └── v1/
│   │   │       ├── health.py          # /health, /ready, /metrics, /disclaimer
│   │   │       ├── news.py            # /news, /news/{id}, /news/refresh
│   │   │       ├── signals.py         # /signals, /signals/top, /signals/generate
│   │   │       ├── market.py          # /market/stocks, /market/sectors
│   │   │       ├── paper_trading.py   # /paper-trading/positions, /metrics
│   │   │       ├── reports.py         # /reports/pre-market/latest
│   │   │       ├── performance.py     # /performance/predictions, /summary
│   │   │       └── settings.py        # /settings, /settings/weights
│   │   └── workers/
│   │       ├── tasks.py               # 5-min news cycle & pre-market report tasks
│   │       └── scheduler.py           # AsyncIOScheduler cron jobs
│   └── tests/
│       ├── conftest.py                # In-memory SQLite async test fixtures
│       ├── test_config.py             # Config & safety phrase tests
│       ├── test_health.py             # /health, /ready, /metrics tests
│       ├── test_database.py           # Database seeding & models test
│       └── test_api.py                # End-to-end API integration tests
└── frontend/
    ├── package.json                   # Next.js 14, Tailwind, Lucide React
    ├── tsconfig.json                  # TypeScript configuration
    ├── tailwind.config.js             # Financial terminal dark theme
    ├── postcss.config.js
    ├── next.config.js                 # API rewrites & optimization
    └── src/
        ├── lib/
        │   ├── api.ts                 # Type-safe API client
        │   └── types.ts               # Core TypeScript definitions
        ├── components/
        │   ├── Navbar.tsx             # IST market clock & cycle trigger
        │   ├── Sidebar.tsx            # Navigation sidebar
        │   └── DisclaimerBanner.tsx   # Persistent regulatory disclaimer
        └── app/
            ├── globals.css            # Dark terminal styling
            ├── layout.tsx             # Root layout with persistent header/sidebar
            ├── page.tsx               # Redirect to /dashboard
            ├── dashboard/page.tsx     # Executive overview & active setups
            ├── news/page.tsx          # 5-minute news feed with sentiment
            ├── signals/page.tsx       # Deterministic signal engine table
            ├── watchlist/page.tsx     # Top setups & No-Trade watchlist
            ├── market/page.tsx        # Sector sensitivity matrix & stocks
            ├── performance/page.tsx   # Prediction calibration & paper P&L
            ├── settings/page.tsx      # Scoring weights & thresholds
            └── system-health/page.tsx # Liveness, DB status, API metrics
```

---

## Development Roadmap & Phases

- [x] **Phase 1: Foundation & Core Architecture**
  - FastAPI backend with async database support (PostgreSQL ready + SQLite zero-config fallback)
  - Full ORM schema (14 tables with indexes on `published_at`, `symbol`, `event_type`, `created_at`)
  - Indian market sector sensitivity matrix & NIFTY 50 seed data
  - Next.js 14 responsive trading terminal dashboard (8 responsive pages)
  - Mandatory safety rules & prohibited phrase validation engine
- [x] **Phase 2: Modular News Engine & Deduplication** *(Current Release)*
  - AbstractNewsProvider interface with RSS, NewsAPI, and Mock providers
  - Multi-feed RSS scraper (Moneycontrol, Economic Times, Livemint, Business Standard)
  - Deduplication pipeline: URL tracking parameter stripping, title token similarity (Jaccard), and SHA-256 fingerprinting
  - Section 5 News classification & Indian equity ticker extraction
  - Preliminary sentiment and market impact pre-scoring gate
  - Automated test suite (31 tests, 100% passing)
- [ ] **Phase 3: OpenAI Structured Analysis & Fact vs. Speculation**
  - GPT-4o-mini structured JSON extraction with schema adherence
  - Explicit separation of confirmed facts, interpretation, and speculation
- [ ] **Phase 4: Market Data & Technical Indicator Pipeline**
  - Live OHLCV, 20/50/200 SMA, 20 EMA, RSI 14, MACD, ATR, VWAP
  - Technical confirmation gate (signals blocked without technical alignment)
- [ ] **Phase 5: Deterministic Signal Engine & Trading Windows**
  - Multi-factor scoring with configurable weights
  - IST market-session aware entry/exit window calculation
- [ ] **Phase 6: Telegram Bot Integration**
  - Interactive bot commands (`/start`, `/report`, `/signals`, `/performance`)
  - Threshold-gated breaking alerts (impact score >= 70)
- [ ] **Phase 7: Pre-Market Indian Stock Market Daily Report**
  - Automated 08:30 IST pre-open report synthesis
- [ ] **Phase 8: Prediction Evaluation & Backtesting Engine**
  - Directional accuracy, win rate, and Brier calibration measurement
- [ ] **Phase 9: Render Deployment & Production CI/CD**
- [ ] **Phase 10: Security Hardening & Cost Optimization**

---

## Quickstart & Local Development

### 1. Prerequisites
- Python 3.11+ or 3.13
- Node.js 18+ or 20+ (with npm)
- Git

### 2. Windows Setup Instructions

Open PowerShell in the project directory:

```powershell
# 1. Clone repository
git clone <repository_url>
cd "Trading Asistent"

# 2. Setup Python Virtual Environment
py -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install Python Dependencies
pip install -r backend/requirements.txt greenlet

# 4. Copy Environment Template
Copy-Item .env.example .env

# 5. Run Backend Pytest Suite
python -m pytest backend/tests -v

# 6. Start FastAPI Backend (Runs at http://127.0.0.1:8000)
python backend/run.py
```

In a second PowerShell window, launch the Next.js frontend:

```powershell
cd "Trading Asistent\frontend"
npm install
npm run dev
# Dashboard opens at http://localhost:3000
```

### 3. Linux / macOS Setup Instructions

```bash
# 1. Clone and enter directory
git clone <repository_url> && cd "Trading Asistent"

# 2. Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Dependencies
pip install -r backend/requirements.txt greenlet
cp .env.example .env

# 4. Run Pytest Suite
pytest backend/tests -v

# 5. Run Backend
python backend/run.py &

# 6. Run Frontend
cd frontend && npm install && npm run dev
```

---

## Example API Responses

### 1. Liveness & Safety Probe (`GET /health`)
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "development",
  "mode": "PAPER_TRADING_ONLY",
  "real_orders_enabled": false,
  "timestamp": "2026-10-28T16:15:00Z",
  "database": "connected",
  "ai_status": "configured",
  "paper_trading_safety": "ENFORCED"
}
```

### 2. Actionable Signal Payload (`GET /api/v1/signals/top`)
```json
{
  "success": true,
  "message": "Retrieved top 1 ranked setups",
  "data": [
    {
      "symbol": "RELIANCE.NS",
      "direction": "BUY",
      "entry_zone": "₹2920 - ₹2935",
      "entry_price": 2925.0,
      "stop_loss": 2890.0,
      "target_1": 2990.0,
      "target_2": 3040.0,
      "risk_reward": "1:2.0",
      "entry_time_window": "After 09:30 IST upon technical confirmation",
      "exit_time_window": "Before 15:15 IST",
      "confidence": 74,
      "news_score": 80.0,
      "technical_score": 70.0,
      "composite_score": 73.5,
      "reasoning": "Strong quarterly performance combined with breakout above 50 SMA.",
      "invalidated_if": "Falls below 2890 or broader market faces severe weakness.",
      "technical_confirmation": "RSI at 59, 20 EMA crossing above 50 SMA on 15m chart",
      "status": "PENDING"
    }
  ],
  "disclaimer": "PAPER TRADING / SIGNAL-ONLY MODE. Decision-support intelligence only."
}
```

### 3. Sector Macro Sensitivity Matrix (`GET /api/v1/market/sectors`)
```json
{
  "success": true,
  "data": [
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
      "name": "Paints & Specialty Chemicals",
      "description": "Decorative paints, coatings, and specialty chemical derivatives",
      "sensitivities": {
        "crude_oil_up": "BEARISH",
        "crude_oil_down": "BULLISH"
      }
    }
  ]
}
```

---

## Important Trading Safety Rules

1. **NO GUARANTEED OUTCOMES**: The application code strictly filters out prohibited claims such as *"Guaranteed profit"*, *"100% accurate"*, or *"Risk-free trade"*.
2. **SAFE DEFAULTS (NO TRADE)**: Whenever news is conflicting, market data is unavailable, or model confidence is below threshold, the engine defaults to **NO TRADE**.
3. **NEVER TRADE ON NEWS ALONE**: Technical indicators and volume momentum must confirm news direction before a BUY/SELL signal is issued.
4. **VIRTUAL CAPITAL ONLY**: In Phase 1, virtual paper orders are simulated to compute Maximum Adverse Excursion (MAE), Maximum Favorable Excursion (MFE), and prediction accuracy without any real financial risk.
