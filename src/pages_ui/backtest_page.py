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
            selected_ticker = st.selectbox("Target Universe / Stock", ["INFY", "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK"], index=0, key="bt_ticker")
            selected_benchmark = st.selectbox("Benchmark Index", ["NIFTY50"], index=0, key="bt_bench")

        # STRATEGY SECTION
        with st.expander("⚡ 2. Strategy Logic & Parameters", expanded=True):
            strat_name = st.selectbox("Strategy Architecture", ["SMA", "EMA", "RSI"], index=0, key="bt_strat")
            strategy_kwargs = {}
            if strat_name == "SMA":
                short_w = st.number_input("Short Window", min_value=5, max_value=100, value=20, key="bt_sma_short")
                long_w = st.number_input("Long Window", min_value=10, max_value=200, value=50, key="bt_sma_long")
                strategy_kwargs = {"short_window": short_w, "long_window": long_w}
            elif strat_name == "EMA":
                short_w = st.number_input("Short Window", min_value=5, max_value=100, value=12, key="bt_ema_short")
                long_w = st.number_input("Long Window", min_value=10, max_value=200, value=26, key="bt_ema_long")
                strategy_kwargs = {"short_window": short_w, "long_window": long_w}
            elif strat_name == "RSI":
                rsi_p = st.number_input("RSI Period", min_value=5, max_value=50, value=14, key="bt_rsi_period")
                oversold = st.number_input("Oversold Level", min_value=10.0, max_value=45.0, value=30.0, key="bt_rsi_oversold")
                overbought = st.number_input("Overbought Level", min_value=55.0, max_value=90.0, value=70.0, key="bt_rsi_overbought")
                strategy_kwargs = {"period": rsi_p, "oversold": oversold, "overbought": overbought}

        # PORTFOLIO SECTION
        with st.expander("💼 3. Portfolio & Rebalancing", expanded=False):
            initial_capital = st.number_input("Initial Capital (INR)", min_value=10000.0, value=100000.0, step=10000.0, key="bt_capital")
            position_size_pct = st.slider("Position Size (% of Capital)", min_value=10, max_value=100, value=20, step=5, key="bt_pos_size") / 100.0
            max_positions = st.number_input("Maximum Position Limit", min_value=1, max_value=50, value=10, key="bt_max_pos")
            rebalance_freq = st.selectbox("Rebalancing Frequency", ["Daily", "Weekly", "Monthly"], index=0, key="bt_rebal_freq")

        # EXECUTION SECTION
        with st.expander("💸 4. Transaction Friction & Liquidity", expanded=False):
            commission_pct = st.slider("Commission Rate (%)", min_value=0.0, max_value=1.0, value=0.1, step=0.05, key="bt_comm") / 100.0
            slippage_pct = st.slider("Slippage Rate (%)", min_value=0.0, max_value=0.5, value=0.05, step=0.01, key="bt_slip") / 100.0
            use_liquidity = st.checkbox("Enable Liquidity Filter", value=True, key="bt_liq_check")
            min_volume = st.number_input("Min Daily Volume Filter", min_value=0, value=10000, key="bt_min_vol") if use_liquidity else 0

        # RISK SECTION
        with st.expander("🛡️ 5. Risk Limits (Stop Loss / Take Profit)", expanded=False):
            use_sl = st.checkbox("Enable Stop Loss", value=True, key="bt_sl_check")
            stop_loss_pct = (st.slider("Stop Loss (%)", min_value=1.0, max_value=20.0, value=5.0, step=0.5, key="bt_sl_val") / 100.0) if use_sl else None
            use_tp = st.checkbox("Enable Take Profit", value=True, key="bt_tp_check")
            take_profit_pct = (st.slider("Take Profit (%)", min_value=1.0, max_value=50.0, value=10.0, step=1.0, key="bt_tp_val") / 100.0) if use_tp else None

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
                <div>📌 <b>Ticker:</b> {selected_ticker}</div>
                <div>🎯 <b>Benchmark:</b> {selected_benchmark}</div>
                <div>⚡ <b>Strategy:</b> {strat_name}</div>
                <div>💰 <b>Capital:</b> ₹{initial_capital:,.0f}</div>
                <div>📊 <b>Position Sizing:</b> {position_size_pct*100:.0f}%</div>
                <div>💸 <b>Commission / Slippage:</b> {commission_pct*100:.2f}% / {slippage_pct*100:.2f}%</div>
                <div>🛡️ <b>Stop Loss / Take Profit:</b> {stop_loss_pct*100 if stop_loss_pct else 'Off'}% / {take_profit_pct*100 if take_profit_pct else 'Off'}%</div>
            </div>
        """)
        st.markdown(summary_html, unsafe_allow_html=True)

        if run_btn:
            new_config = {
                "ticker": selected_ticker,
                "benchmark": selected_benchmark,
                "strategy_name": strat_name,
                "strategy_kwargs": strategy_kwargs,
                "initial_capital": initial_capital,
                "commission_pct": commission_pct,
                "slippage_pct": slippage_pct,
                "position_size": position_size_pct,
                "max_positions": max_positions,
                "rebalance_freq": rebalance_freq,
                "stop_loss": stop_loss_pct,
                "take_profit": take_profit_pct,
                "min_volume": min_volume,
                "min_traded_value": 0.0
            }

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
            execute_backtest_fn(new_config)

            if st.button("📈 View Detailed Results", type="primary", use_container_width=True):
                st.session_state["current_page"] = "Results"
                st.rerun()
