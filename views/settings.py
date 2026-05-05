"""
views/settings.py – System settings and diagnostics.
"""

import streamlit as st
from ui.cards import section_intro


def render_settings():
    section_intro("Settings", "System configuration and diagnostics")

    st.markdown("**Agent Configuration**")
    st.caption("All settings are controlled via the sidebar. Changes take effect immediately.")

    st.markdown("---")

    st.markdown("**Reset**")
    if st.button("Reset All Portfolio States", width="stretch", key="reset_all"):
        if "multi_agent" in st.session_state:
            st.session_state.multi_agent.reset_all_states()
        if "promo_supervisor" in st.session_state:
            st.session_state.promo_supervisor.reset_all()
        for k in ["last_outputs", "crypto_signals", "stock_signals", "futures_signals", "promo_results"]:
            st.session_state.pop(k, None)
        st.success("All states, logs, and promotion history cleared.")

    st.markdown("---")

    st.markdown("**Architecture**")
    st.code("""
app.py                       Main entry (single page)
├── views/                   Tab content (NOT auto-detected)
│   ├── command_center.py
│   ├── crypto.py
│   ├── stocks.py
│   ├── futures.py
│   ├── promotion_dashboard.py
│   └── settings.py
├── ui/                      Shared UI components
├── data/                    Live quote fetchers
├── brokers/                 Broker session management
├── multi_portfolio_agent.py Orchestrates all markets
│   └── supervisor_agent.py  Per-symbol expert panel
│       ├── technical_agent.py
│       ├── volatility_agent.py
│       ├── regime_agent.py
│       ├── sentiment_agent.py
│       └── risk_agent.py
├── strategy_scorer.py       Strategy scoring expert
├── shadow_validator.py      Sim vs live alignment
├── promotion_engine.py      Tier lifecycle manager
├── strategy_memory.py       Rolling analytics
└── promotion_supervisor.py  Promotion orchestrator
    """, language="text")
