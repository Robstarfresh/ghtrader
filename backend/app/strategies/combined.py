"""Combined weighted-vote strategy.

⚠️  PAPER TRADING ONLY.
"""
from __future__ import annotations

from typing import List, Tuple

import pandas as pd

from app.strategies.base import Signal, Strategy, StrategyResult


class CombinedStrategy(Strategy):
    """Aggregate multiple strategies using a weighted voting scheme.

    Each (strategy, weight) pair contributes its signal confidence
    multiplied by weight to a running score:
      +score for BUY, -score for SELL.

    Final decision:
      score > threshold  -> BUY
      score < -threshold -> SELL
      otherwise          -> HOLD
    """

    name = "combined"

    def __init__(
        self,
        strategies: List[Tuple[Strategy, float]],
        threshold: float = 0.5,
    ) -> None:
        if not strategies:
            raise ValueError("At least one strategy is required")
        self.strategies = strategies
        self.threshold = threshold

    @property
    def min_candles(self) -> int:
        return max(s.min_candles for s, _ in self.strategies)

    def generate_signal(self, df: pd.DataFrame) -> StrategyResult:
        if not self.is_applicable(df):
            return StrategyResult(signal=Signal.HOLD, confidence=0.0, reason="insufficient_data")

        total_weight = sum(w for _, w in self.strategies)
        if total_weight == 0:
            return StrategyResult(signal=Signal.HOLD, confidence=0.0, reason="zero_total_weight")

        weighted_score = 0.0
        reasons: List[str] = []

        for strategy, weight in self.strategies:
            if not strategy.is_applicable(df):
                continue
            result = strategy.generate_signal(df)
            if result.signal == Signal.BUY:
                weighted_score += result.confidence * weight
            elif result.signal == Signal.SELL:
                weighted_score -= result.confidence * weight
            reasons.append(f"{strategy.name}:{result.signal.value}({result.confidence:.2f})")

        normalised = weighted_score / total_weight
        reason_str = "; ".join(reasons)

        if normalised > self.threshold:
            return StrategyResult(
                signal=Signal.BUY,
                confidence=min(normalised, 1.0),
                reason=f"combined_buy [{reason_str}]",
                stop_loss_pct=0.02,
                take_profit_pct=0.04,
            )
        if normalised < -self.threshold:
            return StrategyResult(
                signal=Signal.SELL,
                confidence=min(abs(normalised), 1.0),
                reason=f"combined_sell [{reason_str}]",
                stop_loss_pct=0.02,
                take_profit_pct=0.04,
            )

        return StrategyResult(
            signal=Signal.HOLD,
            confidence=abs(normalised),
            reason=f"combined_hold (score={normalised:.3f}) [{reason_str}]",
        )
