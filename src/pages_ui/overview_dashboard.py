"""
overview_dashboard.py

Page 1 — Overview Dashboard Renderer.
Landing dashboard displaying institutional summary KPIs, equity preview chart,
and quick launch inter-page navigation buttons.
"""

import textwrap
import streamlit as st
from components.kpi_card import render_kpi_grid
from components.chart_container import render_equity_curve_plotly
from components.warning_card import render_warning_list

def render_overview_dashboard(backtest_results: dict):
    """
    Render landing overview dashboard.
    """
    st.markdown("## 📊 Equity Research Dashboard")
    subhead_html = textwrap.dedent("<div style='color: #94a3b8; font-size: 1.05rem; margin-bottom: 20px;'>Backtest, validate and analyze Indian equity strategies.</div>")
    st.markdown(subhead_html, unsafe_allow_html=True)

    if not backtest_results or "metrics" not in backtest_results:
        st.info("💡 Welcome! Click **🚀 Run Backtest Engine** in the sidebar to simulate strategy performance.")
        return

    metrics = backtest_results["metrics"]
    bench_comp = backtest_results.get("bench_comp", {})
    portfolio_df = backtest_results.get("portfolio_df")
    benchmark_df = backtest_results.get("benchmark_df")
    warnings_list = backtest_results.get("warnings_list", [])

    # 1. Top KPI Summary Grid
    render_kpi_grid(metrics, bench_comp)

    st.markdown("---")

    # 2. Equity Growth Interactive Chart & Quick Summary
    col_chart, col_summary = st.columns([2, 1])

    with col_chart:
        if portfolio_df is not None:
            render_equity_curve_plotly(
                portfolio_df,
                benchmark_df=benchmark_df,
                ticker=backtest_results.get("ticker", "INFY"),
                benchmark_symbol=backtest_results.get("benchmark", "NIFTY50")
            )

    with col_summary:
        st.markdown("### 🎯 Executive Strategy Summary")
        ticker = backtest_results.get("ticker", "INFY")
        strategy = backtest_results.get("strategy_name", "SMA")
        cagr = metrics.get("CAGR", 0.0) * 100.0
        sharpe = metrics.get("Sharpe Ratio", 0.0)
        max_dd = metrics.get("Maximum Drawdown", 0.0) * 100.0
        n_trades = metrics.get("Number of Trades", 0)

        summary_html = textwrap.dedent(f"""
            <div style="
                background: rgba(22, 28, 45, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 0.75rem;
                padding: 1.2rem;
                line-height: 1.6;
            ">
                <div style="margin-bottom: 8px;">📌 <b>Target Stock:</b> <span style="color: #60a5fa;">{ticker}</span></div>
                <div style="margin-bottom: 8px;">⚙️ <b>Strategy:</b> <span style="color: #60a5fa;">{strategy} Crossover</span></div>
                <div style="margin-bottom: 8px;">📈 <b>Annual Return (CAGR):</b> <b style="color: {'#10b981' if cagr >= 0 else '#ef4444'};">{cagr:+.2f}%</b></div>
                <div style="margin-bottom: 8px;">⚖️ <b>Sharpe Ratio:</b> <b>{sharpe:.2f}</b></div>
                <div style="margin-bottom: 8px;">📉 <b>Max Drawdown:</b> <b style="color: #ef4444;">{max_dd:.2f}%</b></div>
                <div style="margin-bottom: 12px;">📊 <b>Total Trades Executed:</b> {n_trades}</div>
            </div>
        """)
        st.markdown(summary_html, unsafe_allow_html=True)

        if warnings_list:
            st.markdown("<br>", unsafe_allow_html=True)
            render_warning_list(warnings_list[:2])

    st.markdown("---")

    # 3. Inter-Page Quick Action Jump Panel
    st.markdown("### 🔗 Platform Quick Action Hub")
    col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns(5)

    if col_nav1.button("⚙️ Backtest Config", use_container_width=True):
        st.session_state["current_page"] = "Backtest"
        st.rerun()

    if col_nav2.button("📈 Detailed Results", use_container_width=True):
        st.session_state["current_page"] = "Results"
        st.rerun()

    if col_nav3.button("🔬 Experiment Lab", use_container_width=True):
        st.session_state["current_page"] = "Experiments"
        st.rerun()

    if col_nav4.button("🔄 Agent Workflow", use_container_width=True):
        st.session_state["current_page"] = "Agent Workflow"
        st.rerun()

    if col_nav5.button("📄 Fact Sheet", use_container_width=True):
        st.session_state["current_page"] = "Reports"
        st.rerun()
