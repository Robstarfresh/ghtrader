"""Machine learning trainer for adaptive trading strategy optimisation.

Implements an online logistic regression (pure numpy) that learns from
closed trade outcomes and provides:
  - Rolling win-rate tracking
  - Live-trading gate (enable ≥ 60 %, disable < 50 %)
  - Confidence-adjusted signal weighting
  - Strategy parameter suggestions based on recent performance

⚠️  PAPER TRADING ONLY – all predictions are used in simulation only.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
import structlog

from app.indicators.technical import compute_rsi, compute_macd, compute_atr

log = structlog.get_logger(__name__)

# Win-rate thresholds
WIN_RATE_ENABLE_THRESHOLD: float = 0.60   # enable live trading above this
WIN_RATE_DISABLE_THRESHOLD: float = 0.50  # disable live trading below this

# Minimum trades before the gate becomes active
MIN_TRADES_FOR_GATE: int = 10

# Feature vector length (must match _extract_features output)
_N_FEATURES: int = 7

# Learning rate for the online logistic regression
_LEARNING_RATE: float = 0.05

# L2 regularisation strength
_L2_LAMBDA: float = 0.01


@dataclass
class TradeOutcome:
    """Record of a single closed trade used for ML training."""
    features: np.ndarray          # shape (N_FEATURES,)
    won: bool                     # True if trade was profitable
    pnl: float = 0.0
    strategy_name: str = ""
    pair: str = ""


@dataclass
class StrategyParams:
    """Suggested strategy parameter overrides from the ML trainer."""
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04
    confidence_threshold: float = 0.5
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    breakout_period: int = 20
    macd_fast: int = 12
    macd_slow: int = 26


class MLTrainer:
    """Online logistic-regression based trade outcome predictor.

    The model is trained incrementally: every time a trade closes, its
    features and outcome (win/loss) are fed to ``record_outcome`` which
    performs a single gradient-descent step on the logistic loss.

    Live-trading gate
    -----------------
    - trading **enabled**  when rolling win-rate ≥ WIN_RATE_ENABLE_THRESHOLD
    - trading **disabled** when rolling win-rate < WIN_RATE_DISABLE_THRESHOLD
    - while win-rate is in the *neutral zone* [0.50, 0.60) the previous
      state is preserved (hysteresis prevents rapid toggling)

    Strategy adjustment
    -------------------
    ``suggest_params()`` returns conservative parameters when win-rate is
    falling and more aggressive settings when win-rate is healthy.

    ⚠️  PAPER TRADING ONLY.
    """

    def __init__(
        self,
        lookback_trades: int = 30,
        win_rate_enable: float = WIN_RATE_ENABLE_THRESHOLD,
        win_rate_disable: float = WIN_RATE_DISABLE_THRESHOLD,
        min_trades_for_gate: int = MIN_TRADES_FOR_GATE,
    ) -> None:
        self.lookback_trades = lookback_trades
        self.win_rate_enable = win_rate_enable
        self.win_rate_disable = win_rate_disable
        self.min_trades_for_gate = min_trades_for_gate

        # Recent trade history (rolling window)
        self._history: deque[TradeOutcome] = deque(maxlen=lookback_trades)
        # Full history for training
        self._full_history: list[TradeOutcome] = []

        # Logistic regression weights (initialised to zeros → 0.5 probability)
        self._weights: np.ndarray = np.zeros(_N_FEATURES + 1)  # +1 for bias

        # Live-trading gate state
        self._live_trading_enabled: bool = False

        # Total trades ever recorded
        self.total_trades: int = 0

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------

    def extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract a fixed-length feature vector from an OHLCV DataFrame.

        Features (all normalised to roughly [-1, 1] or [0, 1]):
          0. RSI(14) / 100
          1. MACD histogram sign * normalised magnitude
          2. Volume ratio (current / 20-bar avg)
          3. ATR(14) / close  (volatility proxy)
          4. Price momentum: (close - close[5]) / close[5]
          5. Distance from 20-bar SMA: (close - sma) / sma
          6. Candle body ratio: (close - open) / (high - low + ε)

        Returns a 1D ndarray of length _N_FEATURES.
        Falls back to a zero vector if insufficient data.
        """
        if len(df) < 30:
            return np.zeros(_N_FEATURES)

        close = df["close"]
        high = df["high"]
        low = df["low"]
        open_ = df["open"]
        volume = df["volume"]

        try:
            rsi = compute_rsi(close, 14).iloc[-1]
            rsi_feat = float(rsi) / 100.0

            macd_df = compute_macd(close, 12, 26, 9)
            hist = macd_df["histogram"].iloc[-1]
            macd_ref = abs(macd_df["macd"].iloc[-1]) + 1e-9
            macd_feat = float(np.clip(hist / macd_ref, -1.0, 1.0))

            vol_avg = float(volume.rolling(20).mean().iloc[-1]) + 1e-9
            vol_feat = float(np.clip(volume.iloc[-1] / vol_avg, 0.0, 5.0) / 5.0)

            atr = compute_atr(high, low, close, 14).iloc[-1]
            atr_feat = float(np.clip(atr / (close.iloc[-1] + 1e-9), 0.0, 0.1) / 0.1)

            c_now = float(close.iloc[-1])
            c_prev = float(close.iloc[-6]) if len(close) >= 6 else c_now
            mom_feat = float(np.clip((c_now - c_prev) / (c_prev + 1e-9), -0.1, 0.1) / 0.1)

            sma20 = float(close.rolling(20).mean().iloc[-1])
            sma_feat = float(np.clip((c_now - sma20) / (sma20 + 1e-9), -0.1, 0.1) / 0.1)

            body = float(close.iloc[-1]) - float(open_.iloc[-1])
            wick = float(high.iloc[-1]) - float(low.iloc[-1]) + 1e-9
            body_feat = float(np.clip(body / wick, -1.0, 1.0))

            return np.array(
                [rsi_feat, macd_feat, vol_feat, atr_feat, mom_feat, sma_feat, body_feat],
                dtype=float,
            )
        except Exception as exc:
            log.debug("feature_extraction_failed", error=str(exc))
            return np.zeros(_N_FEATURES)

    # ------------------------------------------------------------------
    # Online training
    # ------------------------------------------------------------------

    def record_outcome(
        self,
        features: np.ndarray,
        won: bool,
        pnl: float = 0.0,
        strategy_name: str = "",
        pair: str = "",
    ) -> None:
        """Record a closed trade outcome and perform an online training step.

        Args:
            features: Feature vector produced by ``extract_features``.
            won: True if the trade was profitable.
            pnl: Realised profit/loss amount.
            strategy_name: Name of the strategy that generated the signal.
            pair: Trading pair.
        """
        outcome = TradeOutcome(
            features=features.copy(),
            won=won,
            pnl=pnl,
            strategy_name=strategy_name,
            pair=pair,
        )
        self._history.append(outcome)
        self._full_history.append(outcome)
        self.total_trades += 1

        # Online gradient descent step
        self._train_step(features, float(won))

        # Update gate
        self._update_gate()

        log.debug(
            "ml_outcome_recorded",
            won=won,
            pnl=round(pnl, 4),
            win_rate=round(self.rolling_win_rate, 4),
            live_enabled=self._live_trading_enabled,
            total_trades=self.total_trades,
        )

    def _train_step(self, features: np.ndarray, label: float) -> None:
        """Single stochastic gradient-descent step on the logistic loss."""
        x = np.concatenate([[1.0], features])  # prepend bias term
        z = float(np.dot(self._weights, x))
        z = max(-500.0, min(500.0, z))  # numerical stability
        pred = 1.0 / (1.0 + math.exp(-z))
        error = pred - label

        # Gradient with L2 regularisation
        grad = error * x + _L2_LAMBDA * np.concatenate([[0.0], self._weights[1:]])
        self._weights -= _LEARNING_RATE * grad

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict_win_probability(self, features: np.ndarray) -> float:
        """Estimate probability of a win for a proposed trade.

        Returns a value in [0, 1]. 0.5 is the neutral prior.
        """
        x = np.concatenate([[1.0], features])
        z = float(np.dot(self._weights, x))
        z = max(-500.0, min(500.0, z))
        return 1.0 / (1.0 + math.exp(-z))

    # ------------------------------------------------------------------
    # Win-rate gate
    # ------------------------------------------------------------------

    @property
    def rolling_win_rate(self) -> float:
        """Win rate over the most recent *lookback_trades* closed trades."""
        if not self._history:
            return 0.0
        wins = sum(1 for t in self._history if t.won)
        return wins / len(self._history)

    def is_live_trading_enabled(self) -> bool:
        """Return True if live trading should be active.

        Rules:
        - If fewer than *min_trades_for_gate* trades have been recorded,
          live trading is **disabled** (bot must prove itself first).
        - Otherwise the gate follows the hysteresis logic based on
          win-rate thresholds.
        """
        return self._live_trading_enabled

    def _update_gate(self) -> None:
        """Apply hysteresis logic to the live-trading gate."""
        if self.total_trades < self.min_trades_for_gate:
            self._live_trading_enabled = False
            return

        wr = self.rolling_win_rate
        if wr >= self.win_rate_enable:
            if not self._live_trading_enabled:
                log.info(
                    "live_trading_gate_opened",
                    win_rate=round(wr, 4),
                    threshold=self.win_rate_enable,
                )
            self._live_trading_enabled = True
        elif wr < self.win_rate_disable:
            if self._live_trading_enabled:
                log.warning(
                    "live_trading_gate_closed",
                    win_rate=round(wr, 4),
                    threshold=self.win_rate_disable,
                )
            self._live_trading_enabled = False
        # Neutral zone: preserve current state (hysteresis)

    # ------------------------------------------------------------------
    # Strategy parameter suggestions
    # ------------------------------------------------------------------

    def suggest_params(self) -> StrategyParams:
        """Return suggested strategy parameter overrides.

        Logic:
        - High win-rate (≥ 60 %):  more aggressive (wider TP, lower threshold)
        - Mid win-rate (50–60 %):  neutral defaults
        - Low win-rate (< 50 %):   conservative (tighter SL, higher threshold,
                                   wider confirmation windows)
        """
        wr = self.rolling_win_rate

        if wr >= self.win_rate_enable:
            # Healthy win-rate: allow slightly more aggressive settings
            return StrategyParams(
                stop_loss_pct=0.02,
                take_profit_pct=0.05,
                confidence_threshold=0.45,
                rsi_oversold=32.0,
                rsi_overbought=68.0,
                breakout_period=18,
                macd_fast=12,
                macd_slow=26,
            )
        elif wr >= self.win_rate_disable:
            # Neutral zone: conservative defaults
            return StrategyParams(
                stop_loss_pct=0.018,
                take_profit_pct=0.04,
                confidence_threshold=0.55,
                rsi_oversold=28.0,
                rsi_overbought=72.0,
                breakout_period=20,
                macd_fast=12,
                macd_slow=26,
            )
        else:
            # Poor performance: tighten controls, require stronger signals
            return StrategyParams(
                stop_loss_pct=0.015,
                take_profit_pct=0.035,
                confidence_threshold=0.65,
                rsi_oversold=25.0,
                rsi_overbought=75.0,
                breakout_period=25,
                macd_fast=10,
                macd_slow=30,
            )

    # ------------------------------------------------------------------
    # Status / diagnostics
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Return a summary of the trainer state."""
        params = self.suggest_params()
        return {
            "total_trades": self.total_trades,
            "recent_trades": len(self._history),
            "rolling_win_rate": round(self.rolling_win_rate, 4),
            "live_trading_enabled": self._live_trading_enabled,
            "win_rate_enable_threshold": self.win_rate_enable,
            "win_rate_disable_threshold": self.win_rate_disable,
            "min_trades_for_gate": self.min_trades_for_gate,
            "suggested_params": {
                "stop_loss_pct": params.stop_loss_pct,
                "take_profit_pct": params.take_profit_pct,
                "confidence_threshold": params.confidence_threshold,
                "rsi_oversold": params.rsi_oversold,
                "rsi_overbought": params.rsi_overbought,
                "breakout_period": params.breakout_period,
                "macd_fast": params.macd_fast,
                "macd_slow": params.macd_slow,
            },
        }
