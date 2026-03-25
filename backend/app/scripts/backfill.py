"""Backfill historical OHLCV candles from Kraken public API."""
import asyncio
import argparse
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.ingestion.ingester import DataIngester


async def backfill(pairs: list[str], days: int) -> None:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        ingester = DataIngester(session, settings)
        for pair in pairs:
            print(f"Backfilling {pair} for {days} days...")
            await ingester.backfill(pair, settings.PRIMARY_TIMEFRAME, days)
            print(f"Done: {pair}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill historical OHLCV candles")
    parser.add_argument("--pairs", default="XBT/USD,ETH/USD,SOL/USD", help="Comma-separated pairs")
    parser.add_argument("--days", type=int, default=30, help="Number of days to backfill")
    args = parser.parse_args()
    pairs = [p.strip() for p in args.pairs.split(",")]
    asyncio.run(backfill(pairs, args.days))
