"""
reports_page.py

Page 12 — Reports & Fact Sheet Hub Page Renderer.
Renders final strategy fact sheet, download center, and exported text/JSON reports.
"""

import os
import streamlit as st
from report import generate_summary_report
from components.report_card import render_strategy_fact_sheet

def render_reports_page(backtest_results: dict):
    """
    Render Report Center & Fact Sheet Hub.
    """
    st.markdown("## 📄 Research Report & Fact Sheet Hub")
    st.markdown("<div style='color: #94a3b8; font-size: 1.05rem; margin-bottom: 20px;'>Generate institutional strategy fact sheets and download CSV/JSON research artifacts.</div>", unsafe_allow_html=True)

    if not backtest_results or "metrics" not in backtest_results:
        st.info("Please run a backtest to generate report artifacts.")
        return

    metrics = backtest_results["metrics"]
    bench_comp = backtest_results.get("bench_comp", {})
    portfolio_df = backtest_results.get("portfolio_df")
    warnings_list = backtest_results.get("warnings_list", [])
    ticker = backtest_results.get("ticker", "INFY")
    strategy_name = backtest_results.get("strategy_name", "SMA")
    config = backtest_results.get("config", {})

    # Generate Report Text
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    res_dir = os.path.join(BASE_DIR, "results")
    os.makedirs(res_dir, exist_ok=True)
    report_path = os.path.join(res_dir, "summary.txt")

    report_config = {
        "strategy_name": f"{strategy_name} Strategy",
        "stock_ticker": ticker,
        "start_date": portfolio_df.index.min().strftime("%Y-%m-%d") if portfolio_df is not None else "",
        "end_date": portfolio_df.index.max().strftime("%Y-%m-%d") if portfolio_df is not None else "",
        "initial_capital": config.get("initial_capital", 100000.0),
        "final_value": portfolio_df["Portfolio Value"].iloc[-1] if portfolio_df is not None else 100000.0,
        "position_size": config.get("position_size", 0.2),
        "max_positions": config.get("max_positions", 10),
        "rebalance_freq": config.get("rebalance_freq", "Daily"),
        "txn_cost_rate": config.get("commission_pct", 0.001),
        "slippage_rate": config.get("slippage_pct", 0.0005),
        "stop_loss": config.get("stop_loss"),
        "take_profit": config.get("take_profit")
    }

    generate_summary_report(metrics, report_config, report_path, benchmark_comp=bench_comp, warnings_list=warnings_list)

    report_text = ""
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            report_text = f.read()

    render_strategy_fact_sheet(report_text, report_config, metrics, warnings_list)
