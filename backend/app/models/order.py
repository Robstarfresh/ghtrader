"""Order and Fill ORM models.

⚠️  PAPER TRADING ONLY - no real orders are placed on the exchange.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Order(Base):
    """Simulated paper order."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_order_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    pair: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(4), nullable=False)  # buy / sell
    order_type: Mapped[str] = mapped_column(String(20), nullable=False, default="market")
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    filled_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_fill_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    strategy_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    fills: Mapped[list["Fill"]] = relationship("Fill", back_populates="order", lazy="select")

    def __repr__(self) -> str:
        return f"<Order id={self.id} {self.side} {self.quantity} {self.pair} status={self.status}>"


class Fill(Base):
    """Individual fill event for a paper order."""

    __tablename__ = "fills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    fee: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fee_currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    filled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    order: Mapped["Order"] = relationship("Order", back_populates="fills")

    def __repr__(self) -> str:
        return f"<Fill order_id={self.order_id} qty={self.quantity} price={self.price}>"
