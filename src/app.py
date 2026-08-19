"""
app.py

Streamlit Web Application & Interactive Institutional Financial Dashboard for Equity Backtesting.
Supports parameter tuning (Ticker, Strategy, Capital, Commission, Position Sizing, SL/TP, Liquidity, Benchmark, Rebalance Frequency),
real-time simulation, KPI metric cards, analytical charts, trade log tables, research experiments, LangGraph loop visualizer, and report downloads.

Run with Streamlit:
    streamlit run src/app.py
"""

import os
import sys

# Ensure local imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

import pandas as pd
import numpy as np

# Try importing Streamlit
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

from strategies.factory import StrategyFactory
from strategy import generate_signals
from backtester import run_backtest
from metrics import calculate_metrics
from benchmark import compare_strategy_vs_benchmark, load_benchmark_data
from experiments.parameter_sweep import run_parameter_sweep
from experiments.walk_forward import run_walk_forward_analysis
from experiments.out_of_sample import run_out_of_sample_validation
from experiments.robustness import run_robustness_analysis
from experiments.regime_analysis import run_regime_analysis
from experiments.research_warnings import generate_research_warnings
from agent.workflow import run_agent_workflow
from visualization import (
    plot_signals,
    plot_equity_curve,
    plot_drawdown,
    plot_rolling_sharpe,
    plot_monthly_returns,
    plot_trade_distribution,
    plot_portfolio_allocation
)
from report import generate_summary_report


def run_streamlit_app():
    st.set_page_config(
        page_title="Equity Backtesting Dashboard | Shankh Internship",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS matching index.html dark design system and controlling image/text sizes
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        /* Dark Theme Foundation from index.html */
        .stApp {
            background-color: #0b0f19 !important;
            background-image: radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.15) 0%, transparent 50%) !important;
            color: #f8fafc !important;
            font-family: 'Inter', sans-serif !important;
        }

        html, body, p, div, span, label, input, select {
            font-family: 'Inter', sans-serif !important;
            font-size: 16px !important;
        }

        .block-container {
            padding-top: 1.8rem !important;
            padding-bottom: 3rem !important;
            max-width: 95% !important;
        }

        /* Logo Header */
        .logo-header {
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.025em !important;
            background: linear-gradient(to right, #3b82f6, #60a5fa, #10b981) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            margin-bottom: 0.2rem !important;
        }

        .logo-sub {
            color: #94a3b8 !important;
            font-size: 1.1rem !important;
            font-weight: 500 !important;
            margin-bottom: 1.8rem !important;
        }

        /* Metric Cards matching index.html */
        div[data-testid="metric-container"] {
            background: rgba(22, 28, 45, 0.85) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 0.75rem !important;
            padding: 1.25rem 1.5rem !important;
            backdrop-filter: blur(10px) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
            transition: transform 0.3s, border-color 0.3s !important;
        }

        div[data-testid="metric-container"]:hover {
            transform: translateY(-2px) !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
        }

        div[data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 0.9rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            margin-bottom: 0.4rem !important;
        }

        div[data-testid="stMetricValue"] {
            font-size: 2.0rem !important;
            font-weight: 700 !important;
            color: #f8fafc !important;
        }

        div[data-testid="stMetricDelta"] {
            font-size: 1.0rem !important;
            font-weight: 600 !important;
        }

        /* Section Headings */
        .stMarkdown h2, h2 {
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            color: #f8fafc !important;
            margin-top: 1.2rem !important;
            margin-bottom: 0.8rem !important;
        }

        .stMarkdown h3, h3 {
            font-size: 1.3rem !important;
            font-weight: 600 !important;
            color: #3b82f6 !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #111827 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: #e2e8f0 !important;
            font-size: 1.05rem !important;
            font-weight: 600 !important;
        }

        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3 {
            color: #3b82f6 !important;
            font-size: 1.25rem !important;
            font-weight: 700 !important;
        }

        /* Tabs styling matching index.html */
        button[data-baseweb="tab"] {
            background: rgba(0, 0, 0, 0.2) !important;
            color: #94a3b8 !important;
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            padding: 10px 20px !important;
            border-radius: 0.5rem !important;
            margin-right: 6px !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            background: #3b82f6 !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
        }

        /* CRITICAL FIX: IMAGE SIZING CONTROL (Prevents massive 1000px height images) */
        img {
            max-height: 420px !important;
            max-width: 100% !important;
            object-fit: contain !important;
            border-radius: 8px !important;
            margin: 0 auto !important;
            display: block !important;
            background-color: rgba(15, 23, 42, 0.6) !important;
            padding: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        /* Buttons matching index.html */
        div.stButton > button {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            padding: 12px 26px !important;
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

        /* Preformatted Report & Monospace Code */
        pre, code, div.stCodeBlock {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.95rem !important;
            background: rgba(0, 0, 0, 0.4) !important;
            color: #cbd5e1 !important;
            border-radius: 0.5rem !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
        }

        /* Dataframe tables */
        div[data-testid="stDataFrame"] {
            border-radius: 0.5rem !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            font-size: 0.95rem !important;
        }

        /* Alert boxes */
        div.stAlert {
            font-size: 1.05rem !important;
            border-radius: 0.5rem !important;
            background-color: rgba(30, 41, 59, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='logo-header'>QUANTUM LABS — EQUITY BACKTESTING</div>", unsafe_allow_html=True)
    st.markdown("<div class='logo-sub'>Shankh / Decuple Internship 2026-27 (Project TE1) &bull; Algorithmic Strategy & Risk Engine</div>", unsafe_allow_html=True)

    # --- Sidebar Configuration ---
    st.sidebar.header("⚙️ Strategy & Execution Setup")

    # 1. Ticker & Benchmark Selection
    available_tickers = ["INFY", "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK"]
    selected_ticker = st.sidebar.selectbox("Select Stock Ticker", available_tickers, index=0)
    selected_benchmark = st.sidebar.selectbox("Select Benchmark", ["NIFTY50"], index=0)

    # 2. Strategy Selection
    available_strategies = StrategyFactory.list_strategies()
    selected_strategy = st.sidebar.selectbox("Select Strategy Architecture", available_strategies, index=0)

    # Strategy Specific Parameters
    strategy_kwargs = {}
    if selected_strategy == "SMA":
        short_w = st.sidebar.number_input("Short SMA Window", min_value=5, max_value=100, value=20)
        long_w = st.sidebar.number_input("Long SMA Window", min_value=10, max_value=200, value=50)
        strategy_kwargs = {"short_window": short_w, "long_window": long_w}
    elif selected_strategy == "EMA":
        short_w = st.sidebar.number_input("Short EMA Window", min_value=5, max_value=100, value=12)
        long_w = st.sidebar.number_input("Long EMA Window", min_value=10, max_value=200, value=26)
        strategy_kwargs = {"short_window": short_w, "long_window": long_w}
    elif selected_strategy == "RSI":
        rsi_p = st.sidebar.number_input("RSI Period", min_value=5, max_value=50, value=14)
        oversold = st.sidebar.number_input("Oversold Level", min_value=10.0, max_value=45.0, value=30.0)
        overbought = st.sidebar.number_input("Overbought Level", min_value=55.0, max_value=90.0, value=70.0)
        strategy_kwargs = {"period": rsi_p, "oversold": oversold, "overbought": overbought}

    st.sidebar.markdown("---")
    st.sidebar.header("🛡️ Liquidity & Position Rules")

    # 3. Portfolio & Liquidity Constraints
    max_positions = st.sidebar.number_input("Maximum Position Cap", min_value=1, max_value=50, value=10)
    rebalance_freq = st.sidebar.selectbox("Rebalancing Frequency", ["Daily", "Weekly", "Monthly"], index=0)
    
    use_liquidity = st.sidebar.checkbox("Enable Liquidity Filter", value=True)
    min_volume = st.sidebar.number_input("Min Daily Volume", min_value=0, value=10000) if use_liquidity else 0
    min_traded_val = st.sidebar.number_input("Min Traded Value (INR)", min_value=0, value=500000) if use_liquidity else 0.0

    st.sidebar.markdown("---")
    st.sidebar.header("💰 Risk & Capital Management")

    # 4. Capital & Friction Controls
    initial_capital = st.sidebar.number_input("Initial Capital (INR)", min_value=10000.0, value=100000.0, step=10000.0)
    commission_pct = st.sidebar.slider("Commission Rate (%)", min_value=0.0, max_value=1.0, value=0.1, step=0.05) / 100.0
    slippage_pct = st.sidebar.slider("Slippage Rate (%)", min_value=0.0, max_value=0.5, value=0.05, step=0.01) / 100.0
    position_size_pct = st.sidebar.slider("Position Size (% Capital)", min_value=10, max_value=100, value=20, step=5) / 100.0
    
    use_sl = st.sidebar.checkbox("Enable Stop Loss", value=True)
    stop_loss_pct = (st.sidebar.slider("Stop Loss (%)", min_value=1.0, max_value=20.0, value=5.0, step=0.5) / 100.0) if use_sl else None

    use_tp = st.sidebar.checkbox("Enable Take Profit", value=True)
    take_profit_pct = (st.sidebar.slider("Take Profit (%)", min_value=1.0, max_value=50.0, value=10.0, step=1.0) / 100.0) if use_tp else None

    run_button = st.sidebar.button("🚀 Run Backtest Simulation", type="primary")

    # --- Load Data & Execute Backtest ---
    data_path = os.path.join(BASE_DIR, "data", "processed", f"{selected_ticker}.csv")
    if not os.path.exists(data_path):
        st.error(f"Processed price file for {selected_ticker} not found at {data_path}")
        return

    df = pd.read_csv(data_path, index_col="Date")
    df.index = pd.to_datetime(df.index)

    df_signals = generate_signals(df, strategy_name=selected_strategy, **strategy_kwargs)
    portfolio_df, trade_log_df = run_backtest(
        df_signals,
        initial_capital=initial_capital,
        txn_cost_rate=commission_pct,
        slippage_rate=slippage_pct,
        position_size=position_size_pct,
        stop_loss=stop_loss_pct,
        take_profit=take_profit_pct,
        min_volume=min_volume,
        min_traded_value=min_traded_val,
        max_positions=max_positions,
        rebalance_freq=rebalance_freq
    )
    metrics = calculate_metrics(portfolio_df, trade_log_df, initial_capital=initial_capital)

    # Benchmark comparison
    try:
        bench_df = load_benchmark_data(selected_benchmark)
        bench_comp = compare_strategy_vs_benchmark(portfolio_df, bench_df, benchmark_symbol=selected_benchmark, initial_capital=initial_capital)
    except Exception:
        bench_df = None
        bench_comp = {}

    # Research Warnings
    warnings_list = generate_research_warnings(metrics, bench_comp)

    # --- KPI Metrics Display ---
    st.subheader(f"📊 Performance Summary: {selected_ticker} ({selected_strategy}) vs {selected_benchmark}")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Return", f"{metrics['Total Return']*100:.2f}%")
    col2.metric("CAGR", f"{metrics['CAGR']*100:.2f}%", f"{bench_comp.get('excess_return', 0.0)*100:+.2f}% vs Bench")
    col3.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}", f"Bench: {bench_comp.get('benchmark_sharpe', 0.0):.2f}")
    col4.metric("Sortino Ratio", f"{metrics['Sortino Ratio']:.2f}")
    col5.metric("Calmar Ratio", f"{metrics['Calmar Ratio']:.2f}")

    col6, col7, col8, col9, col10 = st.columns(5)
    col6.metric("Max Drawdown", f"{metrics['Maximum Drawdown']*100:.2f}%")
    col7.metric("Win Rate", f"{metrics['Win Rate']*100:.2f}%")
    col8.metric("Profit Factor", f"{metrics['Profit Factor']:.2f}")
    col9.metric("Beta vs Nifty", f"{bench_comp.get('beta', 1.0):.2f}")
    col10.metric("Executed Trades", f"{int(metrics['Number of Trades'])}")

    # Display Active Warnings Banner if any
    if warnings_list:
        with st.expander(f"⚠️ Research Warnings ({len(warnings_list)} detected)", expanded=True):
            for w in warnings_list:
                st.warning(w)

    st.markdown("---")

    # --- Interactive Tabbed Section ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📉 Charts & Analytics",
        "🔬 Research & Experiments",
        "🔄 Agent Loop Engineering",
        "📋 Trade Log Table",
        "📄 Strategy Fact Sheet",
        "🤖 AI Analyst"
    ])

    with tab1:
        results_dir = os.path.join(BASE_DIR, "results")
        os.makedirs(results_dir, exist_ok=True)

        signals_chart = os.path.join(results_dir, "signals_chart.png")
        equity_chart = os.path.join(results_dir, "equity_curve.png")
        drawdown_chart = os.path.join(results_dir, "drawdown.png")
        sharpe_chart = os.path.join(results_dir, "rolling_sharpe.png")
        monthly_chart = os.path.join(results_dir, "monthly_returns.png")
        trade_dist_chart = os.path.join(results_dir, "trade_dist.png")
        alloc_chart = os.path.join(results_dir, "allocation.png")

        plot_signals(df_signals, selected_ticker, signals_chart)
        plot_equity_curve(portfolio_df, selected_ticker, equity_chart)
        plot_drawdown(portfolio_df, drawdown_chart)
        plot_rolling_sharpe(portfolio_df, sharpe_chart)
        plot_monthly_returns(portfolio_df, monthly_chart)
        plot_trade_distribution(trade_log_df, trade_dist_chart)
        plot_portfolio_allocation(portfolio_df, alloc_chart)

        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.image(signals_chart, caption="Strategy Crossover & Signal Markers")
        with row1_col2:
            st.image(equity_chart, caption="Portfolio Equity Growth Curve")

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.image(drawdown_chart, caption="Underwater Historical Drawdown")
        with row2_col2:
            st.image(sharpe_chart, caption="Rolling Annualized Sharpe Ratio (60-Day)")

        row3_col1, row3_col2 = st.columns(2)
        with row3_col1:
            st.image(monthly_chart, caption="Monthly Return Performance Breakdown")
        with row3_col2:
            st.image(trade_dist_chart, caption="Trade Return Distribution")

        st.image(alloc_chart, caption="Portfolio Capital Allocation (Cash vs Equity)")

    with tab2:
        st.subheader("🔬 Quantitative Experiment Engine & Validation Suite")
        st.markdown("Run multi-parameter sweeps, walk-forward testing, out-of-sample validation, and robustness sensitivity tests.")

        exp_mode = st.radio("Select Experiment Engine", ["Parameter Sweep", "Out-of-Sample Validation", "Robustness Analysis", "Market Regime Breakdown"], horizontal=True)

        if exp_mode == "Parameter Sweep":
            if st.button("▶ Run Parameter Sweep"):
                with st.spinner("Executing grid search parameter sweep..."):
                    sweep_df = run_parameter_sweep(df, strategy_name=selected_strategy, initial_capital=initial_capital)
                    st.dataframe(sweep_df)

        elif exp_mode == "Out-of-Sample Validation":
            if st.button("▶ Run Out-of-Sample Split Audit"):
                with st.spinner("Validating Train/Test split and checking look-ahead bias..."):
                    oos_res = run_out_of_sample_validation(df, strategy_name=selected_strategy, strategy_params=strategy_kwargs, initial_capital=initial_capital)
                    st.json(oos_res)

        elif exp_mode == "Robustness Analysis":
            if st.button("▶ Run Perturbation Sensitivity Test"):
                with st.spinner("Testing sensitivity under execution cost & sizing variations..."):
                    rob_res = run_robustness_analysis(df, strategy_name=selected_strategy, baseline_params=strategy_kwargs, initial_capital=initial_capital)
                    st.write("### Robustness Stability Summary:", rob_res["summary"])
                    st.dataframe(rob_res["details_df"])

        elif exp_mode == "Market Regime Breakdown":
            if bench_df is not None:
                reg_res = run_regime_analysis(portfolio_df, trade_log_df, bench_df, initial_capital=initial_capital)
                st.write("### Strategy Performance by Market Regime:", reg_res)

    with tab3:
        st.subheader("🔄 LangGraph Loop Engineering Visualizer")
        st.markdown("Automated research loop state machine: **HYPOTHESIS → BACKTEST → EVALUATION → ITERATION/VALIDATION → REPORT**")

        if st.button("▶ Execute LangGraph Agent Research Loop"):
            with st.spinner("Executing LangGraph agent loop with controlled stopping logic..."):
                workflow_state = run_agent_workflow(
                    ticker=selected_ticker,
                    strategy_name=selected_strategy,
                    initial_capital=initial_capital,
                    max_iterations=3
                )

                st.success(f"LangGraph Workflow Complete! Final Decision: **{workflow_state['loop_decision']}**")
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Total Iterations Completed", workflow_state["iteration"])
                col_b.metric("Loop Decision Status", workflow_state["loop_decision"])
                col_c.metric("Active Warnings", len(workflow_state["warnings"]))

                st.subheader("📜 Research History Log Across Iterations")
                history_df = pd.DataFrame(workflow_state.get("experiment_history", []))
                if not history_df.empty:
                    st.dataframe(history_df)

    with tab4:
        st.subheader("📋 Executed Trade History")
        if not trade_log_df.empty:
            st.dataframe(trade_log_df)
            csv_data = trade_log_df.to_csv().encode("utf-8")
            st.download_button(
                label="📥 Download Trade Log CSV",
                data=csv_data,
                file_name=f"{selected_ticker}_trade_log.csv",
                mime="text/csv"
            )
        else:
            st.info("No trades executed for the selected date range and strategy parameters.")

    with tab5:
        st.subheader("📄 Automated Final Strategy Fact Sheet")
        report_path = os.path.join(results_dir, "summary.txt")
        report_config = {
            "strategy_name": f"{selected_strategy} Strategy",
            "stock_ticker": selected_ticker,
            "start_date": df.index.min().strftime("%Y-%m-%d"),
            "end_date": df.index.max().strftime("%Y-%m-%d"),
            "initial_capital": initial_capital,
            "final_value": portfolio_df["Portfolio Value"].iloc[-1],
            "position_size": position_size_pct,
            "max_positions": max_positions,
            "rebalance_freq": rebalance_freq,
            "txn_cost_rate": commission_pct,
            "slippage_rate": slippage_pct,
            "stop_loss": stop_loss_pct,
            "take_profit": take_profit_pct
        }
        generate_summary_report(metrics, report_config, report_path, benchmark_comp=bench_comp, warnings_list=warnings_list)

        if os.path.exists(report_path):
            with open(report_path, "r") as f:
                report_text = f.read()
            st.code(report_text, language="text")
            
            st.download_button(
                label="📥 Download Strategy Fact Sheet",
                data=report_text,
                file_name=f"{selected_ticker}_fact_sheet.txt",
                mime="text/plain"
            )

    with tab6:
        st.subheader("🤖 AI Investment Insights & Advisory — Full Institutional Analysis")
        try:
            from llm.analyzer import LLMStrategyAnalyzer
            analyzer = LLMStrategyAnalyzer()
            ai_res = analyzer.analyze_performance(metrics, selected_ticker, selected_strategy)

            rating      = ai_res.get("rating", "N/A")
            risk_level  = ai_res.get("risk", "N/A")
            conf        = ai_res.get("confidence", 0.0)
            emoji_map   = {"Strong Buy": "🟢", "Moderate Buy": "🔵", "Neutral": "🟡", "Underperform": "🔴"}
            rating_emoji = emoji_map.get(rating, "⚪")
            st.markdown(
                f"## {rating_emoji} Rating: **{rating}** &nbsp;|&nbsp; "
                f"Risk: **{risk_level}** &nbsp;|&nbsp; Confidence: **{conf*100:.0f}%**"
            )
            st.markdown("---")

            if ai_res.get("executive_summary"):
                st.markdown("### 📋 Executive Summary")
                st.info(ai_res["executive_summary"])

            if ai_res.get("recommendation"):
                st.markdown("### 📌 Investment Recommendation")
                st.warning(ai_res["recommendation"])

            st.markdown("---")
            st.markdown("## 📊 Detailed Metric-by-Metric Analysis")

            if ai_res.get("return_analysis"):
                with st.expander("📈 Total Return & CAGR Analysis", expanded=True):
                    st.markdown(ai_res["return_analysis"])

            if ai_res.get("sharpe_analysis"):
                with st.expander("⚖️ Sharpe Ratio — Risk-Adjusted Return Deep Dive", expanded=True):
                    st.markdown(ai_res["sharpe_analysis"])

            if ai_res.get("drawdown_analysis"):
                with st.expander("📉 Maximum Drawdown — Tail Risk & Recovery Analysis", expanded=True):
                    st.markdown(ai_res["drawdown_analysis"])

        except Exception as e:
            st.error(f"AI Analyst Error: {e}")


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
