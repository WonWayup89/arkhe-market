from typing import Dict


DEFAULT_TEST_BALANCES = {
    "crypto": 5000.0,
    "stocks": 5000.0,
    "futures": 5000.0,
}


def ensure_balance_state(session_state):
    if "test_balances" not in session_state:
        session_state.test_balances = DEFAULT_TEST_BALANCES.copy()
    if "live_balances" not in session_state:
        session_state.live_balances = {
            "crypto": {"equity": 0.0, "cash": 0.0, "connected": False, "source": "test"},
            "stocks": {"equity": 0.0, "cash": 0.0, "connected": False, "source": "test"},
            "futures": {"equity": 0.0, "cash": 0.0, "connected": False, "source": "test"},
        }


def seed_test_balances(session_state, crypto=5000.0, stocks=5000.0, futures=5000.0):
    ensure_balance_state(session_state)
    session_state.test_balances = {
        "crypto": float(crypto),
        "stocks": float(stocks),
        "futures": float(futures),
    }


def reset_test_balances(session_state):
    seed_test_balances(session_state)


def update_live_market_balance(session_state, market: str, equity: float, cash: float, source: str = "live"):
    ensure_balance_state(session_state)
    session_state.live_balances[market] = {
        "equity": float(equity),
        "cash": float(cash),
        "connected": True,
        "source": source,
    }


def clear_live_market_balance(session_state, market: str):
    ensure_balance_state(session_state)
    session_state.live_balances[market] = {
        "equity": 0.0,
        "cash": 0.0,
        "connected": False,
        "source": "test",
    }


def resolve_market_mode(session_state, market: str) -> str:
    ensure_balance_state(session_state)
    live = session_state.live_balances.get(market, {})
    if live.get("connected") and float(live.get("equity", 0.0)) > 0:
        return "live"
    return "test"


def resolve_market_balance(session_state, market: str) -> Dict[str, float]:
    ensure_balance_state(session_state)
    mode = resolve_market_mode(session_state, market)
    if mode == "live":
        live = session_state.live_balances[market]
        return {
            "mode": "live",
            "equity": float(live.get("equity", 0.0)),
            "cash": float(live.get("cash", 0.0)),
            "source": live.get("source", "live"),
        }
    test_value = float(session_state.test_balances.get(market, 0.0))
    return {
        "mode": "test",
        "equity": test_value,
        "cash": test_value,
        "source": "test",
    }


def resolve_all_balances(session_state):
    return {
        "crypto": resolve_market_balance(session_state, "crypto"),
        "stocks": resolve_market_balance(session_state, "stocks"),
        "futures": resolve_market_balance(session_state, "futures"),
    }
