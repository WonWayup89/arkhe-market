import streamlit as st

def render_status_chip(label: str, tone: str = "neutral"):
    color_map = {
        "neutral": "#FFC83D",
        "success": "#10B981",
        "danger": "#EF4444",
        "info": "#94A3B8",
    }
    color = color_map.get(tone, "#FFC83D")
    st.markdown(
        f'''
        <span style="
            display:inline-block;
            padding:4px 10px;
            border-radius:999px;
            background:rgba(255,255,255,0.04);
            border:1px solid {color};
            color:{color};
            font-size:0.82rem;
            font-weight:700;
        ">{label}</span>
        ''',
        unsafe_allow_html=True,
    )
