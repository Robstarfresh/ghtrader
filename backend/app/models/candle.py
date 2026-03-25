"""Candle (OHLCV) ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Candle(Base):
    """OHLCV candle data fetched from Kraken public API.

    ⚠️  PAPER TRADING ONLY - used for signal generation and backtesting.
    """

    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint("pair", "timeframe", "open_time", name="uq_candle_pair_tf_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pair: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(5), nullable=False)
    open_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    vwap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trades: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Candle pair={self.pair} tf={self.timeframe} "
            f"t={self.open_time} c={self.close}>"
        )
