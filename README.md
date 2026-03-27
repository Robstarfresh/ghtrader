# GHTrader

> ⚠️ **PAPER TRADING ONLY** — This system simulates trading using real Kraken market data. **No real orders are ever placed. No real money is at risk.** For research and educational purposes only.

A full-stack paper-trading simulation platform for Kraken crypto markets. Real-time OHLCV data ingestion, multi-strategy signal generation, risk-managed position simulation, backtesting engine, and live dashboard.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/SETUP.md](docs/SETUP.md) | Step-by-step installation, Docker Compose deployment, environment variable reference, local development setup |
| [docs/OPERATORS_MANUAL.md](docs/OPERATORS_MANUAL.md) | Day-to-day operations: starting the engine, managing strategies, running backtests, risk controls, monitoring, and troubleshooting |
| [docs/architecture.md](docs/architecture.md) | Full system architecture, data flow, strategy logic, backtest methodology, database schema |
| [docs/example-backtest-run.md](docs/example-backtest-run.md) | Example backtest results with metrics and interpretation |
| [docs/example-strategy-config.json](docs/example-strategy-config.json) | Example combined strategy configuration |

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Next.js Frontend                    │
│  Dashboard │ Positions │ Trades │ Backtests │ Risk        │
└─────────────────────┬────────────────────────────────────┘
                      │ REST API
┌─────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                        │
│                                                          │
│  DataIngester → Indicators → Strategies → RiskManager    │
│       │                           │            │         │
│       ▼                           ▼            ▼         │
│  candles table            Signal Router   PaperBroker    │
│       │                           │            │         │
│       └───────────────────────────┴────────────┘         │
│                                   │                      │
│                          PositionManager                 │
│                                   │                      │
│                            PnLTracker                    │
└────────────┬──────────────────────┬──────────────────────┘
             │                      │
     ┌───────▼──────┐    ┌──────────▼────────┐
     │  PostgreSQL  │    │      Redis         │
     │  (candles,   │    │  (pub/sub, cache)  │
     │  positions,  │    └───────────────────┘
     │  trades,     │
     │  backtests)  │
     └──────────────┘
```

---

## Quick Start

### Prerequisites
- Docker and Docker Compose

### 1. Clone and configure

```bash
git clone <repo>
cd ghtrader
cp .env.example .env
```

### 2. Start all services

```bash
make build
make up
```

### 3. Run migrations and seed strategies

```bash
make migrate
make seed
```

### 4. Backfill 30 days of historical data

```bash
make backfill
```

### 5. Start the trading engine

```bash
make start-engine
```

Open **http://localhost:3000** to view the dashboard.

---

## Make Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all containers in detached mode |
| `make down` | Stop all containers |
| `make build` | Rebuild Docker images |
| `make logs` | Tail container logs |
| `make migrate` | Run Alembic database migrations |
| `make seed` | Insert default strategies |
| `make backfill` | Backfill 30 days of OHLCV candles |
| `make start-engine` | Start the trading engine |
| `make stop-engine` | Stop the trading engine |
| `make run-backtest` | Run a sample backtest via curl |
| `make test` | Run backend test suite with coverage |
| `make lint` | Syntax-check Python source |
| `make shell-backend` | Open bash in backend container |
| `make shell-db` | Open psql in database container |

---

## Strategies

| Strategy | Type | Signal Logic |
|----------|------|-------------|
| `macd` | Trend following | Buy on MACD cross above signal; sell on cross below |
| `rsi` | Mean reversion | Buy when RSI crosses above 30 (oversold); sell on cross below 70 |
| `vwap` | Intraday bias | Buy on price cross above VWAP; sell on cross below |
| `breakout` | Momentum | Buy on close above 20-period high; sell on close below 20-period low |
| `combined` | Ensemble | Weighted aggregation of all four strategies with configurable threshold |

Strategies can be enabled/disabled live via the Strategies page or `PATCH /api/v1/strategies/{id}`.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | System health (DB, Redis, uptime) |
| GET | `/api/v1/pairs` | Tracked trading pairs |
| GET | `/api/v1/candles/{pair}` | OHLCV candles (`?timeframe=1m&limit=100`) |
| GET | `/api/v1/engine/status` | Engine running state |
| POST | `/api/v1/engine/start` | Start trading engine |
| POST | `/api/v1/engine/stop` | Stop trading engine |
| GET | `/api/v1/positions` | Open positions |
| GET | `/api/v1/positions/history` | Closed positions |
| GET | `/api/v1/trades` | Paginated trades (`?limit=25&offset=0`) |
| GET | `/api/v1/pnl/summary` | Equity, daily PnL, win rate |
| GET | `/api/v1/pnl/equity-curve` | Equity snapshots for chart |
| GET | `/api/v1/risk/status` | Kill switch, loss metrics |
| POST | `/api/v1/risk/reset` | Reset kill switch |
| GET | `/api/v1/strategies` | List strategies |
| PATCH | `/api/v1/strategies/{id}` | Toggle active / edit params |
| POST | `/api/v1/backtests` | Start a backtest |
| GET | `/api/v1/backtests` | List all backtests |
| GET | `/api/v1/backtests/{id}` | Backtest metrics |
| GET | `/api/v1/backtests/{id}/trades` | Trades from backtest |
| GET | `/api/v1/backtests/leaderboard` | Strategy leaderboard |

---

## Risk Controls

| Control | Default | Description |
|---------|---------|-------------|
| `MAX_DAILY_LOSS_PCT` | 5% | Kill switch threshold — halts all trading for the day |
| `MAX_CONCURRENT_POSITIONS` | 5 | Maximum simultaneous open positions |
| `RISK_PER_TRADE_PCT` | 2% | Percentage of equity risked per trade |
| Stop Loss | 2% | Hard stop per position |
| Take Profit | 4% | Target exit per position |
| Trailing Stop | 1.5% | Locks in gains as price moves favorably |
| `PAPER_TAKER_FEE` | 0.26% | Simulated taker fee per trade |
| `PAPER_MAKER_FEE` | 0.16% | Simulated maker fee per trade |
| `PAPER_SLIPPAGE_BPS` | 5 bps | Simulated slippage on fills |

---

## File Structure

```
ghtrader/
├── frontend/                    # Next.js 14 frontend
│   ├── src/
│   │   ├── app/                 # App Router pages
│   │   │   ├── page.tsx         # Dashboard
│   │   │   ├── positions/       # Positions page
│   │   │   ├── trades/          # Trades page
│   │   │   ├── backtests/       # Backtests page
│   │   │   ├── strategies/      # Strategies page
│   │   │   ├── risk/            # Risk management page
│   │   │   └── settings/        # Settings & health page
│   │   ├── components/
│   │   │   ├── layout/          # AppShell, Sidebar, Header
│   │   │   ├── ui/              # Card, Badge, StatCard, Skeleton
│   │   │   ├── charts/          # EquityCurve, DrawdownChart
│   │   │   └── tables/          # PositionsTable, TradesTable, BacktestTable
│   │   └── lib/
│   │       ├── api.ts           # Axios API client
│   │       └── utils.ts         # Formatting helpers
│   ├── Dockerfile
│   └── package.json
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings from env vars
│   │   ├── database.py          # Async SQLAlchemy engine
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── routers/             # API route handlers
│   │   ├── ingestion/           # Kraken data ingestion
│   │   ├── indicators/          # Technical indicator computation
│   │   ├── strategies/          # Trading strategy implementations
│   │   ├── broker/              # Paper broker / fill simulation
│   │   ├── risk/                # Risk manager
│   │   ├── pnl/                 # PnL tracking
│   │   ├── engine/              # Trading engine loop
│   │   ├── backtest/            # Backtest runner
│   │   └── scripts/             # seed.py, backfill.py
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # pytest test suite
│   └── Dockerfile
├── docs/
│   ├── architecture.md          # Full architecture documentation
│   ├── example-strategy-config.json
│   └── example-backtest-run.md
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

---

## Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` and edit as needed.

```bash
cp .env.example .env
```

Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgres://... | PostgreSQL connection string |
| `REDIS_URL` | redis://... | Redis connection string |
| `KRAKEN_API_BASE` | https://api.kraken.com | Kraken API base URL |
| `TRACKED_PAIRS` | XBT/USD,ETH/USD,SOL/USD | Comma-separated trading pairs |
| `PRIMARY_TIMEFRAME` | 1m | Candle timeframe |
| `PAPER_INITIAL_BALANCE` | 100000.0 | Starting paper balance |
| `LOG_LEVEL` | INFO | Logging verbosity |

---

## Disclaimer

> **⚠️ PAPER TRADING ONLY**
>
> GHTrader is a **simulation platform** that uses Kraken's **public** market data API.
>
> - **No real orders are placed** on any exchange
> - **No real money is at risk** at any time
> - All balances, positions, trades, and PnL figures are **purely simulated**
> - This software is provided for **research and educational purposes only**
> - Past simulated performance does not guarantee future real-world results
> - Crypto markets are highly volatile — never risk money you cannot afford to lose
>
> The authors and contributors of GHTrader accept no liability for any financial decisions made based on this software.