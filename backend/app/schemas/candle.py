"""Candle (OHLCV) Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

class CandleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pair: str
    timeframe: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: Optional[float] = None
    trades: Optional[int] = None
