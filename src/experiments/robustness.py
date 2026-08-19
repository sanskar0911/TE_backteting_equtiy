"""
robustness.py

Robustness & Sensitivity Analysis Module.
Tests strategy stability under small perturbations of cost, slippage, sizing, parameters, and rebalancing.
"""

import os
import sys
from typing import Dict, List, Any
import numpy as np
import pandas as pd

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strategy import generate_signals
from backtester import run_backtest
from metrics import calculate_metrics


def run_robustness_analysis(
    price_df: pd.DataFrame,
    strategy_name: str = "SMA",
    baseline_params: Dict[str, Any] = None,
    initial_capital: float = 100000.0,
    baseline_txn_cost: float = 0.001,
    baseline_slippage: float = 0.0005,
    baseline_position_size: float = 0.2
) -> Dict[str, Any]:
    """
    Run perturbation tests across execution assumptions.

    Returns
    -------
    Dict[str, Any]
        Robustness analysis matrix and stability summary.
    """
    baseline_params = baseline_params or ({"short_window": 20, "long_window": 50} if strategy_name == "SMA" else {})

    # 1. Baseline Run
    signals_base = generate_signals(price_df, strategy_name=strategy_name, **baseline_params)
    port_base, trade_base = run_backtest(
        signals_base, initial_capital=initial_capital, txn_cost_rate=baseline_txn_cost,
        slippage_rate=baseline_slippage, position_size=baseline_position_size
    )
    met_base = calculate_metrics(port_base, trade_base, initial_capital=initial_capital)
    base_sharpe = met_base.get("Sharpe Ratio", 0.0)

    results: List[Dict[str, Any]] = [{
        "Test Case": "Baseline",
        "Txn Cost": f"{baseline_txn_cost*100:.2f}%",
        "Slippage": f"{baseline_slippage*100:.2f}%",
        "Position Size": f"{baseline_position_size*100:.0f}%",
        "Parameters": str(baseline_params),
        "CAGR": met_base.get("CAGR", 0.0),
        "Sharpe": base_sharpe,
        "Max Drawdown": met_base.get("Maximum Drawdown", 0.0),
        "Trades": met_base.get("Number of Trades", 0)
    }]

    # Perturbation Variations
    variations = [
        ("Higher Cost (0.20%)", {"txn_cost_rate": 0.002, "slippage_rate": baseline_slippage, "position_size": baseline_position_size}, baseline_params),
        ("Lower Cost (0.05%)", {"txn_cost_rate": 0.0005, "slippage_rate": baseline_slippage, "position_size": baseline_position_size}, baseline_params),
        ("Higher Slippage (0.10%)", {"txn_cost_rate": baseline_txn_cost, "slippage_rate": 0.001, "position_size": baseline_position_size}, baseline_params),
        ("Larger Size (50%)", {"txn_cost_rate": baseline_txn_cost, "slippage_rate": baseline_slippage, "position_size": 0.5}, baseline_params),
        ("Smaller Size (10%)", {"txn_cost_rate": baseline_txn_cost, "slippage_rate": baseline_slippage, "position_size": 0.1}, baseline_params)
    ]

    # Parameter Perturbations (+/- 10%)
    if strategy_name == "SMA":
        sw = baseline_params.get("short_window", 20)
        lw = baseline_params.get("long_window", 50)
        variations.append(("Params +10%", {"txn_cost_rate": baseline_txn_cost, "slippage_rate": baseline_slippage, "position_size": baseline_position_size}, {"short_window": int(sw*1.1), "long_window": int(lw*1.1)}))
        variations.append(("Params -10%", {"txn_cost_rate": baseline_txn_cost, "slippage_rate": baseline_slippage, "position_size": baseline_position_size}, {"short_window": max(5, int(sw*0.9)), "long_window": max(15, int(lw*0.9))}))

    sharpe_list = [base_sharpe]

    for label, exec_kwargs, p_kwargs in variations:
        try:
            sigs = generate_signals(price_df, strategy_name=strategy_name, **p_kwargs)
            port, trd = run_backtest(
                sigs, initial_capital=initial_capital,
                txn_cost_rate=exec_kwargs["txn_cost_rate"],
                slippage_rate=exec_kwargs["slippage_rate"],
                position_size=exec_kwargs["position_size"]
            )
            met = calculate_metrics(port, trd, initial_capital=initial_capital)
            sh = met.get("Sharpe Ratio", 0.0)
            sharpe_list.append(sh)

            results.append({
                "Test Case": label,
                "Txn Cost": f"{exec_kwargs['txn_cost_rate']*100:.2f}%",
                "Slippage": f"{exec_kwargs['slippage_rate']*100:.2f}%",
                "Position Size": f"{exec_kwargs['position_size']*100:.0f}%",
                "Parameters": str(p_kwargs),
                "CAGR": met.get("CAGR", 0.0),
                "Sharpe": sh,
                "Max Drawdown": met.get("Maximum Drawdown", 0.0),
                "Trades": met.get("Number of Trades", 0)
            })
        except Exception as e:
            print(f"[Robustness Note] Test case '{label}' failed: {e}")

    df_robustness = pd.DataFrame(results)

    sharpe_std = np.std(sharpe_list)
    sharpe_mean = np.mean(sharpe_list)
    cv_sharpe = (sharpe_std / sharpe_mean) if sharpe_mean > 0 else 999.0
    is_robust = bool(cv_sharpe < 0.35)

    return {
        "summary": {
            "baseline_sharpe": float(base_sharpe),
            "mean_perturbed_sharpe": float(sharpe_mean),
            "sharpe_std_dev": float(sharpe_std),
            "coefficient_of_variation": float(cv_sharpe),
            "is_robust": is_robust
        },
        "details_df": df_robustness
    }
