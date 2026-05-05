"""
ui/theme.py — Arkeh Holdings dark/neon-teal visual system.

Provides:
    inject_theme()       — global CSS (page bg, sidebar, cards, metrics, buttons,
                           tabs, dataframe, plus the legacy `arkhe_market-*`
                           classes the views call into).
    arkhe_hero(...)      — full-bleed hero panel with shield, kicker, title,
                           subtitle and pill — used at the top of the app.
    inject_constellation_css()
                          — extra constellation card styling (kept for legacy
                           pages that still reference it).
"""

import streamlit as st

COLORS = {
    "bg_main":          "#05090D",
    "bg_panel":         "rgba(11, 17, 24, 0.92)",
    "bg_panel_soft":    "rgba(17, 25, 35, 0.86)",
    "border":           "rgba(91, 255, 232, 0.28)",
    "cyan":             "#5BFFE8",
    "cyan_soft":        "#19C7B8",
    "gold":             "#C9A24A",
    "text":             "#F7F7F2",
    "muted":            "#9CA7AE",
    "danger":           "#FF4D6D",
    "green":            "#10B981",
}


ARKHE_CSS = """
<style>
:root {
    --arkhe-bg: #05090D;
    --arkhe-panel: rgba(11, 17, 24, 0.92);
    --arkhe-panel-soft: rgba(17, 25, 35, 0.86);
    --arkhe-border: rgba(91, 255, 232, 0.28);
    --arkhe-cyan: #5BFFE8;
    --arkhe-cyan-soft: #19C7B8;
    --arkhe-gold: #C9A24A;
    --arkhe-text: #F7F7F2;
    --arkhe-muted: #9CA7AE;
    --arkhe-danger: #FF4D6D;
    --arkhe-green: #10B981;
}

/* ── App background ───────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 50% 0%, rgba(91,255,232,0.22), transparent 28%),
        radial-gradient(circle at 90% 20%, rgba(25,199,184,0.12), transparent 28%),
        linear-gradient(180deg, #071018 0%, #05090D 50%, #030506 100%) !important;
    color: var(--arkhe-text) !important;
}

[data-testid="stHeader"] { background: transparent !important; }

[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(12,18,26,0.96), rgba(8,10,14,0.98)) !important;
    border-right: 1px solid var(--arkhe-border);
}

[data-testid="stSidebar"] * { color: var(--arkhe-text) !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 { color: var(--arkhe-cyan) !important; }

.block-container { padding-top: 1.4rem; }

/* ── Hero ─────────────────────────────────────────────────────── */
.arkhe-hero {
    position: relative;
    padding: 30px 36px 26px 36px;
    border: 1px solid var(--arkhe-border);
    border-radius: 24px;
    background:
        radial-gradient(circle at 50% 5%, rgba(91,255,232,0.22), transparent 30%),
        linear-gradient(135deg, rgba(12,18,26,0.96), rgba(7,10,14,0.92));
    box-shadow:
        0 0 45px rgba(91,255,232,0.13),
        inset 0 0 30px rgba(91,255,232,0.05);
    overflow: hidden;
    margin-bottom: 24px;
}
.arkhe-hero:before {
    content: "";
    position: absolute; inset: 0;
    background-image:
        linear-gradient(rgba(91,255,232,0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(91,255,232,0.08) 1px, transparent 1px);
    background-size: 42px 42px;
    opacity: 0.26;
    mask-image: radial-gradient(circle at 50% 25%, black, transparent 72%);
}
.arkhe-hero-content { position: relative; z-index: 2; }

.arkhe-kicker {
    color: var(--arkhe-cyan);
    letter-spacing: 0.22em; text-transform: uppercase;
    font-size: 0.78rem; font-weight: 700;
    margin-bottom: 10px;
}
.arkhe-title {
    font-size: 2.85rem; line-height: 1.02; font-weight: 850;
    margin: 0; color: var(--arkhe-text);
    text-shadow: 0 0 18px rgba(91,255,232,0.18);
}
.arkhe-subtitle {
    margin-top: 12px; max-width: 760px;
    color: var(--arkhe-muted); font-size: 1.05rem;
}
.arkhe-shield {
    width: 64px; height: 76px;
    border: 1px solid var(--arkhe-border);
    clip-path: polygon(50% 0%, 92% 16%, 84% 70%, 50% 100%, 16% 70%, 8% 16%);
    background:
        radial-gradient(circle at 50% 35%, rgba(91,255,232,0.55), transparent 35%),
        linear-gradient(135deg, rgba(91,255,232,0.18), rgba(201,162,74,0.12));
    box-shadow: 0 0 28px rgba(91,255,232,0.34);
    margin-bottom: 14px;
}
.arkhe-pill {
    display: inline-block;
    border: 1px solid var(--arkhe-border);
    border-radius: 999px;
    padding: 6px 12px;
    color: var(--arkhe-cyan);
    background: rgba(91,255,232,0.08);
    font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;
}

/* ── Cards / panels ───────────────────────────────────────────── */
.arkhe-card {
    border: 1px solid var(--arkhe-border);
    border-radius: 18px;
    padding: 18px;
    background: linear-gradient(145deg, rgba(17,25,35,0.88), rgba(7,10,14,0.88));
    box-shadow: 0 0 24px rgba(91,255,232,0.08);
}
.arkhe-card h3 { color: var(--arkhe-text); margin-top: 0; }
.arkhe-card p  { color: var(--arkhe-muted); }

/* ── Metric containers ────────────────────────────────────────── */
[data-testid="stMetric"] {
    border: 1px solid var(--arkhe-border);
    border-radius: 18px;
    padding: 14px;
    background:
        linear-gradient(145deg, rgba(17,25,35,0.92), rgba(7,10,14,0.92));
    box-shadow: 0 0 18px rgba(91,255,232,0.06);
}
[data-testid="stMetricLabel"] {
    color: var(--arkhe-muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    font-size: 0.72rem;
    font-weight: 700;
}
[data-testid="stMetricValue"] {
    color: var(--arkhe-text) !important;
    font-weight: 800;
}

/* ── Buttons ──────────────────────────────────────────────────── */
div.stButton > button,
div.stDownloadButton > button {
    border: 1px solid var(--arkhe-border) !important;
    background: linear-gradient(135deg, rgba(91,255,232,0.18), rgba(201,162,74,0.10)) !important;
    color: var(--arkhe-text) !important;
    border-radius: 14px !important;
    box-shadow: 0 0 18px rgba(91,255,232,0.10);
    font-weight: 700 !important;
}
div.stButton > button:hover,
div.stDownloadButton > button:hover {
    border-color: var(--arkhe-cyan) !important;
    box-shadow: 0 0 28px rgba(91,255,232,0.28);
    color: var(--arkhe-cyan) !important;
}

/* ── Inputs / selects ─────────────────────────────────────────── */
input, textarea, select,
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background: rgba(11,17,24,0.85) !important;
    border-color: var(--arkhe-border) !important;
    color: var(--arkhe-text) !important;
}

/* ── Tabs ─────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.4rem;
    border-bottom: 1px solid var(--arkhe-border);
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    color: var(--arkhe-muted);
    font-weight: 700;
    padding-left: 0.4rem; padding-right: 0.4rem;
    margin-right: 0.7rem;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--arkhe-cyan) !important;
    text-shadow: 0 0 12px rgba(91,255,232,0.45);
}

/* ── Dataframes ───────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--arkhe-border);
    border-radius: 16px;
    overflow: hidden;
    background: rgba(11,17,24,0.85);
}

hr { border-color: rgba(91,255,232,0.22) !important; }

/* ──────────────────────────────────────────────────────────────
   Legacy `arkhe_market-*` classes (used by ui/cards.py and views).
   These keep the existing markup working in the new aesthetic.
   ────────────────────────────────────────────────────────────── */
.arkhe_market-shell      { padding: 0.2rem 0 0.8rem 0; }
.arkhe_market-topline {
    color: var(--arkhe-cyan);
    letter-spacing: 0.22em; text-transform: uppercase;
    font-size: 0.78rem; font-weight: 700;
    opacity: 0.92; margin-bottom: 0.35rem;
}
.arkhe_market-title {
    color: var(--arkhe-text); font-size: 2.2rem; line-height: 1.02;
    font-weight: 850; letter-spacing: 0.01em;
    text-shadow: 0 0 18px rgba(91,255,232,0.22);
    margin-bottom: 0.3rem;
}
.arkhe_market-subtitle { color: var(--arkhe-muted); font-size: 1rem; margin-bottom: 0.6rem; }
.arkhe_market-section {
    color: var(--arkhe-cyan);
    font-size: 1.7rem; font-weight: 850;
    margin: 1rem 0 0.4rem 0;
    text-shadow: 0 0 14px rgba(91,255,232,0.20);
}
.arkhe_market-subsection {
    color: var(--arkhe-text);
    font-size: 1.1rem; font-weight: 800;
    margin: 0.6rem 0 0.4rem 0;
}
.arkhe_market-divider {
    height: 1px; margin: 0.4rem 0 1rem 0; border-radius: 999px;
    background: linear-gradient(90deg, rgba(91,255,232,0.32), rgba(91,255,232,0.02));
}
.arkhe_market-card {
    background: linear-gradient(180deg, rgba(17,25,35,0.92) 0%, rgba(11,17,24,0.92) 100%);
    border: 1px solid var(--arkhe-border);
    border-radius: 18px; padding: 16px;
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.03),
        0 0 18px rgba(91,255,232,0.05);
}
.arkhe_market-kicker {
    color: var(--arkhe-muted);
    text-transform: uppercase; letter-spacing: 0.15em;
    font-size: 0.74rem; font-weight: 700; margin-bottom: 0.4rem;
}
.arkhe_market-chip {
    display: inline-block; border-radius: 999px; padding: 4px 10px;
    background: rgba(91,255,232,0.08);
    color: var(--arkhe-cyan);
    border: 1px solid var(--arkhe-border);
    font-size: 0.82rem; font-weight: 700;
}
.arkhe_market-note { color: var(--arkhe-muted); font-size: 0.9rem; }
</style>
"""


def inject_theme():
    st.markdown(ARKHE_CSS, unsafe_allow_html=True)


def apply_theme():
    """Alias kept for backward compatibility."""
    inject_theme()


def arkhe_hero(
    title: str = "Arkhe Market",
    kicker: str = "ARKHE HOLDINGS",
    subtitle: str = (
        "Multi-agent market intelligence built around structure, "
        "risk control, strategy validation, and first-principles execution."
    ),
    motto: str = "Shield. Structure. Launch.",
):
    st.markdown(
        f"""
        <div class="arkhe-hero">
          <div class="arkhe-hero-content">
            <div class="arkhe-shield"></div>
            <div class="arkhe-kicker">{kicker}</div>
            <h1 class="arkhe-title">{title}</h1>
            <div class="arkhe-subtitle">{subtitle}</div>
            <br>
            <span class="arkhe-pill">{motto}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Constellation card CSS (legacy) ────────────────────────────────
CONSTELLATION_CSS = """
<style>
.arkhe-constellation-card {
    position: relative;
    min-height: 210px;
    border: 1px solid rgba(91,255,232,0.28);
    border-radius: 22px;
    padding: 20px;
    background:
        radial-gradient(circle at 50% 35%, rgba(91,255,232,0.18), transparent 34%),
        linear-gradient(145deg, rgba(11,17,24,0.94), rgba(4,7,10,0.96));
    box-shadow: 0 0 30px rgba(91,255,232,0.10);
    overflow: hidden;
    transition: all 0.45s ease;
    margin-bottom: 22px;
}
.arkhe-constellation-card:hover {
    min-height: 430px;
    box-shadow:
        0 0 50px rgba(91,255,232,0.24),
        inset 0 0 36px rgba(91,255,232,0.06);
    border-color: rgba(91,255,232,0.68);
}
</style>
"""


def inject_constellation_css():
    st.markdown(CONSTELLATION_CSS, unsafe_allow_html=True)
