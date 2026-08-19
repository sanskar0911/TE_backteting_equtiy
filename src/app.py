"""
app.py

AI Quantitative Research & Equity Backtesting Platform.
Master Streamlit Application Router & Dashboard Controller.

Features:
- Dark Bloomberg-style institutional design theme.
- Top status header & Presentation Mode toggle.
- 13 dedicated research pages (Dashboard, Backtest, Strategies, Experiments, Validation, Benchmark, Portfolio, Risk, Agent Workflow, AI Analysis, Reports, Data Quality, About).
- Interactive Plotly financial graphics (Equity curves, underwater drawdowns, Buy/Sell scatter signals, monthly heatmaps).
- LangGraph agent workflow & loop engineering state visualizer.

Run with Streamlit:
    streamlit run src/app.py
"""

import os
import sys
import pandas as pd
import numpy as np

# Ensure local imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Backend imports (NO core financial logic modified)
from strategy import generate_signals
from backtester import run_backtest
from metrics import calculate_metrics
from benchmark import compare_strategy_vs_benchmark, load_benchmark_data
from experiments.research_warnings import generate_research_warnings

# Component imports
from components.header import render_top_header
from components.sidebar import render_sidebar

# Page imports
from pages_ui.overview_dashboard import render_overview_dashboard
from pages_ui.backtest_page import render_backtest_page
from pages_ui.results_page import render_results_page
from pages_ui.strategies_page import render_strategies_page
from pages_ui.experiments_page import render_experiments_page
from pages_ui.validation_page import render_validation_page
from pages_ui.benchmark_page import render_benchmark_page
from pages_ui.portfolio_page import render_portfolio_page
from pages_ui.risk_page import render_risk_page
from pages_ui.workflow_page import render_workflow_page
from pages_ui.ai_analysis_page import render_ai_analysis_page
from pages_ui.reports_page import render_reports_page
from pages_ui.data_quality_page import render_data_quality_page
from pages_ui.presentation_mode import render_presentation_mode
from pages_ui.about_page import render_about_page


def execute_backtest_simulation(config: dict):
    """
    Execute backend backtest simulation and store results in session state.
    """
    ticker = config.get("ticker", "INFY")
    benchmark_symbol = config.get("benchmark", "NIFTY50")
    strategy_name = config.get("strategy_name", "SMA")
    strategy_kwargs = config.get("strategy_kwargs", {})

    data_path = os.path.join(BASE_DIR, "data", "processed", f"{ticker}.csv")
    if not os.path.exists(data_path):
        st.error(f"Price file for {ticker} not found at {data_path}")
        return

    df = pd.read_csv(data_path, index_col="Date")
    df.index = pd.to_datetime(df.index)

    df_signals = generate_signals(df, strategy_name=strategy_name, **strategy_kwargs)
    portfolio_df, trade_log_df = run_backtest(
        df_signals,
        initial_capital=config.get("initial_capital", 100000.0),
        txn_cost_rate=config.get("commission_pct", 0.001),
        slippage_rate=config.get("slippage_pct", 0.0005),
        position_size=config.get("position_size", 0.2),
        stop_loss=config.get("stop_loss"),
        take_profit=config.get("take_profit"),
        min_volume=config.get("min_volume", 0.0),
        min_traded_value=config.get("min_traded_value", 0.0),
        max_positions=config.get("max_positions", 10),
        rebalance_freq=config.get("rebalance_freq", "Daily")
    )

    metrics = calculate_metrics(portfolio_df, trade_log_df, initial_capital=config.get("initial_capital", 100000.0))

    try:
        benchmark_df = load_benchmark_data(benchmark_symbol)
        bench_comp = compare_strategy_vs_benchmark(portfolio_df, benchmark_df, benchmark_symbol=benchmark_symbol, initial_capital=config.get("initial_capital", 100000.0))
    except Exception as e:
        benchmark_df = None
        bench_comp = {"status": "ERROR", "warning": str(e)}

    warnings_list = generate_research_warnings(metrics, bench_comp)

    st.session_state["backtest_results"] = {
        "ticker": ticker,
        "benchmark": benchmark_symbol,
        "strategy_name": strategy_name,
        "config": config,
        "signals_df": df_signals,
        "portfolio_df": portfolio_df,
        "trade_log_df": trade_log_df,
        "metrics": metrics,
        "benchmark_df": benchmark_df,
        "bench_comp": bench_comp,
        "warnings_list": warnings_list
    }


def run_streamlit_app():
    st.set_page_config(
        page_title="AI Quant Research Platform | Equity Backtesting Engine",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    import textwrap
    css_str = textwrap.dedent("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        /* Remove top black line / default Streamlit header overlay */
        header[data-testid="stHeader"] {
            display: none !important;
        }

        .stApp {
            background-color: #0b0f19 !important;
            background-image: radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.12) 0%, transparent 50%) !important;
            color: #f8fafc !important;
            font-family: 'Inter', sans-serif;
        }

        .stApp p, .stApp label {
            font-family: 'Inter', sans-serif;
        }

        .block-container {
            padding-top: 1.2rem !important;
            padding-bottom: 3rem !important;
            max-width: 96% !important;
        }

        /* Sidebar Dark Theme */
        section[data-testid="stSidebar"] {
            background-color: #111827 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p {
            color: #cbd5e1 !important;
        }

        /* Tabs styling */
        button[data-baseweb="tab"] {
            background: rgba(0, 0, 0, 0.2) !important;
            color: #94a3b8 !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            padding: 8px 18px !important;
            border-radius: 0.5rem !important;
            margin-right: 6px !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            background: #3b82f6 !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
        }

        /* Primary Action Buttons */
        div.stButton > button {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            padding: 10px 22px !important;
            border-radius: 0.5rem !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
            transition: all 0.3s ease !important;
        }

        div.stButton > button:hover {
            background-color: #2563eb !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 16px rgba(59, 130, 246, 0.45) !important;
        }

        /* Expanders */
        div[data-testid="stExpander"] {
            background: rgba(22, 28, 45, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 0.6rem !important;
        }

        /* Pre & Code */
        pre, code, div.stCodeBlock {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.9rem !important;
            background: rgba(0, 0, 0, 0.4) !important;
            color: #cbd5e1 !important;
            border-radius: 0.5rem !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
        </style>
    """)
    st.markdown(css_str, unsafe_allow_html=True)

    # 1. Render Top Header
    render_top_header()

    # 2. Render Sidebar Navigation & Read Config
    selected_page, config = render_sidebar()

    # Auto-run backtest on initial page load if no backtest stored yet
    if "backtest_results" not in st.session_state or config.get("run_triggered"):
        execute_backtest_simulation(config)

    backtest_results = st.session_state.get("backtest_results", {})

    # 3. Check Presentation Mode Override
    if st.session_state.get("presentation_mode", False):
        render_presentation_mode(backtest_results)
        return

    # 4. Page Routing
    if selected_page == "Dashboard":
        render_overview_dashboard(backtest_results)

    elif selected_page == "Backtest":
        render_backtest_page(config, execute_backtest_simulation)

    elif selected_page == "Results":
        render_results_page(backtest_results)

    elif selected_page == "Strategies":
        render_strategies_page()

    elif selected_page == "Experiments":
        render_experiments_page(backtest_results)

    elif selected_page == "Validation":
        render_validation_page(backtest_results)

    elif selected_page == "Benchmark":
        render_benchmark_page(backtest_results)

    elif selected_page == "Portfolio":
        render_portfolio_page(backtest_results)

    elif selected_page == "Risk Analysis":
        render_risk_page(backtest_results)

    elif selected_page == "Agent Workflow":
        render_workflow_page(backtest_results)

    elif selected_page == "AI Analysis":
        render_ai_analysis_page(backtest_results)

    elif selected_page == "Reports":
        render_reports_page(backtest_results)

    elif selected_page == "Data Quality":
        render_data_quality_page(config.get("ticker", "INFY"))

    elif selected_page == "About":
        render_about_page()


def launch_server_fallback():
    import subprocess
    print("\nLaunching Streamlit Dashboard server...")
    app_file = os.path.abspath(__file__)
    cmd = [sys.executable, "-m", "streamlit", "run", app_file]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopping dashboard...")


def is_running_in_streamlit() -> bool:
    try:
        from streamlit.runtime import exists
        return exists()
    except Exception:
        return False


if __name__ == "__main__":
    if HAS_STREAMLIT and is_running_in_streamlit():
        run_streamlit_app()
    elif HAS_STREAMLIT:
        launch_server_fallback()
    else:
        print("Streamlit package is missing. Please run: pip install streamlit")
