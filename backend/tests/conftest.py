"""Shared pytest fixtures.

⚠️  PAPER TRADING ONLY - all fixtures operate in simulation mode.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.broker.paper_broker import PaperBroker
from app.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Return a test settings instance."""
    return Settings(
        DATABASE_URL="postgresql+asyncpg://trader:trader@localhost:5432/ghtrader_test",
        PAPER_INITIAL_BALANCE=10_000.0,
        PAPER_TAKER_FEE=0.0026,
        PAPER_MAKER_FEE=0.0016,
        PAPER_SLIPPAGE_BPS=0,  # no slippage in tests for predictability
        MAX_CONCURRENT_POSITIONS=5,
        MAX_DAILY_LOSS_PCT=0.05,
        RISK_PER_TRADE_PCT=0.02,
    )


@pytest.fixture
def broker(settings: Settings) -> PaperBroker:
    """Return a fresh PaperBroker instance with zero slippage."""
    return PaperBroker(
        initial_balance=settings.PAPER_INITIAL_BALANCE,
        taker_fee=settings.PAPER_TAKER_FEE,
        maker_fee=settings.PAPER_MAKER_FEE,
        slippage_bps=0,  # disable slippage for deterministic tests
    )


@pytest.fixture
def ohlcv_df() -> pd.DataFrame:
    """Generate a synthetic 300-bar OHLCV DataFrame."""
    np.random.seed(42)
    n = 300
    close = 100.0 + np.cumsum(np.random.randn(n) * 0.5)
    close = np.clip(close, 1.0, None)
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    low = np.clip(low, 0.01, None)
    open_ = close + np.random.randn(n) * 0.2
    volume = np.abs(np.random.randn(n) * 1000) + 100

    index = pd.date_range("2024-01-01", periods=n, freq="1min")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=index,
    )
