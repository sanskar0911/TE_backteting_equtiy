"""
test_backtest_rules.py

Unit tests for equity backtesting framework:
1. No look-ahead bias audit
2. Date alignment
3. Transaction costs & slippage
4. Position sizing & maximum positions cap
5. Rebalancing frequency
6. Benchmark alignment
7. Parameter sweep
8. Walk-forward split
9. Out-of-sample split
10. Loop stopping conditions
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

# Ensure src path is added
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from strategy import generate_signals
from backtester import run_backtest
from metrics import calculate_metrics
from benchmark import load_benchmark_data, compare_strategy_vs_benchmark
from portfolio import LiquidityFilter, RebalanceSchedule, PositionAllocator
from experiments.parameter_sweep import run_parameter_sweep
from experiments.walk_forward import run_walk_forward_analysis
from experiments.out_of_sample import audit_lookahead_bias, run_out_of_sample_validation
from experiments.robustness import run_robustness_analysis
from agent.workflow import run_agent_workflow


@pytest.fixture
def sample_price_df():
    data_path = os.path.join(BASE_DIR, "data", "processed", "RELIANCE.csv")
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, index_col="Date")
        df.index = pd.to_datetime(df.index)
        return df
    else:
        # Create synthetic test dataset if file absent
        dates = pd.date_range("2022-01-01", periods=250, freq="B")
        prices = 100.0 + np.cumsum(np.random.randn(250))
        df = pd.DataFrame({
            "Open": prices, "High": prices+1, "Low": prices-1, "Close": prices,
            "Adj Close": prices, "Volume": 100000, "Returns": pd.Series(prices).pct_change().fillna(0)
        }, index=dates)
        return df


def test_no_lookahead_bias(sample_price_df):
    """Test 1: Verify data is chronologically sorted and signal has no future leakage."""
    signals_df = generate_signals(sample_price_df, strategy_name="SMA", short_window=20, long_window=50)
    has_leakage, warnings = audit_lookahead_bias(sample_price_df, signals_df)
    assert not has_leakage, f"Look-ahead leakage detected: {warnings}"


def test_transaction_costs_and_slippage(sample_price_df):
    """Test 2: Verify transaction costs and slippage reduce portfolio returns correctly."""
    signals_df = generate_signals(sample_price_df, strategy_name="SMA")
    
    port_zero_cost, _ = run_backtest(signals_df, initial_capital=100000.0, txn_cost_rate=0.0, slippage_rate=0.0)
    port_high_cost, _ = run_backtest(signals_df, initial_capital=100000.0, txn_cost_rate=0.005, slippage_rate=0.002)

    val_zero = port_zero_cost["Portfolio Value"].iloc[-1]
    val_high = port_high_cost["Portfolio Value"].iloc[-1]
    
    assert val_zero >= val_high, "Zero cost portfolio should equal or outperform high cost portfolio."


def test_liquidity_filter():
    """Test 3: Verify liquidity filter rejects low volume / low price securities."""
    liq = LiquidityFilter(min_avg_daily_volume=50000, min_price=50.0)
    
    pass_ok, _ = liq.evaluate(price=100.0, volume=100000, avg_volume_20d=80000)
    assert pass_ok is True
    
    fail_price, reason = liq.evaluate(price=30.0, volume=100000, avg_volume_20d=80000)
    assert fail_price is False
    assert "Price" in reason

    fail_vol, reason2 = liq.evaluate(price=100.0, volume=1000, avg_volume_20d=1000)
    assert fail_vol is False
    assert "Volume" in reason2


def test_position_allocator_deterministic_ranking():
    """Test 4: Verify position limit enforces deterministic ranking."""
    allocator = PositionAllocator(max_positions=2)
    candidates = [
        {"ticker": "INFY", "score": 0.05},
        {"ticker": "RELIANCE", "score": 0.12},
        {"ticker": "TCS", "score": 0.08}
    ]
    accepted, rejected = allocator.filter_and_rank_signals(candidates)
    
    assert len(accepted) == 2
    assert len(rejected) == 1
    assert accepted[0]["ticker"] == "RELIANCE"  # Highest score first
    assert rejected[0]["ticker"] == "INFY"      # Lowest score rejected


def test_rebalancing_schedule():
    """Test 5: Verify rebalancing schedule trigger calculation."""
    d1 = pd.Timestamp("2024-01-05") # Friday
    d2 = pd.Timestamp("2024-01-08") # Monday (next week)
    
    assert RebalanceSchedule.is_rebalance_date(d2, d1, "Daily") is True
    assert RebalanceSchedule.is_rebalance_date(d2, d1, "Weekly") is True
    assert RebalanceSchedule.is_rebalance_date(d2, d1, "Monthly") is False


def test_benchmark_alignment_and_metrics(sample_price_df):
    """Test 6: Verify benchmark date alignment and metrics calculation."""
    signals_df = generate_signals(sample_price_df, strategy_name="SMA")
    port_df, trade_df = run_backtest(signals_df)
    
    bench_comp = compare_strategy_vs_benchmark(port_df, benchmark_symbol="NIFTY50")
    assert bench_comp["status"] == "SUCCESS"
    assert "strategy_cagr" in bench_comp
    assert "benchmark_cagr" in bench_comp
    assert "beta" in bench_comp


def test_parameter_sweep(sample_price_df):
    """Test 7: Verify grid search parameter sweep runs systematically."""
    sweep_df = run_parameter_sweep(
        sample_price_df,
        strategy_name="SMA",
        param_grid={"short_window": [10, 20], "long_window": [50]}
    )
    assert not sweep_df.empty
    assert "Sharpe Ratio" in sweep_df.columns


def test_out_of_sample_split(sample_price_df):
    """Test 8: Verify In-Sample vs Out-of-Sample split and metrics degradation."""
    oos_res = run_out_of_sample_validation(sample_price_df, strategy_name="SMA", train_ratio=0.70)
    assert oos_res["status"] in ["SUCCESS", "WARNING", "FAILED"]
    assert "sharpe_degradation_pct" in oos_res


def test_langgraph_loop_stopping_conditions():
    """Test 9: Verify agent workflow loop stops within max_iterations."""
    workflow_state = run_agent_workflow("RELIANCE", "SMA", max_iterations=2)
    assert workflow_state["iteration"] <= 2
    assert workflow_state["loop_decision"] in ["ACCEPT", "ITERATE", "VALIDATE", "STOP", "FAIL"]
