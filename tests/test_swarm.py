"""
Tests for arkhe_market_core.swarm — runnable with stdlib unittest:

    python -m unittest tests.test_swarm
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from arkhe_market_core.swarm import (
    SwarmClient,
    SwarmCoordinator,
    apply_local_override,
    calculate_strategy_score,
    generate_anonymous_daily_report,
    save_daily_report,
)
from arkhe_market_core.swarm.daily_report_generator import _load_or_create_node_id
from arkhe_market_core.swarm.privacy_wrapper import privacy_safe, scrub_sensitive


class TestSwarmLogic(unittest.TestCase):
    """The 'critical rule' from the project handoff."""

    def test_local_wins_when_meaningfully_better(self):
        self.assertTrue(apply_local_override(0.80, 0.70))

    def test_local_loses_when_only_marginally_better(self):
        # Margin (0.01) below default threshold (0.05) → defer to global.
        self.assertFalse(apply_local_override(0.71, 0.70))

    def test_global_wins_when_clearly_better(self):
        self.assertFalse(apply_local_override(0.50, 0.90))

    def test_no_global_score_means_local_default(self):
        self.assertTrue(apply_local_override(0.30, None))

    def test_strategy_score_range(self):
        excellent = calculate_strategy_score(
            {"sharpe": 3.0, "win_rate": 0.7, "profit_factor": 3.0, "max_drawdown": 0.05}
        )
        terrible = calculate_strategy_score(
            {"sharpe": -1.5, "win_rate": 0.1, "profit_factor": 0.5, "max_drawdown": 0.4}
        )
        self.assertGreater(excellent, terrible)
        self.assertGreaterEqual(excellent, 0.0)
        self.assertLessEqual(excellent, 1.0)
        self.assertGreaterEqual(terrible, 0.0)
        self.assertLessEqual(terrible, 1.0)


class TestPrivacyWrapper(unittest.TestCase):
    def test_scrub_drops_unallowed_keys(self):
        raw = {
            "report_id": "abc",
            "api_key": "SECRET",
            "balance": 12345.67,
            "total_pnl": 100.0,
        }
        clean = scrub_sensitive(raw)
        self.assertIn("report_id", clean)
        self.assertIn("total_pnl", clean)
        self.assertNotIn("api_key", clean)
        self.assertNotIn("balance", clean)

    def test_scrub_recurses_into_nested_dicts(self):
        raw = {
            "market_summary": {
                "total_pnl": 1.0,
                "secret_field": "leak",
            },
            "balance": 999.0,
        }
        clean = scrub_sensitive(raw)
        self.assertIn("market_summary", clean)
        self.assertIn("total_pnl", clean["market_summary"])
        self.assertNotIn("secret_field", clean["market_summary"])
        self.assertNotIn("balance", clean)

    def test_scrub_walks_lists(self):
        raw = {
            "key_decisions": [
                {"decision_type": "buy", "regime": "bull", "outcome": "win", "secret": "x"},
                {"decision_type": "sell", "regime": "bear", "outcome": "loss"},
            ]
        }
        clean = scrub_sensitive(raw)
        self.assertEqual(len(clean["key_decisions"]), 2)
        self.assertNotIn("secret", clean["key_decisions"][0])
        self.assertEqual(clean["key_decisions"][0]["decision_type"], "buy")

    def test_decorator_scrubs_dict_return(self):
        @privacy_safe()
        def make_report():
            return {"report_id": "x", "api_key": "SECRET", "total_pnl": 10.0}

        self.assertEqual(make_report(), {"report_id": "x", "total_pnl": 10.0})


class TestDailyReportGenerator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_node_id_is_stable_across_calls(self):
        path = self.tmp_path / "node.json"
        first = _load_or_create_node_id(path)
        second = _load_or_create_node_id(path)
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("arkhe_node_"))

    def test_report_has_required_fields_and_no_sensitive_data(self):
        path = self.tmp_path / "node.json"
        report = generate_anonymous_daily_report(
            portfolio_state={"positions": ["BTC-USD", "ETH-USD"]},
            performance={
                "total_pnl": 50.0,
                "sharpe": 1.5,
                "win_rate": 0.55,
                "profit_factor": 1.8,
                "max_drawdown": 0.04,
                "trade_count": 12,
                # Sensitive — should be scrubbed:
                "api_key": "should_not_appear",
                "balance": 12345.0,
            },
            decisions=[
                {"decision_type": "buy", "regime": "bull", "outcome": "win", "symbol": "BTC-USD"},
            ],
            node_id_path=path,
        )
        self.assertIn("schema_version", report)
        self.assertIn("anonymous_node_id", report)
        self.assertIn("market_summary", report)
        self.assertNotIn("api_key", report)
        self.assertNotIn("balance", report)
        # Per-decision scrub: symbol must not survive.
        decisions = report.get("key_decisions", [])
        self.assertEqual(len(decisions), 1)
        self.assertNotIn("symbol", decisions[0])
        self.assertEqual(decisions[0]["decision_type"], "buy")

    def test_save_and_load_roundtrip(self):
        path = self.tmp_path / "node.json"
        out = self.tmp_path / "report.json"
        report = generate_anonymous_daily_report(
            portfolio_state={"positions": []},
            performance={"sharpe": 0.5, "win_rate": 0.5, "profit_factor": 1.2, "max_drawdown": 0.1},
            decisions=[],
            node_id_path=path,
        )
        save_daily_report(report, out)
        on_disk = json.loads(out.read_text())
        self.assertEqual(on_disk["anonymous_node_id"], report["anonymous_node_id"])


class TestSwarmCoordinator(unittest.TestCase):
    def test_no_global_score_uses_local(self):
        c = SwarmCoordinator()
        decision = c.should_use_local_strategy(
            "BTC-USD", {"sharpe": 0.5, "win_rate": 0.5, "profit_factor": 1.0, "max_drawdown": 0.1}
        )
        self.assertTrue(decision)

    def test_local_beats_global_when_threshold_exceeded(self):
        c = SwarmCoordinator(override_threshold=0.05)
        c.update_global_consensus("BTC-USD", 0.20)
        decision = c.should_use_local_strategy(
            "BTC-USD",
            {"sharpe": 3.0, "win_rate": 0.8, "profit_factor": 3.0, "max_drawdown": 0.02},
        )
        self.assertTrue(decision)

    def test_global_wins_when_local_score_low(self):
        c = SwarmCoordinator()
        c.update_global_consensus("BTC-USD", 0.95)
        decision = c.should_use_local_strategy(
            "BTC-USD",
            {"sharpe": -1.0, "win_rate": 0.2, "profit_factor": 0.5, "max_drawdown": 0.4},
        )
        self.assertFalse(decision)


class TestSwarmClient(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.report_path = self.tmp_path / "report.json"
        self.node_path = self.tmp_path / "node.json"
        # Ensure ARKHE_SWARM_OPT_IN doesn't bleed in from the shell.
        self._old_env = os.environ.pop("ARKHE_SWARM_OPT_IN", None)

    def tearDown(self):
        if self._old_env is not None:
            os.environ["ARKHE_SWARM_OPT_IN"] = self._old_env
        self.tmp.cleanup()

    def test_send_writes_report_locally_when_opt_out(self):
        client = SwarmClient(opt_in=False, report_path=self.report_path)
        report = client.send(
            portfolio_state={"positions": []},
            performance={"sharpe": 1.0, "win_rate": 0.5, "profit_factor": 1.5, "max_drawdown": 0.05},
            decisions=[],
        )
        self.assertTrue(self.report_path.exists())
        on_disk = json.loads(self.report_path.read_text())
        self.assertEqual(on_disk["anonymous_node_id"], report["anonymous_node_id"])

    def test_env_var_drives_opt_in_default(self):
        os.environ["ARKHE_SWARM_OPT_IN"] = "1"
        client = SwarmClient(report_path=self.report_path)
        self.assertTrue(client.opt_in)
        os.environ["ARKHE_SWARM_OPT_IN"] = "0"
        client_off = SwarmClient(report_path=self.report_path)
        self.assertFalse(client_off.opt_in)


if __name__ == "__main__":
    unittest.main()
