"""Tests for technical indicator functions.

⚠️  PAPER TRADING ONLY - indicators are used for simulated signals.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.indicators.technical import (
    compute_atr,
    compute_bollinger,
    compute_ema,
    compute_macd,
    compute_rsi,
    compute_rolling_high,
    compute_rolling_low,
    compute_sma,
    compute_vwap,
)


@pytest.fixture
def price_series() -> pd.Series:
    np.random.seed(0)
    return pd.Series(
        100.0 + np.cumsum(np.random.randn(200) * 0.5),
        name="close",
    )


@pytest.fixture
def ohlcv(price_series: pd.Series) -> pd.DataFrame:
    np.random.seed(0)
    n = len(price_series)
    high = price_series + np.abs(np.random.randn(n) * 0.3)
    low = price_series - np.abs(np.random.randn(n) * 0.3)
    low = low.clip(lower=0.01)
    volume = pd.Series(np.abs(np.random.randn(n) * 1000) + 100)
    return pd.DataFrame(
        {"close": price_series, "high": high, "low": low, "volume": volume}
    )


# ------------------------------------------------------------------
# MACD
# ------------------------------------------------------------------

def test_macd_returns_correct_columns(price_series: pd.Series) -> None:
    result = compute_macd(price_series)
    assert set(result.columns) == {"macd", "signal", "histogram"}


def test_macd_histogram_is_macd_minus_signal(price_series: pd.Series) -> None:
    result = compute_macd(price_series)
    diff = (result["macd"] - result["signal"] - result["histogram"]).abs()
    assert diff.max() < 1e-10


def test_macd_length_matches_input(price_series: pd.Series) -> None:
    result = compute_macd(price_series)
    assert len(result) == len(price_series)


# ------------------------------------------------------------------
# RSI
# ------------------------------------------------------------------

def test_rsi_bounded_0_100(price_series: pd.Series) -> None:
    rsi = compute_rsi(price_series)
    valid = rsi.dropna()
    assert (valid >= 0).all() and (valid <= 100).all()


def test_rsi_length_matches_input(price_series: pd.Series) -> None:
    rsi = compute_rsi(price_series)
    assert len(rsi) == len(price_series)


def test_rsi_rising_series_high() -> None:
    """RSI of a strictly rising series should be above 50."""
    rising = pd.Series(range(1, 101), dtype=float)
    rsi = compute_rsi(rising, period=14)
    assert rsi.iloc[-1] > 50


def test_rsi_falling_series_low() -> None:
    """RSI of a strictly falling series should be below 50."""
    falling = pd.Series(range(100, 0, -1), dtype=float)
    rsi = compute_rsi(falling, period=14)
    assert rsi.iloc[-1] < 50


# ------------------------------------------------------------------
# VWAP
# ------------------------------------------------------------------

def test_vwap_positive(ohlcv: pd.DataFrame) -> None:
    vwap = compute_vwap(ohlcv["high"], ohlcv["low"], ohlcv["close"], ohlcv["volume"])
    assert (vwap.dropna() > 0).all()


def test_vwap_reasonable_range(ohlcv: pd.DataFrame) -> None:
    """VWAP should stay within the overall high/low range of the dataset."""
    vwap = compute_vwap(ohlcv["high"], ohlcv["low"], ohlcv["close"], ohlcv["volume"])
    valid = vwap.dropna()
    assert (valid <= ohlcv["high"].max()).all()
    assert (valid >= ohlcv["low"].min()).all()


# ------------------------------------------------------------------
# ATR
# ------------------------------------------------------------------

def test_atr_positive(ohlcv: pd.DataFrame) -> None:
    atr = compute_atr(ohlcv["high"], ohlcv["low"], ohlcv["close"])
    assert (atr.dropna() > 0).all()


def test_atr_length_matches(ohlcv: pd.DataFrame) -> None:
    atr = compute_atr(ohlcv["high"], ohlcv["low"], ohlcv["close"])
    assert len(atr) == len(ohlcv)


# ------------------------------------------------------------------
# Bollinger Bands
# ------------------------------------------------------------------

def test_bollinger_bands_ordering(price_series: pd.Series) -> None:
    bb = compute_bollinger(price_series)
    valid = bb.dropna()
    assert (valid["upper"] >= valid["mid"]).all()
    assert (valid["mid"] >= valid["lower"]).all()


def test_bollinger_returns_correct_columns(price_series: pd.Series) -> None:
    bb = compute_bollinger(price_series)
    assert set(bb.columns) == {"upper", "mid", "lower"}


def test_bollinger_mid_equals_sma(price_series: pd.Series) -> None:
    period = 20
    bb = compute_bollinger(price_series, period=period)
    sma = compute_sma(price_series, period=period)
    diff = (bb["mid"] - sma).abs().dropna()
    assert diff.max() < 1e-10


# ------------------------------------------------------------------
# Rolling high / low
# ------------------------------------------------------------------

def test_rolling_high_gte_rolling_low(price_series: pd.Series) -> None:
    high = compute_rolling_high(price_series)
    low = compute_rolling_low(price_series)
    valid_high = high.dropna()
    valid_low = low.dropna()
    min_len = min(len(valid_high), len(valid_low))
    assert (valid_high.iloc[-min_len:].values >= valid_low.iloc[-min_len:].values).all()


# ------------------------------------------------------------------
# EMA / SMA
# ------------------------------------------------------------------

def test_ema_length_matches(price_series: pd.Series) -> None:
    assert len(compute_ema(price_series)) == len(price_series)


def test_sma_length_matches(price_series: pd.Series) -> None:
    assert len(compute_sma(price_series)) == len(price_series)
