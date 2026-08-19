"""
warning_card.py

Institutional Warning & Research Risk Alert Banner Component.
Displays color-coded alerts for overfitting risk, excessive drawdown, high turnover,
concentration limits, and data quality flags.
"""

import textwrap
import streamlit as st

def render_warning_card(title: str, text: str, warning_type: str = "warning"):
    """
    Render styled research alert card.
    warning_type: "warning" (amber), "danger" (red), "info" (blue)
    """
    styles = {
        "warning": {
            "border": "rgba(245, 158, 11, 0.4)",
            "bg": "rgba(245, 158, 11, 0.1)",
            "icon": "⚠️",
            "title_color": "#f59e0b"
        },
        "danger": {
            "border": "rgba(239, 68, 68, 0.4)",
            "bg": "rgba(239, 68, 68, 0.1)",
            "icon": "🚨",
            "title_color": "#ef4444"
        },
        "info": {
            "border": "rgba(59, 130, 246, 0.4)",
            "bg": "rgba(59, 130, 246, 0.1)",
            "icon": "ℹ️",
            "title_color": "#3b82f6"
        }
    }
    
    cfg = styles.get(warning_type, styles["warning"])

    card_html = textwrap.dedent(f"""
        <div style="
            background: {cfg['bg']};
            border: 1px solid {cfg['border']};
            border-radius: 0.5rem;
            padding: 0.9rem 1.2rem;
            margin-bottom: 12px;
            backdrop-filter: blur(8px);
        ">
            <div style="font-weight: 700; font-size: 0.95rem; color: {cfg['title_color']}; margin-bottom: 4px; display: flex; align-items: center; gap: 8px;">
                <span>{cfg['icon']}</span> {title}
            </div>
            <div style="color: #cbd5e1; font-size: 0.88rem; line-height: 1.4;">
                {text}
            </div>
        </div>
    """)
    st.markdown(card_html, unsafe_allow_html=True)


def render_warning_list(warnings_list: list):
    """
    Render a list of research warnings with structured formatting.
    """
    if not warnings_list:
        return

    st.markdown("### ⚠️ Quantitative Risk & Overfitting Warnings")
    for w in warnings_list:
        w_lower = w.lower()
        w_type = "danger" if "overfit" in w_lower or "drawdown" in w_lower or "loss" in w_lower else "warning"
        render_warning_card("Research Alert", w, warning_type=w_type)
