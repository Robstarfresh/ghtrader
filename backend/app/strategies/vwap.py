"""VWAP intraday-bias strategy.

⚠️  PAPER TRADING ONLY.
"""
from __future__ import annotations

import pandas as pd

from app.indicators.technical import compute_vwap
from app.strategies.base import Signal, Strategy, StrategyResult


class VWAPStrategy(Strategy):
    """BUY when price crosses above VWAP with volume confirmation.

    SELL when price crosses below VWAP.
    """

    name = "vwap"

    def __init__(self, volume_mult: float = 1.2) -> None:
        """
        Args:
            volume_mult: Volume must be at least this multiple of the rolling
                         mean volume for a crossover to count as confirmed.
        """
        self.volume_mult = volume_mult

    @property
    def min_candles(self) -> int:
        return 30

    def generate_signal(self, df: pd.DataFrame) -> StrategyResult:
        if not self.is_applicable(df):
            return StrategyResult(signal=Signal.HOLD, confidence=0.0, reason="insufficient_data")

        vwap = compute_vwap(df["high"], df["low"], df["close"], df["volume"])
        close = df["close"]
        volume = df["volume"]
        avg_volume = volume.rolling(window=20).mean()

        prev_above = close.iloc[-2] > vwap.iloc[-2]
        curr_above = close.iloc[-1] > vwap.iloc[-1]
        vol_confirmed = volume.iloc[-1] >= avg_volume.iloc[-1] * self.volume_mult

        if not prev_above and curr_above and vol_confirmed:
            spread_pct = abs(close.iloc[-1] - vwap.iloc[-1]) / vwap.iloc[-1]
            return StrategyResult(
                signal=Signal.BUY,
                confidence=min(spread_pct * 50, 1.0),
                reason="vwap_bullish_cross_confirmed",
                stop_loss_pct=0.015,
                take_profit_pct=0.025,
            )

        if prev_above and not curr_above:
            spread_pct = abs(close.iloc[-1] - vwap.iloc[-1]) / vwap.iloc[-1]
            return StrategyResult(
                signal=Signal.SELL,
                confidence=min(spread_pct * 50, 1.0),
                reason="vwap_bearish_cross",
                stop_loss_pct=0.015,
                take_profit_pct=0.025,
            )

        return StrategyResult(signal=Signal.HOLD, confidence=0.0, reason="vwap_no_cross")
