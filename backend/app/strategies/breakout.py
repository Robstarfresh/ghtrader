"""Breakout strategy using N-period rolling high/low.

⚠️  PAPER TRADING ONLY.
"""
from __future__ import annotations

import pandas as pd

from app.indicators.technical import compute_rolling_high, compute_rolling_low
from app.strategies.base import Signal, Strategy, StrategyResult

class BreakoutStrategy(Strategy):
    """BUY when close breaks above the prior N-bar high.

    SELL when close breaks below the prior N-bar low.
    """

    name = "breakout"

    def __init__(self, period: int = 20) -> None:
        self.period = period

    @property
    def min_candles(self) -> int:
        return self.period + 5

    def generate_signal(self, df: pd.DataFrame) -> StrategyResult:
        if not self.is_applicable(df):
            return StrategyResult(signal=Signal.HOLD, confidence=0.0, reason="insufficient_data")

        # Use data up to the *previous* candle to avoid look-ahead bias
        historical = df.iloc[:-1]
        rolling_high = compute_rolling_high(historical["close"], self.period)
        rolling_low = compute_rolling_low(historical["close"], self.period)

        current_close = df["close"].iloc[-1]
        prev_high = rolling_high.iloc[-1]
        prev_low = rolling_low.iloc[-1]

        if current_close > prev_high:
            breakout_pct = (current_close - prev_high) / prev_high
            return StrategyResult(
                signal=Signal.BUY,
                confidence=min(breakout_pct * 100, 1.0),
                reason=f"breakout_above_{self.period}bar_high",
                stop_loss_pct=0.02,
                take_profit_pct=0.04,
            )

        if current_close < prev_low:
            breakout_pct = (prev_low - current_close) / prev_low
            return StrategyResult(
                signal=Signal.SELL,
                confidence=min(breakout_pct * 100, 1.0),
                reason=f"breakdown_below_{self.period}bar_low",
                stop_loss_pct=0.02,
                take_profit_pct=0.04,
            )

        return StrategyResult(signal=Signal.HOLD, confidence=0.0, reason="no_breakout")
