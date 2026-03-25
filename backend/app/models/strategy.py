"""Strategy and StrategyRun ORM models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Strategy(Base):
    """Persisted strategy configuration.

    ⚠️  PAPER TRADING ONLY.
    """

    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    params: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    runs: Mapped[list["StrategyRun"]] = relationship(
        "StrategyRun", back_populates="strategy", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Strategy name={self.name} active={self.is_active}>"


class StrategyRun(Base):
    """Records a strategy execution window."""

    __tablename__ = "strategy_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pair: Mapped[str] = mapped_column(String(20), nullable=False)
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)

    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="runs")

    def __repr__(self) -> str:
        return f"<StrategyRun id={self.id} strategy_id={self.strategy_id} status={self.status}>"
