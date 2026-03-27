"""Paper engine control endpoints.

⚠️  PAPER TRADING ONLY - controls the simulated trading engine.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# The PaperEngine instance is managed at the application level.
# These endpoints delegate to the singleton stored in app.state.
_engine_ref = None  # populated by main.py startup event

def set_engine(engine) -> None:
    global _engine_ref
    _engine_ref = engine

@router.get("/status")
async def engine_status() -> dict:
    """Return the current paper engine state."""
    if _engine_ref is None:
        return {"running": False, "equity": None, "positions_count": 0}
    return _engine_ref.get_status()

@router.post("/start")
async def start_engine() -> dict:
    """Start the paper trading engine."""
    if _engine_ref is None:
        return {"ok": False, "detail": "Engine not initialised"}
    if not _engine_ref._running:
        import asyncio

        asyncio.create_task(_engine_ref.start())
    return {"ok": True, "detail": "Engine start requested"}

@router.post("/stop")
async def stop_engine() -> dict:
    """Stop the paper trading engine."""
    if _engine_ref is None:
        return {"ok": False, "detail": "Engine not initialised"}
    await _engine_ref.stop()
    return {"ok": True, "detail": "Engine stopped"}
