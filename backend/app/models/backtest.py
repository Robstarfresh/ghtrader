"""Backtest ORM models.

⚠️  PAPER TRADING ONLY - historical simulation results.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Backtest(Base):
    """A single backtest run configuration."""

    __tablename__ = "backtests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pair: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(5), nullable=False, default="1m")
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    metrics: Mapped[Optional["BacktestMetrics"]] = relationship(
        "BacktestMetrics", back_populates="backtest", uselist=False, lazy="select"
    )
    trades: Mapped[list["BacktestTrade"]] = relationship(
        "BacktestTrade", back_populates="backtest", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Backtest id={self.id} name={self.name} status={self.status}>"

class BacktestMetrics(Base):
    """Aggregate performance metrics for a backtest run."""

    __tablename__ = "backtest_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("backtests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    net_pnl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    return_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_winner: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_loser: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    profit_factor: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sharpe_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    expectancy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trades_per_day: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    exposure_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    backtest: Mapped["Backtest"] = relationship("Backtest", back_populates="metrics")

class BacktestTrade(Base):
    """Individual round-trip trade recorded during a backtest."""

    __tablename__ = "backtest_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("backtests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pair: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[str] = mapped_column(String(4), nullable=False)
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    pnl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fees: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    exit_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    backtest: Mapped["Backtest"] = relationship("Backtest", back_populates="trades")
