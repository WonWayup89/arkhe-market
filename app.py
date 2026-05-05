import time
import streamlit as st
from arkhe_market_core.ml.features.feature_logger import log_market_state

from brokers.broker_session_manager import BrokerSessionManager
from arkhe_market_core.multi_portfolio_agent import MultiPortfolioAgent
from arkhe_market_core.promotion_supervisor import PromotionSupervisor
from services.account_mode_resolver import (
    ensure_balance_state,
    resolve_all_balances,
)
from arkhe_market_core.ml.inference.model_service import score_features
from arkhe_market_core.ml.inference.neural_stats import init_neural_stats
from ui.layout import render_shell
from ui.theme import inject_theme
from views.command_center import render_command_center
from services.command_center_pipeline import ensure_command_center_state, log_market_outputs
from views.crypto import render_crypto
from views.futures import render_futures
from views.promotion_dashboard import render_promotion_dashboard
from views.settings import render_settings
from views.stocks import render_stocks

DEFAULT_STABLE = ["BTC-USD", "ETH-USD"]
DEFAULT_ALT = ["SOL-USD", "XRP-USD", "AVAX-USD", "SUI-USD"]
DEFAULT_STOCKS = ["MSFT", "NVDA", "AAPL", "AMZN", "META", "GOOGL", "TSLA", "JPM"]
DEFAULT_FUTURES = ["ES", "NQ", "RTY", "YM", "CL", "NG"]


def build_agent(config):
    return MultiPortfolioAgent(
        total_balance=config["crypto_balance"],
        stock_balance=config["stock_balance"],
        futures_balance=config["futures_balance"],
        stable_allocation=config["stable_allocation"],
        stable_symbols=config["stable_symbols"],
        alt_symbols=config["alt_symbols"],
        stock_symbols=config["stock_symbols"],
        futures_symbols=config["futures_symbols"],
        risk_pct_stable=config["risk_pct_stable"],
        risk_pct_alt=config["risk_pct_alt"],
        timeframe=config["timeframe"],
        history_limit=config["history_limit"],
        daily_drawdown_limit=config["daily_drawdown_limit"],
        test_mode=config["test_mode"],
        cooldown_seconds=config["cooldown_seconds"],
    )


def main():
    st.set_page_config(page_title="Arkhe Market V4", layout="wide")
    init_neural_stats()
    inject_theme()
    ensure_command_center_state()
    ensure_balance_state(st.session_state)

    if "broker_manager" not in st.session_state:
        st.session_state.broker_manager = BrokerSessionManager()

    if "promo_supervisor" not in st.session_state:
        st.session_state.promo_supervisor = PromotionSupervisor()

    with st.sidebar:
        st.markdown("### Global navigation and system controls")
        run_all = st.button("Run All Markets", width="stretch", key="run_all_markets_global")
        test_mode = st.checkbox("Test Mode", value=True)
        auto_loop = st.checkbox("Auto Loop", value=st.session_state.get("auto_loop", False))
        loop_seconds = st.slider("Loop Interval (sec)", 5, 300, int(st.session_state.get("loop_seconds", 30)), 5)
        st.session_state.auto_loop = auto_loop
        st.session_state.loop_seconds = loop_seconds
        daily_drawdown_limit = st.slider("Daily Drawdown %", 1.0, 20.0, 4.0, 0.5) / 100.0
        cooldown_seconds = st.slider("Global Cooldown", 0, 3600, 900, 60)
        st.session_state.entry_gate_threshold = st.number_input("Entry Gate Threshold", min_value=0.0, max_value=1.0, value=float(st.session_state.get("entry_gate_threshold", 0.75)), step=0.05)
        st.session_state.exit_gate_threshold = st.number_input("Exit Gate Threshold", min_value=0.0, value=float(st.session_state.get("exit_gate_threshold", 0.25)), step=0.05)
        st.markdown("### Neural Controls")
        st.caption(f"Entry threshold: {st.session_state.entry_gate_threshold}")
        st.caption(f"Exit threshold: {st.session_state.exit_gate_threshold}")
        st.caption(f"Entry blocks: {st.session_state.get('neural_blocks_entry', 0)}")
        st.caption(f"Exit blocks: {st.session_state.get('neural_blocks_exit', 0)}")

    balances = resolve_all_balances(st.session_state)

    neural_features = {
        "feature_equity_crypto_cash": balances["crypto"]["cash"],
        "feature_equity_crypto_equity": balances["crypto"]["equity"],
        "feature_equity_futures_cash": balances["futures"]["cash"],
        "feature_equity_futures_equity": balances["futures"]["equity"],
        "feature_equity_stocks_cash": balances["stocks"]["cash"],
        "feature_equity_stocks_equity": balances["stocks"]["equity"],
        "feature_ok": 1,
        "feature_price": 1,
        "feature_volatility": 0.1,
    }
    neural_score = score_features(neural_features)
    st.session_state.neural_score = neural_score

    # Neural logging
    try:
        log_market_state("SYSTEM", "global", {"equity": balances}, {"mode": "test"})
    except Exception as e:
        print(e)


    config = {
        "crypto_balance": balances["crypto"]["equity"],
        "stock_balance": balances["stocks"]["equity"],
        "futures_balance": balances["futures"]["equity"],
        "stable_allocation": 0.70,
        "stable_symbols": st.session_state.get("stable_symbols", DEFAULT_STABLE),
        "alt_symbols": st.session_state.get("alt_symbols", DEFAULT_ALT),
        "stock_symbols": st.session_state.get("stock_symbols", DEFAULT_STOCKS),
        "futures_symbols": st.session_state.get("futures_symbols", DEFAULT_FUTURES),
        "risk_pct_stable": st.session_state.get("risk_pct_stable", 0.01),
        "risk_pct_alt": st.session_state.get("risk_pct_alt", 0.015),
        "timeframe": st.session_state.get("timeframe", 3600),
        "history_limit": st.session_state.get("history_limit", 200),
        "daily_drawdown_limit": daily_drawdown_limit,
        "cooldown_seconds": cooldown_seconds,
        "test_mode": test_mode,
    }

    sig = tuple(
        (
            config["crypto_balance"],
            config["stock_balance"],
            config["futures_balance"],
            config["stable_allocation"],
            tuple(config["stable_symbols"]),
            tuple(config["alt_symbols"]),
            tuple(config["stock_symbols"]),
            tuple(config["futures_symbols"]),
            config["risk_pct_stable"],
            config["risk_pct_alt"],
            config["timeframe"],
            config["history_limit"],
            config["daily_drawdown_limit"],
            config["test_mode"],
            config["cooldown_seconds"],
        )
    )

    if "multi_agent" not in st.session_state or st.session_state.get("config_sig") != sig:
        st.session_state.multi_agent = build_agent(config)
        st.session_state.config_sig = sig

    multi_agent = st.session_state.multi_agent
    broker_manager = st.session_state.broker_manager

    now_ts = time.time()
    if "last_loop_ts" not in st.session_state:
        st.session_state.last_loop_ts = 0.0

    loop_due = (
        st.session_state.get("auto_loop", False)
        and (now_ts - float(st.session_state.get("last_loop_ts", 0.0))) >= float(st.session_state.get("loop_seconds", 30))
    )

    if run_all or loop_due:
        crypto_out = multi_agent.run_once_crypto()
        stocks_out = multi_agent.run_once_stocks()
        futures_out = multi_agent.run_once_futures()

        st.session_state.crypto_signals = crypto_out
        st.session_state.stock_signals = stocks_out
        st.session_state.futures_signals = futures_out
        st.session_state.last_outputs = {
            "crypto": crypto_out,
            "stocks": stocks_out,
            "futures": futures_out,
        }
        st.session_state.last_loop_ts = now_ts

        log_market_outputs("crypto", [str(x) for x in crypto_out] if isinstance(crypto_out, list) else [str(crypto_out)])
        log_market_outputs("stocks", [str(x) for x in stocks_out] if isinstance(stocks_out, list) else [str(stocks_out)])
        log_market_outputs("futures", [str(x) for x in futures_out] if isinstance(futures_out, list) else [str(futures_out)])

    tabs = render_shell()
    with tabs[0]:
        render_command_center(multi_agent, config, broker_manager)
        if st.session_state.get("neural_score") is not None:
            st.metric("Neural Score", f"{st.session_state.neural_score:.4f}")
    with tabs[1]:
        render_crypto(multi_agent, config, broker_manager)
    with tabs[2]:
        render_stocks(multi_agent, config, broker_manager)
    with tabs[3]:
        render_futures(multi_agent, config, broker_manager)
    with tabs[4]:
        all_syms = config["stable_symbols"] + config["alt_symbols"] + config["stock_symbols"] + config["futures_symbols"]
        starting_equities = {}
        crypto_stable_each = (config["crypto_balance"] * config["stable_allocation"]) / max(len(config["stable_symbols"]), 1)
        crypto_alt_each = (config["crypto_balance"] * (1 - config["stable_allocation"])) / max(len(config["alt_symbols"]), 1)
        stock_each = config["stock_balance"] / max(len(config["stock_symbols"]), 1)
        futures_each = config["futures_balance"] / max(len(config["futures_symbols"]), 1)
        for s in config["stable_symbols"]:
            starting_equities[s] = crypto_stable_each
        for s in config["alt_symbols"]:
            starting_equities[s] = crypto_alt_each
        for s in config["stock_symbols"]:
            starting_equities[s] = stock_each
        for s in config["futures_symbols"]:
            starting_equities[s] = futures_each
        render_promotion_dashboard(st.session_state.promo_supervisor, multi_agent, all_syms, starting_equities)
    with tabs[5]:
        render_settings()

if __name__ == "__main__":
    main()
    if st.session_state.get("auto_loop", False):
        time.sleep(1)
        st.rerun()
