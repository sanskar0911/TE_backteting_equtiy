"""
results_page.py

Page 3 — Performance Results & Interactive Analytics Page.
Displays interactive Plotly charts, performance summary grids, and filterable trade log table.
"""

import pandas as pd
import streamlit as st
from components.kpi_card import render_kpi_grid
from components.chart_container import (
    render_equity_curve_plotly,
    render_drawdown_plotly,
    render_signals_plotly,
    render_monthly_heatmap_plotly,
    render_rolling_sharpe_plotly,
    render_portfolio_allocation_plotly
)

def render_results_page(backtest_results: dict):
    """
    Render complete backtest results and analytics.
    """
    if not backtest_results or "metrics" not in backtest_results:
        st.info("No backtest results available. Please run a backtest from the sidebar or Backtest page.")
        return

    ticker = backtest_results.get("ticker", "INFY")
    strategy_name = backtest_results.get("strategy_name", "SMA")
    benchmark_symbol = backtest_results.get("benchmark", "NIFTY50")
    portfolio_df = backtest_results.get("portfolio_df")
    benchmark_df = backtest_results.get("benchmark_df")
    signals_df = backtest_results.get("signals_df")
    trade_log_df = backtest_results.get("trade_log_df")
    metrics = backtest_results.get("metrics")
    bench_comp = backtest_results.get("bench_comp")

    # Top Header Banner
    start_date = portfolio_df.index.min().strftime("%Y-%m-%d") if portfolio_df is not None else ""
    end_date = portfolio_df.index.max().strftime("%Y-%m-%d") if portfolio_df is not None else ""

    st.markdown(f"## 📈 Results: {strategy_name} Strategy on {ticker}")
    st.markdown(f"<div style='color: #94a3b8; font-size: 1.0rem; margin-bottom: 20px;'>Testing Period: <b>{start_date}</b> to <b>{end_date}</b> &bull; Benchmark: <b>{benchmark_symbol}</b></div>", unsafe_allow_html=True)

    # KPI Grid
    render_kpi_grid(metrics, bench_comp)

    st.markdown("---")

    # Tabbed Interactive Visualizations
    tab_equity, tab_signals, tab_drawdown, tab_heatmap, tab_risk, tab_trades = st.tabs([
        "📈 Equity Growth",
        "🎯 BUY/SELL Signals",
        "📉 Drawdown Underwater",
        "🗓️ Monthly Return Heatmap",
        "⚖️ Rolling Risk & Sharpe",
        "📋 Executed Trade History"
    ])

    with tab_equity:
        if portfolio_df is not None:
            render_equity_curve_plotly(portfolio_df, benchmark_df, ticker, benchmark_symbol)

    with tab_signals:
        if signals_df is not None:
            render_signals_plotly(signals_df, ticker)

    with tab_drawdown:
        if portfolio_df is not None:
            render_drawdown_plotly(portfolio_df)

    with tab_heatmap:
        if portfolio_df is not None:
            render_monthly_heatmap_plotly(portfolio_df)

    with tab_risk:
        if portfolio_df is not None:
            col1, col2 = st.columns(2)
            with col1:
                render_rolling_sharpe_plotly(portfolio_df)
            with col2:
                render_portfolio_allocation_plotly(portfolio_df)

    with tab_trades:
        st.markdown("### 📋 Executed Trade Table & Filter")
        if trade_log_df is not None and not trade_log_df.empty:
            # Filters
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                type_col = "BUY/SELL" if "BUY/SELL" in trade_log_df.columns else "Type"
                if type_col in trade_log_df.columns:
                    action_filter = st.multiselect("Filter Action", options=trade_log_df[type_col].unique(), default=list(trade_log_df[type_col].unique()))
                    filtered_df = trade_log_df[trade_log_df[type_col].isin(action_filter)]
                else:
                    filtered_df = trade_log_df
            with col_f2:
                search_symbol = st.text_input("Search Symbol / Date", "")
                if search_symbol:
                    filtered_df = filtered_df[filtered_df.astype(str).apply(lambda row: row.str.contains(search_symbol, case=False).any(), axis=1)]

            st.dataframe(filtered_df, use_container_width=True)

            csv_bytes = filtered_df.to_csv().encode("utf-8")
            st.download_button(
                label="📥 Download Filtered Trade Log CSV",
                data=csv_bytes,
                file_name=f"{ticker}_trade_log.csv",
                mime="text/csv"
            )
        else:
            st.info("No trades executed during the selected date range.")
