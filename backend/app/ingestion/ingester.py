"""Market data ingester.

Stores OHLCV candles from Kraken into the database.

⚠️  PAPER TRADING ONLY - historical and live data for simulation purposes.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.kraken_client import KrakenClient, _to_interval
from app.models.candle import Candle

log = structlog.get_logger(__name__)

def _row_to_candle(row: list, pair: str, timeframe: str) -> dict:
    """Convert a raw Kraken OHLC row to a Candle insert dict."""
    ts, o, h, l, c, vwap, volume, trades = row
    return {
        "pair": pair.upper(),
        "timeframe": timeframe,
        "open_time": datetime.fromtimestamp(int(ts), tz=timezone.utc),
        "open": float(o),
        "high": float(h),
        "low": float(l),
        "close": float(c),
        "vwap": float(vwap) if vwap else None,
        "volume": float(volume),
        "trades": int(trades) if trades else None,
    }

async def upsert_candles(
    session: AsyncSession,
    rows: list[dict],
) -> int:
    """Upsert candle rows, ignoring conflicts on (pair, timeframe, open_time)."""
    if not rows:
        return 0
    stmt = pg_insert(Candle).values(rows)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["pair", "timeframe", "open_time"]
        # relies on the UniqueConstraint defined on the model
    )
    result = await session.execute(stmt)
    return result.rowcount or 0

class Ingester:
    """Fetches OHLCV data from Kraken and persists it in the database.

    ⚠️  PAPER TRADING ONLY.
    """

    def __init__(self, client: Optional[KrakenClient] = None) -> None:
        self._client = client or KrakenClient()

    async def backfill(
        self,
        session: AsyncSession,
        pair: str,
        timeframe: str,
        days_back: int = 7,
    ) -> int:
        """Fetch *days_back* days of candles and store them.

        Returns the number of new rows inserted.
        """
        interval = _to_interval(timeframe)
        since_dt = datetime.now(timezone.utc) - timedelta(days=days_back)
        since_ts = int(since_dt.timestamp())

        total_inserted = 0
        log.info("backfill_start", pair=pair, timeframe=timeframe, days_back=days_back)

        while True:
            raw = await self._client.get_ohlcv(pair, interval_minutes=interval, since=since_ts)
            if not raw:
                break

            rows = [_row_to_candle(r, pair, timeframe) for r in raw]
            inserted = await upsert_candles(session, rows)
            await session.commit()
            total_inserted += inserted

            last_ts = int(raw[-1][0])
            log.debug(
                "backfill_batch",
                pair=pair,
                batch_size=len(rows),
                inserted=inserted,
                last_ts=last_ts,
            )

            # Kraken returns up to 720 candles; if fewer, we are done
            if len(raw) < 720:
                break
            since_ts = last_ts + 1
            await asyncio.sleep(0.5)  # be a good API citizen

        log.info("backfill_done", pair=pair, total_inserted=total_inserted)
        return total_inserted

    async def live_feed(
        self,
        session: AsyncSession,
        pair: str,
        timeframe: str = "1m",
        poll_interval_seconds: int = 60,
    ) -> None:
        """Poll Kraken for the latest candles and upsert new ones in a loop.

        This is an infinite coroutine; cancel it to stop.

        ⚠️  PAPER TRADING ONLY.
        """
        interval = _to_interval(timeframe)
        log.info("live_feed_start", pair=pair, timeframe=timeframe)

        while True:
            try:
                raw = await self._client.get_ohlcv(pair, interval_minutes=interval)
                if raw:
                    rows = [_row_to_candle(r, pair, timeframe) for r in raw[-10:]]
                    inserted = await upsert_candles(session, rows)
                    await session.commit()
                    if inserted:
                        log.debug("live_feed_new_candles", pair=pair, count=inserted)
            except Exception as exc:
                log.warning("live_feed_error", pair=pair, error=str(exc))

            await asyncio.sleep(poll_interval_seconds)
