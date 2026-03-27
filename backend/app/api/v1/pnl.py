"""PnL summary and equity curve endpoints.

⚠️  PAPER TRADING ONLY.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.engine import _engine_ref

router = APIRouter()

@router.get("/summary")
async def pnl_summary() -> dict:
    """Return balance, equity, daily PnL and total PnL from the paper broker."""
    if _engine_ref is None or _engine_ref.broker is None:
        return {
            "balance": None,
            "equity": None,
            "daily_pnl": None,
            "total_pnl": None,
            "mode": "paper_trading",
        }
    return _engine_ref.broker.get_pnl_summary()

@router.get("/equity-curve")
async def equity_curve() -> dict:
    """Return the equity time series recorded by the paper broker."""
    if _engine_ref is None or _engine_ref.broker is None:
        return {"equity_curve": []}
    return {"equity_curve": _engine_ref.broker.equity_curve}
