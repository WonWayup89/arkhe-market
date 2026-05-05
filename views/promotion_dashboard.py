"""
pages/promotion_dashboard.py – Strategy Scoring & Promotion UI panel.

Shows each symbol's tier, score, alignment, trend, and promotion path.
Includes the "Run Promotion Cycle" button.
"""

import pandas as pd
import streamlit as st
from ui.cards import market_summary_row, section_intro
from ui.tables import show_table
from ui.constellation import promotion_constellation


TIER_EMOJI = {
    "sim_only": "🔵",
    "shadow_validated": "🟡",
    "live_eligible": "🟢",
}

TIER_COLOR = {
    "sim_only": "#94A3B8",
    "shadow_validated": "#FFC83D",
    "live_eligible": "#10B981",
}

TREND_EMOJI = {
    "improving": "📈",
    "degrading": "📉",
    "stable": "➡️",
    "insufficient_data": "⏳",
}


def render_promotion_dashboard(promotion_supervisor, agent, symbols, starting_equities):
    """Render the full promotion dashboard."""

    section_intro("Strategy Scoring & Promotion", "Evaluate, validate, and promote strategies from simulation to live")

    # Pipeline constellation at top of view
    try:
        _pipeline_summary = promotion_supervisor.tier_summary()
    except Exception:
        _pipeline_summary = {}
    promotion_constellation(_pipeline_summary, height=320)

    # ── Run cycle button ───────────────────────────────────────────
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("Run Promotion Cycle", width="stretch", key="run_promo"):
            with st.spinner("Scoring → Validating → Promoting..."):
                results = promotion_supervisor.run_cycle(agent, symbols, starting_equities)
                st.session_state.promo_results = results
            st.success(f"Evaluated {len(results)} symbols")

    with c2:
        tier_summary = promotion_supervisor.tier_summary()
        market_summary_row([
            {"label": "Sim Only", "value": str(len(tier_summary.get("sim_only", [])))},
            {"label": "Shadow Validated", "value": str(len(tier_summary.get("shadow_validated", [])))},
            {"label": "Live Eligible", "value": str(len(tier_summary.get("live_eligible", [])))},
            {"label": "Total Tracked", "value": str(tier_summary.get("total", 0))},
        ])

    # ── Results table ──────────────────────────────────────────────
    results = st.session_state.get("promo_results", [])

    if results:
        st.markdown("---")

        rows = []
        for r in results:
            sym = r["symbol"]
            score = r["score"].get("score", 0)
            tier_label = r["score"].get("tier", "—")
            alignment = r["shadow"].get("alignment", 0)
            promo = r["promotion"]
            trend = r["trend"]

            tier = promo["new_tier"]
            emoji = TIER_EMOJI.get(tier, "⚪")
            trend_emoji = TREND_EMOJI.get(trend.get("trend", ""), "")
            action = promo.get("action", "hold")

            action_display = {"promote": "⬆ PROMOTED", "demote": "⬇ DEMOTED", "hold": "— hold"}.get(action, action)

            rows.append({
                "symbol": sym,
                "tier": f"{emoji} {tier}",
                "score": score,
                "alignment": alignment,
                "trend": f"{trend_emoji} {trend.get('trend', '?')}",
                "action": action_display,
                "reason": promo.get("reason", ""),
                "trades": r["score"].get("trade_count", 0),
            })

        df = pd.DataFrame(rows)
        show_table(df, height=min(len(rows) * 40 + 60, 600))

        # ── Detailed cards per symbol ──────────────────────────────
        st.markdown("---")
        st.markdown('<div class="arkhe_market-subsection">Symbol Detail Cards</div>', unsafe_allow_html=True)

        for r in results:
            sym = r["symbol"]
            score = r["score"]
            shadow = r["shadow"]
            promo = r["promotion"]
            trend = r["trend"]
            tier = promo["new_tier"]
            emoji = TIER_EMOJI.get(tier, "⚪")

            with st.expander(f"{emoji} {sym} — {tier} (score: {score.get('score', 0)})", expanded=False):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Score", score.get("score", 0))
                c2.metric("Alignment", shadow.get("alignment", 0))
                c3.metric("Trades", score.get("trade_count", 0))
                c4.metric("Trend", trend.get("trend", "?"))

                c5, c6, c7, c8 = st.columns(4)
                c5.metric("Return", f"{score.get('total_return', 0)*100:.2f}%")
                c6.metric("Sharpe", f"{score.get('sharpe', 0):.3f}")
                c7.metric("Win Rate", f"{score.get('win_rate', 0)*100:.0f}%")
                c8.metric("Max DD", f"{score.get('max_drawdown', 0)*100:.1f}%")

                # Score components
                comps = score.get("components", {})
                if comps:
                    st.caption("Score Components")
                    comp_cols = st.columns(len(comps))
                    for col, (k, v) in zip(comp_cols, comps.items()):
                        col.metric(k, f"{v:.2f}")

                st.caption(f"Promotion reason: {promo.get('reason', '')}")
                st.caption(f"Trend delta: {trend.get('delta', 0):+.1f} pts over last {trend.get('window', 0)} evaluations")

    else:
        st.info("Press 'Run Promotion Cycle' to evaluate all symbols.")

    # ── Portfolio health ───────────────────────────────────────────
    st.markdown("---")
    health = promotion_supervisor.portfolio_health()
    if health.get("total_symbols", 0) > 0:
        st.markdown('<div class="arkhe_market-subsection">Portfolio Health</div>', unsafe_allow_html=True)
        h1, h2, h3, h4 = st.columns(4)
        h1.metric("Avg Score", health.get("avg_score", 0))
        h2.metric("Improving", len(health.get("improving", [])))
        h3.metric("Stable", len(health.get("stable", [])))
        h4.metric("Degrading", len(health.get("degrading", [])))
