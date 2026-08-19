"""
regime_analysis.py

Market Regime Analysis Module.
Classifies market environment into Bull, Bear, Sideways, and High/Low Volatility regimes,
and evaluates strategy P&L performance separately per regime.
"""

import os
import sys
from typing import Dict, Any
import numpy as np
import pandas as pd

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from metrics import calculate_metrics


def classify_market_regimes(
    benchmark_or_price_df: pd.DataFrame,
    lookback_window: int = 20,
    vol_lookback: int = 20
) -> pd.Series:
    """
    Classify daily price regime into 'Bull', 'Bear', or 'Sideways'.
    """
    price_col = "Adj Close" if "Adj Close" in benchmark_or_price_df.columns else "Close"
    prices = benchmark_or_price_df[price_col]

    # Calculate 20-day return
    ret_20d = prices.pct_change(lookback_window)

    regimes = pd.Series("Sideways", index=benchmark_or_price_df.index)
    regimes[ret_20d > 0.02] = "Bull"
    regimes[ret_20d < -0.02] = "Bear"

    return regimes


def run_regime_analysis(
    portfolio_df: pd.DataFrame,
    trade_log_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    initial_capital: float = 100000.0
) -> Dict[str, Any]:
    """
    Evaluate strategy metrics broken down by market regime.
    """
    regimes = classify_market_regimes(benchmark_df)
    
    # Align regimes with portfolio tracking
    aligned_portfolio = portfolio_df.copy()
    aligned_portfolio["Regime"] = regimes.reindex(portfolio_df.index).ffill().bfill()

    regime_metrics = {}

    for regime in ["Bull", "Bear", "Sideways"]:
        sub_port = aligned_portfolio[aligned_portfolio["Regime"] == regime]
        if len(sub_port) < 10:
            regime_metrics[regime] = {"note": "Insufficient data in this regime"}
            continue

        ret = sub_port["Portfolio Return"]
        daily_vol = ret.std()
        ann_vol = daily_vol * np.sqrt(252) if daily_vol > 0 else 0.0
        mean_ret = ret.mean()
        sharpe = (mean_ret / daily_vol) * np.sqrt(252) if daily_vol > 0 else 0.0

        cum_ret = (1.0 + ret).prod() - 1.0
        exposure = (sub_port["Shares"] > 0).mean() if "Shares" in sub_port.columns else 0.0

        regime_metrics[regime] = {
            "trading_days": len(sub_port),
            "cumulative_return": float(cum_ret),
            "annualized_volatility": float(ann_vol),
            "sharpe_ratio": float(sharpe),
            "market_exposure": float(exposure)
        }

    return regime_metrics
