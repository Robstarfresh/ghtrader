# GHTrader — Setup & Deployment Guide

> ⚠️ **PAPER TRADING ONLY** — GHTrader simulates trading using Kraken's public market data.
> No real orders are placed. No real money is at risk.

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Quick Start (Docker Compose)](#2-quick-start-docker-compose)
3. [Environment Configuration](#3-environment-configuration)
4. [First-Run Checklist](#4-first-run-checklist)
5. [Verifying the Installation](#5-verifying-the-installation)
6. [Local Development (Without Docker)](#6-local-development-without-docker)
7. [Upgrading](#7-upgrading)
8. [Resetting All Data](#8-resetting-all-data)
9. [Port Reference](#9-port-reference)

---

## 1. System Requirements

### Minimum (Docker deployment)

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 2 GB | 4 GB |
| Disk | 5 GB | 20 GB |
| Docker Engine | 24.x | 25.x+ |
| Docker Compose | v2.20+ | v2.24+ |
| Outbound internet | HTTPS to `api.kraken.com` | — |

### For local development (no Docker)

| Requirement | Version |
|-------------|---------|
| Python | 3.12 |
| Node.js | 20 LTS |
| PostgreSQL | 16 |
| Redis | 7 |

### Check Docker versions

```bash
docker --version          # Docker version 24.x or higher
docker compose version    # Docker Compose version v2.20.x or higher
```

If Docker Compose shows `v1.x` you are using the legacy `docker-compose` command.
Update Docker Desktop or install the Compose plugin: <https://docs.docker.com/compose/install/>

---

## 2. Quick Start (Docker Compose)

This is the recommended deployment method. All four services (database, cache, backend, frontend)
are managed by a single `docker-compose.yml`.

### Step 1 — Clone the repository

```bash
git clone https://github.com/Robstarfresh/ghtrader.git
cd ghtrader
```

### Step 2 — Create your environment file

```bash
cp .env.example .env
```

Edit `.env` if you need to change the starting balance, tracked pairs, or any other setting.
The defaults work out-of-the-box for local Docker Compose deployment. See
[Section 3](#3-environment-configuration) for a full variable reference.

### Step 3 — Build the Docker images

```bash
make build
# equivalent: docker compose build
```

This downloads base images and installs Python and Node dependencies.
Expect 3–5 minutes on first run.

### Step 4 — Start all services

```bash
make up
# equivalent: docker compose up -d
```

Services started:
| Service | Image | Port |
|---------|-------|------|
| `db` | postgres:16-alpine | 5432 |
| `redis` | redis:7-alpine | 6379 |
| `backend` | built from `./backend` | 8000 |
| `frontend` | built from `./frontend` | 3000 |

The `backend` container automatically runs `alembic upgrade head` before starting uvicorn,
so database migrations are applied every time the container starts.

### Step 5 — Seed default strategies

```bash
make seed
# equivalent: docker compose exec backend python -m app.scripts.seed
```

This inserts the five built-in strategies (`macd`, `rsi`, `vwap`, `breakout`, `combined`)
into the `strategies` table. It is idempotent — safe to run multiple times.

### Step 6 — Backfill historical market data

```bash
make backfill
# equivalent: docker compose exec backend python -m app.scripts.backfill \
#   --pairs XBT/USD,ETH/USD,SOL/USD --days 30
```

This fetches 30 days of 1-minute OHLCV candles from Kraken's public REST API and stores
them in the `candles` table. Expect several minutes depending on your internet connection.

To backfill a different set of pairs or a longer history:

```bash
docker compose exec backend python -m app.scripts.backfill \
  --pairs XBT/USD,ETH/USD,SOL/USD,ADA/USD \
  --days 60
```

### Step 7 — Open the dashboard

Navigate to **<http://localhost:3000>** in your browser.

The backend API and interactive docs are available at:
- API: **<http://localhost:8000/api/v1/>**
- Swagger UI: **<http://localhost:8000/docs>**
- ReDoc: **<http://localhost:8000/redoc>**

---

## 3. Environment Configuration

All runtime configuration is set via environment variables. Copy `.env.example` to `.env`
and edit before starting the stack.

Variables marked **Docker only** have different defaults when running inside Docker Compose
(where `db` and `redis` are the service hostnames). If running locally without Docker, use
`localhost` instead.

### Database

| Variable | Docker default | Local default | Description |
|----------|----------------|---------------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://trader:trader@db:5432/ghtrader` | `postgresql+asyncpg://trader:trader@localhost:5432/ghtrader` | SQLAlchemy async connection string. Must use `asyncpg` driver. |

### Redis

| Variable | Docker default | Local default | Description |
|----------|----------------|---------------|-------------|
| `REDIS_URL` | `redis://redis:6379/0` | `redis://localhost:6379/0` | Redis connection URL. Database index 0 is used by default. |

### Kraken API

| Variable | Default | Description |
|----------|---------|-------------|
| `KRAKEN_API_BASE` | `https://api.kraken.com` | Base URL for Kraken's public REST API. Change only if using a proxy. |

### Trading pairs & timeframe

| Variable | Default | Description |
|----------|---------|-------------|
| `TRACKED_PAIRS` | `XBT/USD,ETH/USD,SOL/USD` | Comma-separated list of Kraken spot pairs to ingest and trade. Use Kraken notation (`XBT` not `BTC`). |
| `PRIMARY_TIMEFRAME` | `1m` | Primary candle resolution for market data ingestion and strategy evaluation. |

### Paper broker

| Variable | Default | Description |
|----------|---------|-------------|
| `PAPER_INITIAL_BALANCE` | `100000.0` | Starting virtual cash balance in USD. |
| `PAPER_TAKER_FEE` | `0.0026` | Simulated taker fee (0.26%) — applied to market orders. |
| `PAPER_MAKER_FEE` | `0.0016` | Simulated maker fee (0.16%) — applied to passive limit-style entries. |
| `PAPER_SLIPPAGE_BPS` | `5` | Simulated slippage in basis points added to the fill price in the direction of the trade. |

### Risk controls

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONCURRENT_POSITIONS` | `5` | Maximum number of open positions at any time. New signals are ignored when this limit is reached. |
| `MAX_DAILY_LOSS_PCT` | `0.05` | Daily loss kill switch threshold (5%). If simulated equity falls more than this percentage from the start-of-day value, all new trading is halted until the kill switch is reset. |
| `RISK_PER_TRADE_PCT` | `0.02` | Fixed-fractional risk per trade (2%). Position size is calculated so that the distance from entry to stop loss equals this percentage of current equity. |

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Python logging level. Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `ENV` | `development` | Environment label. Set to `production` in production deployments. |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL the frontend uses to reach the backend API. In Docker Compose this is still `http://localhost:8000` because API calls are made from the browser, not from inside the container. |

---

## 4. First-Run Checklist

Use this checklist after a fresh clone to ensure everything is wired up correctly.

- [ ] `cp .env.example .env` — environment file created
- [ ] `make build` — Docker images built without errors
- [ ] `make up` — all four containers running (`docker compose ps` shows `Up` for db, redis, backend, frontend)
- [ ] `make seed` — strategies seeded (`Seeded 5 strategies` in output, or `Already seeded` if re-run)
- [ ] `make backfill` — historical data loaded (check `Done: XBT/USD` etc. in output)
- [ ] `curl http://localhost:8000/api/v1/health` — returns `{"status":"ok",...}`
- [ ] `http://localhost:3000` — dashboard loads in browser
- [ ] `make start-engine` — engine start requested (`{"ok":true,...}`)
- [ ] Dashboard shows engine running and equity at starting balance

---

## 5. Verifying the Installation

### Health check

```bash
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
```

Expected response:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2024-03-15T10:30:00.000000+00:00",
  "mode": "paper_trading"
}
```

### Check all containers are running

```bash
docker compose ps
```

Expected output (all services should show `running`):

```
NAME              IMAGE                    STATUS
ghtrader-db-1     postgres:16-alpine       Up (healthy)
ghtrader-redis-1  redis:7-alpine           Up (healthy)
ghtrader-backend-1 ghtrader-backend        Up
ghtrader-frontend-1 ghtrader-frontend      Up
```

### Check the database has candle data

```bash
make shell-db
# Inside psql:
SELECT pair, timeframe, COUNT(*) AS candles, MIN(open_time) AS oldest, MAX(open_time) AS newest
FROM candles
GROUP BY pair, timeframe;
\q
```

### Check the strategies table

```bash
make shell-db
SELECT id, name, is_active FROM strategies;
\q
```

Expected:

```
 id | name      | is_active
----+-----------+-----------
  1 | macd      | t
  2 | rsi       | t
  3 | vwap      | t
  4 | breakout  | t
  5 | combined  | t
```

### Check engine status via API

```bash
curl -s http://localhost:8000/api/v1/engine/status | python3 -m json.tool
```

When the engine is running:

```json
{
  "running": true,
  "equity": 100000.0,
  "positions_count": 0,
  "mode": "paper_trading"
}
```

### View live logs

```bash
make logs
# or for a specific service:
docker compose logs -f backend
docker compose logs -f frontend
```

---

## 6. Local Development (Without Docker)

This section describes running the backend and frontend directly on your machine,
which is useful for active development.

### Prerequisites

- Python 3.12 (use `pyenv` or similar)
- Node.js 20 LTS
- PostgreSQL 16 running locally
- Redis 7 running locally

### Create the database

```bash
createdb -U postgres ghtrader
psql -U postgres -c "CREATE USER trader WITH PASSWORD 'trader';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ghtrader TO trader;"
```

### Backend

```bash
cd backend

# Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment (use localhost URLs)
cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://trader:trader@localhost:5432/ghtrader
REDIS_URL=redis://localhost:6379/0
KRAKEN_API_BASE=https://api.kraken.com
TRACKED_PAIRS=XBT/USD,ETH/USD,SOL/USD
PRIMARY_TIMEFRAME=1m
PAPER_INITIAL_BALANCE=100000.0
PAPER_TAKER_FEE=0.0026
PAPER_MAKER_FEE=0.0016
PAPER_SLIPPAGE_BPS=5
MAX_CONCURRENT_POSITIONS=5
MAX_DAILY_LOSS_PCT=0.05
RISK_PER_TRADE_PCT=0.02
LOG_LEVEL=DEBUG
ENV=development
EOF

# Apply migrations
alembic upgrade head

# Seed strategies
python -m app.scripts.seed

# Backfill data
python -m app.scripts.backfill --pairs XBT/USD,ETH/USD,SOL/USD --days 7

# Start the API server (with hot-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend

npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
```

Open <http://localhost:3000>.

### Run tests (local)

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 7. Upgrading

### Pull the latest code

```bash
git pull origin main
```

### Rebuild images and restart

```bash
make build
make down
make up
```

The backend container automatically runs `alembic upgrade head` on startup, applying any
new database migrations.

### Check for new environment variables

Compare `.env.example` with your `.env` file after pulling to check for any newly added
variables that need to be configured:

```bash
diff .env.example .env
```

---

## 8. Resetting All Data

> **Warning:** This permanently deletes all candles, positions, trades, and backtest results.

### Reset just the paper trading state (keep candles)

Stop the engine, then reset the daily risk counters:

```bash
make stop-engine
curl -X POST http://localhost:8000/api/v1/risk/reset
```

To start from a fresh balance, you must restart the backend container
(the balance is held in memory):

```bash
docker compose restart backend
```

### Full database reset

```bash
make down
docker volume rm ghtrader_postgres_data
make up
make seed
make backfill
```

This removes the named Docker volume containing all PostgreSQL data.

---

## 9. Port Reference

| Port | Service | Description |
|------|---------|-------------|
| 3000 | Frontend | Next.js dashboard |
| 8000 | Backend | FastAPI REST API + Swagger docs |
| 5432 | Database | PostgreSQL (exposed for local tools like pgAdmin, DBeaver) |
| 6379 | Redis | Redis (exposed for debugging with `redis-cli`) |

If any of these ports are already in use on your machine, edit `docker-compose.yml` and
change the left-hand side of the port mapping, for example:

```yaml
ports:
  - "8001:8000"   # maps host:8001 → container:8000
```

Then update `NEXT_PUBLIC_API_URL` in your `.env` accordingly.
