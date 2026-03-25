"""FastAPI application factory.

⚠️  PAPER TRADING ONLY - GHTrader is a research and simulation platform.
    It is NOT connected to any live exchange and places NO real orders.
"""
from __future__ import annotations

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import get_settings

log = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="GHTrader - Kraken Paper Trading System",
        description=(
            "⚠️  PAPER TRADING ONLY - Research and simulation platform. "
            "Not connected to live exchange. No real orders are placed."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    async def _startup() -> None:
        log.info(
            "ghtrader_startup",
            env=settings.ENV,
            pairs=settings.tracked_pairs_list,
            mode="paper_trading",
        )

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        log.info("ghtrader_shutdown")

    return app


app = create_app()
