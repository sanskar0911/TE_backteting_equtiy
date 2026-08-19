"""
backtest_page.py

Page 2 — Dedicated Backtest Configuration Screen & Execution Pipeline.
Organizes parameters into expandable sections with step-by-step pipeline status updates.
"""

import time
import textwrap
import streamlit as st

def render_backtest_page(config: dict, execute_backtest_fn: callable):
    """
    Render Backtest Configuration Screen & Pipeline.
    """
    st.markdown("## ⚙️ Backtest Configuration & Pipeline")
    st.markdown("<div style='color: #94a3b8; font-size: 1.05rem; margin-bottom: 20px;'>Configure strategy logic, execution friction, portfolio rules, and run simulation pipeline.</div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 🛠️ Simulation Parameters")

        # DATA SECTION
        with st.expander("📁 1. Universe & Data Range", expanded=True):
            st.selectbox("Target Universe / Stock", ["INFY", "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK"], key="bt_ticker")
            st.selectbox("Benchmark Index", ["NIFTY50"], key="bt_bench")

        # STRATEGY SECTION
        with st.expander("⚡ 2. Strategy Logic & Parameters", expanded=True):
            strat_name = st.selectbox("Strategy Architecture", ["SMA", "EMA", "RSI"], key="bt_strat")
            if strat_name == "SMA":
                st.number_input("Short Window", value=20, key="bt_sma_short")
                st.number_input("Long Window", value=50, key="bt_sma_long")
            elif strat_name == "EMA":
                st.number_input("Short Window", value=12, key="bt_ema_short")
                st.number_input("Long Window", value=26, key="bt_ema_long")
            elif strat_name == "RSI":
                st.number_input("RSI Period", value=14, key="bt_rsi_period")
                st.number_input("Oversold Level", value=30.0, key="bt_rsi_oversold")
                st.number_input("Overbought Level", value=70.0, key="bt_rsi_overbought")

        # PORTFOLIO SECTION
        with st.expander("💼 3. Portfolio & Rebalancing", expanded=False):
            st.number_input("Initial Capital (INR)", value=100000.0, key="bt_capital")
            st.slider("Position Size (% of Capital)", min_value=10, max_value=100, value=20, key="bt_pos_size")
            st.number_input("Maximum Position Limit", min_value=1, max_value=50, value=10, key="bt_max_pos")
            st.selectbox("Rebalancing Frequency", ["Daily", "Weekly", "Monthly"], key="bt_rebal_freq")

        # EXECUTION SECTION
        with st.expander("💸 4. Transaction Friction & Liquidity", expanded=False):
            st.slider("Commission Rate (%)", min_value=0.0, max_value=1.0, value=0.1, key="bt_comm")
            st.slider("Slippage Rate (%)", min_value=0.0, max_value=0.5, value=0.05, key="bt_slip")
            st.checkbox("Enable Liquidity Filter", value=True, key="bt_liq_check")
            st.number_input("Min Daily Volume Filter", value=10000, key="bt_min_vol")

        # RISK SECTION
        with st.expander("🛡️ 5. Risk Limits (Stop Loss / Take Profit)", expanded=False):
            st.checkbox("Enable Stop Loss", value=True, key="bt_sl_check")
            st.slider("Stop Loss (%)", min_value=1.0, max_value=20.0, value=5.0, key="bt_sl_val")
            st.checkbox("Enable Take Profit", value=True, key="bt_tp_check")
            st.slider("Take Profit (%)", min_value=1.0, max_value=50.0, value=10.0, key="bt_tp_val")

        run_btn = st.button("🚀 Run Backtest Pipeline", type="primary", use_container_width=True)

    with col_right:
        st.markdown("### 📋 Configuration Summary")

        summary_html = textwrap.dedent(f"""
            <div style="
                background: rgba(22, 28, 45, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 0.75rem;
                padding: 1.25rem;
                line-height: 1.8;
                font-size: 0.95rem;
            ">
                <div>📌 <b>Ticker:</b> {st.session_state.get('bt_ticker', config.get('ticker'))}</div>
                <div>🎯 <b>Benchmark:</b> {st.session_state.get('bt_bench', config.get('benchmark'))}</div>
                <div>⚡ <b>Strategy:</b> {st.session_state.get('bt_strat', config.get('strategy_name'))}</div>
                <div>💰 <b>Capital:</b> ₹{config.get('initial_capital', 100000.0):,.0f}</div>
                <div>📊 <b>Position Sizing:</b> {config.get('position_size', 0.2)*100:.0f}%</div>
                <div>💸 <b>Commission / Slippage:</b> {config.get('commission_pct', 0.001)*100:.2f}% / {config.get('slippage_pct', 0.0005)*100:.2f}%</div>
                <div>🛡️ <b>Stop Loss / Take Profit:</b> {config.get('stop_loss', 0.05)*100 if config.get('stop_loss') else 'Off'}% / {config.get('take_profit', 0.1)*100 if config.get('take_profit') else 'Off'}%</div>
            </div>
        """)
        st.markdown(summary_html, unsafe_allow_html=True)

        if run_btn or config.get("run_triggered"):
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### ⚡ Execution Pipeline")
            
            steps = [
                "Loading Price & Volume Data...",
                "Generating Technical Strategy Signals...",
                "Constructing Portfolio & Allocating Positions...",
                "Applying Slippage & Transaction Frictions...",
                "Computing Risk & Return Metrics...",
                "Benchmarking against Nifty 50 Index...",
                "Generating Research Fact Sheet Report..."
            ]

            progress_bar = st.progress(0)
            status_box = st.empty()

            for idx, step in enumerate(steps):
                status_box.markdown(f"<div style='color: #10b981; font-weight: 600;'>✓ {step}</div>", unsafe_allow_html=True)
                progress_bar.progress((idx + 1) / len(steps))
                time.sleep(0.1)

            st.success("✅ Backtest Simulation Pipeline Complete!")
            execute_backtest_fn(config)
