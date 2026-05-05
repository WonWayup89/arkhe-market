import streamlit as st

def neural_gate(score, mode="entry"):
    if score is None:
        return "unknown"

    score = float(score)

    entry_threshold = float(st.session_state.get("entry_gate_threshold", 0.75))
    exit_threshold = float(st.session_state.get("exit_gate_threshold", 0.25))

    threshold = entry_threshold if mode == "entry" else exit_threshold
    return "allow" if score >= threshold else "block"
