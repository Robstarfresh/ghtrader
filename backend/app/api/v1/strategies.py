"""Strategy management endpoints.

⚠️  PAPER TRADING ONLY.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyOut, StrategyUpdate

router = APIRouter()


@router.get("", response_model=List[StrategyOut])
async def list_strategies(session: AsyncSession = Depends(get_session)) -> List[StrategyOut]:
    """List all registered strategy configurations."""
    result = await session.execute(select(Strategy).order_by(Strategy.id))
    return list(result.scalars().all())


@router.post("", response_model=StrategyOut, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    payload: StrategyCreate,
    session: AsyncSession = Depends(get_session),
) -> StrategyOut:
    """Create or register a new strategy configuration."""
    strategy = Strategy(**payload.model_dump())
    session.add(strategy)
    await session.flush()
    await session.refresh(strategy)
    return strategy


@router.patch("/{strategy_id}", response_model=StrategyOut)
async def update_strategy(
    strategy_id: int,
    payload: StrategyUpdate,
    session: AsyncSession = Depends(get_session),
) -> StrategyOut:
    """Toggle enable/disable or update a strategy configuration."""
    result = await session.execute(select(Strategy).where(Strategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(strategy, field, value)

    await session.flush()
    await session.refresh(strategy)
    return strategy
