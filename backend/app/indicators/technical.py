"""Pure pandas/numpy technical indicator functions.

All functions accept pandas Series/DataFrame and return Series/DataFrame.
They are side-effect free and suitable for both live and backtest use.

⚠️  PAPER TRADING ONLY - used for signal generation in simulation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_ema(close: pd.Series, period: int = 20) -> pd.Series:
    """Exponential moving average."""
    return close.ewm(span=period, adjust=False).mean()


def compute_sma(close: pd.Series, period: int = 20) -> pd.Series:
    """Simple moving average."""
    return close.rolling(window=period).mean()


def compute_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """MACD indicator.

    Returns DataFrame with columns: macd, signal, histogram.
    """
    ema_fast = compute_ema(close, fast)
    ema_slow = compute_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame(
        {"macd": macd_line, "signal": signal_line, "histogram": histogram},
        index=close.index,
    )


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder's smoothing).

    Values are bounded [0, 100].
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    # When avg_loss == 0: no losses → RSI = 100; when avg_gain == 0: no gains → RSI = 0
    rsi = np.where(
        avg_loss == 0,
        100.0,
        np.where(
            avg_gain == 0,
            0.0,
            100.0 - 100.0 / (1.0 + avg_gain / avg_loss),
        ),
    )
    result = pd.Series(rsi, index=close.index)
    # First bar is NaN (delta.diff() → NaN); fill with neutral 50
    return result.where(~(gain.isna() & loss.isna()), other=np.nan).fillna(50)


def compute_vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:
    """Volume-Weighted Average Price (cumulative intraday VWAP).

    Resets at each natural day boundary in the index.
    """
    typical_price = (high + low + close) / 3
    cumulative_tpv = (typical_price * volume).cumsum()
    cumulative_vol = volume.cumsum()
    return cumulative_tpv / cumulative_vol.replace(0, np.nan)


def compute_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Average True Range."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def compute_bollinger(
    close: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> pd.DataFrame:
    """Bollinger Bands.

    Returns DataFrame with columns: upper, mid, lower.
    """
    mid = compute_sma(close, period)
    std = close.rolling(window=period).std(ddof=0)
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    return pd.DataFrame({"upper": upper, "mid": mid, "lower": lower}, index=close.index)


def compute_rolling_high(close: pd.Series, period: int = 20) -> pd.Series:
    """Rolling maximum of close prices over *period* bars."""
    return close.rolling(window=period).max()


def compute_rolling_low(close: pd.Series, period: int = 20) -> pd.Series:
    """Rolling minimum of close prices over *period* bars."""
    return close.rolling(window=period).min()
