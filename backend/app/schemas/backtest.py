"""Backtest Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

class BacktestCreate(BaseModel):
    name: str
    strategy_name: str
    pair: str
    timeframe: str = "1m"
    start_date: datetime
    end_date: datetime
    config: Optional[dict[str, Any]] = None

class BacktestMetricsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    net_pnl: float
    return_pct: float
    max_drawdown_pct: float
    win_rate: float
    avg_winner: float
    avg_loser: float
    profit_factor: float
    sharpe_ratio: float
    expectancy: float
    trades_per_day: float
    exposure_pct: float
    total_trades: int

class BacktestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    strategy_name: str
    pair: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    config: Optional[dict[str, Any]] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    metrics: Optional[BacktestMetricsOut] = None
