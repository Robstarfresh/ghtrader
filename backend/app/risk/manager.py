"""Risk management controls.

⚠️  PAPER TRADING ONLY - enforces position sizing and drawdown limits
    within the simulation environment.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from app.broker.paper_broker import PaperBroker
    from app.config import Settings

log = structlog.get_logger(__name__)

class RiskManager:
    """Enforces paper trading risk controls.

    Controls applied:
    - Maximum concurrent open positions
    - Daily loss kill switch (halt trading if daily loss > threshold)
    - Risk-based position sizing (risk fixed % of equity per trade)
    - Per-pair maximum exposure
    - Minimum cash reserve
    - Daily trade cap

    ⚠️  PAPER TRADING ONLY.
    """

    DAILY_TRADE_CAP: int = 50
    MIN_CASH_RESERVE_PCT: float = 0.10  # Keep at least 10% as cash
    MAX_EXPOSURE_PER_PAIR_PCT: float = 0.20  # Max 20% equity in one pair

    def __init__(self, config: "Settings") -> None:
        self._config = config
        self.daily_pnl: float = 0.0
        self.daily_trades: int = 0
        self._start_of_day_equity: float = config.PAPER_INITIAL_BALANCE

    # ------------------------------------------------------------------
    # Core checks
    # ------------------------------------------------------------------

    def check_trade(
        self,
        pair: str,
        side: str,
        quantity: float,
        price: float,
        broker: "PaperBroker",
    ) -> tuple[bool, str]:
        """Validate a proposed trade against all risk controls.

        Returns (allowed: bool, reason: str).
        """
        equity = broker._compute_equity()

        # Kill switch
        if self.check_daily_loss_kill_switch(broker):
            return False, "daily_loss_kill_switch_active"

        # Max concurrent positions
        if (
            pair not in broker.positions
            and len(broker.positions) >= self._config.MAX_CONCURRENT_POSITIONS
        ):
            return False, f"max_concurrent_positions_{self._config.MAX_CONCURRENT_POSITIONS}"

        # Daily trade cap
        if self.daily_trades >= self.DAILY_TRADE_CAP:
            return False, f"daily_trade_cap_{self.DAILY_TRADE_CAP}"

        # Minimum cash reserve
        cost = price * quantity
        min_reserve = equity * self.MIN_CASH_RESERVE_PCT
        if broker.balance - cost < min_reserve:
            return False, "insufficient_cash_reserve"

        # Max per-pair exposure
        max_pair_value = equity * self.MAX_EXPOSURE_PER_PAIR_PCT
        current_pair_value = 0.0
        if pair in broker.positions:
            pos = broker.positions[pair]
            current_pair_value = pos["current_price"] * pos["quantity"]
        if current_pair_value + cost > max_pair_value:
            return False, f"max_pair_exposure_exceeded ({self.MAX_EXPOSURE_PER_PAIR_PCT * 100:.0f}%)"

        return True, "ok"

    def size_position(
        self,
        pair: str,
        price: float,
        stop_loss_price: float,
        broker: "PaperBroker",
    ) -> float:
        """Calculate position size based on fixed-fractional risk per trade.

        Risk = equity * RISK_PER_TRADE_PCT
        Size = Risk / (price - stop_loss_price)
        """
        if price <= 0 or stop_loss_price <= 0 or price == stop_loss_price:
            return 0.0

        equity = broker._compute_equity()
        risk_amount = equity * self._config.RISK_PER_TRADE_PCT
        risk_per_unit = abs(price - stop_loss_price)
        quantity = risk_amount / risk_per_unit

        # Cap by available balance
        max_qty = (broker.balance * (1 - self.MIN_CASH_RESERVE_PCT)) / price
        quantity = min(quantity, max_qty)

        log.debug(
            "position_sized",
            pair=pair,
            price=price,
            stop=stop_loss_price,
            risk_amount=risk_amount,
            quantity=round(quantity, 6),
        )
        return max(quantity, 0.0)

    def check_daily_loss_kill_switch(self, broker: "PaperBroker") -> bool:
        """Return True (kill switch active) if daily loss exceeds threshold."""
        equity = broker._compute_equity()
        daily_loss_pct = (self._start_of_day_equity - equity) / self._start_of_day_equity
        active = daily_loss_pct >= self._config.MAX_DAILY_LOSS_PCT
        if active:
            log.warning(
                "risk_kill_switch_triggered",
                daily_loss_pct=round(daily_loss_pct * 100, 2),
                threshold_pct=self._config.MAX_DAILY_LOSS_PCT * 100,
            )
        return active

    def record_trade(self) -> None:
        """Increment the daily trade counter."""
        self.daily_trades += 1

    def reset_daily_stats(self) -> None:
        """Reset counters at the start of a new trading day."""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        log.info("risk_daily_stats_reset")
