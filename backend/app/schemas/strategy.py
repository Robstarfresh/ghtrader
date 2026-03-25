"""Strategy Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    is_active: bool = True


class StrategyUpdate(BaseModel):
    description: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class StrategyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
