import streamlit as st

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
}

html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 50% 0%, rgba(91,255,232,0.22), transparent 28%),
        radial-gradient(circle at 90% 20%, rgba(25,199,184,0.12), transparent 28%),
        linear-gradient(180deg, #071018 0%, #05090D 50%, #030506 100%) !important;
    color: var(--arkhe-text) !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(12,18,26,0.96), rgba(8,10,14,0.98)) !important;
    border-right: 1px solid var(--arkhe-border);
}

.block-container {
    padding-top: 1.4rem;
}

.arkhe-hero {
    position: relative;
    padding: 34px 36px;
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
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(91,255,232,0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(91,255,232,0.08) 1px, transparent 1px);
    background-size: 42px 42px;
    opacity: 0.26;
    mask-image: radial-gradient(circle at 50% 25%, black, transparent 72%);
}

.arkhe-hero-content {
    position: relative;
    z-index: 2;
}

.arkhe-kicker {
    color: var(--arkhe-cyan);
    letter-spacing: 0.22em;
    text-transform: uppercase;
    font-size: 0.78rem;
    font-weight: 700;
    margin-bottom: 10px;
}

.arkhe-title {
    font-size: 3rem;
    line-height: 1.02;
    font-weight: 850;
    margin: 0;
    color: var(--arkhe-text);
    text-shadow: 0 0 18px rgba(91,255,232,0.18);
}

.arkhe-subtitle {
    margin-top: 12px;
    max-width: 760px;
    color: var(--arkhe-muted);
    font-size: 1.08rem;
}

.arkhe-shield {
    width: 72px;
    height: 86px;
    border: 1px solid var(--arkhe-border);
    clip-path: polygon(50% 0%, 92% 16%, 84% 70%, 50% 100%, 16% 70%, 8% 16%);
    background:
        radial-gradient(circle at 50% 35%, rgba(91,255,232,0.55), transparent 35%),
        linear-gradient(135deg, rgba(91,255,232,0.18), rgba(201,162,74,0.12));
    box-shadow: 0 0 28px rgba(91,255,232,0.34);
    margin-bottom: 12px;
}

.arkhe-card {
    border: 1px solid var(--arkhe-border);
    border-radius: 18px;
    padding: 18px;
    background:
        linear-gradient(145deg, rgba(17,25,35,0.88), rgba(7,10,14,0.88));
    box-shadow: 0 0 24px rgba(91,255,232,0.08);
}

.arkhe-card h3 {
    color: var(--arkhe-text);
    margin-top: 0;
}

.arkhe-card p {
    color: var(--arkhe-muted);
}

.arkhe-metric {
    border: 1px solid var(--arkhe-border);
    border-radius: 18px;
    padding: 16px 18px;
    background:
        linear-gradient(145deg, rgba(17,25,35,0.92), rgba(7,10,14,0.92));
    box-shadow: 0 0 20px rgba(91,255,232,0.07);
}

.arkhe-metric-label {
    color: var(--arkhe-muted);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

.arkhe-metric-value {
    color: var(--arkhe-text);
    font-size: 1.65rem;
    font-weight: 800;
    margin-top: 6px;
}

.arkhe-pill {
    display: inline-block;
    border: 1px solid var(--arkhe-border);
    border-radius: 999px;
    padding: 7px 12px;
    color: var(--arkhe-cyan);
    background: rgba(91,255,232,0.08);
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

div.stButton > button {
    border: 1px solid var(--arkhe-border) !important;
    background: linear-gradient(135deg, rgba(91,255,232,0.16), rgba(201,162,74,0.10)) !important;
    color: var(--arkhe-text) !important;
    border-radius: 14px !important;
    box-shadow: 0 0 18px rgba(91,255,232,0.10);
}

div.stButton > button:hover {
    border-color: var(--arkhe-cyan) !important;
    box-shadow: 0 0 28px rgba(91,255,232,0.28);
}

[data-testid="stMetric"] {
    border: 1px solid var(--arkhe-border);
    border-radius: 18px;
    padding: 14px;
    background: rgba(11,17,24,0.86);
}

hr {
    border-color: rgba(91,255,232,0.22) !important;
}
</style>
"""

def apply_theme():
    st.markdown(ARKHE_CSS, unsafe_allow_html=True)

def arkhe_hero():
    st.markdown(
        """
        <div class="arkhe-hero">
          <div class="arkhe-hero-content">
            <div class="arkhe-shield"></div>
            <div class="arkhe-kicker">ARKHE HOLDINGS</div>
            <h1 class="arkhe-title">Arkhe Market</h1>
            <div class="arkhe-subtitle">
              Multi agent market intelligence built around structure, risk control, strategy validation, and first principles execution.
            </div>
            <br>
            <span class="arkhe-pill">Shield. Structure. Launch.</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_theme():
    apply_theme()

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

.arkhe-constellation-header {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    position: relative;
    z-index: 4;
}

.arkhe-constellation-kicker {
    color: #5BFFE8;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 800;
}

.arkhe-constellation-title {
    color: #F7F7F2;
    font-size: 1.75rem;
    font-weight: 850;
    margin-top: 4px;
}

.arkhe-constellation-subtitle {
    color: #9CA7AE;
    font-size: 0.9rem;
    margin-top: 4px;
}

.arkhe-constellation-value {
    color: #F7F7F2;
    font-size: 1.55rem;
    font-weight: 850;
    text-shadow: 0 0 18px rgba(91,255,232,0.25);
}

.arkhe-constellation-stage {
    position: absolute;
    inset: 82px 16px 48px 16px;
    opacity: 0.55;
    transform: scale(0.72) translateY(20px);
    transform-origin: center;
    transition: all 0.55s ease;
}

.arkhe-constellation-card:hover .arkhe-constellation-stage {
    opacity: 1;
    transform: scale(1) translateY(0);
}

.arkhe-orbit {
    position: absolute;
    left: 50%;
    top: 50%;
    border: 1px solid rgba(91,255,232,0.22);
    border-radius: 999px;
    transform: translate(-50%, -50%);
    box-shadow: 0 0 20px rgba(91,255,232,0.08);
}

.orbit-one {
    width: 230px;
    height: 130px;
}

.orbit-two {
    width: 340px;
    height: 210px;
    transform: translate(-50%, -50%) rotate(-18deg);
}

.arkhe-node {
    position: absolute;
    width: 54px;
    height: 54px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    color: #F7F7F2;
    font-size: 0.72rem;
    font-weight: 850;
    border: 1px solid rgba(91,255,232,0.62);
    background:
        radial-gradient(circle at 35% 30%, rgba(255,255,255,0.30), transparent 18%),
        radial-gradient(circle, rgba(91,255,232,0.34), rgba(8,12,17,0.96) 62%);
    box-shadow:
        0 0 16px rgba(91,255,232,0.32),
        inset 0 0 12px rgba(91,255,232,0.16);
    transition: all 0.45s ease;
}

.arkhe-node:hover {
    transform: scale(1.18);
    box-shadow:
        0 0 28px rgba(91,255,232,0.72),
        inset 0 0 16px rgba(91,255,232,0.22);
    z-index: 5;
}

.core-node {
    left: calc(50% - 32px);
    top: calc(50% - 32px);
    width: 64px;
    height: 64px;
    color: #05090D;
    background:
        radial-gradient(circle, #F7F7F2, #5BFFE8 56%, #0B1118 100%);
}

.node-btc { left: 12%; top: 42%; }
.node-eth { right: 12%; top: 42%; }
.node-sol { left: 27%; top: 8%; }
.node-xrp { right: 27%; top: 8%; }
.node-ada { left: 26%; bottom: 4%; }
.node-link { right: 26%; bottom: 4%; }
.node-doge { left: 48%; top: -2%; }
.node-avax { left: 48%; bottom: -2%; }

.arkhe-line {
    position: absolute;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(91,255,232,0.58), transparent);
    transform-origin: center;
    box-shadow: 0 0 12px rgba(91,255,232,0.38);
}

.line-a {
    width: 62%;
    left: 19%;
    top: 50%;
}

.line-b {
    width: 48%;
    left: 26%;
    top: 32%;
    transform: rotate(28deg);
}

.line-c {
    width: 48%;
    left: 26%;
    top: 66%;
    transform: rotate(-28deg);
}

.line-d {
    width: 36%;
    left: 32%;
    top: 50%;
    transform: rotate(90deg);
}

.arkhe-constellation-footer {
    position: absolute;
    left: 20px;
    right: 20px;
    bottom: 16px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    opacity: 0;
    transform: translateY(8px);
    transition: all 0.45s ease;
}

.arkhe-constellation-card:hover .arkhe-constellation-footer {
    opacity: 1;
    transform: translateY(0);
}

.arkhe-constellation-footer span {
    border: 1px solid rgba(91,255,232,0.26);
    border-radius: 999px;
    padding: 6px 10px;
    color: #5BFFE8;
    background: rgba(91,255,232,0.07);
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
</style>
"""

def inject_constellation_css():
    st.markdown(CONSTELLATION_CSS, unsafe_allow_html=True)
