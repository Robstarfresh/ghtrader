"""Risk management endpoints.

⚠️  PAPER TRADING ONLY.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.engine import _engine_ref

router = APIRouter()

@router.get("/status")
async def risk_status() -> dict:
    """Return current risk state and kill switch status."""
    if _engine_ref is None or _engine_ref.risk_manager is None:
        return {
            "kill_switch_active": False,
            "daily_loss_pct": 0.0,
            "open_positions": 0,
            "mode": "paper_trading",
        }
    rm = _engine_ref.risk_manager
    broker = _engine_ref.broker
    return {
        "kill_switch_active": rm.check_daily_loss_kill_switch(broker),
        "daily_pnl": rm.daily_pnl,
        "daily_trades": rm.daily_trades,
        "open_positions": len(broker.positions),
        "mode": "paper_trading",
    }

@router.post("/reset")
async def reset_risk() -> dict:
    """Reset daily risk counters (e.g. at start of new trading day)."""
    if _engine_ref is None or _engine_ref.risk_manager is None:
        return {"ok": False, "detail": "Engine not initialised"}
    _engine_ref.risk_manager.reset_daily_stats()
    return {"ok": True, "detail": "Daily risk counters reset"}
