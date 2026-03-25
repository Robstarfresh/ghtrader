"""Async Kraken public REST client.

⚠️  PAPER TRADING ONLY - only public market-data endpoints are used.
    No authenticated endpoints, no order placement.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx
import structlog

from app.config import get_settings

log = structlog.get_logger(__name__)

# Kraken pair name normalisation: friendly -> Kraken internal
_PAIR_MAP: Dict[str, str] = {
    "XBT/USD": "XBTUSD",
    "BTC/USD": "XBTUSD",
    "ETH/USD": "ETHUSD",
    "SOL/USD": "SOLUSD",
    "LTC/USD": "LTCUSD",
    "XRP/USD": "XRPUSD",
    "ADA/USD": "ADAUSD",
    "DOT/USD": "DOTUSD",
}

# Kraken OHLC interval codes (minutes)
_INTERVAL_MAP: Dict[str, int] = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
    "1w": 10080,
}


def _to_kraken_pair(pair: str) -> str:
    """Map a friendly pair name to the Kraken API pair code."""
    return _PAIR_MAP.get(pair.upper(), pair.replace("/", "").upper())


def _to_interval(timeframe: str) -> int:
    """Convert a timeframe string to Kraken interval minutes."""
    return _INTERVAL_MAP.get(timeframe, 1)


class KrakenClient:
    """Async client for the Kraken public REST API.

    Uses httpx with automatic retries and exponential back-off.

    ⚠️  PAPER TRADING ONLY - read-only market data access.
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        settings = get_settings()
        self._base = (base_url or settings.KRAKEN_API_BASE).rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base,
                timeout=httpx.Timeout(30.0),
                headers={"User-Agent": "GHTrader/1.0 (paper-trading)"},
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(self, path: str, params: Dict[str, Any], retries: int = 3) -> Dict:
        """Perform a GET request with exponential back-off on failure."""
        client = await self._get_client()
        delay = 1.0
        last_exc: Exception = RuntimeError("No attempts made")
        for attempt in range(retries):
            try:
                resp = await client.get(path, params=params)
                resp.raise_for_status()
                data = resp.json()
                if data.get("error"):
                    raise ValueError(f"Kraken API error: {data['error']}")
                return data.get("result", {})
            except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
                last_exc = exc
                log.warning(
                    "kraken_request_failed",
                    attempt=attempt + 1,
                    retries=retries,
                    path=path,
                    error=str(exc),
                )
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
        raise last_exc

    async def get_ohlcv(
        self,
        pair: str,
        interval_minutes: int = 1,
        since: Optional[int] = None,
    ) -> List[List]:
        """Fetch OHLCV candles from Kraken.

        Returns a list of rows: [timestamp, open, high, low, close, vwap, volume, trades]
        """
        kraken_pair = _to_kraken_pair(pair)
        params: Dict[str, Any] = {"pair": kraken_pair, "interval": interval_minutes}
        if since is not None:
            params["since"] = since

        log.debug("fetching_ohlcv", pair=kraken_pair, interval=interval_minutes, since=since)
        result = await self._request("/0/public/OHLC", params)

        # The result key is the pair name; Kraken may alter casing
        candle_key = next(
            (k for k in result if k != "last"),
            kraken_pair,
        )
        candles: List[List] = result.get(candle_key, [])
        return candles

    async def get_ticker(self, pair: str) -> Dict[str, Any]:
        """Fetch current ticker for a pair."""
        kraken_pair = _to_kraken_pair(pair)
        result = await self._request("/0/public/Ticker", {"pair": kraken_pair})
        ticker_key = next(iter(result), kraken_pair)
        return result.get(ticker_key, {})

    async def get_server_time(self) -> int:
        """Return Kraken server Unix timestamp."""
        result = await self._request("/0/public/Time", {})
        return int(result.get("unixtime", 0))
