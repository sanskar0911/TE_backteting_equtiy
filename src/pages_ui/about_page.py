"""
about_page.py

Page 14 — About Platform Page Renderer.
Provides platform architecture documentation, technologies used, validation methodology,
and disclaimer notice.
"""

import textwrap
import streamlit as st

def render_about_page():
    """
    Render About Platform Page.
    """
    st.markdown("## ℹ️ About AI Quant Research Platform")
    st.markdown("<div style='color: #94a3b8; font-size: 1.05rem; margin-bottom: 20px;'>Institutional Quantitative Backtesting & Autonomous Agent Research System.</div>", unsafe_allow_html=True)

    about_html = textwrap.dedent("""
        <h3>🎯 Project Objective</h3>
        <p>The <b>AI Quantitative Research & Equity Backtesting Platform</b> is engineered for quantitative research, strategy backtesting, out-of-sample validation, and automated LLM-driven strategy analysis on Indian equities (NSE).</p>
        
        <hr style="border-top: 1px solid rgba(255,255,255,0.08); margin: 20px 0;">

        <h3>🏗️ Platform Architecture & Tech Stack</h3>
        <ul>
            <li><b>UI / UX Layer:</b> Streamlit with custom dark financial terminal CSS system and Plotly interactive chart engines.</li>
            <li><b>Quantitative Core:</b> Python Pandas & NumPy vectorization engine for indicators, transaction costs, slippage, and stop-loss execution.</li>
            <li><b>Agent Engine:</b> LangGraph state machine (<code>StateGraph</code>) with research evaluator loop engineering.</li>
            <li><b>LLM Insights:</b> OpenAI Structured JSON Outputs & qualitative strategy analysis prompts.</li>
            <li><b>Data Pipeline:</b> Preprocessed OHLCV CSV data with data quality verification.</li>
        </ul>

        <hr style="border-top: 1px solid rgba(255,255,255,0.08); margin: 20px 0;">

        <h3>🔬 Research & Validation Methodology</h3>
        <ol>
            <li><b>Friction Accounting:</b> Real-world transaction costs (brokerage, STT, turnover charges) and market slippage modeling.</li>
            <li><b>Look-Ahead Protection:</b> Strictly split 70:30 In-Sample vs Out-of-Sample backtesting to eliminate curve-fitting.</li>
            <li><b>Walk-Forward Analysis:</b> Rolling walk-forward windows testing parameter stability across market regimes.</li>
            <li><b>Robustness Perturbations:</b> ±10% parameter sensitivity tests checking strategy robustness against parameter overfitting.</li>
        </ol>

        <hr style="border-top: 1px solid rgba(255,255,255,0.08); margin: 20px 0;">

        <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); padding: 1rem; border-radius: 0.5rem; color: #f8fafc; font-size: 0.95rem;">
            <b>IMPORTANT DISCLAIMER:</b><br>
            This platform is strictly for research, backtesting, and academic demonstration purposes.<br>
            <b>No real-money trading is performed by this project.</b> Past performance is not indicative of future returns.
        </div>
    """)
    st.markdown(about_html, unsafe_allow_html=True)
