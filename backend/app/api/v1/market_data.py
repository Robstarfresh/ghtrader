"""Market data endpoints.

⚠️  PAPER TRADING ONLY - data sourced from Kraken public REST API.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config import get_settings
from app.models.candle import Candle
from app.schemas.candle import CandleOut

router = APIRouter()


@router.get("/pairs")
async def list_pairs() -> List[dict]:
    """Return tracked trading pairs and their configuration."""
    settings = get_settings()
    return [
        {"pair": pair, "timeframe": settings.PRIMARY_TIMEFRAME, "status": "active"}
        for pair in settings.tracked_pairs_list
    ]


@router.get("/candles/{pair}", response_model=List[CandleOut])
async def get_candles(
    pair: str,
    timeframe: str = Query(default="1m"),
    limit: int = Query(default=200, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
) -> List[CandleOut]:
    """Return the most recent candles for a given pair and timeframe."""
    result = await session.execute(
        select(Candle)
        .where(Candle.pair == pair.upper(), Candle.timeframe == timeframe)
        .order_by(Candle.open_time.desc())
        .limit(limit)
    )
    candles = result.scalars().all()
    return list(reversed(candles))
