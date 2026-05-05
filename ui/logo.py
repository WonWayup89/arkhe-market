import os
import streamlit as st

LOGO_PATH = "assets/arkhe_market_logo.png"

def render_logo(width=58):
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=width)
    else:
        st.markdown("### Arkhe Market")

def render_brand_header():
    c1, c2, c3 = st.columns([1, 8, 2])
    with c1:
        render_logo(64)
    with c2:
        st.markdown('<div class="arkhe_market-shell">', unsafe_allow_html=True)
        st.markdown('<div class="arkhe_market-topline">Value deepens with time</div>', unsafe_allow_html=True)
        st.markdown('<div class="arkhe_market-title">Arkhe Market</div>', unsafe_allow_html=True)
        st.markdown('<div class="arkhe_market-subtitle">Multi market trading workspace · Crypto · Stocks · Futures · Expert agents</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div style="text-align:right;padding-top:0.5rem;"><span class="arkhe_market-chip">Paper</span></div>', unsafe_allow_html=True)
