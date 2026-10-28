from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class DailyReportRead(BaseModel):
    id: int
    report_date: str
    report_type: str
    title: str
    global_overnight_summary: Dict[str, Any]
    top_global_events: List[Dict[str, Any]]
    nifty_outlook: Dict[str, Any]
    bank_nifty_outlook: Dict[str, Any]
    top_watchlist: List[Dict[str, Any]]
    no_trade_watchlist: List[Dict[str, Any]]
    risk_warnings: List[str]
    markdown_content: str
    is_published: bool
    telegram_sent: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AlertRead(BaseModel):
    id: int
    title: str
    message: str
    alert_type: str
    impact_score: int
    channel: str
    is_sent: bool
    metadata_json: Dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
