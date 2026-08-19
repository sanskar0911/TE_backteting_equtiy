"""
parameter_sweep.py

Systematic parameter sweep engine.
Executes grid search across strategy parameters and exports full comparative results.

IMPORTANT RESEARCH RULE:
Does NOT automatically select the highest Sharpe configuration as the final strategy.
Outputs full grid results for research evaluation and stability testing.
"""

import os
import sys
import itertools
from typing import Dict, List, Any
import pandas as pd

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strategy import generate_signals
from backtester import run_backtest
from metrics import calculate_metrics
from benchmark import compare_strategy_vs_benchmark, load_benchmark_data


def run_parameter_sweep(
    price_df: pd.DataFrame,
    strategy_name: str = "SMA",
    param_grid: Dict[str, List[Any]] = None,
    initial_capital: float = 100000.0,
    txn_cost_rate: float = 0.001,
    slippage_rate: float = 0.0005,
    position_size: float = 0.2,
    stop_loss: float = 0.05,
    take_profit: float = 0.10,
    benchmark_symbol: str = "NIFTY50"
) -> pd.DataFrame:
    """
    Run systematic grid search across strategy parameters.

    Parameters
    ----------
    price_df : pd.DataFrame
        Stock price dataframe.
    strategy_name : str
        Strategy type ('SMA', 'EMA', or 'RSI').
    param_grid : Dict[str, List[Any]]
        Parameter ranges dict (e.g. {'short_window': [20, 30], 'long_window': [50, 100]}).

    Returns
    -------
    pd.DataFrame
        Table of parameter combinations and key performance KPIs.
    """
    if param_grid is None:
        if strategy_name in ["SMA", "EMA"]:
            param_grid = {
                "short_window": [10, 20, 30],
                "long_window": [50, 100, 150]
            }
        elif strategy_name == "RSI":
            param_grid = {
                "rsi_period": [10, 14, 21],
                "overbought": [65, 70, 75],
                "oversold": [25, 30, 35]
            }
        else:
            param_grid = {}

    keys = list(param_grid.keys())
    values = list(param_grid.values())
    combinations = list(itertools.product(*values))

    results: List[Dict[str, Any]] = []

    # Try loading benchmark for comparison
    try:
        bench_df = load_benchmark_data(benchmark_symbol)
    except Exception:
        bench_df = None

    for comb in combinations:
        params = dict(zip(keys, comb))
        
        # Filter invalid combinations (e.g. short >= long for moving averages)
        if "short_window" in params and "long_window" in params:
            if params["short_window"] >= params["long_window"]:
                continue

        try:
            signals_df = generate_signals(price_df, strategy_name=strategy_name, **params)
            port_df, trade_df = run_backtest(
                signals_df,
                initial_capital=initial_capital,
                txn_cost_rate=txn_cost_rate,
                slippage_rate=slippage_rate,
                position_size=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            met = calculate_metrics(port_df, trade_df, initial_capital=initial_capital)

            bench_comp = {}
            if bench_df is not None:
                bench_comp = compare_strategy_vs_benchmark(port_df, bench_df, benchmark_symbol=benchmark_symbol)

            row = {**params}
            row.update({
                "Total Return": met.get("Total Return", 0.0),
                "CAGR": met.get("CAGR", 0.0),
                "Annual Volatility": met.get("Annual Volatility", 0.0),
                "Sharpe Ratio": met.get("Sharpe Ratio", 0.0),
                "Sortino Ratio": met.get("Sortino Ratio", 0.0),
                "Max Drawdown": met.get("Maximum Drawdown", 0.0),
                "Win Rate": met.get("Win Rate", 0.0),
                "Profit Factor": met.get("Profit Factor", 0.0),
                "Trades": int(met.get("Number of Trades", 0)),
                "Turnover": met.get("Turnover", 0.0),
                "Exposure": met.get("Exposure", 0.0),
                "Excess Return": bench_comp.get("excess_return", 0.0),
                "Benchmark Sharpe": bench_comp.get("benchmark_sharpe", 0.0)
            })
            results.append(row)
        except Exception as e:
            print(f"[Parameter Sweep Warning] Combination {params} failed: {e}")

    sweep_df = pd.DataFrame(results)
    return sweep_df
