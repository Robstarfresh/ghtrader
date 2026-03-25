"""Order Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_order_id: str
    pair: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None
    filled_quantity: float
    avg_fill_price: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime
    strategy_id: Optional[int] = None
    notes: Optional[str] = None
