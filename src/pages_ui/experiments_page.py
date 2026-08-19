"""
experiments_page.py

Page 5 — Research Experiment Lab Page Renderer.
Allows quants to specify research hypotheses, parameter ranges, and execute baseline,
grid sweeps, walk-forward, and out-of-sample validation runs.
"""

import pandas as pd
import streamlit as st
from experiments.parameter_sweep import run_parameter_sweep
from experiments.walk_forward import run_walk_forward_analysis
from experiments.out_of_sample import run_out_of_sample_validation
from components.experiment_table import render_experiment_table

def render_experiments_page(backtest_results: dict):
    """
    Render Research Experiment Lab.
    """
    st.markdown("## 🔬 Research Experiment Lab")
    st.markdown("<div style='color: #94a3b8; font-size: 1.05rem; margin-bottom: 20px;'>Formulate hypotheses, run grid parameter sweeps, and execute walk-forward & out-of-sample splits.</div>", unsafe_allow_html=True)

    # Hypothesis Definition Form
    with st.expander("📝 Formulate Quantitative Hypothesis", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            hypothesis = st.text_area("Research Hypothesis Statement", value="Testing moving average crossover edge with transaction costs on Indian equities.")
            selected_ticker = st.selectbox("Target Ticker", ["INFY", "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK"], key="exp_ticker")
            selected_strategy = st.selectbox("Target Strategy", ["SMA", "EMA", "RSI"], key="exp_strat")
        with col2:
            st.markdown("<b>Assumptions & Friction Setup:</b>", unsafe_allow_html=True)
            capital = st.number_input("Initial Capital (INR)", value=100000.0, key="exp_cap")
            commission = st.number_input("Commission Rate (%)", value=0.1, key="exp_comm") / 100.0
            slippage = st.number_input("Slippage Rate (%)", value=0.05, key="exp_slip") / 100.0

    st.markdown("### ⚡ Execute Experiment Engines")

    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
    run_sweep = btn_col1.button("▶ Parameter Sweep Grid", type="primary", use_container_width=True)
    run_wf = btn_col2.button("▶ Walk-Forward Analysis", use_container_width=True)
    run_oos = btn_col3.button("▶ Out-of-Sample Split Audit", use_container_width=True)
    run_baseline = btn_col4.button("▶ Baseline Single Run", use_container_width=True)

    # Load price data
    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_path = os.path.join(BASE_DIR, "data", "processed", f"{selected_ticker}.csv")

    if not os.path.exists(data_path):
        st.error(f"Price data for {selected_ticker} not found.")
        return

    df = pd.read_csv(data_path, index_col="Date")
    df.index = pd.to_datetime(df.index)

    if run_sweep:
        with st.spinner("Executing parameter grid sweep across parameter combinations..."):
            sweep_df = run_parameter_sweep(
                df,
                strategy_name=selected_strategy,
                initial_capital=capital,
                txn_cost_rate=commission,
                slippage_rate=slippage
            )
            st.session_state["last_sweep_df"] = sweep_df

    if run_wf:
        with st.spinner("Executing Walk-Forward Rolling Analysis..."):
            wf_res = run_walk_forward_analysis(
                df,
                strategy_name=selected_strategy,
                initial_capital=capital
            )
            st.session_state["last_wf_res"] = wf_res

    if run_oos:
        with st.spinner("Executing Train/Test 70:30 Out-of-Sample Split..."):
            oos_res = run_out_of_sample_validation(
                df,
                strategy_name=selected_strategy,
                initial_capital=capital
            )
            st.session_state["last_oos_res"] = oos_res

    # Render results if available
    if "last_sweep_df" in st.session_state:
        render_experiment_table(st.session_state["last_sweep_df"])

    if "last_wf_res" in st.session_state:
        st.markdown("### 🔄 Walk-Forward Rolling Results")
        st.json(st.session_state["last_wf_res"])

    if "last_oos_res" in st.session_state:
        st.markdown("### 🛡️ Out-of-Sample Split Results")
        st.json(st.session_state["last_oos_res"])
