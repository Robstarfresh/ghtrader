"""Token scanner – discovers rising altcoins on Kraken.

Criteria applied to every scan:
  • 24-hour USD-equivalent volume ≥ MIN_VOLUME_24H_USD (default 100 000)
  • Positive 24-hour price momentum (close > open for the period)
  • Exclude stablecoins (USDT, USDC, DAI, BUSD, TUSD, FRAX, …)
  • Exclude BTC / XBT, ETH, SOL, XMR (Monero)

⚠️  PAPER TRADING ONLY – scanner is used for research and simulation.
"""
from __future__ import annotations

import asyncio
from typing import Optional

import structlog

from app.ingestion.kraken_client import KrakenClient

log = structlog.get_logger(__name__)

# Base currencies that should NEVER be traded (per requirements)
_EXCLUDED_BASE: frozenset[str] = frozenset(
    {
        # Bitcoin variants
        "XBT", "BTC", "XXBT",
        # Ethereum
        "ETH", "XETH",
        # Solana
        "SOL",
        # Monero
        "XMR", "XXMR",
    }
)

# Quote currencies that identify stablecoins or undesirable quote sides
_STABLECOIN_IDENTIFIERS: frozenset[str] = frozenset(
    {
        "USDT", "USDC", "DAI", "BUSD", "TUSD", "FRAX", "UST", "USDP",
        "GUSD", "HUSD", "PAX", "SUSD", "USDN", "LUSD", "MUSD",
        # Fiat-pegged tokens also filtered
        "EUR", "GBP", "AUD", "CAD", "CHF", "JPY",
    }
)

# Only consider pairs quoted in USD / ZUSD
_USD_QUOTES: frozenset[str] = frozenset({"USD", "ZUSD"})


def _is_stablecoin(base: str) -> bool:
    """Return True if *base* is a known stablecoin symbol."""
    normalized = base.upper().lstrip("X").lstrip("Z")
    return normalized in _STABLECOIN_IDENTIFIERS or base.upper() in _STABLECOIN_IDENTIFIERS


def _is_excluded_base(base: str) -> bool:
    """Return True if *base* is in the excluded list (BTC/ETH/SOL/XMR)."""
    normalized = base.upper()
    return normalized in _EXCLUDED_BASE


class TokenScanner:
    """Scans Kraken for rising altcoins meeting volume and momentum criteria.

    ⚠️  PAPER TRADING ONLY.

    Usage::

        scanner = TokenScanner(min_volume_24h_usd=100_000)
        pairs = await scanner.scan()   # returns ["ADA/USD", "LINK/USD", …]
    """

    def __init__(
        self,
        min_volume_24h_usd: float = 100_000.0,
        require_positive_momentum: bool = True,
        client: Optional[KrakenClient] = None,
    ) -> None:
        self.min_volume_24h_usd = min_volume_24h_usd
        self.require_positive_momentum = require_positive_momentum
        self._client = client or KrakenClient()
        self._last_pairs: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def scan(self) -> list[str]:
        """Discover eligible altcoin pairs on Kraken.

        Returns a list of Kraken pair strings like ``["ADAUSD", "LINKUSD"]``
        that pass all filters.
        """
        try:
            asset_pairs = await self._fetch_asset_pairs()
            eligible_pairs = self._filter_pairs(asset_pairs)
            if not eligible_pairs:
                log.warning("scanner_no_eligible_pairs_pre_ticker")
                return self._last_pairs  # fall back to previous result

            ticker_data = await self._fetch_ticker(eligible_pairs)
            result = self._apply_volume_and_momentum_filters(eligible_pairs, ticker_data)
        except Exception as exc:
            log.warning("scanner_error", error=str(exc))
            return self._last_pairs  # fall back gracefully

        self._last_pairs = result
        log.info(
            "scanner_complete",
            total_eligible=len(eligible_pairs),
            passing=len(result),
            pairs=result[:10],  # log first 10 to avoid noise
        )
        return result

    @property
    def last_pairs(self) -> list[str]:
        """Return the pairs discovered in the most recent scan."""
        return list(self._last_pairs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_asset_pairs(self) -> dict:
        """Retrieve all available Kraken asset pairs."""
        client = await self._client._get_client()
        resp = await client.get("/0/public/AssetPairs")
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            raise ValueError(f"Kraken AssetPairs error: {data['error']}")
        return data.get("result", {})

    def _filter_pairs(self, asset_pairs: dict) -> list[str]:
        """Return Kraken pair keys that meet base/quote criteria."""
        eligible: list[str] = []
        for kraken_key, info in asset_pairs.items():
            # Skip dark-pool and index pairs
            if kraken_key.endswith(".d") or kraken_key.startswith("."):
                continue

            base: str = info.get("base", "")
            quote: str = info.get("quote", "")

            # Only USD-quoted pairs
            if quote.upper() not in _USD_QUOTES:
                continue

            # Exclude blacklisted base currencies
            if _is_excluded_base(base):
                continue

            # Exclude stablecoins in the base currency
            if _is_stablecoin(base):
                continue

            eligible.append(kraken_key)

        log.debug("scanner_eligible_after_asset_filter", count=len(eligible))
        return eligible

    async def _fetch_ticker(self, pairs: list[str]) -> dict:
        """Fetch ticker data for *pairs* in batches to avoid URI limits."""
        results: dict = {}
        # Kraken allows a comma-separated list but caps at ~100 pairs per call
        batch_size = 50
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i : i + batch_size]
            try:
                ticker_result = await self._client._request(
                    "/0/public/Ticker", {"pair": ",".join(batch)}
                )
                results.update(ticker_result)
            except Exception as exc:
                log.warning("scanner_ticker_batch_error", batch_start=i, error=str(exc))
            await asyncio.sleep(0.3)  # polite rate limiting
        return results

    def _apply_volume_and_momentum_filters(
        self,
        eligible_pairs: list[str],
        ticker_data: dict,
    ) -> list[str]:
        """Apply volume threshold and (optionally) momentum filter."""
        passing: list[str] = []
        for kraken_key in eligible_pairs:
            ticker = ticker_data.get(kraken_key)
            if ticker is None:
                continue

            try:
                # Kraken ticker fields:
                #   "v": [today_volume, 24h_volume]  (in base currency)
                #   "p": [today_vwap, 24h_vwap]      (in quote = USD)
                #   "o": open_price (today)
                #   "c": [last_price, lot_volume]
                volume_base_24h = float(ticker["v"][1])
                vwap_24h = float(ticker["p"][1])
                volume_usd_24h = volume_base_24h * vwap_24h

                if volume_usd_24h < self.min_volume_24h_usd:
                    continue

                if self.require_positive_momentum:
                    open_price = float(ticker["o"])
                    last_price = float(ticker["c"][0])
                    if last_price <= open_price:
                        continue

            except (KeyError, IndexError, ValueError, TypeError):
                continue

            passing.append(kraken_key)

        return passing
