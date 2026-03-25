# Example Backtest Run

> ⚠️ **PAPER TRADING ONLY** — All figures below are simulated results from historical data replay. Not indicative of future performance. No real money was involved.

---

## Run Configuration

| Parameter | Value |
|-----------|-------|
| **Strategy** | MACD |
| **Pair** | XBT/USD |
| **Timeframe** | 1-minute candles |
| **Start Date** | 2024-01-01 00:00 UTC |
| **End Date** | 2024-03-01 00:00 UTC |
| **Period** | ~61 days |
| **Initial Balance** | $100,000.00 |
| **Taker Fee** | 0.26% |
| **Maker Fee** | 0.16% |
| **Slippage** | 5 bps |
| **Stop Loss** | 2.0% |
| **Take Profit** | 4.0% |
| **Trailing Stop** | 1.5% |
| **Risk Per Trade** | 2.0% of equity |
| **Max Concurrent Positions** | 5 |

---

## Aggregate Performance Metrics

| Metric | Value |
|--------|-------|
| **Net PnL** | +$8,412.37 |
| **Total Return %** | +8.41% |
| **Max Drawdown** | -4.23% |
| **Sharpe Ratio** | 1.47 |
| **Sortino Ratio** | 2.14 |
| **Calmar Ratio** | 1.99 |
| **Win Rate** | 54.3% |
| **Total Trades** | 162 |
| **Winning Trades** | 88 |
| **Losing Trades** | 74 |
| **Avg Trade PnL** | +$51.93 |
| **Avg Win** | +$318.72 |
| **Avg Loss** | -$241.18 |
| **Profit Factor** | 1.61 |
| **Total Fees Paid** | $1,240.55 |
| **Avg Hold Time** | 2h 14m |

---

## Equity Curve Summary

| Date | Equity | Daily PnL | Drawdown |
|------|--------|-----------|----------|
| 2024-01-01 | $100,000.00 | — | 0.00% |
| 2024-01-08 | $101,284.50 | +$183.50 | -0.41% |
| 2024-01-15 | $102,891.20 | +$229.10 | -0.23% |
| 2024-01-22 | $101,740.80 | -$164.30 | -1.12% |
| 2024-01-29 | $103,512.60 | +$396.40 | -0.08% |
| 2024-02-05 | $105,210.30 | +$242.50 | -0.60% |
| 2024-02-12 | $103,890.40 | -$188.70 | -1.82% |
| 2024-02-19 | $106,741.90 | +$407.40 | -0.14% |
| 2024-02-26 | $108,312.10 | +$224.60 | -0.07% |
| 2024-03-01 | $108,412.37 | +$14.31 | 0.00% |

Peak equity: **$109,204.80** (2024-02-28)
Max drawdown trough: **$104,590.12** (2024-02-13) — drawdown of **4.23%** from the 2024-02-12 peak

---

## Monthly Breakdown

| Month | Trades | Win Rate | Net PnL | Return |
|-------|--------|----------|---------|--------|
| January 2024 | 84 | 52.4% | +$3,512.60 | +3.51% |
| February 2024 | 78 | 56.4% | +$4,899.77 | +4.74% |

---

## Trade Distribution

| Bucket | Count | % of Total |
|--------|-------|-----------|
| PnL > +$500 | 14 | 8.6% |
| PnL +$100–$500 | 42 | 25.9% |
| PnL $0–$100 | 32 | 19.8% |
| PnL -$100–$0 | 38 | 23.5% |
| PnL -$100–-$300 | 28 | 17.3% |
| PnL < -$300 | 8 | 4.9% |

---

## Signal Quality

| Signal Type | Count | Win Rate | Avg PnL |
|-------------|-------|----------|---------|
| MACD Cross Up (strong) | 47 | 63.8% | +$124.50 |
| MACD Cross Up (weak) | 38 | 47.4% | +$18.20 |
| MACD Cross Down (strong) | 41 | 58.5% | -$88.30* |
| MACD Cross Down (weak) | 36 | 44.4% | -$31.10* |

*Short-side trades show negative avg PnL in a bull-trending market — expected behaviour.

---

## Interpretation

The MACD strategy produced a modest **+8.41% return** over 61 days on a $100,000 paper account, against a BTC market that trended upward ~25% in the same period. The strategy underperformed buy-and-hold but achieved a reasonable risk-adjusted return with a **Sharpe of 1.47** and max drawdown held below 5% (the kill-switch threshold was never triggered).

Key observations:
- Win rate of 54.3% and profit factor of 1.61 indicate edge above randomness
- Short signals significantly underperformed in a trending market — consider disabling shorts or applying trend filter
- Fee drag of $1,240 (~1.24% of initial balance) is non-trivial at 1-minute granularity — higher timeframes may improve net return

---

> This is a simulated backtest. Past performance of a simulation does not guarantee future results in live markets.
