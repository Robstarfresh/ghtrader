# GHTrader — Operator's Manual

> ⚠️ **PAPER TRADING ONLY** — GHTrader simulates trading using Kraken's public market data.
> No real orders are placed. No real money is at risk.

This manual covers the day-to-day operation of a running GHTrader instance.
For initial installation, see [SETUP.md](SETUP.md).

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Startup & Shutdown](#2-startup--shutdown)
3. [Dashboard Tour](#3-dashboard-tour)
4. [Starting & Stopping the Trading Engine](#4-starting--stopping-the-trading-engine)
5. [Managing Strategies](#5-managing-strategies)
6. [Running Backtests](#6-running-backtests)
7. [Risk Management](#7-risk-management)
8. [Market Data & Pairs](#8-market-data--pairs)
9. [Monitoring & Logs](#9-monitoring--logs)
10. [Troubleshooting](#10-troubleshooting)
11. [Maintenance](#11-maintenance)

---

## 1. System Overview

GHTrader has four moving parts that must all be healthy before live paper trading can begin:

```
Browser  →  Frontend (port 3000)  →  Backend API (port 8000)
                                          │
                                    PostgreSQL (5432)
                                    Redis     (6379)
```

The **trading engine** is a background loop inside the backend process. It is *not* a separate
container — it runs as an `asyncio` task inside the FastAPI process. It is started and stopped
via the `/api/v1/engine/start` and `/api/v1/engine/stop` endpoints (or through the dashboard
Header).

### State that survives a restart

- **Candle history** — stored in PostgreSQL. Safe across restarts.
- **Backtest records** — stored in PostgreSQL. Safe across restarts.
- **Strategy configuration** — stored in PostgreSQL. Safe across restarts.
- **Paper broker state** (balance, open positions, equity curve) — held **in memory** inside
  the backend process. **Lost on backend restart.** The starting balance is reset to
  `PAPER_INITIAL_BALANCE` each time the backend container starts.

---

## 2. Startup & Shutdown

### Full stack startup

```bash
# From the repo root
make up
```

Wait ~10 seconds for the database healthcheck to pass and the backend to complete its
migration step, then verify:

```bash
curl -s http://localhost:8000/api/v1/health
# → {"status":"ok","version":"1.0.0","mode":"paper_trading",...}
```

### Start the trading engine

The stack being up does **not** automatically start the trading engine.
You must start it explicitly:

```bash
make start-engine
# → {"ok":true,"detail":"Engine start requested"}
```

Or use the **Start Engine** button in the dashboard Header.

### Graceful stop — engine only

```bash
make stop-engine
# → {"ok":true,"detail":"Engine stopped"}
```

Stopping the engine does not close any open positions. They remain in memory and will
continue to be tracked if the engine is restarted.

### Full stack shutdown

```bash
make down
```

This stops and removes all containers. Postgres data is preserved in the `postgres_data`
Docker volume.

### Restart the backend only (e.g. after config change)

```bash
docker compose restart backend
```

> **Note:** Restarting the backend resets the in-memory paper broker state (balance, open
> positions, equity curve). Running backtests and strategy configurations in the database
> are not affected.

---

## 3. Dashboard Tour

Open **<http://localhost:3000>** to access the dashboard.
The sidebar on the left provides navigation to all pages.
The header shows live engine status and current equity.

### Dashboard (Home — `/`)

Auto-refreshes every 5 seconds. Shows:

| Widget | Description |
|--------|-------------|
| **Balance** | Current virtual cash (unfilled = capital not deployed) |
| **Equity** | Balance + unrealized PnL across all open positions |
| **Daily PnL** | Change in equity since midnight UTC (or since last reset) |
| **Win Rate** | Percentage of closed trades that were profitable |
| **Equity Curve** | Time-series chart of equity since engine start |
| **Open Positions** | Table of currently held positions |
| **Recent Trades** | Last few closed trades |
| **Risk Status** | Kill switch state, daily loss %, positions count |

### Positions (`/positions`)

Two tabs:
- **Open** — currently held positions with unrealized PnL, stop loss, take profit levels
- **History** — all closed positions with realized PnL and exit reason

### Trades (`/trades`)

Paginated list of all closed trades: entry/exit time, prices, quantity, PnL, fees, and the
reason the trade was closed (`stop_loss`, `take_profit`, `trailing_stop`, `signal`, or
`manual`).

### Backtests (`/backtests`)

- **Run new backtest** form: select pair, strategy, date range, and starting balance
- **Past backtest list** with key metrics (return %, Sharpe, max drawdown, win rate)
- **Strategy leaderboard**: ranks all completed backtests by return %

### Strategies (`/strategies`)

Shows all five built-in strategies. Each card displays:
- Current enabled/disabled state
- Key parameters
- Toggle button to enable or disable the strategy in the live engine

Changes take effect on the next engine cycle (within 60 seconds).

### Risk (`/risk`)

Shows the live risk manager state:
- Kill switch active/inactive
- Daily PnL and trade count
- Open position count

Includes a **Reset** button to clear the kill switch and reset daily counters.

### Settings (`/settings`)

Shows the current application configuration (pairs, fees, timeframe) read from the running
backend. Configuration changes require editing `.env` and restarting the backend container.

---

## 4. Starting & Stopping the Trading Engine

### Start via API

```bash
curl -X POST http://localhost:8000/api/v1/engine/start
```

Response:

```json
{"ok": true, "detail": "Engine start requested"}
```

### Stop via API

```bash
curl -X POST http://localhost:8000/api/v1/engine/stop
```

Response:

```json
{"ok": true, "detail": "Engine stopped"}
```

### Check engine status

```bash
curl -s http://localhost:8000/api/v1/engine/status | python3 -m json.tool
```

Response when running:

```json
{
  "running": true,
  "equity": 100000.0,
  "positions_count": 2,
  "mode": "paper_trading"
}
```

### What the engine does

Once started, the engine runs a continuous loop:

1. **Fetch** the latest candles for each tracked pair from Kraken's public REST API
2. **Compute** technical indicators (RSI, MACD, VWAP, ATR, Bollinger Bands) on the rolling
   candle window
3. **Evaluate** each active strategy to produce a signal (buy / sell / hold + strength)
4. **Check risk** — kill switch, position limits, daily trade cap, cash reserve
5. **Submit** paper orders to the broker if a signal passes risk checks
6. **Update** open positions — check stop loss, take profit, trailing stop against latest prices
7. **Record** equity snapshot

---

## 5. Managing Strategies

### Built-in strategies

| Name | Type | Default params |
|------|------|---------------|
| `macd` | Trend following | fast=12, slow=26, signal=9 |
| `rsi` | Mean reversion | period=14, oversold=30, overbought=70 |
| `vwap` | Intraday bias | — |
| `breakout` | Momentum | period=20 |
| `combined` | Weighted ensemble | threshold=0.5 |

### Enable or disable a strategy

**Via the dashboard:** Go to **Strategies** page → click the toggle on any strategy card.

**Via the API:**

```bash
# Get strategy IDs
curl -s http://localhost:8000/api/v1/strategies | python3 -m json.tool

# Disable strategy ID 1 (macd)
curl -s -X PATCH http://localhost:8000/api/v1/strategies/1 \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Re-enable strategy ID 1
curl -s -X PATCH http://localhost:8000/api/v1/strategies/1 \
  -H "Content-Type: application/json" \
  -d '{"is_active": true}'
```

### Modify strategy parameters

```bash
# Change RSI oversold/overbought thresholds
curl -s -X PATCH http://localhost:8000/api/v1/strategies/2 \
  -H "Content-Type: application/json" \
  -d '{"params": {"period": 14, "oversold": 25, "overbought": 75}}'
```

Parameter changes are persisted to the database and take effect on the next engine cycle.

### Running a single strategy

To trade with only one strategy, disable all others via the Strategies page or API,
then ensure the desired strategy is enabled.

### The combined strategy

The `combined` strategy aggregates signals from all active sub-strategies using a weighted
vote. The default weight distribution is:
- MACD: 35%
- RSI: 25%
- VWAP: 20%
- Breakout: 20%
- Threshold: 0.50 (a weighted score above 0.50 triggers a buy; below −0.50 triggers a sell)

When `combined` is active, the engine uses it as the signal source. The individual strategies
(`macd`, `rsi`, `vwap`, `breakout`) act as sub-components — disabling them in the database
removes them from the weighted vote inside `combined`.

---

## 6. Running Backtests

### Via the dashboard

1. Go to **Backtests** (`/backtests`)
2. Fill in the **Run New Backtest** form:
   - **Name** — a label for your reference
   - **Strategy** — one of `macd`, `rsi`, `vwap`, `breakout`, or `combined`
   - **Pair** — e.g. `XBT/USD` (must have candle data for the selected period)
   - **Timeframe** — `1m` (primary timeframe)
   - **Start date / End date** — date range to replay
   - **Initial balance** — virtual starting capital
3. Click **Run Backtest**

The backtest result appears in the list below the form once complete.

### Via the API (curl)

```bash
curl -X POST http://localhost:8000/api/v1/backtests \
  -H "Content-Type: application/json" \
  -d '{
    "name": "macd-btc-jan2024",
    "strategy_name": "macd",
    "pair": "XBT/USD",
    "timeframe": "1m",
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-02-01T00:00:00",
    "initial_balance": 100000
  }'
```

### Via the Makefile (sample run)

```bash
make run-backtest
```

This runs a sample two-month MACD backtest on XBT/USD with $100,000 starting balance.

### Retrieving results

```bash
# List all backtest runs
curl -s http://localhost:8000/api/v1/backtests | python3 -m json.tool

# Get metrics for backtest ID 1
curl -s http://localhost:8000/api/v1/backtests/1 | python3 -m json.tool

# Get individual trades for backtest ID 1
curl -s http://localhost:8000/api/v1/backtests/1/trades | python3 -m json.tool

# Strategy leaderboard (requires at least one completed backtest)
curl -s http://localhost:8000/api/v1/backtests/leaderboard | python3 -m json.tool
```

### Key backtest metrics explained

| Metric | Meaning |
|--------|---------|
| `net_pnl` | Absolute profit/loss after fees |
| `return_pct` | Percentage return on initial balance |
| `max_drawdown_pct` | Largest peak-to-trough equity decline |
| `win_rate` | Fraction of trades that were profitable (0.0–1.0) |
| `profit_factor` | Gross profit ÷ gross loss (>1 means net profitable) |
| `sharpe_ratio` | Risk-adjusted return (annualised). > 1.0 is generally considered good. |
| `expectancy` | Expected dollar PnL per trade |
| `trades_per_day` | Average number of trades per calendar day |
| `exposure_pct` | Percentage of candles where a position was open |

### Ensuring enough candle data

Before running a backtest, check that candle data exists for the pair and date range you
want to test:

```bash
make shell-db
SELECT pair, MIN(open_time), MAX(open_time), COUNT(*)
FROM candles
GROUP BY pair;
\q
```

If the date range you need is not covered, backfill more data:

```bash
docker compose exec backend python -m app.scripts.backfill \
  --pairs XBT/USD \
  --days 90
```

---

## 7. Risk Management

### Understanding the kill switch

The kill switch is a hard safety mechanism. When the simulated account loses more than
`MAX_DAILY_LOSS_PCT` (default 5%) of its start-of-day equity, the engine stops opening new
positions for the remainder of the day.

The kill switch fires automatically. You will see a warning in the backend logs:

```
risk_kill_switch_triggered daily_loss_pct=5.12 threshold_pct=5.0
```

And the Risk page in the dashboard will show `Kill Switch: ACTIVE`.

### Checking risk status

```bash
curl -s http://localhost:8000/api/v1/risk/status | python3 -m json.tool
```

Response:

```json
{
  "kill_switch_active": false,
  "daily_pnl": -1240.50,
  "daily_trades": 12,
  "open_positions": 3,
  "mode": "paper_trading"
}
```

### Resetting the kill switch

After reviewing what triggered the kill switch, reset the daily counters to allow trading
to resume:

```bash
curl -X POST http://localhost:8000/api/v1/risk/reset
# → {"ok": true, "detail": "Daily risk counters reset"}
```

Or use the **Reset** button on the Risk page.

### Hard-coded risk parameters

Some risk parameters are hard-coded in `RiskManager` and cannot currently be changed via
environment variables. To modify them, edit `backend/app/risk/manager.py` and rebuild:

| Constant | Value | Description |
|----------|-------|-------------|
| `DAILY_TRADE_CAP` | 50 | Maximum trades per day |
| `MIN_CASH_RESERVE_PCT` | 0.10 | Minimum cash to keep uninvested (10%) |
| `MAX_EXPOSURE_PER_PAIR_PCT` | 0.20 | Maximum equity in any single pair (20%) |

### Understanding position sizing

Position size is calculated using fixed-fractional risk sizing:

```
risk_amount   = current_equity × RISK_PER_TRADE_PCT
risk_per_unit = |entry_price - stop_loss_price|
quantity      = risk_amount / risk_per_unit
```

The resulting quantity is then capped by the available balance minus the cash reserve.

Default stop loss is 2% below entry (for long positions), take profit is 4% above entry,
and trailing stop trails at 1.5% below the highest price reached since entry.

---

## 8. Market Data & Pairs

### Tracked pairs

The set of pairs ingested and traded is controlled by `TRACKED_PAIRS` in `.env`.
Changes require restarting the backend:

```bash
# Edit .env: TRACKED_PAIRS=XBT/USD,ETH/USD,SOL/USD,ADA/USD
docker compose restart backend
# Then backfill data for the new pair
docker compose exec backend python -m app.scripts.backfill --pairs ADA/USD --days 30
```

### Kraken pair notation

Kraken uses non-standard ticker names for some assets. Common mappings:

| Common name | Kraken notation |
|-------------|----------------|
| BTC/USD | `XBT/USD` |
| ETH/USD | `ETH/USD` |
| SOL/USD | `SOL/USD` |
| ADA/USD | `ADA/USD` |
| DOT/USD | `DOT/USD` |
| MATIC/USD | `MATIC/USD` |

Use `XBT` (not `BTC`) for Bitcoin. The client maps `/` to an empty string when calling the
Kraken OHLC endpoint (e.g. `XBTUSD`).

### Manually backfilling a pair

```bash
docker compose exec backend python -m app.scripts.backfill \
  --pairs XBT/USD \
  --days 60
```

### Checking data freshness

```bash
curl -s "http://localhost:8000/api/v1/candles/XBT%2FUSD?timeframe=1m&limit=1" \
  | python3 -m json.tool
```

The `open_time` of the last candle should be within the last few minutes when the engine
is running.

### Getting the list of tracked pairs via API

```bash
curl -s http://localhost:8000/api/v1/pairs | python3 -m json.tool
```

---

## 9. Monitoring & Logs

### Tail all container logs

```bash
make logs
# equivalent: docker compose logs -f
```

### Tail a specific service

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
docker compose logs -f redis
```

### Typical backend log lines

Successful candle fetch:
```
{"event":"candles_upserted","pair":"XBT/USD","timeframe":"1m","count":1,...}
```

Position opened:
```
{"event":"position_opened","pair":"XBT/USD","side":"buy","quantity":0.0234,"price":67400.0,...}
```

Position closed at take profit:
```
{"event":"position_closed","pair":"XBT/USD","reason":"take_profit","pnl":156.32,...}
```

Kill switch triggered:
```
{"level":"warning","event":"risk_kill_switch_triggered","daily_loss_pct":5.12,...}
```

### Useful API checks from the command line

```bash
# Summary of current PnL
curl -s http://localhost:8000/api/v1/pnl/summary | python3 -m json.tool

# Open positions
curl -s http://localhost:8000/api/v1/positions | python3 -m json.tool

# Last 10 trades
curl -s "http://localhost:8000/api/v1/trades?limit=10" | python3 -m json.tool

# Risk state
curl -s http://localhost:8000/api/v1/risk/status | python3 -m json.tool
```

### Log level

Change `LOG_LEVEL=DEBUG` in `.env` and restart the backend for verbose output including
indicator computation details and position sizing calculations.

---

## 10. Troubleshooting

### Backend container keeps restarting

```bash
docker compose logs backend --tail 50
```

**Common causes:**
- `DATABASE_URL` is wrong or the database is not ready — look for `connection refused` or
  `password authentication failed`
- Migration failure — look for `alembic` errors
- Import error in Python code — look for `ModuleNotFoundError` or `ImportError`

### `make migrate` fails with "relation already exists"

The migration has already been applied. This is safe to ignore. The backend handles this
automatically on startup (`alembic upgrade head` is idempotent).

### Dashboard shows "Failed to load" on all panels

Check that the backend is running and reachable:

```bash
curl http://localhost:8000/api/v1/health
```

If the backend is running but the frontend cannot reach it, check `NEXT_PUBLIC_API_URL`
in `.env`. For local Docker Compose, it should be `http://localhost:8000` (the browser
makes requests directly to the backend, not via the frontend container).

### Engine status shows `running: false` after restart

The trading engine does not auto-start when the backend restarts. Always explicitly start
it after any backend restart:

```bash
make start-engine
```

### No candles in the database after backfill

Check Kraken connectivity:

```bash
curl -s "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1" | python3 -m json.tool
```

If this returns data, check the backend logs for errors from the ingestion module:

```bash
docker compose logs backend | grep -i "error\|exception\|kraken"
```

### Kill switch is active and trading has stopped

1. Check the Risk page or `GET /api/v1/risk/status` to confirm
2. Review recent trades to understand what caused the loss
3. When ready to resume, reset:

```bash
curl -X POST http://localhost:8000/api/v1/risk/reset
make start-engine
```

### High memory usage

Each backend restart clears the in-memory equity curve. If the process has been running
for a long time and memory is growing, restart the backend:

```bash
docker compose restart backend
make start-engine
```

### Port already in use

If Docker reports `address already in use` for port 5432, 6379, 8000, or 3000:

1. Find what is using the port: `lsof -i :5432`
2. Either stop that process, or change the host port in `docker-compose.yml` (left side of
   the `ports:` mapping).

---

## 11. Maintenance

### Backup the database

```bash
docker compose exec db pg_dump -U trader ghtrader > ghtrader_backup_$(date +%Y%m%d).sql
```

### Restore a database backup

```bash
make down
docker volume rm ghtrader_postgres_data
make up
# Wait for db to be healthy, then:
cat ghtrader_backup_20240315.sql | docker compose exec -T db psql -U trader ghtrader
```

### Clean up old candle data

To remove candles older than 90 days (to save disk space):

```bash
make shell-db
DELETE FROM candles WHERE open_time < NOW() - INTERVAL '90 days';
VACUUM ANALYZE candles;
\q
```

### Clean up old backtest records

```bash
make shell-db
-- Remove backtests older than 30 days
DELETE FROM backtest_trades WHERE backtest_id IN (
  SELECT id FROM backtests WHERE created_at < NOW() - INTERVAL '30 days'
);
DELETE FROM backtest_metrics WHERE backtest_id IN (
  SELECT id FROM backtests WHERE created_at < NOW() - INTERVAL '30 days'
);
DELETE FROM backtests WHERE created_at < NOW() - INTERVAL '30 days';
\q
```

### Extend disk space

The `postgres_data` volume grows as more candle history is stored.
To check its size:

```bash
docker system df -v | grep ghtrader
```

Prune all unused Docker objects (images, stopped containers, unused volumes):

```bash
docker system prune --volumes
```

> **Warning:** `docker system prune --volumes` removes **all** unused volumes, including
> `postgres_data` if the database container is stopped. Only run this if you have a backup
> or are happy to lose all data.

### Updating dependencies

After a code update that changes `backend/requirements.txt` or `frontend/package.json`:

```bash
make down
make build
make up
```

Docker Compose rebuilds only the layers that changed.

### Running the test suite

```bash
make test
# equivalent: docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing
```

All 40 tests should pass. A failing test after an update indicates a regression that should
be investigated before running the engine in paper trading mode.
