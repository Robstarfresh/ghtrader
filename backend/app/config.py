"""Application configuration via pydantic-settings.

⚠️  PAPER TRADING ONLY - all settings pertain to simulated trading.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://trader:trader@db:5432/ghtrader"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Kraken public REST
    KRAKEN_API_BASE: str = "https://api.kraken.com"

    # Tracked trading pairs (comma-separated)
    TRACKED_PAIRS: str = "XBT/USD,ETH/USD,SOL/USD"

    # Primary OHLCV timeframe
    PRIMARY_TIMEFRAME: str = "1m"

    # Paper broker parameters
    PAPER_INITIAL_BALANCE: float = 100_000.0
    PAPER_TAKER_FEE: float = 0.0026
    PAPER_MAKER_FEE: float = 0.0016
    PAPER_SLIPPAGE_BPS: int = 5

    # Risk controls
    MAX_CONCURRENT_POSITIONS: int = 5
    MAX_DAILY_LOSS_PCT: float = 0.05
    RISK_PER_TRADE_PCT: float = 0.02

    # Application
    LOG_LEVEL: str = "INFO"
    ENV: str = "development"

    @field_validator("TRACKED_PAIRS", mode="before")
    @classmethod
    def _strip_pairs(cls, v: str) -> str:
        return v.strip()

    @property
    def tracked_pairs_list(self) -> List[str]:
        return [p.strip() for p in self.TRACKED_PAIRS.split(",") if p.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
