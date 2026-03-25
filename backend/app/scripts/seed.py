"""Seed script - inserts default strategies into database."""
import asyncio
from app.database import AsyncSessionLocal
from app.models.strategy import Strategy
from sqlalchemy import select


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Strategy))
        if result.scalars().first():
            print("Already seeded.")
            return

        strategies = [
            Strategy(
                name="macd",
                description="MACD trend continuation",
                params={"fast": 12, "slow": 26, "signal": 9},
                is_active=True,
            ),
            Strategy(
                name="rsi",
                description="RSI mean reversion",
                params={"period": 14, "oversold": 30, "overbought": 70},
                is_active=True,
            ),
            Strategy(
                name="vwap",
                description="VWAP intraday bias",
                params={},
                is_active=True,
            ),
            Strategy(
                name="breakout",
                description="Range breakout",
                params={"period": 20},
                is_active=True,
            ),
            Strategy(
                name="combined",
                description="Weighted combined strategy",
                params={"threshold": 0.5},
                is_active=True,
            ),
        ]
        session.add_all(strategies)
        await session.commit()
        print(f"Seeded {len(strategies)} strategies.")


if __name__ == "__main__":
    asyncio.run(seed())
