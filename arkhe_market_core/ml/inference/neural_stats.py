"""
arkhe_market_core/ml/inference/neural_stats.py

Plain-Python counters for neural-gate block events. Used by the supervisor
to record how often the gate fired without depending on Streamlit at all.

The Streamlit UI (app.py / sidebar) reads these counters via
`get_neural_stats()` and displays them in the sidebar. Mutations happen
exclusively through the bump functions below.

Audit reference: previously this module did `import streamlit as st` at
the top, which was pulled into supervisor_agent.py and broke headless /
CI use of the engine.
"""

from __future__ import annotations

from typing import Dict


_NEURAL_STATS: Dict[str, int] = {
    "neural_blocks_entry": 0,
    "neural_blocks_exit":  0,
}


def init_neural_stats() -> None:
    # Idempotent. Kept for API compatibility — the dict is already
    # initialized at import time, so this is a no-op in practice.
    _NEURAL_STATS.setdefault("neural_blocks_entry", 0)
    _NEURAL_STATS.setdefault("neural_blocks_exit", 0)


def bump_entry_block() -> None:
    _NEURAL_STATS["neural_blocks_entry"] = int(_NEURAL_STATS.get("neural_blocks_entry", 0)) + 1


def bump_exit_block() -> None:
    _NEURAL_STATS["neural_blocks_exit"] = int(_NEURAL_STATS.get("neural_blocks_exit", 0)) + 1


def get_neural_stats() -> Dict[str, int]:
    """Return a snapshot the UI can read into st.session_state for display."""
    return {k: int(v) for k, v in _NEURAL_STATS.items()}


def reset_neural_stats() -> None:
    """Test-only helper."""
    _NEURAL_STATS["neural_blocks_entry"] = 0
    _NEURAL_STATS["neural_blocks_exit"] = 0
