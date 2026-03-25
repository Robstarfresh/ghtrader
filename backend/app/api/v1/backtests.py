"""Backtest management endpoints.

⚠️  PAPER TRADING ONLY - historical simulation only.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.backtest import Backtest, BacktestMetrics, BacktestTrade
from app.schemas.backtest import BacktestCreate, BacktestOut, BacktestMetricsOut

router = APIRouter()

@router.post("", response_model=BacktestOut, status_code=201)
async def run_backtest(
    payload: BacktestCreate,
    session: AsyncSession = Depends(get_session),
) -> BacktestOut:
    """Create a new backtest run record.

    The actual computation is delegated to a background task or worker.
    This endpoint stores the configuration and returns the created record.
    """
    bt = Backtest(**payload.model_dump())
    session.add(bt)
    await session.flush()
    await session.refresh(bt)
    return bt

@router.get("", response_model=list[BacktestOut])
async def list_backtests(session: AsyncSession = Depends(get_session)) -> list[BacktestOut]:
    """List all backtest runs."""
    result = await session.execute(
        select(Backtest).order_by(Backtest.created_at.desc())
    )
    return list(result.scalars().all())

@router.get("/leaderboard")
async def leaderboard(session: AsyncSession = Depends(get_session)) -> list[dict]:
    """Return strategy performance comparison sorted by return_pct."""
    result = await session.execute(
        select(Backtest, BacktestMetrics)
        .join(BacktestMetrics, BacktestMetrics.backtest_id == Backtest.id, isouter=True)
        .where(Backtest.status == "completed")
        .order_by(BacktestMetrics.return_pct.desc())
    )
    rows = result.all()
    return [
        {
            "backtest_id": bt.id,
            "name": bt.name,
            "strategy_name": bt.strategy_name,
            "pair": bt.pair,
            "return_pct": m.return_pct if m else None,
            "sharpe_ratio": m.sharpe_ratio if m else None,
            "max_drawdown_pct": m.max_drawdown_pct if m else None,
            "win_rate": m.win_rate if m else None,
            "total_trades": m.total_trades if m else None,
        }
        for bt, m in rows
    ]

@router.get("/{backtest_id}", response_model=BacktestOut)
async def get_backtest(
    backtest_id: int,
    session: AsyncSession = Depends(get_session),
) -> BacktestOut:
    """Return a specific backtest run with its metrics."""
    result = await session.execute(select(Backtest).where(Backtest.id == backtest_id))
    bt = result.scalar_one_or_none()
    if bt is None:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return bt

@router.get("/{backtest_id}/trades")
async def get_backtest_trades(
    backtest_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Return individual trades from a backtest run."""
    result = await session.execute(
        select(BacktestTrade)
        .where(BacktestTrade.backtest_id == backtest_id)
        .order_by(BacktestTrade.entry_time)
    )
    trades = result.scalars().all()
    return [
        {
            "id": t.id,
            "pair": t.pair,
            "side": t.side,
            "entry_time": t.entry_time.isoformat(),
            "exit_time": t.exit_time.isoformat() if t.exit_time else None,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "quantity": t.quantity,
            "pnl": t.pnl,
            "fees": t.fees,
            "exit_reason": t.exit_reason,
        }
        for t in trades
    ]
