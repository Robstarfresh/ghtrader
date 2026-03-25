"""Deterministic backtest engine.

Replays historical OHLCV candles and simulates paper trading.

⚠️  PAPER TRADING ONLY - historical simulation, not live trading.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

import numpy as np
import pandas as pd
import structlog

from app.broker.paper_broker import PaperBroker
from app.strategies.base import Signal

if TYPE_CHECKING:
    from app.strategies.base import Strategy

log = structlog.get_logger(__name__)


@dataclass
class BacktestResult:
    """Results from a completed backtest run."""

    trades: List[dict] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)
    equity_curve: List[dict] = field(default_factory=list)


def _compute_metrics(
    trades: List[dict],
    equity_curve: List[dict],
    initial_balance: float,
    df: pd.DataFrame,
) -> dict:
    """Compute aggregate performance metrics from completed trades."""
    if not trades:
        return {
            "net_pnl": 0.0,
            "return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "win_rate": 0.0,
            "avg_winner": 0.0,
            "avg_loser": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "expectancy": 0.0,
            "trades_per_day": 0.0,
            "exposure_pct": 0.0,
            "total_trades": 0,
        }

    pnls = [t["pnl"] for t in trades]
    winners = [p for p in pnls if p > 0]
    losers = [p for p in pnls if p <= 0]

    net_pnl = sum(pnls)
    return_pct = net_pnl / initial_balance * 100
    win_rate = len(winners) / len(pnls) if pnls else 0
    avg_winner = float(np.mean(winners)) if winners else 0.0
    avg_loser = float(np.mean(losers)) if losers else 0.0

    gross_profit = sum(winners)
    gross_loss = abs(sum(losers))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    expectancy = (win_rate * avg_winner) + ((1 - win_rate) * avg_loser)

    # Max drawdown from equity curve
    equities = [e["equity"] for e in equity_curve]
    if equities:
        peak = equities[0]
        max_dd = 0.0
        for eq in equities:
            peak = max(peak, eq)
            dd = (peak - eq) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        max_drawdown_pct = max_dd * 100
    else:
        max_drawdown_pct = 0.0

    # Sharpe ratio (daily returns from equity curve)
    if len(equities) > 1:
        eq_series = pd.Series(equities)
        daily_returns = eq_series.pct_change().dropna()
        std = daily_returns.std()
        mean = daily_returns.mean()
        sharpe = (mean / std * np.sqrt(252)) if std > 0 else 0.0
    else:
        sharpe = 0.0

    # Trades per day
    duration_days = len(df) / (24 * 60) if len(df) > 0 else 1
    trades_per_day = len(trades) / max(duration_days, 1)

    # Exposure %: fraction of candles where a position was open
    candles_with_position = sum(1 for t in trades if t.get("exit_time") is not None)
    exposure_pct = candles_with_position / len(df) * 100 if len(df) > 0 else 0.0

    return {
        "net_pnl": round(net_pnl, 4),
        "return_pct": round(return_pct, 4),
        "max_drawdown_pct": round(max_drawdown_pct, 4),
        "win_rate": round(win_rate, 4),
        "avg_winner": round(avg_winner, 4),
        "avg_loser": round(avg_loser, 4),
        "profit_factor": round(profit_factor, 4),
        "sharpe_ratio": round(float(sharpe), 4),
        "expectancy": round(expectancy, 4),
        "trades_per_day": round(trades_per_day, 4),
        "exposure_pct": round(exposure_pct, 4),
        "total_trades": len(trades),
    }


class BacktestEngine:
    """Deterministic candle-by-candle replay engine.

    Iterates over historical OHLCV data. At each step it:
    1. Checks open positions for stop-loss / take-profit triggers.
    2. Passes a *view* of data up to (and including) the current candle
       to the strategy — no future data leaks.
    3. Opens a position if the signal warrants it and no position is open.

    ⚠️  PAPER TRADING ONLY.
    """

    def __init__(
        self,
        strategy: "Strategy",
        initial_balance: float = 100_000.0,
        taker_fee: float = 0.0026,
        maker_fee: float = 0.0016,
        slippage_bps: int = 5,
    ) -> None:
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.taker_fee = taker_fee
        self.maker_fee = maker_fee
        self.slippage_bps = slippage_bps

    def run(self, df: pd.DataFrame, pair: str) -> BacktestResult:
        """Execute a full backtest over *df* for *pair*.

        Args:
            df: OHLCV DataFrame with columns open/high/low/close/volume.
                Index should be a DatetimeIndex.
            pair: Trading pair label (for logging/trade records).

        Returns:
            BacktestResult with trades, metrics and equity curve.
        """
        broker = PaperBroker(
            self.initial_balance, self.taker_fee, self.maker_fee, self.slippage_bps
        )
        completed_trades: List[dict] = []  # only closed round-trips

        # Reset equity curve so we only capture this run
        broker.equity_curve.clear()

        df = df.reset_index(drop=False)  # preserve timestamp if in index

        for i in range(self.strategy.min_candles, len(df)):
            # !! Only pass data up to current candle — no look-ahead !!
            window = df.iloc[:i + 1].copy()
            candle = df.iloc[i]

            current_price = float(candle["close"])
            current_time = candle.get("open_time", candle.name if hasattr(candle, "name") else None)

            # Capture trade log length before price update to detect stop/TP closes
            log_len_before = len(broker.trade_log)

            # Update prices + check stops
            broker.update_prices({pair: current_price})

            # Record any positions closed by stops/TP during price update
            for tl_entry in broker.trade_log[log_len_before:]:
                if "pnl" in tl_entry:
                    completed_trades.append(tl_entry)

            # Generate signal from strategy using only historical data
            result = self.strategy.generate_signal(window)

            # Only open one position at a time per pair
            if result.signal == Signal.BUY and pair not in broker.positions:
                sl_price = (
                    current_price * (1 - result.stop_loss_pct)
                    if result.stop_loss_pct
                    else None
                )
                tp_price = (
                    current_price * (1 + result.take_profit_pct)
                    if result.take_profit_pct
                    else None
                )
                equity = broker._compute_equity()
                quantity = (equity * 0.02) / current_price  # 2% risk allocation
                if quantity > 0:
                    broker.submit_order(
                        pair, "buy", quantity, current_price,
                        stop_loss=sl_price, take_profit=tp_price,
                    )

            elif result.signal == Signal.SELL and pair in broker.positions:
                close_result = broker.close_position(pair, current_price, reason="signal_sell")
                close_result["exit_time"] = str(current_time) if current_time is not None else None
                completed_trades.append(close_result)

        # Close any remaining open position at last candle's close
        if pair in broker.positions and len(df) > 0:
            last_price = float(df.iloc[-1]["close"])
            close_result = broker.close_position(pair, last_price, reason="end_of_backtest")
            completed_trades.append(close_result)

        metrics = _compute_metrics(completed_trades, broker.equity_curve, self.initial_balance, df)

        log.info(
            "backtest_complete",
            pair=pair,
            strategy=self.strategy.name,
            total_trades=metrics["total_trades"],
            net_pnl=metrics["net_pnl"],
            return_pct=metrics["return_pct"],
        )

        return BacktestResult(
            trades=completed_trades,
            metrics=metrics,
            equity_curve=broker.equity_curve,
        )
