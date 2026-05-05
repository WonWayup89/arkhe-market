import pandas as pd
from services.live_market_resolver import live_market_status
import streamlit as st
from ui.constellation import system_constellation
from services.command_center_pipeline import get_recent_activity, get_summary

def _metric_row(items):
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            st.markdown(
                f"""
                <div style="padding:16px;border:1px solid rgba(255,255,255,.08);border-radius:16px;background:rgba(255,255,255,.02);">
                    <div style="font-size:12px;opacity:.75;margin-bottom:8px;">{item['label']}</div>
                    <div style="font-size:20px;font-weight:700;">{item['value']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

def _show_table(df, height=260):
    st.dataframe(df, width="stretch", height=height)

def _collect_rows(agent, symbols, market):
    rows = []
    for sym in symbols:
        try:
            s = agent.symbol_snapshot(sym)
        except Exception:
            continue
        rows.append({
            "market": market,
            "symbol": sym,
            "qty": round(float(s.get("asset_qty", 0)), 8),
            "equity": round(float(s.get("equity", 0)), 2),
            "cash": round(float(s.get("cash", 0)), 2),
            "unreal_pnl": round(float(s.get("unrealized_pnl", 0)), 4),
            "trades": int(s.get("trade_count", 0)),
            "win_rate": round(float(s.get("win_rate", 0)), 1),
            "avg_entry": round(float(s.get("avg_entry", 0)), 4),
        })
    return rows


def _collect_cost_totals(multi_agent):
    """Aggregate cost analytics across all symbol agents."""
    totals = {
        "gross_realized_pnl": 0.0,
        "realized_pnl": 0.0,
        "unrealized_pnl": 0.0,
        "equity": 0.0,
        "cash": 0.0,
        "total_fees": 0.0,
        "total_commission": 0.0,
        "total_spread_cost": 0.0,
        "total_slippage_cost": 0.0,
        "total_execution_drag": 0.0,
        "trade_count": 0,
        "win_count": 0,
        "loss_count": 0,
    }
    rows = []

    agents = getattr(multi_agent, "agents", {})
    for symbol, agent in agents.items():
        try:
            snap = agent.execution.paper.snapshot()
        except Exception:
            continue

        market = getattr(agent, "asset_class", "unknown")
        row = {"market": market, "symbol": symbol}
        for k in totals.keys():
            v = snap.get(k, 0)
            if isinstance(v, (int, float)):
                totals[k] += v
                row[k] = v
            else:
                row[k] = 0
        rows.append(row)

    totals["net_realized_pnl"] = totals["realized_pnl"]
    totals["win_rate"] = round(
        totals["win_count"] / max(totals["win_count"] + totals["loss_count"], 1) * 100.0, 1
    )
    return totals, pd.DataFrame(rows)


def _collect_live_status_rows(multi_agent):
    """Collect live-mode eligibility status for every symbol."""
    rows = []
    agents = getattr(multi_agent, "agents", {})
    for symbol, agent in agents.items():
        try:
            snap = agent.execution.paper.snapshot()
            balance = float(snap.get("equity", 0))
        except Exception:
            balance = 0.0

        asset_class = getattr(agent, "asset_class", "crypto")
        status = live_market_status(
            asset_class,
            bool(st.session_state.get(f"live_{asset_class}_connected", False)) if not bool(getattr(agent, "test_mode", True)) else False,
            balance,
            override_minimum=bool(st.session_state.get(f"{asset_class}_override_minimum", False)),
            market_enabled=bool(st.session_state.get(f"{asset_class}_enabled", True)),
            market_paused=bool(st.session_state.get(f"{asset_class}_paused", False)),
        )

        rows.append({
            "market": asset_class,
            "symbol": symbol,
            "connected": status.get("connected"),
            "mode": status.get("mode"),
            "live_eligible": status.get("live_eligible"),
            "health": status.get("health"),
            "balance": round(status.get("balance", 0), 2),
            "minimum_live_balance": round(status.get("minimum_live_balance", 0), 2),
            "recommended_balance": round(status.get("recommended_balance", 0), 2),
            "reason": status.get("reason"),
        })
    return pd.DataFrame(rows)


def render_command_center(agent, config, broker_manager):
    system_constellation(height=420)
    st.subheader("Command Center")
    st.caption("Cross market visibility and operations")

    crypto_symbols = config.get("stable_symbols", []) + config.get("alt_symbols", [])
    stock_symbols = config.get("stock_symbols", [])
    futures_symbols = config.get("futures_symbols", [])

    rows = []
    rows += _collect_rows(agent, crypto_symbols, "crypto")
    rows += _collect_rows(agent, stock_symbols, "stocks")
    rows += _collect_rows(agent, futures_symbols, "futures")

    df = pd.DataFrame(rows)
    if df.empty:
        st.info("No market rows available yet.")
        return

    total_equity = float(df["equity"].sum())
    total_unreal = float(df["unreal_pnl"].sum())
    total_trades = int(df["trades"].sum())
    open_positions = int((df["qty"] > 0).sum())

    crypto_equity = float(df[df["market"] == "crypto"]["equity"].sum())
    stock_equity = float(df[df["market"] == "stocks"]["equity"].sum())
    futures_equity = float(df[df["market"] == "futures"]["equity"].sum())

    _metric_row([
        {"label": "Total Equity", "value": f"${total_equity:,.2f}"},
        {"label": "Unrealized PnL", "value": f"${total_unreal:,.2f}"},
        {"label": "Open Positions", "value": str(open_positions)},
        {"label": "Total Trades", "value": str(total_trades)},
    ])
    st.markdown("")

    # FIX #2: Read 'neural_score' to match what app.py writes
    _metric_row([
        {"label": "Crypto Equity", "value": f"${crypto_equity:,.2f}"},
        {"label": "Stock Equity", "value": f"${stock_equity:,.2f}"},
        {"label": "Futures Equity", "value": f"${futures_equity:,.2f}"},
        {"label": "Neural Score", "value": f"{float(st.session_state.get('neural_score') or 0.0):.4f}"},
    ])
    st.markdown("")

    _metric_row([
        {"label": "Entry Threshold", "value": str(st.session_state.get("entry_gate_threshold", 0.75))},
        {"label": "Exit Threshold", "value": str(st.session_state.get("exit_gate_threshold", 0.25))},
        {"label": "Entry Blocks", "value": str(st.session_state.get("neural_blocks_entry", 0))},
        {"label": "Exit Blocks", "value": str(st.session_state.get("neural_blocks_exit", 0))},
    ])
    st.markdown("")

    left, right = st.columns([2, 1])

    with left:
        st.markdown("#### All Positions")
        _show_table(
            df[["market", "symbol", "qty", "equity", "unreal_pnl", "trades", "win_rate", "avg_entry"]],
            height=360,
        )

    with right:
        st.markdown("#### Top Winners")
        winners = df.sort_values("unreal_pnl", ascending=False).head(5)[["market", "symbol", "unreal_pnl", "trades"]]
        _show_table(winners, height=175)

        st.markdown("#### Top Losers")
        losers = df.sort_values("unreal_pnl", ascending=True).head(5)[["market", "symbol", "unreal_pnl", "trades"]]
        _show_table(losers, height=175)

    st.markdown("#### Recent Activity")
    recent = get_recent_activity(15)
    if recent:
        recent_df = pd.DataFrame(recent)[["ts", "market", "symbol", "kind", "message"]]
        _show_table(recent_df, height=260)
    else:
        st.info("No recent activity logged yet. Run signals or Run All Markets.")

    st.markdown("#### Activity Summary")
    summary = get_summary()
    _metric_row([
        {"label": "Buys", "value": str(summary.get("buys", 0))},
        {"label": "Sells", "value": str(summary.get("sells", 0))},
        {"label": "Holds", "value": str(summary.get("holds", 0))},
        {"label": "Waits", "value": str(summary.get("waits", 0))},
    ])
    st.markdown("")
    _metric_row([
        {"label": "Entry Blocks", "value": str(summary.get("entry_blocks", 0))},
        {"label": "Exit Blocks", "value": str(summary.get("exit_blocks", 0))},
        {"label": "Cooldowns", "value": str(summary.get("cooldowns", 0))},
        {"label": "Last Run", "value": str(st.session_state.get("cc_last_run", "never"))[:19]},
    ])

    # FIX #1 & #6: Cost analytics — was dead code after a return statement
    st.markdown("#### Cost Analytics")
    cost_totals, cost_df = _collect_cost_totals(agent)

    _metric_row([
        {"label": "Gross Realized PnL", "value": f"${cost_totals['gross_realized_pnl']:,.2f}"},
        {"label": "Net Realized PnL", "value": f"${cost_totals['net_realized_pnl']:,.2f}"},
        {"label": "Execution Drag", "value": f"${cost_totals['total_execution_drag']:,.2f}"},
        {"label": "Win Rate (net)", "value": f"{cost_totals['win_rate']:.1f}%"},
    ])
    st.markdown("")
    _metric_row([
        {"label": "Total Commission", "value": f"${cost_totals['total_commission']:,.2f}"},
        {"label": "Total Spread Cost", "value": f"${cost_totals['total_spread_cost']:,.2f}"},
        {"label": "Total Slippage Cost", "value": f"${cost_totals['total_slippage_cost']:,.2f}"},
        {"label": "Total Fees", "value": f"${cost_totals['total_fees']:,.2f}"},
    ])

    if not cost_df.empty:
        st.markdown("")
        _show_table(
            cost_df[[
                "market", "symbol",
                "gross_realized_pnl", "realized_pnl", "unrealized_pnl",
                "total_commission", "total_spread_cost", "total_slippage_cost",
                "total_execution_drag",
                "trade_count", "win_count", "loss_count",
            ]],
            height=320,
        )

    # FIX #6: Live eligibility — was defined but never rendered
    st.markdown("#### Live Eligibility")
    live_df = _collect_live_status_rows(agent)
    if not live_df.empty:
        _show_table(
            live_df[[
                "market", "symbol", "mode", "health",
                "live_eligible", "balance",
                "minimum_live_balance", "recommended_balance", "reason",
            ]],
            height=320,
        )
    else:
        st.info("No live status data.")
