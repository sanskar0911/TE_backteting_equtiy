"""
report_card.py

Strategy Fact Sheet & Export Center Component.
Renders formatted institutional strategy fact sheets and download controls.
"""

import os
import json
import textwrap
import streamlit as st

def render_strategy_fact_sheet(report_text: str, report_config: dict, metrics: dict, warnings_list: list):
    """
    Render institutional strategy fact sheet container.
    """
    st.markdown("### 📄 Institutional Strategy Fact Sheet")

    header_html = textwrap.dedent(f"""
        <div style="
            background: rgba(22, 28, 45, 0.9);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 0.75rem;
            padding: 1.25rem 1.5rem;
            margin-bottom: 16px;
        ">
            <div style="font-size: 1.4rem; font-weight: 800; color: #f8fafc; margin-bottom: 4px;">
                {report_config.get('strategy_name', 'Quant Strategy')} Fact Sheet
            </div>
            <div style="color: #94a3b8; font-size: 0.9rem;">
                <b>Universe:</b> {report_config.get('stock_ticker', 'NSE')} | 
                <b>Testing Period:</b> {report_config.get('start_date', '')} to {report_config.get('end_date', '')}
            </div>
        </div>
    """)
    st.markdown(header_html, unsafe_allow_html=True)

    # Fact Sheet Code block
    st.code(report_text, language="text")

    # Download Actions
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            label="📥 Download Fact Sheet (.txt)",
            data=report_text,
            file_name=f"{report_config.get('stock_ticker', 'strategy')}_fact_sheet.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col2:
        metrics_json = json.dumps(metrics, indent=2)
        st.download_button(
            label="📥 Download Metrics (.json)",
            data=metrics_json,
            file_name=f"{report_config.get('stock_ticker', 'strategy')}_metrics.json",
            mime="application/json",
            use_container_width=True
        )
