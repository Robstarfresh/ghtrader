# GHTrader Architecture

> ⚠️ **PAPER TRADING ONLY** — This system simulates trading using real Kraken market data. No real orders are placed and no real money is at risk.

---

## System Overview

GHTrader is an event-driven paper-trading simulation platform built on Kraken's public REST API. It ingests real-time OHLCV candles, computes technical indicators, generates trading signals via pluggable strategies, routes those signals through a paper broker that simulates fills, and tracks positions and PnL in a PostgreSQL database. A Next.js dashboard provides a live view of the system.

### Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, Tailwind CSS, Recharts |
| Backend API | FastAPI, SQLAlchemy (async), Alembic |
| Database | PostgreSQL 16 |
| Cache / Pub-Sub | Redis 7 |
| Market Data | Kraken public REST API |
| Containerisation | Docker Compose |

---

## Data Flow

```
Kraken Public REST API
        │
        ▼
┌───────────────────┐
│   DataIngester    │  Polls /OHLC endpoint per pair/timeframe
│  (ingestion/)     │  Upserts candles into `candles` table
└────────┬──────────┘
         │  new candle event
         ▼
┌───────────────────┐
│IndicatorEngine    │  Computes RSI, MACD, VWAP, ATR, Bollinger
│ (indicators/)     │  Stores computed values alongside candle rows
└────────┬──────────┘
         │  indicator snapshot
         ▼
┌───────────────────┐
│StrategyRouter     │  Iterates registered active strategies
│ (strategies/)     │  Each strategy returns a Signal (buy/sell/hold + strength)
└────────┬──────────┘
         │  aggregated signal
         ▼
┌───────────────────┐
│ RiskManager       │  Checks kill switch, daily loss cap, max positions
│ (risk/)           │  Sizes position using risk_per_trade_pct * equity / ATR
└────────┬──────────┘
         │  approved order
         ▼
┌───────────────────┐
│ PaperBroker       │  Simulates fill at current price + slippage
│ (broker/)         │  Deducts taker/maker fee from equity
│                   │  Opens position record in DB
└────────┬──────────┘
         │  position update
         ▼
┌───────────────────┐
│ PositionManager   │  Tracks open positions
│ (positions/)      │  Checks stop-loss, take-profit, trailing stop each tick
│                   │  Closes positions and records realized PnL
└────────┬──────────┘
         │  equity update
         ▼
┌───────────────────┐
│ PnLTracker        │  Computes running equity, daily PnL, snapshots equity
│ (pnl/)            │  Stores equity_snapshots for chart rendering
└───────────────────┘
```

---

## Strategy Signal Generation

### Signal Interface

Every strategy implements a common interface:

```python
class BaseStrategy:
    name: str
    params: dict

    def generate_signal(self, candles: pd.DataFrame, indicators: dict) -> Signal:
        """Return Signal with direction ('buy'|'sell'|'hold') and strength (0.0–1.0)."""
        ...
```

### Individual Strategies

#### MACD (`macd`)
- Computes MACD line (EMA12 − EMA26) and signal line (EMA9 of MACD)
- **Buy**: MACD crosses above signal line with positive histogram
- **Sell**: MACD crosses below signal line with negative histogram
- Strength proportional to histogram magnitude relative to price

#### RSI (`rsi`)
- 14-period RSI
- **Buy**: RSI crosses above oversold threshold (default 30) — mean reversion long
- **Sell**: RSI crosses below overbought threshold (default 70) — mean reversion short
- Strength = distance from midpoint (50) normalized 0–1

#### VWAP (`vwap`)
- Computes intraday VWAP using cumulative (price × volume) / cumulative volume
- **Buy**: Price crosses above VWAP (bullish intraday bias)
- **Sell**: Price crosses below VWAP (bearish intraday bias)
- Strength = deviation from VWAP as % of price, capped at 1.0

#### Breakout (`breakout`)
- Computes 20-period rolling high/low channel
- **Buy**: Price closes above 20-period high
- **Sell**: Price closes below 20-period low
- Strength = (close − channel_mid) / (channel_width / 2), capped at 1.0

### Signal Aggregation (Combined Strategy)

The `combined` strategy applies configurable weights to each sub-strategy:

```
weighted_score = Σ (strategy_i.strength × weight_i × direction_sign_i)
```

- If `weighted_score > threshold` → **Buy** signal with strength = weighted_score
- If `weighted_score < -threshold` → **Sell** signal with strength = |weighted_score|
- Otherwise → **Hold**

Default weights: MACD=0.35, RSI=0.25, VWAP=0.20, Breakout=0.20, threshold=0.50.

---

## Risk Management

### Kill Switch

The kill switch is a hard stop that prevents any new positions from being opened. It activates automatically when:

- `daily_loss_pct` ≥ `MAX_DAILY_LOSS_PCT` (default 5%)

The kill switch can be manually reset via `POST /api/v1/risk/reset` (or via the Risk page in the UI).

### Daily Loss Cap

The system tracks the daily PnL from midnight UTC. If realized + unrealized losses exceed the configured percentage of starting-of-day equity, the kill switch fires.

### Position Sizing

Position size is computed using ATR-based volatility scaling:

```
risk_amount = equity × RISK_PER_TRADE_PCT          # e.g. $100,000 × 0.02 = $2,000
atr_distance = ATR(14) × stop_loss_atr_multiplier   # e.g. 1.5×ATR
quantity = risk_amount / (atr_distance × price)
```

Maximum concurrent positions are enforced by `MAX_CONCURRENT_POSITIONS` (default 5).

### Stop Loss, Take Profit, Trailing Stop

Each position is opened with:
- **Stop loss**: `entry_price × (1 − stop_loss_pct)` for longs (default 2%)
- **Take profit**: `entry_price × (1 + take_profit_pct)` for longs (default 4%)
- **Trailing stop**: Updated each tick — if price moves favorably by `trailing_stop_pct` (default 1.5%), the stop is raised to lock in gains

On each candle close, the PositionManager evaluates all open positions and closes any that breach their stop or target.

### Fee and Slippage Simulation

| Parameter | Default | Description |
|-----------|---------|-------------|
| `PAPER_TAKER_FEE` | 0.26% | Applied to market orders |
| `PAPER_MAKER_FEE` | 0.16% | Applied to limit-like entries |
| `PAPER_SLIPPAGE_BPS` | 5 bps | Added to fill price in direction of trade |

---

## Backtest Methodology

### Event-Driven Simulation

Backtests replay historical candles sequentially in chronological order. For each candle:

1. Indicators are recomputed on the rolling window up to that candle
2. Strategy generates a signal
3. Risk checks are applied (using simulated equity at that point in time)
4. If approved, a paper fill is simulated at the candle's close price + slippage
5. Open positions are checked for stop/target breaches using the candle's high/low
6. PnL and equity are updated

### Look-Ahead Bias Prevention

- Indicators are computed strictly on candles with `timestamp <= current_candle.timestamp`
- Entry is executed at the **close** of the signal candle, not the open
- Stop/target checks use the **next** candle's OHLC to avoid look-ahead

### Performance Metrics

| Metric | Formula |
|--------|---------|
| **Net PnL** | `final_equity − initial_balance` |
| **Total Return %** | `(final_equity / initial_balance − 1) × 100` |
| **Win Rate** | `winning_trades / total_trades` |
| **Profit Factor** | `gross_profit / gross_loss` |
| **Sharpe Ratio** | `mean(daily_returns) / std(daily_returns) × √252` |
| **Sortino Ratio** | `mean(daily_returns) / std(negative_daily_returns) × √252` |
| **Max Drawdown** | `max((peak_equity − trough_equity) / peak_equity)` |
| **Avg Trade PnL** | `net_pnl / total_trades` |
| **Avg Win** | `gross_profit / winning_trades` |
| **Avg Loss** | `gross_loss / losing_trades` |
| **Calmar Ratio** | `annualized_return / max_drawdown` |

---

## Database Schema

### `candles`
Stores raw OHLCV data from Kraken.

| Column | Type | Description |
|--------|------|-------------|
| `id` | bigint PK | |
| `pair` | varchar | e.g. `XBT/USD` |
| `timeframe` | varchar | e.g. `1m` |
| `timestamp` | timestamptz | Candle open time |
| `open` | numeric | |
| `high` | numeric | |
| `low` | numeric | |
| `close` | numeric | |
| `volume` | numeric | |
| `created_at` | timestamptz | Row insertion time |

Unique index on `(pair, timeframe, timestamp)`.

### `positions`
Tracks both open and closed paper positions.

| Column | Type | Description |
|--------|------|-------------|
| `id` | bigint PK | |
| `pair` | varchar | |
| `side` | varchar | `buy` or `sell` |
| `quantity` | numeric | |
| `entry_price` | numeric | |
| `current_price` | numeric | Last known price |
| `exit_price` | numeric | Null if open |
| `unrealized_pnl` | numeric | |
| `realized_pnl` | numeric | Null if open |
| `fee_paid` | numeric | |
| `stop_loss` | numeric | |
| `take_profit` | numeric | |
| `trailing_stop` | numeric | |
| `exit_reason` | varchar | `stop_loss`, `take_profit`, `trailing_stop`, `signal`, `manual` |
| `strategy_name` | varchar | |
| `opened_at` | timestamptz | |
| `closed_at` | timestamptz | Null if open |

### `trades`
Alias view / denormalized table of closed positions for fast query access.

### `equity_snapshots`
Hourly snapshots of account equity used to render the equity curve.

| Column | Type | Description |
|--------|------|-------------|
| `id` | bigint PK | |
| `timestamp` | timestamptz | |
| `equity` | numeric | |
| `balance` | numeric | Cash balance |
| `open_pnl` | numeric | Unrealized PnL |

### `strategies`
Registry of available strategies and their active state.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer PK | |
| `name` | varchar unique | |
| `description` | text | |
| `params` | jsonb | Strategy-specific parameters |
| `is_active` | boolean | Whether engine uses this strategy |
| `created_at` | timestamptz | |

### `backtests`
Metadata and aggregate metrics for each backtest run.

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer PK | |
| `name` | varchar | User-provided label |
| `strategy_name` | varchar | |
| `pair` | varchar | |
| `timeframe` | varchar | |
| `start_date` | timestamptz | |
| `end_date` | timestamptz | |
| `initial_balance` | numeric | |
| `final_equity` | numeric | |
| `net_pnl` | numeric | |
| `total_return_pct` | numeric | |
| `win_rate` | numeric | 0.0–1.0 |
| `sharpe_ratio` | numeric | |
| `sortino_ratio` | numeric | |
| `max_drawdown_pct` | numeric | |
| `profit_factor` | numeric | |
| `total_trades` | integer | |
| `status` | varchar | `pending`, `running`, `completed`, `failed` |
| `config` | jsonb | Full strategy + risk config snapshot |
| `created_at` | timestamptz | |

### `backtest_trades`
Individual trades recorded during a backtest run. Same schema as `positions` with an additional `backtest_id` foreign key.

---

## API Overview

All endpoints are prefixed `/api/v1/`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | System health check |
| GET | `/pairs` | Tracked trading pairs |
| GET | `/candles/{pair}` | OHLCV candles |
| GET | `/engine/status` | Trading engine state |
| POST | `/engine/start` | Start trading engine |
| POST | `/engine/stop` | Stop trading engine |
| GET | `/positions` | Open positions |
| GET | `/positions/history` | Closed positions |
| GET | `/trades` | Paginated trade history |
| GET | `/pnl/summary` | Equity and PnL metrics |
| GET | `/pnl/equity-curve` | Equity snapshots for charting |
| GET | `/risk/status` | Risk manager state |
| POST | `/risk/reset` | Reset kill switch and daily loss counter |
| GET | `/strategies` | List strategies |
| PATCH | `/strategies/{id}` | Update strategy (toggle active, edit params) |
| POST | `/backtests` | Start a new backtest |
| GET | `/backtests` | List all backtests |
| GET | `/backtests/{id}` | Get single backtest with metrics |
| GET | `/backtests/{id}/trades` | Trades from a specific backtest |
| GET | `/backtests/leaderboard` | Aggregated strategy performance |
