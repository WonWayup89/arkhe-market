import streamlit as st

def init_neural_stats():
    if "neural_blocks_entry" not in st.session_state:
        st.session_state.neural_blocks_entry = 0
    if "neural_blocks_exit" not in st.session_state:
        st.session_state.neural_blocks_exit = 0

def bump_entry_block():
    init_neural_stats()
    st.session_state.neural_blocks_entry += 1

def bump_exit_block():
    init_neural_stats()
    st.session_state.neural_blocks_exit += 1
