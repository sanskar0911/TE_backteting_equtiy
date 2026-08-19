"""
walk_forward.py

Walk-Forward Testing Engine.
Evaluates strategy stability across rolling train/test windows.

Workflow:
1. Training Window -> Parameter Selection / Calibration
2. Testing Window -> Out-of-Sample Execution
3. Advance Window Forward -> Repeat
"""

import os
import sys
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strategy import generate_signals
from backtester import run_backtest
from metrics import calculate_metrics
from experiments.parameter_sweep import run_parameter_sweep


def run_walk_forward_analysis(
    price_df: pd.DataFrame,
    strategy_name: str = "SMA",
    train_years: int = 3,
    test_years: int = 1,
    step_years: int = 1,
    param_grid: Optional[Dict[str, List[Any]]] = None,
    initial_capital: float = 100000.0,
    txn_cost_rate: float = 0.001,
    slippage_rate: float = 0.0005,
    position_size: float = 0.2
) -> Dict[str, Any]:
    """
    Execute walk-forward testing.

    Returns
    -------
    Dict[str, Any]
        Walk-forward summary results and window-by-window performance.
    """
    dates = price_df.index
    min_date = dates.min()
    max_date = dates.max()

    window_results: List[Dict[str, Any]] = []
    
    current_start = min_date
    window_id = 1

    while True:
        train_end = current_start + pd.DateOffset(years=train_years)
        test_end = train_end + pd.DateOffset(years=test_years)

        if train_end >= max_date:
            break

        test_end_actual = min(test_end, max_date)

        # Slice data
        train_df = price_df[(price_df.index >= current_start) & (price_df.index < train_end)]
        test_df = price_df[(price_df.index >= train_end) & (price_df.index <= test_end_actual)]

        if len(train_df) < 200 or len(test_df) < 50:
            current_start = current_start + pd.DateOffset(years=step_years)
            continue

        # In-Sample Parameter Selection via Sweep
        sweep_df = run_parameter_sweep(
            train_df,
            strategy_name=strategy_name,
            param_grid=param_grid,
            initial_capital=initial_capital,
            txn_cost_rate=txn_cost_rate,
            slippage_rate=slippage_rate,
            position_size=position_size
        )

        if sweep_df.empty:
            best_params = {"short_window": 20, "long_window": 50} if strategy_name == "SMA" else {}
            is_sharpe = 0.0
        else:
            # Select parameter combination with highest Sharpe in-sample
            best_row = sweep_df.sort_values(by="Sharpe Ratio", ascending=False).iloc[0]
            param_cols = [c for c in sweep_df.columns if c not in [
                "Total Return", "CAGR", "Annual Volatility", "Sharpe Ratio", "Sortino Ratio",
                "Max Drawdown", "Win Rate", "Profit Factor", "Trades", "Turnover", "Exposure",
                "Excess Return", "Benchmark Sharpe"
            ]]
            best_params = {col: best_row[col] for col in param_cols}
            is_sharpe = float(best_row["Sharpe Ratio"])

        # Out-of-Sample Test using selected parameters
        test_signals = generate_signals(test_df, strategy_name=strategy_name, **best_params)
        test_port, test_trades = run_backtest(
            test_signals,
            initial_capital=initial_capital,
            txn_cost_rate=txn_cost_rate,
            slippage_rate=slippage_rate,
            position_size=position_size
        )
        oos_met = calculate_metrics(test_port, test_trades, initial_capital=initial_capital)
        oos_sharpe = float(oos_met.get("Sharpe Ratio", 0.0))

        window_results.append({
            "Window": window_id,
            "Train Start": current_start.strftime("%Y-%m-%d"),
            "Train End": train_end.strftime("%Y-%m-%d"),
            "Test Start": train_end.strftime("%Y-%m-%d"),
            "Test End": test_end_actual.strftime("%Y-%m-%d"),
            "Selected Params": best_params,
            "In-Sample Sharpe": is_sharpe,
            "Out-of-Sample Sharpe": oos_sharpe,
            "Out-of-Sample CAGR": oos_met.get("CAGR", 0.0),
            "Out-of-Sample MDD": oos_met.get("Maximum Drawdown", 0.0),
            "Out-of-Sample Win Rate": oos_met.get("Win Rate", 0.0),
            "OOS/IS Sharpe Ratio": (oos_sharpe / is_sharpe) if is_sharpe > 0 else 0.0
        })

        window_id += 1
        current_start = current_start + pd.DateOffset(years=step_years)

    df_wf = pd.DataFrame(window_results)

    avg_is_sharpe = df_wf["In-Sample Sharpe"].mean() if not df_wf.empty else 0.0
    avg_oos_sharpe = df_wf["Out-of-Sample Sharpe"].mean() if not df_wf.empty else 0.0
    stability_ratio = (avg_oos_sharpe / avg_is_sharpe) if avg_is_sharpe > 0 else 0.0

    return {
        "summary": {
            "num_windows": len(df_wf),
            "avg_in_sample_sharpe": float(avg_is_sharpe),
            "avg_out_of_sample_sharpe": float(avg_oos_sharpe),
            "walk_forward_efficiency": float(stability_ratio),
            "is_stable": bool(stability_ratio >= 0.5)
        },
        "windows_df": df_wf
    }
