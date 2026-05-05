"""
Integration smoke tests for the swarm + ML wiring.

Verifies that:
- the new modules import cleanly alongside the existing core
- MultiPortfolioAgent constructs with empty symbol lists (no network)
- compute_local_metrics() and generate_swarm_report() run without crashing
- SupervisorAgent honors a passed-in MLExpertAgent and includes its
  result in run_experts() output

These avoid the data feed by either using empty symbols or feeding a
synthetic OHLCV frame directly into run_experts().
"""

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

# Project root must be on the path for `cooldown_store`, `services.*` etc.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _has(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


# The existing supervisor_agent → ml.inference.model_service pulls in joblib.
# Skip integration tests that import that chain when joblib isn't available
# (e.g., a clean CI sandbox). The pure-swarm and pure-ML tests in the
# sibling test files don't depend on it and run everywhere.
HAS_SUPERVISOR_DEPS = _has("joblib")
SKIP_REASON = "joblib not installed; supervisor_agent import chain requires it"


def _synthetic_ohlcv(n: int = 150) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    rets = rng.normal(0.0006, 0.01, size=n)
    close = 100.0 * np.exp(np.cumsum(rets))
    high = close * 1.002
    low = close * 0.998
    open_ = np.concatenate([[close[0]], close[:-1]])
    volume = rng.integers(1_000, 5_000, size=n).astype(float)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume})


@unittest.skipUnless(HAS_SUPERVISOR_DEPS, SKIP_REASON)
class TestMultiPortfolioWiring(unittest.TestCase):
    """Construct a MultiPortfolioAgent with no symbols → no network calls."""

    def setUp(self):
        # Sandbox state/log dirs so the test doesn't pollute real ones.
        self.tmp = tempfile.TemporaryDirectory()
        self._cwd = os.getcwd()
        os.chdir(self.tmp.name)
        # Force opt-out so SwarmClient never tries to dispatch.
        self._old_env = os.environ.pop("ARKHE_SWARM_OPT_IN", None)

    def tearDown(self):
        os.chdir(self._cwd)
        if self._old_env is not None:
            os.environ["ARKHE_SWARM_OPT_IN"] = self._old_env
        self.tmp.cleanup()

    def test_construct_with_empty_symbols(self):
        from arkhe_market_core.multi_portfolio_agent import MultiPortfolioAgent

        agent = MultiPortfolioAgent(
            total_balance=1000.0,
            stable_symbols=[],
            alt_symbols=[],
            stock_symbols=[],
            futures_symbols=[],
            stock_balance=0.0,
            futures_balance=0.0,
            test_mode=True,
            enable_ml_advisor=True,
            swarm_opt_in=False,
        )
        # Swarm + ML wiring is present.
        self.assertIsNotNone(agent.swarm_coordinator)
        self.assertIsNotNone(agent.swarm_client)
        self.assertFalse(agent.swarm_client.opt_in)
        self.assertIsNotNone(agent._shared_ml_expert)
        # No agents because no symbols.
        self.assertEqual(agent.agents, {})

    def test_compute_local_metrics_empty_portfolio(self):
        from arkhe_market_core.multi_portfolio_agent import MultiPortfolioAgent

        agent = MultiPortfolioAgent(
            total_balance=1000.0,
            stable_symbols=[],
            alt_symbols=[],
            stock_symbols=[],
            futures_symbols=[],
            test_mode=True,
            enable_ml_advisor=False,
            swarm_opt_in=False,
        )
        metrics = agent.compute_local_metrics()
        for key in ("sharpe", "win_rate", "profit_factor", "max_drawdown", "trade_count", "total_pnl", "local_strategy_score"):
            self.assertIn(key, metrics)
        # Empty portfolio: no trades → score is bounded.
        self.assertGreaterEqual(metrics["local_strategy_score"], 0.0)
        self.assertLessEqual(metrics["local_strategy_score"], 1.0)

    def test_generate_swarm_report_runs_and_writes(self):
        from arkhe_market_core.multi_portfolio_agent import MultiPortfolioAgent

        agent = MultiPortfolioAgent(
            total_balance=1000.0,
            stable_symbols=[],
            alt_symbols=[],
            stock_symbols=[],
            futures_symbols=[],
            test_mode=True,
            enable_ml_advisor=False,
            swarm_opt_in=False,
        )
        report = agent.generate_swarm_report()
        self.assertIn("anonymous_node_id", report)
        self.assertIn("market_summary", report)
        # Default report path lands under cwd/logs/.
        expected = Path("logs") / "daily_swarm_report.json"
        self.assertTrue(expected.exists())


@unittest.skipUnless(HAS_SUPERVISOR_DEPS, SKIP_REASON)
class TestSupervisorMLWiring(unittest.TestCase):
    """SupervisorAgent should run the MLExpert when one is provided."""

    def test_run_experts_includes_ml_when_advisor_is_provided(self):
        # Heavy import inside the test so module-load failures show up here.
        from arkhe_market_core.ml.ml_expert_agent import MLExpertAgent
        from arkhe_market_core.supervisor_agent import SupervisorAgent

        df = _synthetic_ohlcv(150)

        # Build a real supervisor but stub out network/persistence pieces
        # by using empty test_mode paths inside a tmp dir.
        tmp = tempfile.TemporaryDirectory()
        try:
            os.makedirs(os.path.join(tmp.name, "states"), exist_ok=True)
            os.makedirs(os.path.join(tmp.name, "logs"), exist_ok=True)
            cwd = os.getcwd()
            os.chdir(tmp.name)
            try:
                agent = SupervisorAgent(
                    symbol="TEST",
                    market_type="stable",
                    asset_class="crypto",
                    starting_balance=1000.0,
                    test_mode=True,
                    state_path="states/test.json",
                    log_path="logs/test.csv",
                    ml_expert=MLExpertAgent(model_path=None),
                )
                panel = agent.run_experts(df)
            finally:
                os.chdir(cwd)
        finally:
            tmp.cleanup()

        self.assertIn("ml", panel)
        ml = panel["ml"]
        self.assertIsNotNone(ml)
        self.assertIn("signal", ml)
        self.assertIn("mode", ml)
        self.assertIn(ml["mode"], {"heuristic", "model", "insufficient_data"})

    def test_run_experts_ml_is_none_when_no_advisor(self):
        from arkhe_market_core.supervisor_agent import SupervisorAgent

        df = _synthetic_ohlcv(150)

        tmp = tempfile.TemporaryDirectory()
        try:
            cwd = os.getcwd()
            os.chdir(tmp.name)
            os.makedirs("states", exist_ok=True)
            os.makedirs("logs", exist_ok=True)
            try:
                agent = SupervisorAgent(
                    symbol="TEST",
                    market_type="stable",
                    asset_class="crypto",
                    starting_balance=1000.0,
                    test_mode=True,
                    state_path="states/test.json",
                    log_path="logs/test.csv",
                )
                panel = agent.run_experts(df)
            finally:
                os.chdir(cwd)
        finally:
            tmp.cleanup()

        # When no advisor is wired, the key is still present but None —
        # callers that rely on the shape don't have to special-case.
        self.assertIn("ml", panel)
        self.assertIsNone(panel["ml"])


if __name__ == "__main__":
    unittest.main()
