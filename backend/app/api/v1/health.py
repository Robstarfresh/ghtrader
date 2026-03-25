"""Health check endpoint."""
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Return service health status.

    ⚠️  PAPER TRADING ONLY system health check.
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "paper_trading",
    }
