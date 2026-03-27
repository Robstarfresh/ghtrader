.PHONY: up down build logs migrate seed backfill start-engine stop-engine run-backtest test lint shell-backend shell-db

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.scripts.seed

backfill:
	docker compose exec backend python -m app.scripts.backfill --pairs XBT/USD,ETH/USD,SOL/USD --days 30

start-engine:
	curl -X POST http://localhost:8000/api/v1/engine/start

stop-engine:
	curl -X POST http://localhost:8000/api/v1/engine/stop

run-backtest:
	curl -X POST http://localhost:8000/api/v1/backtests \
	  -H "Content-Type: application/json" \
	  -d '{"name":"test-run","strategy_name":"combined","pair":"XBT/USD","timeframe":"1m","start_date":"2024-01-01T00:00:00","end_date":"2024-03-01T00:00:00","initial_balance":100000}'

test:
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	docker compose exec backend python -m py_compile app/**/*.py

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec db psql -U trader -d ghtrader
