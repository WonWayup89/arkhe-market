import streamlit as st

def metric_card(title, value, delta=None):
    st.metric(title, value, delta=delta)

def market_summary_row(items):
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            st.metric(item["label"], item["value"], delta=item.get("delta"))

def section_intro(title: str, note: str = ""):
    st.markdown(f'<div class="arkhe_market-section">{title}</div>', unsafe_allow_html=True)
    if note:
        st.markdown(f'<div class="arkhe_market-note">{note}</div>', unsafe_allow_html=True)
    st.markdown('<div class="arkhe_market-divider"></div>', unsafe_allow_html=True)
