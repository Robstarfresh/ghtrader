"""Positions endpoints.

⚠️  PAPER TRADING ONLY.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.position import Position
from app.schemas.position import PositionOut

router = APIRouter()


@router.get("", response_model=List[PositionOut])
async def get_open_positions(session: AsyncSession = Depends(get_session)) -> List[PositionOut]:
    """Return all currently open paper positions."""
    result = await session.execute(
        select(Position).where(Position.status == "open").order_by(Position.opened_at.desc())
    )
    return list(result.scalars().all())


@router.get("/history", response_model=List[PositionOut])
async def get_position_history(
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
) -> List[PositionOut]:
    """Return closed paper positions (most recent first)."""
    result = await session.execute(
        select(Position)
        .where(Position.status == "closed")
        .order_by(Position.closed_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
