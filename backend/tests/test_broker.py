"""Tests for the PaperBroker.

⚠️  PAPER TRADING ONLY - all tests operate in simulation mode.
"""
from __future__ import annotations

import pytest

from app.broker.paper_broker import PaperBroker


INITIAL_BALANCE = 10_000.0
PRICE = 100.0
QUANTITY = 10.0


@pytest.fixture
def broker() -> PaperBroker:
    """Zero-slippage broker for deterministic tests."""
    return PaperBroker(
        initial_balance=INITIAL_BALANCE,
        taker_fee=0.0026,
        maker_fee=0.0016,
        slippage_bps=0,
    )


# ------------------------------------------------------------------
# Order submission
# ------------------------------------------------------------------

def test_submit_buy_order_reduces_balance(broker: PaperBroker) -> None:
    fill = broker.submit_order("XBT/USD", "buy", QUANTITY, PRICE)
    assert fill["status"] == "filled"
    fee = PRICE * QUANTITY * broker.taker_fee
    expected_balance = INITIAL_BALANCE - PRICE * QUANTITY - fee
    assert abs(broker.balance - expected_balance) < 1e-6


def test_position_opened_after_buy(broker: PaperBroker) -> None:
    broker.submit_order("XBT/USD", "buy", QUANTITY, PRICE)
    assert "XBT/USD" in broker.positions
    pos = broker.positions["XBT/USD"]
    assert pos["quantity"] == QUANTITY
    assert pos["avg_entry_price"] == PRICE


def test_rejected_order_when_insufficient_balance(broker: PaperBroker) -> None:
    result = broker.submit_order("XBT/USD", "buy", 1_000_000.0, PRICE)
    assert result["status"] == "rejected"
    assert result["reason"] == "insufficient_balance"


def test_rejected_sell_without_position(broker: PaperBroker) -> None:
    result = broker.submit_order("XBT/USD", "sell", QUANTITY, PRICE)
    assert result["status"] == "rejected"


# ------------------------------------------------------------------
# Fee calculation
# ------------------------------------------------------------------

def test_fee_applied(broker: PaperBroker) -> None:
    fill = broker.submit_order("ETH/USD", "buy", 1.0, 1000.0)
    expected_fee = 1000.0 * 1.0 * broker.taker_fee
    assert abs(fill["fee"] - expected_fee) < 1e-8


# ------------------------------------------------------------------
# Stop loss
# ------------------------------------------------------------------

def test_stop_loss_triggers(broker: PaperBroker) -> None:
    sl = PRICE * 0.95  # 5% below entry
    broker.submit_order("XBT/USD", "buy", QUANTITY, PRICE, stop_loss=sl)
    assert "XBT/USD" in broker.positions

    # Price drops to stop level
    broker.update_prices({"XBT/USD": sl - 0.01})
    assert "XBT/USD" not in broker.positions, "Stop loss should have closed the position"

    closed_trade = broker.trade_log[-1]
    assert closed_trade["reason"] == "stop_loss"


def test_stop_loss_does_not_trigger_above_level(broker: PaperBroker) -> None:
    sl = PRICE * 0.95
    broker.submit_order("XBT/USD", "buy", QUANTITY, PRICE, stop_loss=sl)
    broker.update_prices({"XBT/USD": PRICE * 0.96})  # above stop
    assert "XBT/USD" in broker.positions


# ------------------------------------------------------------------
# Take profit
# ------------------------------------------------------------------

def test_take_profit_triggers(broker: PaperBroker) -> None:
    tp = PRICE * 1.05  # 5% above entry
    broker.submit_order("XBT/USD", "buy", QUANTITY, PRICE, take_profit=tp)
    broker.update_prices({"XBT/USD": tp + 0.01})
    assert "XBT/USD" not in broker.positions, "Take profit should have closed the position"

    closed_trade = broker.trade_log[-1]
    assert closed_trade["reason"] == "take_profit"


def test_take_profit_does_not_trigger_below_level(broker: PaperBroker) -> None:
    tp = PRICE * 1.05
    broker.submit_order("XBT/USD", "buy", QUANTITY, PRICE, take_profit=tp)
    broker.update_prices({"XBT/USD": PRICE * 1.03})
    assert "XBT/USD" in broker.positions


# ------------------------------------------------------------------
# PnL
# ------------------------------------------------------------------

def test_pnl_summary_structure(broker: PaperBroker) -> None:
    summary = broker.get_pnl_summary()
    for key in ("balance", "equity", "daily_pnl", "total_pnl", "open_positions"):
        assert key in summary


def test_profitable_trade_increases_equity(broker: PaperBroker) -> None:
    broker.submit_order("XBT/USD", "buy", QUANTITY, PRICE)
    broker.close_position("XBT/USD", PRICE * 1.10, reason="take_profit")
    summary = broker.get_pnl_summary()
    assert summary["total_pnl"] > 0


def test_losing_trade_decreases_equity(broker: PaperBroker) -> None:
    broker.submit_order("XBT/USD", "buy", QUANTITY, PRICE)
    broker.close_position("XBT/USD", PRICE * 0.90, reason="stop_loss")
    summary = broker.get_pnl_summary()
    assert summary["total_pnl"] < 0


# ------------------------------------------------------------------
# Equity curve
# ------------------------------------------------------------------

def test_equity_curve_records_snapshots(broker: PaperBroker) -> None:
    initial_len = len(broker.equity_curve)
    broker.submit_order("XBT/USD", "buy", QUANTITY, PRICE)
    assert len(broker.equity_curve) > initial_len


def test_equity_curve_has_time_and_equity_keys(broker: PaperBroker) -> None:
    for entry in broker.equity_curve:
        assert "time" in entry
        assert "equity" in entry
