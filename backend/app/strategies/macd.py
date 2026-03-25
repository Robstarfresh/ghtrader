"""MACD trend-continuation strategy.

⚠️  PAPER TRADING ONLY.
"""
from __future__ import annotations

import pandas as pd

from app.indicators.technical import compute_macd
from app.strategies.base import Signal, Strategy, StrategyResult


class MACDStrategy(Strategy):
    """Signal BUY when MACD crosses above signal and histogram is positive.

    Signal SELL when MACD crosses below signal line.
    """

    name = "macd"

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9) -> None:
        self.fast = fast
        self.slow = slow
        self.signal = signal

    @property
    def min_candles(self) -> int:
        return self.slow + self.signal + 5

    def generate_signal(self, df: pd.DataFrame) -> StrategyResult:
        if not self.is_applicable(df):
            return StrategyResult(signal=Signal.HOLD, confidence=0.0, reason="insufficient_data")

        macd_df = compute_macd(df["close"], self.fast, self.slow, self.signal)
        macd = macd_df["macd"]
        sig = macd_df["signal"]
        hist = macd_df["histogram"]

        # Crossover detection: previous bar vs current bar
        prev_above = macd.iloc[-2] > sig.iloc[-2]
        curr_above = macd.iloc[-1] > sig.iloc[-1]

        if not prev_above and curr_above and hist.iloc[-1] > 0:
            confidence = min(abs(hist.iloc[-1]) / (abs(macd.iloc[-1]) + 1e-9), 1.0)
            return StrategyResult(
                signal=Signal.BUY,
                confidence=float(confidence),
                reason="macd_bullish_crossover",
                stop_loss_pct=0.02,
                take_profit_pct=0.04,
            )

        if prev_above and not curr_above and hist.iloc[-1] < 0:
            confidence = min(abs(hist.iloc[-1]) / (abs(macd.iloc[-1]) + 1e-9), 1.0)
            return StrategyResult(
                signal=Signal.SELL,
                confidence=float(confidence),
                reason="macd_bearish_crossover",
                stop_loss_pct=0.02,
                take_profit_pct=0.04,
            )

        return StrategyResult(signal=Signal.HOLD, confidence=0.0, reason="no_crossover")
