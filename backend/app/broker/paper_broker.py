"""Paper trading broker.

Simulates order execution with fees, slippage, and position management.

⚠️  PAPER TRADING ONLY - absolutely no real orders are placed on any exchange.
    This module exists solely for research and simulation purposes.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import structlog

log = structlog.get_logger(__name__)


class PaperBroker:
    """Simulated paper execution engine.

    Tracks balance, open positions, fills, equity curve, and stop management.

    ⚠️  PAPER TRADING ONLY.
    """

    def __init__(
        self,
        initial_balance: float,
        taker_fee: float = 0.0026,
        maker_fee: float = 0.0016,
        slippage_bps: int = 5,
    ) -> None:
        self.initial_balance = initial_balance
        self.taker_fee = taker_fee
        self.maker_fee = maker_fee
        self.slippage_bps = slippage_bps

        self.balance: float = initial_balance
        self.positions: Dict[str, dict] = {}
        self.trade_log: List[dict] = []
        self.equity_curve: List[dict] = []
        self._daily_start_equity: float = initial_balance

        # Record initial equity point
        self._record_equity()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit_order(
        self,
        pair: str,
        side: str,
        quantity: float,
        price: float,
        order_type: str = "market",
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop_pct: Optional[float] = None,
        strategy_id: Optional[int] = None,
    ) -> dict:
        """Execute a paper order immediately at the adjusted price.

        Applies slippage and taker fee for market orders.

        ⚠️  PAPER TRADING ONLY.
        """
        fill_price = self._apply_slippage(price, side)
        fee_rate = self.taker_fee if order_type == "market" else self.maker_fee
        fee = fill_price * quantity * fee_rate
        cost = fill_price * quantity + (fee if side == "buy" else 0)

        if side == "buy":
            if cost > self.balance:
                log.warning(
                    "paper_order_rejected",
                    reason="insufficient_balance",
                    cost=cost,
                    balance=self.balance,
                )
                return {"status": "rejected", "reason": "insufficient_balance"}
            self.balance -= cost
            self._open_or_add_position(
                pair, side, quantity, fill_price, fee,
                stop_loss, take_profit, trailing_stop_pct, strategy_id
            )
        elif side == "sell":
            position = self.positions.get(pair)
            if position is None:
                log.warning("paper_order_rejected", reason="no_open_position", pair=pair)
                return {"status": "rejected", "reason": "no_open_position"}
            return self.close_position(pair, fill_price, reason="manual_sell")

        order_id = str(uuid.uuid4())
        fill = {
            "order_id": order_id,
            "pair": pair,
            "side": side,
            "quantity": quantity,
            "fill_price": fill_price,
            "fee": fee,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "filled",
        }
        self.trade_log.append(fill)
        self._record_equity()

        log.info(
            "paper_order_filled",
            pair=pair,
            side=side,
            quantity=quantity,
            fill_price=fill_price,
            fee=fee,
        )
        return fill

    def close_position(self, pair: str, price: float, reason: str = "manual") -> dict:
        """Close an open position and realise PnL.

        ⚠️  PAPER TRADING ONLY.
        """
        position = self.positions.pop(pair, None)
        if position is None:
            return {"status": "no_position", "pair": pair}

        fill_price = self._apply_slippage(price, "sell")
        fee = fill_price * position["quantity"] * self.taker_fee
        proceeds = fill_price * position["quantity"] - fee

        if position["side"] == "buy":
            pnl = proceeds - position["cost_basis"]
        else:
            pnl = position["cost_basis"] - proceeds

        # Add only the sale proceeds; cost_basis was already deducted on entry.
        self.balance += proceeds

        result = {
            "pair": pair,
            "side": position["side"],
            "quantity": position["quantity"],
            "entry_price": position["avg_entry_price"],
            "exit_price": fill_price,
            "pnl": pnl,
            "fee": fee,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.trade_log.append(result)
        self._record_equity()

        log.info("paper_position_closed", pair=pair, pnl=pnl, reason=reason)
        return result

    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update current prices, recalculate unrealised PnL, check stops.

        ⚠️  PAPER TRADING ONLY.
        """
        for pair, price in prices.items():
            pos = self.positions.get(pair)
            if pos is None:
                continue
            pos["current_price"] = price

            if pos["side"] == "buy":
                pos["unrealized_pnl"] = (price - pos["avg_entry_price"]) * pos["quantity"]
            else:
                pos["unrealized_pnl"] = (pos["avg_entry_price"] - price) * pos["quantity"]

            # Trailing stop update
            if pos.get("trailing_stop_pct") is not None:
                trail = pos["trailing_stop_pct"]
                if pos["side"] == "buy":
                    new_stop = price * (1 - trail)
                    pos["stop_loss"] = max(pos.get("stop_loss") or 0, new_stop)
                else:
                    new_stop = price * (1 + trail)
                    current_stop = pos.get("stop_loss")
                    if current_stop is None or new_stop < current_stop:
                        pos["stop_loss"] = new_stop

            # Check stop loss
            sl = pos.get("stop_loss")
            if sl is not None:
                if pos["side"] == "buy" and price <= sl:
                    self.close_position(pair, price, reason="stop_loss")
                    continue
                if pos["side"] == "sell" and price >= sl:
                    self.close_position(pair, price, reason="stop_loss")
                    continue

            # Check take profit
            tp = pos.get("take_profit")
            if tp is not None:
                if pos["side"] == "buy" and price >= tp:
                    self.close_position(pair, price, reason="take_profit")
                    continue
                if pos["side"] == "sell" and price <= tp:
                    self.close_position(pair, price, reason="take_profit")

        self._record_equity()

    def get_positions(self) -> List[dict]:
        """Return list of current open positions."""
        return list(self.positions.values())

    def get_pnl_summary(self) -> dict:
        """Return a snapshot of current PnL metrics.

        ⚠️  PAPER TRADING ONLY.
        """
        equity = self._compute_equity()
        total_pnl = equity - self.initial_balance
        daily_pnl = equity - self._daily_start_equity
        return {
            "balance": round(self.balance, 4),
            "equity": round(equity, 4),
            "daily_pnl": round(daily_pnl, 4),
            "total_pnl": round(total_pnl, 4),
            "total_pnl_pct": round(total_pnl / self.initial_balance * 100, 4),
            "open_positions": len(self.positions),
            "mode": "paper_trading",
        }

    def can_trade(self, risk_manager=None) -> bool:
        """Return True if new trades can be opened."""
        if risk_manager is not None:
            return not risk_manager.check_daily_loss_kill_switch(self)
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_slippage(self, price: float, side: str) -> float:
        """Apply configurable slippage in basis points."""
        slip = price * self.slippage_bps / 10_000
        return price + slip if side == "buy" else price - slip

    def _open_or_add_position(
        self,
        pair: str,
        side: str,
        quantity: float,
        fill_price: float,
        fee: float,
        stop_loss: Optional[float],
        take_profit: Optional[float],
        trailing_stop_pct: Optional[float],
        strategy_id: Optional[int],
    ) -> None:
        """Open a new position or average into an existing one."""
        existing = self.positions.get(pair)
        cost = fill_price * quantity + fee

        if existing is None:
            self.positions[pair] = {
                "pair": pair,
                "side": side,
                "quantity": quantity,
                "avg_entry_price": fill_price,
                "cost_basis": cost,
                "current_price": fill_price,
                "unrealized_pnl": 0.0,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "trailing_stop_pct": trailing_stop_pct,
                "strategy_id": strategy_id,
                "opened_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            # Average in
            total_qty = existing["quantity"] + quantity
            existing["avg_entry_price"] = (
                existing["avg_entry_price"] * existing["quantity"] + fill_price * quantity
            ) / total_qty
            existing["quantity"] = total_qty
            existing["cost_basis"] += cost
            if stop_loss is not None:
                existing["stop_loss"] = stop_loss
            if take_profit is not None:
                existing["take_profit"] = take_profit

    def _compute_equity(self) -> float:
        """Sum cash balance and unrealised position values."""
        unrealised = sum(
            pos.get("unrealized_pnl", 0.0) for pos in self.positions.values()
        )
        return self.balance + unrealised

    def _record_equity(self) -> None:
        """Append a snapshot to the equity curve."""
        self.equity_curve.append(
            {
                "time": datetime.now(timezone.utc).isoformat(),
                "equity": round(self._compute_equity(), 4),
            }
        )
