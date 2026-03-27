"""Parameter sweep optimizer for paper trading strategies.

⚠️  PAPER TRADING ONLY - historical optimisation, not live trading.
"""
from __future__ import annotations

from itertools import product
from typing import Any, Callable, Generator

import pandas as pd
import structlog

from app.backtest.engine import BacktestEngine, BacktestResult
from app.strategies.base import Strategy

log = structlog.get_logger(__name__)

def _generate_param_combinations(param_grid: dict[str, list[Any]]) -> Generator[dict, None, None]:
    """Yield every combination of parameter values from *param_grid*."""
    keys = list(param_grid.keys())
    for values in product(*param_grid.values()):
        yield dict(zip(keys, values))

class Optimizer:
    """Grid-search parameter optimizer.

    Runs the backtest engine with every parameter combination and
    returns results sorted by the chosen metric.

    ⚠️  PAPER TRADING ONLY.
    """

    def __init__(
        self,
        strategy_cls: type[Strategy],
        param_grid: dict[str, list[Any]],
        initial_balance: float = 100_000.0,
        taker_fee: float = 0.0026,
        maker_fee: float = 0.0016,
        slippage_bps: int = 5,
        sort_by: str = "sharpe_ratio",
    ) -> None:
        self.strategy_cls = strategy_cls
        self.param_grid = param_grid
        self.initial_balance = initial_balance
        self.taker_fee = taker_fee
        self.maker_fee = maker_fee
        self.slippage_bps = slippage_bps
        self.sort_by = sort_by

    def run(
        self,
        df: pd.DataFrame,
        pair: str,
    ) -> list[dict[str, Any]]:
        """Execute the parameter sweep.

        Returns a list of result dicts (params + metrics), sorted by
        *sort_by* descending.
        """
        combinations = list(_generate_param_combinations(self.param_grid))
        log.info(
            "optimizer_start",
            strategy=self.strategy_cls.__name__,
            combinations=len(combinations),
            pair=pair,
        )

        results: list[dict[str, Any]] = []
        for i, params in enumerate(combinations, start=1):
            try:
                strategy = self.strategy_cls(**params)
                engine = BacktestEngine(
                    strategy,
                    self.initial_balance,
                    self.taker_fee,
                    self.maker_fee,
                    self.slippage_bps,
                )
                bt_result: BacktestResult = engine.run(df, pair)
                results.append({"params": params, **bt_result.metrics})
                log.debug(
                    "optimizer_iteration",
                    iteration=i,
                    total=len(combinations),
                    params=params,
                    metric=bt_result.metrics.get(self.sort_by),
                )
            except Exception as exc:
                log.warning("optimizer_iteration_failed", params=params, error=str(exc))

        results.sort(key=lambda r: r.get(self.sort_by, float("-inf")), reverse=True)
        log.info("optimizer_done", best=results[0] if results else None)
        return results
