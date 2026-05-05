import streamlit as st


def render_workspace(left_renderer, right_renderer, left_ratio=1, right_ratio=3):
    left, right = st.columns([left_ratio, right_ratio], gap="large")
    with left:
        left_renderer()
    with right:
        right_renderer()
