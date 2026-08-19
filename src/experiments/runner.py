"""
runner.py

Experiment class and reproducible runner.
Ensures every research run is logged with an immutable ID, hypothesis, strategy parameters,
execution constraints, benchmark comparison, metrics, and warnings.
"""

import os
import json
import hashlib
import time
from typing import Dict, Any, Optional
import pandas as pd


class Experiment:
    """Encapsulates a reproducible backtesting experiment."""

    def __init__(
        self,
        hypothesis: str,
        strategy_name: str,
        strategy_params: Dict[str, Any],
        ticker: str = "INFY",
        date_range: Optional[Dict[str, str]] = None,
        initial_capital: float = 100000.0,
        transaction_cost: float = 0.001,
        slippage: float = 0.0005,
        position_size: float = 0.2,
        max_positions: int = 10,
        rebalance_freq: str = "Daily",
        stop_loss: Optional[float] = 0.05,
        take_profit: Optional[float] = 0.10,
        benchmark_symbol: str = "NIFTY50"
    ):
        self.hypothesis = hypothesis
        self.strategy_name = strategy_name
        self.strategy_params = strategy_params
        self.ticker = ticker
        self.date_range = date_range or {}
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.slippage = slippage
        self.position_size = position_size
        self.max_positions = max_positions
        self.rebalance_freq = rebalance_freq
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.benchmark_symbol = benchmark_symbol

        # Generate unique experiment ID
        hash_input = f"{strategy_name}_{json.dumps(strategy_params, sort_keys=True)}_{ticker}_{time.time()}"
        self.experiment_id = "EXP_" + hashlib.md5(hash_input.encode()).hexdigest()[:8]

        self.metrics: Dict[str, Any] = {}
        self.benchmark_comparison: Dict[str, Any] = {}
        self.validation_results: Dict[str, Any] = {}
        self.warnings: List[str] = []
        self.conclusion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize experiment object to dictionary."""
        return {
            "experiment_id": self.experiment_id,
            "hypothesis": self.hypothesis,
            "ticker": self.ticker,
            "strategy_name": self.strategy_name,
            "strategy_params": self.strategy_params,
            "date_range": self.date_range,
            "initial_capital": self.initial_capital,
            "transaction_cost": self.transaction_cost,
            "slippage": self.slippage,
            "position_size": self.position_size,
            "max_positions": self.max_positions,
            "rebalance_freq": self.rebalance_freq,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "benchmark_symbol": self.benchmark_symbol,
            "metrics": self.metrics,
            "benchmark_comparison": self.benchmark_comparison,
            "validation_results": self.validation_results,
            "warnings": self.warnings,
            "conclusion": self.conclusion
        }
