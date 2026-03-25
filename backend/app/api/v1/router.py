"""API v1 router - aggregates all sub-routers."""
from fastapi import APIRouter

from app.api.v1 import (
    health,
    market_data,
    strategies,
    engine,
    positions,
    trades,
    pnl,
    backtests,
    risk,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(market_data.router, prefix="/market", tags=["market-data"])
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(engine.router, prefix="/engine", tags=["engine"])
api_router.include_router(positions.router, prefix="/positions", tags=["positions"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(pnl.router, prefix="/pnl", tags=["pnl"])
api_router.include_router(backtests.router, prefix="/backtests", tags=["backtests"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
