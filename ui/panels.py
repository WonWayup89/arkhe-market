import streamlit as st
from ui.status import render_status_chip

def account_status_cards(session_snapshot: dict):
    cols = st.columns(4)
    with cols[0]:
        st.metric("Broker", session_snapshot.get("broker", "Unknown"))
    with cols[1]:
        tone = "success" if session_snapshot.get("connected") else "info"
        render_status_chip("CONNECTED" if session_snapshot.get("connected") else "PAPER", tone=tone)
    with cols[2]:
        st.metric("Source", session_snapshot.get("source", "paper"))
    with cols[3]:
        st.metric("Last Sync", session_snapshot.get("last_sync") or "Not synced")
