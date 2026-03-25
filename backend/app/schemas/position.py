"""Position Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PositionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pair: str
    side: str
    quantity: float
    avg_entry_price: float
    current_price: Optional[float] = None
    unrealized_pnl: float
    realized_pnl: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop_pct: Optional[float] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None
    status: str
    strategy_id: Optional[int] = None
