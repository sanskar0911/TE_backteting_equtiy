"""
experiment_table.py

Research Experiment Table Component.
Displays experiment sweep history using research-sound terminology
("Top Historical Result" rather than misleading "Best Strategy")
and includes validation status tags.
"""

import pandas as pd
import streamlit as st

def render_experiment_table(sweep_df: pd.DataFrame):
    """
    Render clean searchable experiment sweep results with research badges.
    """
    if sweep_df is None or sweep_df.empty:
        st.info("No experiment results generated yet.")
        return

    st.markdown("### 🔬 Parameter Grid Search & Experiment History")
    
    # Sort by Sharpe Ratio descending to identify top historical result
    display_df = sweep_df.copy()
    if "Sharpe Ratio" in display_df.columns:
        display_df = display_df.sort_values(by="Sharpe Ratio", ascending=False).reset_index(drop=True)

    # Format percentages and ratios
    for col in display_df.columns:
        if "CAGR" in col or "Return" in col or "Drawdown" in col or "Win Rate" in col:
            display_df[col] = display_df[col].apply(lambda x: f"{x*100:.2f}%" if isinstance(x, (int, float)) else x)
        elif "Sharpe" in col or "Sortino" in col or "Calmar" in col or "Factor" in col:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else x)

    # Add Research Label column
    labels = []
    for idx in range(len(display_df)):
        if idx == 0:
            labels.append("🏆 Top Historical Result (Pending Validation)")
        elif idx < 3:
            labels.append("🥈 High Performant Variant")
        else:
            labels.append(" Baseline Variant")
    
    display_df.insert(0, "Research Status", labels)

    st.dataframe(display_df, use_container_width=True)

    st.caption("ⓘ Note: The highest historical return parameter set is designated as 'Top Historical Result' and must undergo Out-of-Sample validation to rule out look-ahead bias and overfitting.")
