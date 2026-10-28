from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    disclaimer: str = (
        "PAPER TRADING / SIGNAL-ONLY MODE. Decision-support intelligence only. "
        "No guaranteed returns. All trading involves financial risk."
    )


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    total: int
    page: int
    page_size: int
    items: List[T]
    disclaimer: str = "PAPER TRADING / DECISION SUPPORT ONLY. No guaranteed outcomes."


class DisclaimerResponse(BaseModel):
    mode: str = "PAPER_TRADING_ONLY"
    real_orders_enabled: bool = False
    disclaimer: str
    guarantee_statement: str
    regulatory_framework: str = "Indian Capital Markets (NSE/BSE/SEBI context) - Educational & Algorithmic Research Only"
