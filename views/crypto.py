"""
views/crypto.py – Crypto workspace with portfolio, prices, signals, expert scan.
"""

import pandas as pd
import streamlit as st
from services.command_center_pipeline import log_market_outputs
from ui.cards import market_summary_row, section_intro
from ui.tables import show_table
from arkhe_market_core.ml.inference.symbol_scorer import score_symbol
from arkhe_market_core.ml.inference.neural_gate import neural_gate


def _expert_panel(agent, symbol):
    panel = agent.expert_panel(symbol)
    if not panel:
        st.caption("No expert data (fetch failed or insufficient bars).")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", f"${panel['price']:.4f}")
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


def render_crypto(agent, config, broker):
    snap = agent.snapshot()
    session = broker.snapshot("crypto")
    crypto_eq = snap["stable"]["equity"] + snap["alt"]["equity"]

    section_intro("Crypto", "Core market workspace")

    tabs = st.tabs(["Overview", "Portfolio", "Live Prices", "Signals", "Expert Scan"])

    with tabs[0]:
        market_summary_row([
            {"label": "Crypto Equity", "value": f"${crypto_eq:,.2f}"},
            {"label": "Stable", "value": f"${snap['stable']['equity']:,.2f}"},
            {"label": "Alt", "value": f"${snap['alt']['equity']:,.2f}"},
            {"label": "Source", "value": session["source"].title()},
        ])

    with tabs[1]:
        all_crypto = config["stable_symbols"] + config["alt_symbols"]
        rows = []
        for sym in all_crypto:
            s = agent.symbol_snapshot(sym)
            try:
                live = agent.get_live_price(sym)
            except Exception:
                live = float(s.get("last_price", 0))
            entry = float(s.get("avg_entry", 0))
            qty = float(s.get("asset_qty", 0))
            pnl = ((live - entry) / entry * 100) if entry > 0 and qty > 0 else 0
            rows.append({
                "symbol": sym,
                "price": round(live, 4),
                "position": round(qty, 8),
                "avg_entry": round(entry, 4),
                "equity": round(float(s.get("equity", 0)), 2),
                "unreal%": round(pnl, 2),
                "trades": int(s.get("trade_count", 0)),
                "neural": round(score_symbol(sym, {"price": live, "volatility": 0.1}, "crypto") or 0, 4),
                "gate": neural_gate(score_symbol(sym, {"price": live, "volatility": 0.1}, "crypto")),
                "win%": round(float(s.get("win_rate", 0)), 1),
            })
        show_table(pd.DataFrame(rows), height=460)

    with tabs[2]:
        quote_rows = []
        for sym in config["stable_symbols"] + config["alt_symbols"]:
            s = agent.symbol_snapshot(sym)
            try:
                price = float(agent.get_live_price(sym))
                source = "live"
                ok = True
            except Exception:
                price = float(s.get("last_price", 0))
                source = "snapshot"
                ok = False
            quote_rows.append({
                "symbol": sym,
                "price": round(price, 6),
                "source": source,
                "ok": ok,
                "updated_equity": round(float(s.get("equity", 0)), 2),
            })
        show_table(pd.DataFrame(quote_rows), height=420)
    with tabs[3]:
        if st.button("Run Crypto Signals", key="run_crypto_signals"):
            out = agent.run_once_crypto()
            log_market_outputs("crypto", [str(x) for x in out] if isinstance(out, list) else [str(out)])
            st.session_state.crypto_signals = out
        for line in st.session_state.get("crypto_signals", ["No run yet."]):
            st.write(line)

    with tabs[4]:
        all_crypto = config["stable_symbols"] + config["alt_symbols"]
        pick = st.selectbox("Symbol", all_crypto, key="expert_crypto")
        if st.button("Scan", key="scan_crypto"):
            with st.spinner("Running experts..."):
                _expert_panel(agent, pick)
