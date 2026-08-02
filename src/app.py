"""
app.py

Streamlit Web Application & Interactive Financial Dashboard for Equity Backtesting.
Supports parameter tuning (Ticker, Strategy, Capital, Commission, Position Sizing, SL/TP),
real-time simulation, KPI metric cards, analytical charts, trade log tables, and report downloads.

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
        page_title="Equity Quantitative Backtester",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📈 Quantitative Equity Backtesting Dashboard")
    st.markdown("Professional algorithmic backtesting engine & performance analytics.")

    # --- Sidebar Configuration ---
    st.sidebar.header("⚙️ Simulation Parameters")

    # 1. Ticker Selection
    available_tickers = ["INFY", "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK"]
    selected_ticker = st.sidebar.selectbox("Select Stock Ticker", available_tickers, index=0)

    # 2. Strategy Selection
    available_strategies = StrategyFactory.list_strategies()
    selected_strategy = st.sidebar.selectbox("Select Strategy", available_strategies, index=0)

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
    st.sidebar.header("💰 Risk & Capital Management")

    # 3. Capital & Risk Controls
    initial_capital = st.sidebar.number_input("Initial Capital (INR)", min_value=10000.0, value=100000.0, step=10000.0)
    commission_pct = st.sidebar.slider("Commission Rate (%)", min_value=0.0, max_value=1.0, value=0.1, step=0.05) / 100.0
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
        slippage_rate=0.0005,
        position_size=position_size_pct,
        stop_loss=stop_loss_pct,
        take_profit=take_profit_pct
    )
    metrics = calculate_metrics(portfolio_df, trade_log_df, initial_capital=initial_capital)

    # --- KPI Metrics Display ---
    st.subheader(f"📊 Strategy Performance Summary: {selected_ticker} ({selected_strategy})")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Return", f"{metrics['Total Return']*100:.2f}%")
    col2.metric("CAGR", f"{metrics['CAGR']*100:.2f}%")
    col3.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")
    col4.metric("Sortino Ratio", f"{metrics['Sortino Ratio']:.2f}")
    col5.metric("Calmar Ratio", f"{metrics['Calmar Ratio']:.2f}")

    col6, col7, col8, col9, col10 = st.columns(5)
    col6.metric("Max Drawdown", f"{metrics['Maximum Drawdown']*100:.2f}%")
    col7.metric("Win Rate", f"{metrics['Win Rate']*100:.2f}%")
    col8.metric("Profit Factor", f"{metrics['Profit Factor']:.2f}")
    col9.metric("Avg Holding (Days)", f"{metrics['Average Holding Period']:.1f}")
    col10.metric("Executed Trades", f"{int(metrics['Number of Trades'])}")

    st.markdown("---")

    # --- Interactive Tabbed Section ---
    tab1, tab2, tab3, tab4 = st.tabs(["📉 Charts & Analytics", "📋 Trade Log Table", "📄 Detailed Report", "🤖 AI Analyst"])

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
            st.image(signals_chart, caption="Strategy Crossover & Signal Markers", use_container_width=True)
        with row1_col2:
            st.image(equity_chart, caption="Portfolio Equity Growth Curve", use_container_width=True)

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.image(drawdown_chart, caption="Underwater Historical Drawdown", use_container_width=True)
        with row2_col2:
            st.image(sharpe_chart, caption="Rolling Annualized Sharpe Ratio (60-Day)", use_container_width=True)

        row3_col1, row3_col2 = st.columns(2)
        with row3_col1:
            st.image(monthly_chart, caption="Monthly Return Performance Breakdown", use_container_width=True)
        with row3_col2:
            st.image(trade_dist_chart, caption="Trade Return Distribution", use_container_width=True)

        st.image(alloc_chart, caption="Portfolio Capital Allocation (Cash vs Equity)", use_container_width=True)

    with tab2:
        st.subheader("📋 Executed Trade History")
        if not trade_log_df.empty:
            st.dataframe(trade_log_df, use_container_width=True)
            csv_data = trade_log_df.to_csv().encode("utf-8")
            st.download_button(
                label="📥 Download Trade Log CSV",
                data=csv_data,
                file_name=f"{selected_ticker}_trade_log.csv",
                mime="text/csv"
            )
        else:
            st.info("No trades executed for the selected date range and strategy parameters.")

    with tab3:
        st.subheader("📄 Automated Backtest Summary Report")
        report_path = os.path.join(results_dir, "summary.txt")
        report_config = {
            "strategy_name": f"{selected_strategy} Strategy",
            "stock_ticker": selected_ticker,
            "start_date": df.index.min().strftime("%Y-%m-%d"),
            "end_date": df.index.max().strftime("%Y-%m-%d"),
            "initial_capital": initial_capital,
            "final_value": portfolio_df["Portfolio Value"].iloc[-1]
        }
        generate_summary_report(metrics, report_config, report_path)

        if os.path.exists(report_path):
            with open(report_path, "r") as f:
                report_text = f.read()
            st.code(report_text, language="text")
            
            st.download_button(
                label="📥 Download Summary Report",
                data=report_text,
                file_name=f"{selected_ticker}_summary.txt",
                mime="text/plain"
            )

    with tab4:
        st.subheader("🤖 AI Investment Insights & Advisory")
        st.info("Run Phase 6 & Phase 7 LLM / LangGraph workflows to view full automated AI analysis.")
        
        try:
            from llm.analyzer import LLMStrategyAnalyzer
            analyzer = LLMStrategyAnalyzer()
            ai_res = analyzer.analyze_performance(metrics, selected_ticker, selected_strategy)
            st.json(ai_res)
        except Exception as e:
            st.warning(f"LLM Analyzer preview: {e}")


def launch_server_fallback():
    """Fallback runner when Streamlit is executed via standard python CLI."""
    import subprocess
    print("\nLaunching Streamlit Dashboard server...")
    app_file = os.path.abspath(__file__)
    cmd = [sys.executable, "-m", "streamlit", "run", app_file]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopping dashboard...")


def is_running_in_streamlit() -> bool:
    """Check if the script is currently being run via Streamlit CLI."""
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
