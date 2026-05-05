import streamlit as st
from ui.logo import render_brand_header

def render_shell():
    render_brand_header()
    return st.tabs(["Command Center", "Crypto", "Stocks", "Futures", "Promotion", "Settings"])
