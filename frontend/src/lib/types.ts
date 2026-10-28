export type TradingDirection = "BUY" | "SELL" | "WATCH" | "NO_TRADE";

export interface Stock {
  id: number;
  symbol: string;
  exchange_ticker: string;
  company_name: string;
  is_nifty50: boolean;
  is_bank_nifty: boolean;
  market_cap_tier: string;
  sector?: {
    id: number;
    name: string;
    description?: string;
    sensitivities?: Record<string, string>;
  };
}

export interface NewsArticle {
  id: number;
  title: string;
  description?: string;
  url: string;
  source: string;
  author?: string;
  published_at: string;
  source_reliability_score: number;
  analysis?: {
    summary: string;
    event_type: string;
    sentiment: "BULLISH" | "BEARISH" | "NEUTRAL";
    impact_score: number;
    confidence: number;
    time_horizon: string;
    affected_sectors: string[];
    affected_stocks: string[];
    affected_indices: string[];
    reasoning: string;
    risk_factors: string[];
    confirmed_facts: string[];
  };
}

export interface TradingSignal {
  id: number;
  symbol: string;
  direction: TradingDirection;
  entry_zone: string;
  entry_price?: number;
  stop_loss?: number;
  target_1?: number;
  target_2?: number;
  risk_reward: string;
  entry_time_window: string;
  exit_time_window: string;
  confidence: number;
  news_score: number;
  technical_score: number;
  volume_score: number;
  market_score: number;
  sector_score: number;
  composite_score: number;
  reasoning: string;
  invalidated_if: string;
  technical_confirmation: string;
  status: string;
  created_at: string;
}

export interface PaperTrade {
  id: number;
  symbol: string;
  direction: "BUY" | "SELL";
  quantity: number;
  entry_price: number;
  current_price: number;
  exit_price?: number;
  stop_loss: number;
  target_1: number;
  unrealized_pnl: number;
  realized_pnl: number;
  pnl_percentage: number;
  status: string;
  entered_at: string;
}

export interface PaperTradingMetrics {
  total_trades: number;
  open_positions: number;
  closed_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  loss_rate_pct: number;
  total_realized_pnl: number;
  total_unrealized_pnl: number;
  profit_factor: number;
  average_trade_return_pct: number;
  max_drawdown_pct: number;
}

export interface DailyReport {
  id: number;
  report_date: string;
  report_type: string;
  title: string;
  global_overnight_summary: Record<string, any>;
  top_global_events: Array<{
    headline: string;
    summary: string;
    impact_score: number;
    confidence: number;
    affected_sectors: string[];
    affected_stocks: string[];
  }>;
  nifty_outlook: {
    sentiment: string;
    levels: string;
    catalysts: string[];
  };
  bank_nifty_outlook: {
    sentiment: string;
    levels: string;
    catalysts: string[];
  };
  top_watchlist: Array<any>;
  no_trade_watchlist: Array<any>;
  risk_warnings: string[];
  markdown_content: string;
}

export interface SystemHealth {
  status: string;
  version: string;
  mode: string;
  real_orders_enabled: boolean;
  database: string;
  ai_status: string;
  paper_trading_safety: string;
  timestamp: string;
}

export interface SystemMetrics {
  uptime_seconds: number;
  news_articles_total: number;
  signals_generated_total: number;
  paper_trades_active: number;
  daily_reports_generated: number;
  api_calls_count: number;
  estimated_ai_cost_usd: number;
  timestamp: string;
}
