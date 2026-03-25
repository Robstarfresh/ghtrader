"""Trades (order fills) endpoints.

⚠️  PAPER TRADING ONLY.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.order import Order
from app.schemas.order import OrderOut

router = APIRouter()


@router.get("", response_model=List[OrderOut])
async def list_trades(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> List[OrderOut]:
    """Return paginated list of paper trades (filled orders)."""
    offset = (page - 1) * page_size
    result = await session.execute(
        select(Order)
        .where(Order.status == "filled")
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().all())
