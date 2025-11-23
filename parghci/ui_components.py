# ui_components.py
import streamlit as st
import pandas as pd
from datetime import datetime

def page_header(title, subtitle=None):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)

def info_card(title, body):
    with st.container():
        st.markdown(f"**{title}**")
        st.write(body)

def display_loans_table(loans):
    # loans: list of LoanApplication
    rows = []
    for l in loans:
        rows.append({
            "ID": l.id,
            "Submitted": l.created_at,
            "Status": l.status.value if l.status else str(l.status),
            "Decision": l.decision or "",
            "Explanation": l.explanation or ""
        })
    if rows:
        st.dataframe(pd.DataFrame(rows))
    else:
        st.info("No records to display.")
