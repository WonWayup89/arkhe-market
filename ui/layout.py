"""ui/layout.py — App shell: theme + hero + 6-tab navigation."""

import streamlit as st

from ui.theme import inject_theme, arkhe_hero


def render_shell():
    """Apply theme, draw the Arkeh Holdings hero, and return the 6 tabs."""
    inject_theme()
    arkhe_hero(
        title="Arkhe Market",
        kicker="ARKHE HOLDINGS",
        subtitle=(
            "Multi-agent market intelligence built around structure, "
            "risk control, strategy validation, and first-principles execution."
        ),
        motto="Shield. Structure. Launch.",
    )
    return st.tabs(
        ["Command Center", "Crypto", "Stocks", "Futures", "Promotion", "Settings"]
    )
