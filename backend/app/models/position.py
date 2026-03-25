"""Position ORM model.

⚠️  PAPER TRADING ONLY.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Position(Base):
    """Open or closed paper position."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pair: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(4), nullable=False)  # buy / sell
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    avg_entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unrealized_pnl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    realized_pnl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    stop_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trailing_stop_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="open")  # open / closed
    strategy_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<Position id={self.id} {self.side} {self.quantity} {self.pair} "
            f"status={self.status}>"
        )
