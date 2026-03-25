"""Abstract base class for all trading strategies.

⚠️  PAPER TRADING ONLY - strategies produce signals for simulated execution.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import pandas as pd


class Signal(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class StrategyResult:
    """Output from a strategy signal generation pass."""

    signal: Signal
    confidence: float  # 0.0 to 1.0
    reason: str
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None


class Strategy(ABC):
    """Abstract strategy interface.

    Concrete strategies must implement ``generate_signal``.
    """

    name: str = "abstract"

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> StrategyResult:
        """Generate a trading signal from an OHLCV DataFrame.

        The DataFrame must have at minimum columns:
        open, high, low, close, volume.
        The last row represents the *current* candle.

        ⚠️  PAPER TRADING ONLY - no real orders result from this call.
        """

    def is_applicable(self, df: pd.DataFrame) -> bool:
        """Return True if there is sufficient data to generate a signal."""
        return len(df) >= self.min_candles

    @property
    def min_candles(self) -> int:
        """Minimum number of candles required by this strategy."""
        return 50
