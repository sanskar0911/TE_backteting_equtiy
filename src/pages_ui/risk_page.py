"""
risk_page.py

Page 9 — Institutional Risk Dashboard Page Renderer.
Displays Volatility, Sharpe, Sortino, Calmar, Downside Risk, Tail Risk, and Risk Warning Cards.
"""

import streamlit as st
from components.kpi_card import render_kpi_card
from components.warning_card import render_warning_card, render_warning_list
from components.chart_container import render_drawdown_plotly, render_rolling_sharpe_plotly

def render_risk_page(backtest_results: dict):
    """
    Render Institutional Risk Dashboard.
    """
    st.markdown("## 📉 Institutional Risk Dashboard")
    st.markdown("<div style='color: #94a3b8; font-size: 1.05rem; margin-bottom: 20px;'>In-depth assessment of market exposure, drawdown duration, downside tail risk, and volatility dynamics.</div>", unsafe_allow_html=True)

    if not backtest_results or "metrics" not in backtest_results:
        st.info("Please run a backtest to populate risk analytics.")
        return

    metrics = backtest_results["metrics"]
    bench_comp = backtest_results.get("bench_comp", {})
    portfolio_df = backtest_results.get("portfolio_df")
    warnings_list = backtest_results.get("warnings_list", [])

    # 1. Primary Risk KPI Grid
    col1, col2, col3, col4, col5 = st.columns(5)
    
    vol = metrics.get("Annual Volatility", 0.0) * 100.0
    sharpe = metrics.get("Sharpe Ratio", 0.0)
    sortino = metrics.get("Sortino Ratio", 0.0)
    calmar = metrics.get("Calmar Ratio", 0.0)
    max_dd = metrics.get("Maximum Drawdown", 0.0) * 100.0

    with col1:
        render_kpi_card("Annual Volatility", f"{vol:.2f}%", tooltip="Annualized standard deviation of daily returns", icon="⚡")
    with col2:
        render_kpi_card("Sharpe Ratio", f"{sharpe:.2f}", delta_color="positive" if sharpe >= 1.0 else "warning", tooltip="Excess return per unit of total risk", icon="⚖️")
    with col3:
        render_kpi_card("Sortino Ratio", f"{sortino:.2f}", delta_color="positive" if sortino >= 1.5 else "neutral", tooltip="Excess return per unit of downside risk", icon="🛡️")
    with col4:
        render_kpi_card("Calmar Ratio", f"{calmar:.2f}", tooltip="CAGR divided by Maximum Drawdown", icon="📐")
    with col5:
        render_kpi_card("Max Drawdown", f"{max_dd:.2f}%", delta_color="negative" if abs(max_dd) > 15 else "warning", tooltip="Peak-to-trough worst drop", icon="📉")

    st.markdown("---")

    # 2. Risk Warnings Section
    st.markdown("### 🚨 Active Risk Warnings & Guardrails")
    
    if warnings_list:
        render_warning_list(warnings_list)
    else:
        render_warning_card("Low Risk Flag", "No severe risk threshold breaches detected in current simulation.", warning_type="info")

    st.markdown("---")

    # 3. Interactive Risk Graphics
    col_dd, col_sharpe = st.columns(2)

    with col_dd:
        if portfolio_df is not None:
            render_drawdown_plotly(portfolio_df)

    with col_sharpe:
        if portfolio_df is not None:
            render_rolling_sharpe_plotly(portfolio_df)
