"""Tests for the BacktestEngine.

⚠️  PAPER TRADING ONLY - backtest engine replays historical data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.backtest.engine import BacktestEngine
from app.strategies.macd import MACDStrategy
from app.strategies.rsi import RSIStrategy
from app.strategies.breakout import BreakoutStrategy


INITIAL_BALANCE = 10_000.0
PAIR = "XBT/USD"


@pytest.fixture
def synthetic_df() -> pd.DataFrame:
    """300-bar synthetic OHLCV DataFrame with a clear up-trend."""
    np.random.seed(7)
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
        {
            "open_time": index,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


@pytest.fixture
def macd_engine() -> BacktestEngine:
    return BacktestEngine(
        strategy=MACDStrategy(),
        initial_balance=INITIAL_BALANCE,
        taker_fee=0.0026,
        maker_fee=0.0016,
        slippage_bps=0,
    )


@pytest.fixture
def rsi_engine() -> BacktestEngine:
    return BacktestEngine(
        strategy=RSIStrategy(),
        initial_balance=INITIAL_BALANCE,
        taker_fee=0.0026,
        maker_fee=0.0016,
        slippage_bps=0,
    )


@pytest.fixture
def breakout_engine() -> BacktestEngine:
    return BacktestEngine(
        strategy=BreakoutStrategy(period=10),
        initial_balance=INITIAL_BALANCE,
        taker_fee=0.0026,
        maker_fee=0.0016,
        slippage_bps=0,
    )


# ------------------------------------------------------------------
# Basic execution
# ------------------------------------------------------------------

def test_backtest_runs_without_error_macd(macd_engine: BacktestEngine, synthetic_df: pd.DataFrame) -> None:
    result = macd_engine.run(synthetic_df, PAIR)
    assert result is not None


def test_backtest_runs_without_error_rsi(rsi_engine: BacktestEngine, synthetic_df: pd.DataFrame) -> None:
    result = rsi_engine.run(synthetic_df, PAIR)
    assert result is not None


def test_backtest_runs_without_error_breakout(breakout_engine: BacktestEngine, synthetic_df: pd.DataFrame) -> None:
    result = breakout_engine.run(synthetic_df, PAIR)
    assert result is not None


# ------------------------------------------------------------------
# Metrics structure
# ------------------------------------------------------------------

def test_metrics_computed(macd_engine: BacktestEngine, synthetic_df: pd.DataFrame) -> None:
    result = macd_engine.run(synthetic_df, PAIR)
    required_keys = {
        "net_pnl", "return_pct", "max_drawdown_pct", "win_rate",
        "avg_winner", "avg_loser", "profit_factor", "sharpe_ratio",
        "expectancy", "trades_per_day", "exposure_pct", "total_trades",
    }
    assert required_keys.issubset(result.metrics.keys())


def test_metrics_types(macd_engine: BacktestEngine, synthetic_df: pd.DataFrame) -> None:
    result = macd_engine.run(synthetic_df, PAIR)
    assert isinstance(result.metrics["total_trades"], int)
    assert isinstance(result.metrics["win_rate"], float)
    assert isinstance(result.metrics["net_pnl"], float)


def test_win_rate_bounded(macd_engine: BacktestEngine, synthetic_df: pd.DataFrame) -> None:
    result = macd_engine.run(synthetic_df, PAIR)
    assert 0.0 <= result.metrics["win_rate"] <= 1.0


def test_max_drawdown_non_negative(macd_engine: BacktestEngine, synthetic_df: pd.DataFrame) -> None:
    result = macd_engine.run(synthetic_df, PAIR)
    assert result.metrics["max_drawdown_pct"] >= 0.0


def test_equity_curve_populated(macd_engine: BacktestEngine, synthetic_df: pd.DataFrame) -> None:
    result = macd_engine.run(synthetic_df, PAIR)
    assert isinstance(result.equity_curve, list)


# ------------------------------------------------------------------
# No look-ahead bias
# ------------------------------------------------------------------

def test_no_lookahead_bias(synthetic_df: pd.DataFrame) -> None:
    """Verify that signals on candle i only use data up to candle i.

    We instrument a custom strategy that records the window size it
    received and assert it never exceeds i+1 rows.
    """
    from app.strategies.base import Strategy, Signal, StrategyResult

    window_sizes: list[int] = []

    class RecordingStrategy(Strategy):
        name = "recording"

        @property
        def min_candles(self) -> int:
            return 30

        def generate_signal(self, df: pd.DataFrame) -> StrategyResult:
            window_sizes.append(len(df))
            return StrategyResult(signal=Signal.HOLD, confidence=0.0, reason="recording")

    engine = BacktestEngine(
        strategy=RecordingStrategy(),
        initial_balance=INITIAL_BALANCE,
    )
    engine.run(synthetic_df, PAIR)

    for idx, ws in enumerate(window_sizes):
        candle_idx = engine.strategy.min_candles + idx  # 0-based index in df
        # window should be exactly candle_idx + 1 rows
        assert ws == candle_idx + 1, (
            f"At iteration {idx}, window had {ws} rows but should have {candle_idx + 1}"
        )
