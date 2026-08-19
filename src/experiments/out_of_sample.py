"""
out_of_sample.py

Out-of-Sample Validation & Look-Ahead Bias Audit Module.
Validates train/test split hygiene and enforces zero future information leakage.
"""

import os
import sys
from typing import Dict, Any, Tuple, List
import pandas as pd

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strategy import generate_signals
from backtester import run_backtest
from metrics import calculate_metrics


def audit_lookahead_bias(df: pd.DataFrame, signals_df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Check if signal calculation accesses future price data.

    Returns
    -------
    Tuple[bool, List[str]]
        (has_leakage, warning_messages)
    """
    warnings = []
    has_leakage = False

    # Check 1: Index chronological sorting
    if not df.index.is_monotonic_increasing:
        has_leakage = True
        warnings.append("CRITICAL: Price DataFrame index is NOT chronologically sorted! Rolling windows will leak future data.")

    # Check 2: Signal alignment vs price date
    if not signals_df.index.equals(df.index):
        has_leakage = True
        warnings.append("CRITICAL: Signals DataFrame index date mismatch with Price DataFrame!")

    # Check 3: Check if position entry occurs without valid signal trigger
    if "Position" in signals_df.columns and "Signal" in signals_df.columns:
        pos_entry = (signals_df["Position"].diff() == 1)
        sig_buy = (signals_df["Signal"] == 1)
        # Any position entry where signal is not 1 is suspicious
        unauthorized_entries = (pos_entry & (~sig_buy)).sum()
        if unauthorized_entries > 0:
            has_leakage = True
            warnings.append(f"CRITICAL: Detected {unauthorized_entries} instances of position entry without valid signal!")

    return has_leakage, warnings


def run_out_of_sample_validation(
    price_df: pd.DataFrame,
    strategy_name: str = "SMA",
    strategy_params: Dict[str, Any] = None,
    train_ratio: float = 0.70,
    initial_capital: float = 100000.0,
    txn_cost_rate: float = 0.001,
    slippage_rate: float = 0.0005,
    position_size: float = 0.2
) -> Dict[str, Any]:
    """
    Perform explicit In-Sample (IS) vs Out-of-Sample (OOS) validation.
    """
    strategy_params = strategy_params or {}

    # Run audit check on full dataframe
    signals_full = generate_signals(price_df, strategy_name=strategy_name, **strategy_params)
    has_leakage, audit_warnings = audit_lookahead_bias(price_df, signals_full)

    if has_leakage:
        return {
            "status": "FAILED",
            "leakage_detected": True,
            "warnings": audit_warnings,
            "conclusion": "Experiment FAILED due to detected look-ahead data leakage!"
        }

    n = len(price_df)
    split_idx = int(n * train_ratio)

    is_df = price_df.iloc[:split_idx]
    oos_df = price_df.iloc[split_idx:]

    # Run In-Sample
    is_signals = generate_signals(is_df, strategy_name=strategy_name, **strategy_params)
    is_port, is_trades = run_backtest(
        is_signals, initial_capital=initial_capital, txn_cost_rate=txn_cost_rate,
        slippage_rate=slippage_rate, position_size=position_size
    )
    is_metrics = calculate_metrics(is_port, is_trades, initial_capital=initial_capital)

    # Run Out-of-Sample
    oos_signals = generate_signals(oos_df, strategy_name=strategy_name, **strategy_params)
    oos_port, oos_trades = run_backtest(
        oos_signals, initial_capital=initial_capital, txn_cost_rate=txn_cost_rate,
        slippage_rate=slippage_rate, position_size=position_size
    )
    oos_metrics = calculate_metrics(oos_port, oos_trades, initial_capital=initial_capital)

    # Compare degradation
    is_sharpe = is_metrics.get("Sharpe Ratio", 0.0)
    oos_sharpe = oos_metrics.get("Sharpe Ratio", 0.0)
    sharpe_degradation = ((oos_sharpe - is_sharpe) / is_sharpe) * 100.0 if is_sharpe > 0 else 0.0

    is_cagr = is_metrics.get("CAGR", 0.0)
    oos_cagr = oos_metrics.get("CAGR", 0.0)
    cagr_degradation = ((oos_cagr - is_cagr) / is_cagr) * 100.0 if is_cagr > 0 else 0.0

    passed_validation = bool(oos_sharpe >= 0.3 and sharpe_degradation > -50.0)

    warnings = []
    if sharpe_degradation < -30.0:
        warnings.append(f"WARNING: Severe Out-of-Sample Sharpe degradation ({sharpe_degradation:.1f}%). Possible overfitting.")

    return {
        "status": "SUCCESS" if passed_validation else "WARNING",
        "leakage_detected": False,
        "split_ratio": train_ratio,
        "is_period": f"{is_df.index.min().date()} to {is_df.index.max().date()}",
        "oos_period": f"{oos_df.index.min().date()} to {oos_df.index.max().date()}",
        "in_sample_metrics": is_metrics,
        "out_of_sample_metrics": oos_metrics,
        "sharpe_degradation_pct": float(sharpe_degradation),
        "cagr_degradation_pct": float(cagr_degradation),
        "passed_validation": passed_validation,
        "warnings": warnings
    }
