"""
presentation_mode.py

Presentation Mode Executive View Renderer.
Provides a clean, uncluttered high-level presentation view suitable for live demonstrations.
"""

import textwrap
import streamlit as st
from components.kpi_card import render_kpi_card
from components.chart_container import render_equity_curve_plotly, render_drawdown_plotly

def render_presentation_mode(backtest_results: dict):
    """
    Render executive presentation layout.
    """
    banner_html = textwrap.dedent("""
        <div style="
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(16, 185, 129, 0.2));
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1rem;
            padding: 1.5rem 2rem;
            margin-bottom: 24px;
            text-align: center;
        ">
            <div style="font-size: 2.2rem; font-weight: 800; color: #ffffff; letter-spacing: -0.02em;">
                QUANTUM LABS &bull; QUANTITATIVE STRATEGY DEMO
            </div>
            <div style="font-size: 1.1rem; color: #94a3b8; margin-top: 6px;">
                AI-Driven Equity Backtesting & Risk Engine &bull; Internship Presentation View
            </div>
        </div>
    """)
    st.markdown(banner_html, unsafe_allow_html=True)

    if not backtest_results or "metrics" not in backtest_results:
        st.info("💡 Please run a backtest from the sidebar to populate presentation metrics.")
        return

    metrics = backtest_results["metrics"]
    bench_comp = backtest_results.get("bench_comp", {})
    portfolio_df = backtest_results.get("portfolio_df")
    benchmark_df = backtest_results.get("benchmark_df")
    ticker = backtest_results.get("ticker", "INFY")
    strategy_name = backtest_results.get("strategy_name", "SMA")
    benchmark_symbol = backtest_results.get("benchmark", "NIFTY50")

    col1, col2, col3, col4, col5 = st.columns(5)

    tot_ret = metrics.get("Total Return", 0.0) * 100.0
    cagr = metrics.get("CAGR", 0.0) * 100.0
    sharpe = metrics.get("Sharpe Ratio", 0.0)
    max_dd = metrics.get("Maximum Drawdown", 0.0) * 100.0
    excess = bench_comp.get("excess_return", 0.0) * 100.0

    with col1:
        render_kpi_card("Strategy Target", f"{ticker} ({strategy_name})", icon="⚡")
    with col2:
        render_kpi_card("Total Return", f"{tot_ret:+.2f}%", delta_color="positive" if tot_ret >= 0 else "negative", icon="💰")
    with col3:
        render_kpi_card("CAGR", f"{cagr:.2f}%", delta=f"{excess:+.2f}% vs Bench", delta_color="positive" if cagr >= 0 else "negative", icon="📈")
    with col4:
        render_kpi_card("Sharpe Ratio", f"{sharpe:.2f}", delta_color="positive" if sharpe >= 1.0 else "warning", icon="秤")
    with col5:
        render_kpi_card("Max Drawdown", f"{max_dd:.2f}%", delta_color="negative", icon="📉")

    st.markdown("---")

    if portfolio_df is not None:
        render_equity_curve_plotly(portfolio_df, benchmark_df, ticker, benchmark_symbol)

    st.markdown("---")

    col_dd, col_conclusion = st.columns([3, 2])

    with col_dd:
        if portfolio_df is not None:
            render_drawdown_plotly(portfolio_df)

    with col_conclusion:
        st.markdown("### 🎓 Research Conclusion & Takeaways")
        outperformed = excess > 0.0

        conclusion_html = textwrap.dedent(f"""
            <div style="
                background: rgba(22, 28, 45, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 0.75rem;
                padding: 1.5rem;
                line-height: 1.7;
                font-size: 0.95rem;
            ">
                <div>📌 <b>Benchmark Comparison:</b> {benchmark_symbol}</div>
                <div>⚡ <b>Alpha Generation:</b> <b style="color: {'#10b981' if outperformed else '#ef4444'};">{excess:+.2f}% CAGR Excess Return</b></div>
                <div>🛡️ <b>Risk Profile:</b> Beta = <b>{bench_comp.get('beta', 1.0):.2f}</b> | Volatility = <b>{bench_comp.get('strategy_volatility', 0.15)*100:.1f}%</b></div>
                <hr style="border-top: 1px solid rgba(255,255,255,0.08); margin: 12px 0;">
                <div>💡 <b>Final Key Takeaway:</b></div>
                <div style="color: #cbd5e1; font-size: 0.9rem; margin-top: 4px;">
                    {'The strategy successfully captures directional momentum while outperforming the benchmark on a risk-adjusted basis.' if outperformed else 'Strategy performance was limited by trend whipsaws during consolidation phases. Further parameter optimization recommended.'}
                </div>
            </div>
        """)
        st.markdown(conclusion_html, unsafe_allow_html=True)
