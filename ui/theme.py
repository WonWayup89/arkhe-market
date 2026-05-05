import streamlit as st

COLORS = {
    "bg_main": "#06080D",
    "bg_panel": "#0E131B",
    "bg_card": "#141B24",
    "bg_card_soft": "#18212D",
    "arkhe_market": "#FFB000",
    "arkhe_market_soft": "#FFC83D",
    "arkhe_market_dark": "#D97706",
    "text_primary": "#E6EDF3",
    "text_secondary": "#94A3B8",
    "green": "#10B981",
    "red": "#EF4444",
    "line": "rgba(255, 200, 61, 0.14)",
}

def inject_theme():
    st.markdown(
        f'''
        <style>
        .stApp {{
            background:
                radial-gradient(circle at top right, rgba(255,176,0,0.08), transparent 18%),
                radial-gradient(circle at top left, rgba(255,138,0,0.05), transparent 15%),
                linear-gradient(180deg, {COLORS["bg_main"]} 0%, #090D13 100%);
            color: {COLORS["text_primary"]};
        }}

        section[data-testid="stSidebar"] {{
            background:
                linear-gradient(180deg, #6A3A11 0%, #8E4D1B 35%, #6A3A11 100%);
            border-right: 1px solid rgba(255,200,61,0.14);
        }}

        [data-testid="stHeader"] {{
            background: rgba(0,0,0,0);
        }}

        .arkhe_market-shell {{
            padding: 0.2rem 0 0.8rem 0;
        }}

        .arkhe_market-topline {{
            color: {COLORS["arkhe_market_soft"]};
            letter-spacing: 0.22em;
            text-transform: uppercase;
            font-size: 0.78rem;
            font-weight: 700;
            opacity: 0.9;
            margin-bottom: 0.35rem;
        }}

        .arkhe_market-title {{
            color: {COLORS["arkhe_market_soft"]};
            font-size: 3rem;
            line-height: 1;
            font-weight: 800;
            letter-spacing: 0.01em;
            margin-bottom: 0.35rem;
            text-shadow: 0 0 18px rgba(255,176,0,0.18);
        }}

        .arkhe_market-subtitle {{
            color: {COLORS["text_secondary"]};
            margin-bottom: 1rem;
            font-size: 1rem;
        }}

        .arkhe_market-section {{
            color: {COLORS["arkhe_market_soft"]};
            font-size: 2rem;
            font-weight: 800;
            margin: 1rem 0 0.75rem 0;
        }}

        .arkhe_market-subsection {{
            color: {COLORS["text_primary"]};
            font-size: 1.18rem;
            font-weight: 700;
            margin: 0.65rem 0 0.45rem 0;
        }}

        .arkhe_market-divider {{
            height: 1px;
            background: linear-gradient(90deg, rgba(255,200,61,0.22), rgba(255,200,61,0.02));
            margin: 0.5rem 0 1rem 0;
            border-radius: 999px;
        }}

        .arkhe_market-card {{
            background:
                linear-gradient(180deg, {COLORS["bg_card_soft"]} 0%, {COLORS["bg_card"]} 100%);
            border: 1px solid rgba(255,176,0,0.14);
            border-radius: 18px;
            padding: 16px;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.03),
                0 0 18px rgba(255,176,0,0.05);
        }}

        .arkhe_market-kicker {{
            color: {COLORS["text_secondary"]};
            text-transform: uppercase;
            letter-spacing: 0.15em;
            font-size: 0.74rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }}

        .arkhe_market-chip {{
            display: inline-block;
            border-radius: 999px;
            padding: 4px 10px;
            background: rgba(255,176,0,0.08);
            color: {COLORS["arkhe_market_soft"]};
            border: 1px solid rgba(255,176,0,0.18);
            font-size: 0.84rem;
            font-weight: 700;
        }}

        div[data-testid="stMetric"] {{
            background:
                linear-gradient(180deg, {COLORS["bg_card_soft"]} 0%, {COLORS["bg_card"]} 100%);
            border: 1px solid rgba(255,176,0,0.12);
            padding: 14px 14px 12px 14px;
            border-radius: 16px;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.03),
                0 0 16px rgba(255,176,0,0.03);
        }}

        div[data-testid="stMetricLabel"] {{
            color: {COLORS["text_secondary"]};
            text-transform: uppercase;
            letter-spacing: 0.13em;
            font-size: 0.72rem;
            font-weight: 700;
        }}

        div[data-testid="stMetricValue"] {{
            color: {COLORS["text_primary"]};
            font-weight: 800;
        }}

        div.stButton > button {{
            background: linear-gradient(180deg, #1A2430 0%, #131B24 100%);
            color: {COLORS["text_primary"]};
            border: 1px solid rgba(255,176,0,0.16);
            border-radius: 12px;
            padding: 0.62rem 0.95rem;
            box-shadow: 0 0 12px rgba(255,176,0,0.03);
            font-weight: 700;
        }}

        div.stButton > button:hover {{
            border-color: rgba(255,200,61,0.30);
            box-shadow: 0 0 18px rgba(255,176,0,0.08);
            color: {COLORS["arkhe_market_soft"]};
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.4rem;
            border-bottom: 1px solid rgba(255,200,61,0.12);
        }}

        .stTabs [data-baseweb="tab"] {{
            color: {COLORS["text_secondary"]};
            font-weight: 700;
            padding-left: 0;
            padding-right: 0;
            margin-right: 1rem;
        }}

        .stTabs [aria-selected="true"] {{
            color: {COLORS["arkhe_market_soft"]} !important;
        }}

        [data-testid="stDataFrame"] {{
            border: 1px solid rgba(255,176,0,0.12);
            border-radius: 16px;
            overflow: hidden;
        }}

        .arkhe_market-note {{
            color: {COLORS["text_secondary"]};
            font-size: 0.9rem;
        }}
        </style>
        ''',
        unsafe_allow_html=True,
    )
