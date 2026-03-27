"""Paper trading engine service.

Orchestrates market data ingestion, strategy signal generation and
paper broker execution in a continuous async loop.

⚠️  PAPER TRADING ONLY - no real orders are placed on any exchange.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.kraken_client import KrakenClient, _to_interval
from app.models.candle import Candle
from app.strategies.base import Signal

if TYPE_CHECKING:
    from app.broker.paper_broker import PaperBroker
    from app.config import Settings
    from app.risk.manager import RiskManager
    from app.strategies.base import Strategy

log = structlog.get_logger(__name__)

_CYCLE_INTERVAL_SECONDS = 60  # 1-minute default

class PaperEngine:
    """Orchestrates ingestion + signal generation + paper execution.

    Usage::

        engine = PaperEngine(config, db_session_factory, broker,
                             risk_manager, strategies)
        await engine.start()   # runs in background task

    ⚠️  PAPER TRADING ONLY.
    """

    def __init__(
        self,
        config: "Settings",
        session_factory,  # async_sessionmaker
        broker: "PaperBroker",
        risk_manager: "RiskManager",
        strategies: list["Strategy"],
    ) -> None:
        self._config = config
        self._session_factory = session_factory
        self.broker = broker
        self.risk_manager = risk_manager
        self.strategies = strategies
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._kraken = KrakenClient()
        self._cycle_count = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the engine loop in the background.

        ⚠️  PAPER TRADING ONLY.
        """
        if self._running:
            log.warning("paper_engine_already_running")
            return
        self._running = True
        log.info("paper_engine_starting", pairs=self._config.tracked_pairs_list)
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Gracefully stop the engine."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        log.info("paper_engine_stopped")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def _loop(self) -> None:
        while self._running:
            try:
                await self.run_cycle()
            except Exception as exc:
                log.exception("paper_engine_cycle_error", error=str(exc))
            await asyncio.sleep(_CYCLE_INTERVAL_SECONDS)

    async def run_cycle(self) -> None:
        """One iteration: fetch latest candles → generate signals → execute.

        ⚠️  PAPER TRADING ONLY.
        """
        self._cycle_count += 1
        interval = _to_interval(self._config.PRIMARY_TIMEFRAME)

        async with self._session_factory() as session:
            for pair in self._config.tracked_pairs_list:
                try:
                    await self._process_pair(session, pair, interval)
                except Exception as exc:
                    log.warning("cycle_pair_error", pair=pair, error=str(exc))

    async def _process_pair(
        self,
        session: AsyncSession,
        pair: str,
        interval: int,
    ) -> None:
        """Fetch candles for one pair, generate signal, optionally trade."""
        # Fetch recent candles from DB
        result = await session.execute(
            select(Candle)
            .where(
                Candle.pair == pair.upper(),
                Candle.timeframe == self._config.PRIMARY_TIMEFRAME,
            )
            .order_by(Candle.open_time.desc())
            .limit(200)
        )
        candles = list(reversed(result.scalars().all()))

        if len(candles) < 50:
            log.debug("insufficient_candles", pair=pair, count=len(candles))
            return

        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "open_time": c.open_time,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in candles
            ]
        )

        current_price = float(df["close"].iloc[-1])
        self.broker.update_prices({pair: current_price})

        if not self.broker.can_trade(self.risk_manager):
            log.info("trading_halted_by_risk", pair=pair)
            return

        for strategy in self.strategies:
            if not strategy.is_applicable(df):
                continue

            signal_result = strategy.generate_signal(df)
            log.debug(
                "signal_generated",
                pair=pair,
                strategy=strategy.name,
                signal=signal_result.signal.value,
                confidence=signal_result.confidence,
                reason=signal_result.reason,
            )

            if signal_result.signal == Signal.BUY and pair not in self.broker.positions:
                sl_price = (
                    current_price * (1 - signal_result.stop_loss_pct)
                    if signal_result.stop_loss_pct
                    else None
                )
                tp_price = (
                    current_price * (1 + signal_result.take_profit_pct)
                    if signal_result.take_profit_pct
                    else None
                )
                quantity = self.risk_manager.size_position(
                    pair, current_price, sl_price or current_price * 0.98, self.broker
                )
                allowed, reason = self.risk_manager.check_trade(
                    pair, "buy", quantity, current_price, self.broker
                )
                if allowed and quantity > 0:
                    self.broker.submit_order(
                        pair, "buy", quantity, current_price,
                        stop_loss=sl_price, take_profit=tp_price,
                    )
                    self.risk_manager.record_trade()
                else:
                    log.debug("trade_blocked_by_risk", pair=pair, reason=reason)

            elif signal_result.signal == Signal.SELL and pair in self.broker.positions:
                self.broker.close_position(pair, current_price, reason="signal_sell")
                self.risk_manager.record_trade()

            break  # Only execute first applicable strategy signal per cycle

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Return a snapshot of the engine state."""
        equity = self.broker._compute_equity() if self.broker else None
        return {
            "running": self._running,
            "cycle_count": self._cycle_count,
            "equity": equity,
            "balance": self.broker.balance if self.broker else None,
            "positions_count": len(self.broker.positions) if self.broker else 0,
            "mode": "paper_trading",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
