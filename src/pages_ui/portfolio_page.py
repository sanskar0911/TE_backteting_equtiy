"""
portfolio_page.py

Page 8 — Portfolio Analytics Page Renderer.
Displays asset allocation breakdown, cash vs equity exposure dynamics, turnover,
and concentration warning cards.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
from components.chart_container import render_portfolio_allocation_plotly
from components.warning_card import render_warning_card

def render_portfolio_page(backtest_results: dict):
    """
    Render Portfolio Analytics Page.
    """
    st.markdown("## 💼 Portfolio Analytics & Asset Allocation")
    st.markdown("<div style='color: #94a3b8; font-size: 1.05rem; margin-bottom: 20px;'>Monitor cash balances, active equity exposure, portfolio turnover, and asset concentration limits.</div>", unsafe_allow_html=True)

    if not backtest_results or "portfolio_df" not in backtest_results:
        st.info("Please run a backtest to display portfolio analytics.")
        return

    portfolio_df = backtest_results["portfolio_df"]
    metrics = backtest_results.get("metrics", {})
    ticker = backtest_results.get("ticker", "INFY")
    pos_size_pct = backtest_results.get("config", {}).get("position_size", 0.2) * 100.0

    # 1. Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    final_val = portfolio_df["Portfolio Value"].iloc[-1]
    last_cash = portfolio_df["Cash"].iloc[-1] if "Cash" in portfolio_df.columns else final_val * 0.2
    invested = final_val - last_cash
    exposure_pct = (invested / final_val) * 100.0 if final_val > 0 else 0.0

    col1.metric("Final Portfolio Value", f"₹{final_val:,.0f}")
    col2.metric("Cash Balance", f"₹{last_cash:,.0f}")
    col3.metric("Invested Capital", f"₹{invested:,.0f}")
    col4.metric("Active Equity Exposure", f"{exposure_pct:.1f}%")

    st.markdown("---")

    col_chart, col_pie = st.columns([2, 1])

    with col_chart:
        render_portfolio_allocation_plotly(portfolio_df)

    with col_pie:
        st.markdown("### 🍩 Current Asset Breakdown")
        pie_df = pd.DataFrame({
            "Asset": ["Cash Reserves", f"{ticker} Equity Position"],
            "Value": [last_cash, invested]
        })
        fig = px.pie(
            pie_df,
            names="Asset",
            values="Value",
            hole=0.4,
            color_discrete_sequence=["#64748b", "#3b82f6"]
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8"),
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)

        # Concentration Warning
        if pos_size_pct >= 25.0:
            render_warning_card(
                title="Single-Stock Concentration Flag",
                text=f"Single position sizing is set to {pos_size_pct:.0f}% of total portfolio capital. Consider reducing cap to <20% for diversification.",
                warning_type="warning"
            )
