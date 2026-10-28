from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class HealthStatus(BaseModel):
    status: str = "ok"
    version: str
    environment: str
    mode: str = "PAPER_TRADING_ONLY"
    real_orders_enabled: bool = False
    timestamp: datetime
    database: str
    ai_status: str
    paper_trading_safety: str = "ENFORCED"


class ReadinessStatus(BaseModel):
    status: str = "ready"
    checks: Dict[str, bool]
    timestamp: datetime


class MetricsStatus(BaseModel):
    uptime_seconds: float
    news_articles_total: int
    signals_generated_total: int
    paper_trades_active: int
    daily_reports_generated: int
    api_calls_count: int
    estimated_ai_cost_usd: float
    memory_usage_mb: Optional[float] = None
    timestamp: datetime


class PredictionEvaluationRead(BaseModel):
    id: int
    signal_id: int
    symbol: str
    predicted_direction: str
    predicted_confidence: int
    price_at_prediction: float
    evaluation_horizon: str
    evaluation_due_at: datetime
    evaluated_at: Optional[datetime] = None
    actual_price_at_eval: Optional[float] = None
    actual_price_change_pct: Optional[float] = None
    actual_direction: Optional[str] = None
    is_direction_correct: Optional[bool] = None
    is_evaluated: bool
    evaluation_notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SystemSettingRead(BaseModel):
    id: int
    key: str
    value_json: Dict[str, Any]
    description: Optional[str] = None
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
