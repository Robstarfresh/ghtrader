"""RSI mean-reversion strategy.

⚠️  PAPER TRADING ONLY.
"""
from __future__ import annotations

import pandas as pd

from app.indicators.technical import compute_rsi
from app.strategies.base import Signal, Strategy, StrategyResult


class RSIStrategy(Strategy):
    """Signal BUY when RSI crosses below oversold and starts rising.

    Signal SELL when RSI crosses above overbought and starts falling.
    """

    name = "rsi"

    def __init__(
        self,
        period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
    ) -> None:
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    @property
    def min_candles(self) -> int:
        return self.period * 3

    def generate_signal(self, df: pd.DataFrame) -> StrategyResult:
        if not self.is_applicable(df):
            return StrategyResult(signal=Signal.HOLD, confidence=0.0, reason="insufficient_data")

        rsi = compute_rsi(df["close"], self.period)

        prev = rsi.iloc[-2]
        curr = rsi.iloc[-1]

        # Oversold cross: was below threshold, now rising
        if prev < self.oversold and curr > prev:
            distance = self.oversold - min(prev, curr)
            confidence = min(distance / self.oversold, 1.0)
            return StrategyResult(
                signal=Signal.BUY,
                confidence=float(confidence),
                reason=f"rsi_oversold_reversal (rsi={curr:.1f})",
                stop_loss_pct=0.015,
                take_profit_pct=0.03,
            )

        # Overbought cross: was above threshold, now falling
        if prev > self.overbought and curr < prev:
            distance = max(prev, curr) - self.overbought
            confidence = min(distance / (100 - self.overbought), 1.0)
            return StrategyResult(
                signal=Signal.SELL,
                confidence=float(confidence),
                reason=f"rsi_overbought_reversal (rsi={curr:.1f})",
                stop_loss_pct=0.015,
                take_profit_pct=0.03,
            )

        return StrategyResult(signal=Signal.HOLD, confidence=0.0, reason=f"rsi_neutral ({curr:.1f})")
