"""
views/futures.py – Futures workspace with live data, signals, and expert scan.

Uses yfinance continuous-contract tickers (ES=F, NQ=F, etc.)
for live prices and candle data via the DataFeed layer.
"""

import pandas as pd
import streamlit as st
from services.command_center_pipeline import log_market_outputs
from ui.cards import market_summary_row, section_intro
from ui.tables import show_table
from ui.constellation import market_constellation
from arkhe_market_core.ml.inference.symbol_scorer import score_symbol
from arkhe_market_core.ml.inference.neural_gate import neural_gate


# Contract reference info
FUTURES_INFO = {
    "ES": {"name": "E-mini S&P 500", "exchange": "CME", "multiplier": 50, "tick": 0.25},
    "NQ": {"name": "E-mini Nasdaq 100", "exchange": "CME", "multiplier": 20, "tick": 0.25},
    "RTY": {"name": "E-mini Russell 2000", "exchange": "CME", "multiplier": 50, "tick": 0.10},
    "YM": {"name": "E-mini Dow", "exchange": "CBOT", "multiplier": 5, "tick": 1.0},
    "CL": {"name": "Crude Oil", "exchange": "NYMEX", "multiplier": 1000, "tick": 0.01},
    "NG": {"name": "Natural Gas", "exchange": "NYMEX", "multiplier": 10000, "tick": 0.001},
    "GC": {"name": "Gold", "exchange": "COMEX", "multiplier": 100, "tick": 0.10},
    "SI": {"name": "Silver", "exchange": "COMEX", "multiplier": 5000, "tick": 0.005},
    "ZN": {"name": "10-Year T-Note", "exchange": "CBOT", "multiplier": 1000, "tick": 0.015625},
    "6E": {"name": "Euro FX", "exchange": "CME", "multiplier": 125000, "tick": 0.00005},
}


def _expert_panel(agent, symbol):
    panel = agent.expert_panel(symbol)
    if not panel:
        st.caption("No expert data (fetch failed or insufficient bars).")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", f"${panel['price']:.2f}")
    sig = panel["signal"] or "—"
    emoji = {"buy": "🟢", "sell": "🔴"}.get(panel["signal"], "⚪")
    c2.metric("Signal", f"{emoji} {sig.upper()}")
    c3.metric("Vol Regime", panel["vol"].get("regime", "—"))
    c4.metric("Mkt Regime", panel["regime"].get("regime", "—"))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Sentiment", f"{panel['sentiment'].get('score', 0)}")
    c6.metric("Vol Size×", f"{panel['vol'].get('size_factor', 1):.2f}")
    c7.metric("Bias", panel["regime"].get("bias", "—"))
    c8.metric("BB Squeeze", "YES" if panel["vol"].get("bb_squeeze") else "no")

    ind = panel.get("indicators", {})
    if ind:
        ic1, ic2, ic3, ic4 = st.columns(4)
        ic1.metric("RSI", ind.get("rsi", "—"))
        ic2.metric("MACD", ind.get("macd", "—"))
        ic3.metric("Stoch %K", ind.get("stoch_k", "—"))
        ic4.metric("ATR%", ind.get("atr_pct", "—"))

    st.caption(f"Reason: {panel['reason']}")


def render_futures(agent, config, broker):
    if not config.get("futures_symbols"):
        st.info("Add futures symbols in the sidebar.")
        return

    snap = agent.snapshot()
    futures_eq = snap.get("futures", {}).get("equity", 0)
    session = broker.snapshot("futures")

    section_intro("Futures", "Contract-level workspace")
    market_constellation("futures", list(config.get("futures_symbols", [])), height=320)

    tabs = st.tabs(["Overview", "Portfolio", "Live Prices", "Signals", "Expert Scan", "Contracts"])

    with tabs[0]:
        market_summary_row([
            {"label": "Futures Equity", "value": f"${futures_eq:,.2f}"},
            {"label": "Cash", "value": f"${snap.get('futures', {}).get('cash', config['futures_balance']):,.2f}"},
            {"label": "Tracked", "value": str(len(config["futures_symbols"]))},
            {"label": "Source", "value": session["source"].title()},
        ])

    with tabs[1]:
        rows = []
        for sym in config["futures_symbols"]:
            s = agent.symbol_snapshot(sym)
            try:
                live = agent.get_live_price(sym)
            except Exception:
                live = float(s.get("last_price", 0))
            entry = float(s.get("avg_entry", 0))
            qty = float(s.get("asset_qty", 0))
            info = FUTURES_INFO.get(sym, {})
            notional = live * info.get("multiplier", 1) * qty if qty > 0 else 0
            pnl = ((live - entry) / entry * 100) if entry > 0 and qty > 0 else 0
            rows.append({
                "contract": sym,
                "name": info.get("name", sym),
                "price": round(live, 4),
                "position": round(qty, 4),
                "notional": round(notional, 2),
                "equity": round(float(s.get("equity", 0)), 2),
                "unreal%": round(pnl, 2),
                "trades": int(s.get("trade_count", 0)),
                "neural": round(score_symbol(sym, {"price": live, "volatility": 0.1}, "futures") or 0, 4),
                "gate": neural_gate(score_symbol(sym, {"price": live, "volatility": 0.1}, "futures")),
            })
        show_table(pd.DataFrame(rows), height=460)

    with tabs[2]:
        quote_rows = []
        for sym in config["futures_symbols"]:
            s = agent.symbol_snapshot(sym)
            try:
                price = float(agent.get_live_price(sym))
                source = "live"
                ok = True
            except Exception:
                price = float(s.get("last_price", 0))
                source = "snapshot"
                ok = False
            info = FUTURES_INFO.get(sym, {})
            quote_rows.append({
                "contract": sym,
                "name": info.get("name", sym),
                "price": round(price, 4),
                "source": source,
                "ok": ok,
                "updated_equity": round(float(s.get("equity", 0)), 2),
            })
        show_table(pd.DataFrame(quote_rows), height=420)
    with tabs[3]:
        if st.button("Run Futures Signals", key="run_futures_signals"):
            out = agent.run_once_futures()
            log_market_outputs("futures", [str(x) for x in out] if isinstance(out, list) else [str(out)])
            st.session_state.futures_signals = out
        for line in st.session_state.get("futures_signals", ["No run yet."]):
            st.write(line)

    with tabs[4]:
        pick = st.selectbox("Contract", config["futures_symbols"], key="expert_futures")
        if st.button("Scan", key="scan_futures"):
            with st.spinner("Running experts..."):
                _expert_panel(agent, pick)

    with tabs[5]:
        st.markdown('<div class="arkhe_market-subsection">Contract Reference</div>', unsafe_allow_html=True)
        contract_rows = []
        for sym in config["futures_symbols"]:
            info = FUTURES_INFO.get(sym, {})
            contract_rows.append({
                "symbol": sym,
                "name": info.get("name", "—"),
                "exchange": info.get("exchange", "—"),
                "multiplier": info.get("multiplier", "—"),
                "tick_size": info.get("tick", "—"),
            })
        show_table(pd.DataFrame(contract_rows), height=340)
