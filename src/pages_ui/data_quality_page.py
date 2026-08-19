"""
data_quality_page.py

Page 13 — Data Quality Audit Page Renderer.
Audits historical stock dataset integrity, checking missing values, price anomalies,
duplicate dates, and volume coverage.
"""

import os
import textwrap
import pandas as pd
import streamlit as st

def render_data_quality_page(selected_ticker: str = "INFY"):
    """
    Render Data Quality Audit Dashboard.
    """
    st.markdown("## 🧹 Data Quality & Integrity Audit")
    st.markdown("<div style='color: #94a3b8; font-size: 1.05rem; margin-bottom: 20px;'>Audit data completeness, missing value counts, price zero/negative anomalies, and volume availability.</div>", unsafe_allow_html=True)

    ticker = st.selectbox("Select Dataset to Audit", ["INFY", "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "NIFTY50"], index=0, key="dq_ticker")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_path = os.path.join(BASE_DIR, "data", "processed", f"{ticker}.csv")

    if not os.path.exists(data_path):
        st.error(f"Dataset file not found at {data_path}")
        return

    df = pd.read_csv(data_path)

    n_rows = len(df)
    has_date = "Date" in df.columns
    if has_date:
        df["Date"] = pd.to_datetime(df["Date"])
        start_date = df["Date"].min().strftime("%Y-%m-%d")
        end_date = df["Date"].max().strftime("%Y-%m-%d")
        n_dup_dates = df["Date"].duplicated().sum()
    else:
        start_date = "N/A"
        end_date = "N/A"
        n_dup_dates = 0

    n_missing = df.isnull().sum().sum()
    
    price_col = "Adj Close" if "Adj Close" in df.columns else ("Close" if "Close" in df.columns else None)
    n_anomalies = 0
    if price_col:
        n_anomalies = (df[price_col] <= 0).sum()

    has_volume = "Volume" in df.columns
    vol_status = "Available" if has_volume else "Missing"

    is_valid = (n_missing == 0) and (n_dup_dates == 0) and (n_anomalies == 0)

    if is_valid:
        valid_html = textwrap.dedent("""
            <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); padding: 1rem 1.5rem; border-radius: 0.75rem; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
                <div style="font-size: 1.2rem; font-weight: 700; color: #10b981;">
                    ✓ DATASET VALIDATED — HIGH INTEGRITY
                </div>
                <div style="background: #10b981; color: #000; padding: 4px 12px; border-radius: 12px; font-weight: 700; font-size: 0.8rem;">
                    PASSED
                </div>
            </div>
        """)
        st.markdown(valid_html, unsafe_allow_html=True)
    else:
        invalid_html = textwrap.dedent("""
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); padding: 1rem 1.5rem; border-radius: 0.75rem; margin-bottom: 20px;">
                <div style="font-size: 1.2rem; font-weight: 700; color: #ef4444;">
                    ⚠️ DATA QUALITY ISSUES DETECTED
                </div>
            </div>
        """)
        st.markdown(invalid_html, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Rows", f"{n_rows:,}")
    col2.metric("Date Range", f"{start_date} to {end_date}")
    col3.metric("Missing Values", n_missing, delta_color="positive" if n_missing == 0 else "negative")
    col4.metric("Duplicate Dates", n_dup_dates, delta_color="positive" if n_dup_dates == 0 else "negative")

    st.markdown("---")

    col5, col6, col7 = st.columns(3)
    col5.metric("Price Anomalies (≤0)", n_anomalies, delta_color="positive" if n_anomalies == 0 else "negative")
    col6.metric("Volume Coverage", vol_status)
    col7.metric("Adjusted Price Status", "Adj Close Active" if "Adj Close" in df.columns else "Close Price Only")

    st.markdown("### 📋 Preview Dataset (First 10 Rows)")
    st.dataframe(df.head(10), use_container_width=True)
