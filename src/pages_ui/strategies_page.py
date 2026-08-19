"""
strategies_page.py

Page 4 — Strategy Library Page Renderer.
Displays available quant strategy architectures, parameters, signal logic formulas,
and 1-click strategy activation & backtest execution buttons.
"""

import streamlit as st
from components.strategy_card import render_strategy_card

def render_strategies_page(execute_backtest_fn: callable = None):
    """
    Render Strategy Library Page with inter-page strategy activation.
    """
    st.markdown("## 📚 Quantitative Strategy Library")
    subhead_html = "<div style='color: #94a3b8; font-size: 1.05rem; margin-bottom: 20px;'>Institutional strategy catalog. Click <b>🚀 Test Strategy</b> on any architecture to simulate performance and view results.</div>"
    st.markdown(subhead_html, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        render_strategy_card(
            name="SMA Crossover",
            description="Classic trend-following strategy using simple moving average crossovers to identify trend direction.",
            parameters={"Short Window": "20 Days", "Long Window": "50 Days"},
            signal_logic="BUY when Fast SMA > Slow SMA; SELL when Fast SMA < Slow SMA.",
            best_use_case="Trending markets with sustained momentum (e.g. Bluechip stocks in bull markets).",
            status="Active"
        )
        if st.button("🚀 Test SMA Strategy", key="btn_run_sma", use_container_width=True):
            st.session_state["override_strategy"] = "SMA"
            st.session_state["override_strategy_kwargs"] = {"short_window": 20, "long_window": 50}
            st.session_state["current_page"] = "Results"
            st.rerun()

    with col2:
        render_strategy_card(
            name="EMA Crossover",
            description="Exponential moving average strategy giving higher weighting to recent prices for faster trend entry.",
            parameters={"Short Window": "12 Days", "Long Window": "26 Days"},
            signal_logic="BUY when Fast EMA > Slow EMA; SELL when Fast EMA < Slow EMA.",
            best_use_case="Volatile markets requiring swift signal reaction time.",
            status="Active"
        )
        if st.button("🚀 Test EMA Strategy", key="btn_run_ema", use_container_width=True):
            st.session_state["override_strategy"] = "EMA"
            st.session_state["override_strategy_kwargs"] = {"short_window": 12, "long_window": 26}
            st.session_state["current_page"] = "Results"
            st.rerun()

    with col3:
        render_strategy_card(
            name="RSI Mean Reversion",
            description="Oscillator strategy capturing overbought and oversold price extremes for tactical mean-reversion trades.",
            parameters={"Period": "14 Days", "Oversold": 30.0, "Overbought": 70.0},
            signal_logic="BUY when RSI < Oversold (30); SELL when RSI > Overbought (70).",
            best_use_case="Range-bound or sideways consolidating equity markets.",
            status="Active"
        )
        if st.button("🚀 Test RSI Strategy", key="btn_run_rsi", use_container_width=True):
            st.session_state["override_strategy"] = "RSI"
            st.session_state["override_strategy_kwargs"] = {"period": 14, "oversold": 30.0, "overbought": 70.0}
            st.session_state["current_page"] = "Results"
            st.rerun()

    st.markdown("---")
    st.markdown("### 🧮 Custom Strategy Architecture Extension")
    st.info("💡 To implement additional quantitative strategy algorithms (e.g., MACD, Bollinger Bands, Multi-factor Ranking), extend `src/strategies/base.py` and register the strategy in `src/strategies/factory.py`.")
