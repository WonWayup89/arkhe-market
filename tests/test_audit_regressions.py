"""
tests/test_audit_regressions.py

Regression tests for the nine findings in the trading-platform audit.
Each test is named after the finding it locks in. Run with:

    pytest -q tests/test_audit_regressions.py

Tests #1–#7 are designed so they could be run in a process where
streamlit is NOT installed (the engine path must stay headless).
Tests #8 and #9 are pure-Python and don't touch any UI either.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from datetime import date, datetime, time, timezone
from pathlib import Path

import pytest


# Make the project importable when pytest is invoked from anywhere.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


# ────────────────────────────────────────────────────────────────────
# Finding #1 — ML gate must fail-OPEN when no score is available.
# ────────────────────────────────────────────────────────────────────
def test_neural_gate_fail_open_when_no_score():
    from arkhe_market_core.ml.inference.neural_gate import evaluate_gate
    from arkhe_market_core.ml.config import GATE_CONFIG

    GATE_CONFIG["fail_open_when_no_model"] = True

    res = evaluate_gate(None, mode="entry")
    assert res["allow"] is True
    assert res["gate"] == "unknown"
    assert res["reason"] == "no_score_fail_open"


def test_neural_gate_fail_closed_when_configured():
    from arkhe_market_core.ml.inference.neural_gate import evaluate_gate
    from arkhe_market_core.ml.config import GATE_CONFIG

    prior = GATE_CONFIG.get("fail_open_when_no_model", True)
    GATE_CONFIG["fail_open_when_no_model"] = False
    try:
        res = evaluate_gate(None, mode="entry")
        assert res["allow"] is False
        assert res["reason"] == "no_score_fail_closed"
    finally:
        GATE_CONFIG["fail_open_when_no_model"] = prior


def test_neural_gate_threshold_semantics():
    from arkhe_market_core.ml.inference.neural_gate import evaluate_gate
    from arkhe_market_core.ml.config import GATE_CONFIG

    GATE_CONFIG["entry_threshold"] = 0.75
    GATE_CONFIG["exit_threshold"]  = 0.25

    assert evaluate_gate(0.9, "entry")["allow"] is True
    assert evaluate_gate(0.1, "entry")["allow"] is False
    # Lower threshold for exits.
    assert evaluate_gate(0.30, "exit")["allow"] is True
    assert evaluate_gate(0.10, "exit")["allow"] is False


# ────────────────────────────────────────────────────────────────────
# Finding #2 — Engine path must import without streamlit.
# ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "module",
    [
        "arkhe_market_core.supervisor_agent",
        "arkhe_market_core.multi_portfolio_agent",
        "arkhe_market_core.ml.inference.neural_gate",
        "arkhe_market_core.ml.inference.neural_decision",
        "arkhe_market_core.ml.inference.neural_stats",
        "arkhe_market_core.ml.inference.model_service",
        "services.live_market_resolver",
        "services.market_controls",
        "services.atomic_io",
        "services.market_calendar",
    ],
)
def test_engine_modules_have_no_streamlit_import(module: str):
    """
    Spawn a subprocess with PYTHONPATH set so it can find the project,
    but with streamlit shadowed by an import-time hook so the import
    fails noisily if anything in the chain reaches for it.
    """
    code = (
        "import sys\n"
        "class _Stub:\n"
        "    def find_module(self, name, path=None):\n"
        "        if name == 'streamlit' or name.startswith('streamlit.'):\n"
        "            raise ImportError('streamlit is forbidden in engine path')\n"
        "        return None\n"
        "sys.meta_path.insert(0, _Stub())\n"
        f"import {module}\n"
        "print('OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
        timeout=30,
    )
    assert result.returncode == 0, (
        f"importing {module} failed:\nSTDOUT:{result.stdout}\nSTDERR:{result.stderr}"
    )
    assert "OK" in result.stdout


# ────────────────────────────────────────────────────────────────────
# Finding #3 — `stocks` and `stock` must resolve identically.
# ────────────────────────────────────────────────────────────────────
def test_stocks_and_stock_keys_resolve_identically():
    from services.live_market_resolver import live_market_status

    a = live_market_status("stocks", connected=True, balance=3000.0)
    b = live_market_status("stock",  connected=True, balance=3000.0)

    for field in ("minimum_live_balance", "recommended_balance", "live_eligible", "health"):
        assert a[field] == b[field], f"{field} mismatch: {a[field]} vs {b[field]}"

    assert a["minimum_live_balance"] == 2500.0


def test_underfunded_stock_account_is_not_live_eligible():
    from services.live_market_resolver import live_market_status

    res = live_market_status("stock", connected=True, balance=100.0)
    assert res["live_eligible"] is False
    assert res["reason"] == "under_minimum"


# ────────────────────────────────────────────────────────────────────
# Finding #4 — Empty symbol lists must NOT be replaced with defaults.
# ────────────────────────────────────────────────────────────────────
def test_empty_symbol_lists_are_honored():
    from arkhe_market_core.multi_portfolio_agent import MultiPortfolioAgent

    mpa = MultiPortfolioAgent(
        stable_symbols=[],
        alt_symbols=[],
        stock_symbols=[],
        futures_symbols=[],
    )
    assert mpa.stable_symbols  == []
    assert mpa.alt_symbols     == []
    assert mpa.stock_symbols   == []
    assert mpa.futures_symbols == []
    # And no SupervisorAgent instances were built.
    assert mpa.agents == {}


def test_default_symbol_lists_when_none_passed():
    from arkhe_market_core.multi_portfolio_agent import MultiPortfolioAgent

    mpa = MultiPortfolioAgent()
    assert mpa.stable_symbols == ["BTC-USD", "ETH-USD"]
    assert mpa.alt_symbols    == ["SOL-USD", "XRP-USD", "AVAX-USD", "SUI-USD"]


# ────────────────────────────────────────────────────────────────────
# Finding #5 — One canonical model path; both subsystems use it.
# ────────────────────────────────────────────────────────────────────
def test_model_path_is_unified():
    from arkhe_market_core.ml import config

    p = config.model_path()
    # Path must live under the project tree, not under cwd-relative "ml/".
    assert "arkhe_market_core" in str(p)
    assert p.name in {"arkhe_market_model.pkl", "amber_model.pkl"}


def test_score_features_and_ml_expert_share_one_path(monkeypatch, tmp_path):
    """
    Override ARKHE_MODEL_PATH and confirm both the inference service and
    the ML expert agent honor it.
    """
    from arkhe_market_core.ml import config
    from arkhe_market_core.ml.inference import model_service
    from arkhe_market_core.ml.ml_expert_agent import MLExpertAgent

    fake = tmp_path / "fake_model.pkl"
    monkeypatch.setenv("ARKHE_MODEL_PATH", str(fake))

    assert config.model_path() == fake

    # Reset cached state so the new path takes effect.
    model_service.reset_cache()
    m, s, fc = model_service.load_model()
    assert m is None and s is None and fc is None  # no model on disk

    # MLExpertAgent should also pick up the same path.
    expert = MLExpertAgent()
    assert expert.model_path == fake


# ────────────────────────────────────────────────────────────────────
# Finding #6 — Runnable scripts/utilities must import cleanly.
# ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("module", ["run_loop", "data.live_quotes"])
def test_runnable_scripts_import(module: str):
    import importlib

    importlib.import_module(module)


# ────────────────────────────────────────────────────────────────────
# Finding #7 — Drawdown gate must see fresh equity, not stale.
# ────────────────────────────────────────────────────────────────────
def test_supervisor_marks_to_market_before_drawdown_gate():
    from arkhe_market_core.supervisor_agent import SupervisorAgent

    sa = SupervisorAgent.__new__(SupervisorAgent)  # don't run __init__
    # Stub out the moving parts.
    calls: list[str] = []

    class _Risk:
        def __init__(self):
            self.equity = 0.0
        def reset_daily_balance(self): calls.append("reset")
        def exceeded_drawdown(self):
            calls.append(f"check_dd@{self.equity}")
            return self.equity <= 90.0  # breach
        def update_balance_position(self, snap):
            calls.append("update_balance_position")
            self.equity = float(snap["equity"])

    class _Paper:
        def snapshot(self):
            calls.append("snapshot")
            return {"equity": 80.0, "cash": 80.0, "asset_qty": 0.0}

    class _Exec:
        def __init__(self):
            self.paper = _Paper()
        def mark_price(self, price):
            calls.append(f"mark_price@{price}")

    sa.symbol = "TEST"
    sa.test_mode = True
    sa.execution = _Exec()
    sa.risk = _Risk()
    sa.cooldowns = type("C", (), {"get_last_trade_time": lambda self, s: None})()
    sa.cooldown_seconds = 0
    sa.asset_class = "crypto"
    sa.get_live_price = lambda: 123.45
    sa._live_status = lambda: {"reason": "ok", "live_eligible": True}

    msg = sa.run_once()

    # The mark/update step must run BEFORE the drawdown check.
    assert "mark_price@123.45" in calls
    mark_idx   = calls.index("mark_price@123.45")
    update_idx = calls.index("update_balance_position")
    dd_idx     = next(i for i, c in enumerate(calls) if c.startswith("check_dd"))
    assert mark_idx < update_idx < dd_idx
    # And the drawdown branch fired with the *fresh* equity (80), not 0.
    assert "check_dd@80.0" in calls
    assert "drawdown limit" in msg


# ────────────────────────────────────────────────────────────────────
# Finding #8 — Atomic JSON writes survive partial-failure / concurrency.
# ────────────────────────────────────────────────────────────────────
def test_atomic_write_replaces_target_atomically(tmp_path):
    from services.atomic_io import atomic_write_json

    target = tmp_path / "cooldowns.json"
    atomic_write_json(target, {"BTC-USD": "2026-05-05T00:00:00+00:00"})

    assert target.exists()
    loaded = json.loads(target.read_text())
    assert loaded == {"BTC-USD": "2026-05-05T00:00:00+00:00"}

    # Overwriting should not leave a half-written file even if the dict
    # is bigger.
    atomic_write_json(target, {f"k{i}": i for i in range(500)})
    loaded = json.loads(target.read_text())
    assert len(loaded) == 500


def test_cooldown_store_concurrent_writes_do_not_corrupt(tmp_path):
    """Hammer the store from many threads; the file must always parse."""
    from cooldown_store import CooldownStore

    path = tmp_path / "cooldowns.json"
    store = CooldownStore(path=str(path))

    def worker(symbol: str, n: int):
        for _ in range(n):
            store.set_last_trade_time(symbol, datetime.now(timezone.utc))

    threads = [
        threading.Thread(target=worker, args=(f"SYM{i}", 25))
        for i in range(8)
    ]
    for t in threads: t.start()
    for t in threads: t.join()

    # File must still parse and contain every symbol that was written.
    loaded = json.loads(path.read_text())
    for i in range(8):
        assert f"SYM{i}" in loaded


# ────────────────────────────────────────────────────────────────────
# Finding #9 — Exchange-calendar session checks.
# ────────────────────────────────────────────────────────────────────
def _utc(year, month, day, hour, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def test_crypto_is_always_open():
    from services.market_calendar import is_market_open

    # Sunday 03:00 UTC — middle of nothing.
    assert is_market_open("crypto", now_utc=_utc(2026, 5, 3, 3)) is True
    # Saturday noon UTC.
    assert is_market_open("crypto", now_utc=_utc(2026, 5, 2, 12)) is True


def test_stocks_closed_on_weekends():
    from services.market_calendar import is_market_open

    # Saturday 14:00 UTC = 10:00 ET.
    assert is_market_open("stocks", now_utc=_utc(2026, 5, 2, 14)) is False
    # Sunday 14:00 UTC = 10:00 ET.
    assert is_market_open("stocks", now_utc=_utc(2026, 5, 3, 14)) is False


def test_stocks_open_inside_regular_session_and_closed_outside():
    from services.market_calendar import is_market_open

    # Monday 2026-05-04 — 14:30 UTC = 10:30 EDT (open).
    assert is_market_open("stocks", now_utc=_utc(2026, 5, 4, 14, 30)) is True
    # Same Monday at 21:00 UTC = 17:00 EDT (closed, after 16:00 ET).
    assert is_market_open("stocks", now_utc=_utc(2026, 5, 4, 21, 0)) is False
    # 13:00 UTC = 09:00 EDT (closed, before 09:30 open).
    assert is_market_open("stocks", now_utc=_utc(2026, 5, 4, 13, 0)) is False


def test_stocks_holiday_hook():
    from services.market_calendar import (
        clear_holidays,
        is_market_open,
        register_holidays,
    )

    clear_holidays("stocks")
    monday = _utc(2026, 5, 4, 14, 30)
    assert is_market_open("stocks", now_utc=monday) is True

    register_holidays("stocks", [date(2026, 5, 4)])
    try:
        assert is_market_open("stocks", now_utc=monday) is False
    finally:
        clear_holidays("stocks")


def test_futures_weekend_and_daily_halt():
    from services.market_calendar import is_market_open

    # Saturday is closed all day.
    assert is_market_open("futures", now_utc=_utc(2026, 5, 2, 12)) is False
    # Sunday before 18:00 CT (= 23:00 UTC) is closed.
    assert is_market_open("futures", now_utc=_utc(2026, 5, 3, 22)) is False
    # Sunday 19:00 CT (= 00:00 UTC Mon) reopens.
    assert is_market_open("futures", now_utc=_utc(2026, 5, 4, 0)) is True
    # Tuesday 17:30 CT (= 22:30 UTC) is in the daily halt.
    assert is_market_open("futures", now_utc=_utc(2026, 5, 5, 22, 30)) is False
    # Tuesday 18:30 CT (= 23:30 UTC) is back open after halt.
    assert is_market_open("futures", now_utc=_utc(2026, 5, 5, 23, 30)) is True
    # Friday 17:30 CT (= 22:30 UTC) — closed for the weekend.
    assert is_market_open("futures", now_utc=_utc(2026, 5, 8, 22, 30)) is False
