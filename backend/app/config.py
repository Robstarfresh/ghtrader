"""Application configuration via pydantic-settings.

⚠️  PAPER TRADING ONLY - all settings pertain to simulated trading.
"""
from __future__ import annotations

from functools import lru_cache

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

    # Tracked trading pairs (comma-separated).
    # Leave blank to let the TokenScanner populate the list automatically.
    TRACKED_PAIRS: str = ""

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

    # Token scanner
    MIN_VOLUME_24H_USD: float = 100_000.0   # minimum 24 h USD volume for a pair
    SCANNER_INTERVAL_SECONDS: int = 3600    # how often to re-scan for tokens (1 h)
    SCANNER_REQUIRE_MOMENTUM: bool = True   # only include rising tokens

    # ML trainer / win-rate gate
    WIN_RATE_ENABLE_THRESHOLD: float = 0.60   # turn ON live trading above this
    WIN_RATE_DISABLE_THRESHOLD: float = 0.50  # turn OFF live trading below this
    ML_LOOKBACK_TRADES: int = 30              # rolling window for win-rate calc
    ML_MIN_TRADES_FOR_GATE: int = 10          # min trades before gate activates

    @field_validator("TRACKED_PAIRS", mode="before")
    @classmethod
    def _strip_pairs(cls, v: str) -> str:
        return v.strip()

    @property
    def tracked_pairs_list(self) -> list[str]:
        return [p.strip() for p in self.TRACKED_PAIRS.split(",") if p.strip()]

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
