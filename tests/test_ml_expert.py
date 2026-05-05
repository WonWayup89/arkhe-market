"""
Tests for arkhe_market_core.ml — runnable with stdlib unittest:

    python -m unittest tests.test_ml_expert
"""

import unittest

import numpy as np
import pandas as pd

from arkhe_market_core.ml.data_preprocessor import DataPreprocessor
from arkhe_market_core.ml.feature_engineer import FeatureEngineer, FEATURE_PREFIX
from arkhe_market_core.ml.ml_expert_agent import MLExpertAgent, MIN_BARS


def _make_ohlcv(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """Synthetic OHLCV with a slight upward drift."""
    rng = np.random.default_rng(seed)
    # Geometric brownian-ish walk.
    returns = rng.normal(0.0008, 0.012, size=n)
    close = 100.0 * np.exp(np.cumsum(returns))
    high = close * (1.0 + np.abs(rng.normal(0, 0.003, size=n)))
    low = close * (1.0 - np.abs(rng.normal(0, 0.003, size=n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    volume = rng.integers(1_000, 10_000, size=n).astype(float)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume})


class TestFeatureEngineer(unittest.TestCase):
    def test_adds_prefixed_columns(self):
        df = _make_ohlcv(120)
        feats = FeatureEngineer().populate_features(df)
        feat_cols = FeatureEngineer.feature_columns(feats)
        self.assertGreater(len(feat_cols), 5)
        for c in feat_cols:
            self.assertTrue(c.startswith(FEATURE_PREFIX))
        # Sanity: didn't drop the original close column.
        self.assertIn("close", feats.columns)

    def test_does_not_mutate_input(self):
        df = _make_ohlcv(120)
        df_before = df.copy()
        FeatureEngineer().populate_features(df)
        pd.testing.assert_frame_equal(df, df_before)

    def test_rsi_in_expected_range(self):
        df = _make_ohlcv(200)
        feats = FeatureEngineer().populate_features(df)
        rsi = feats["%-rsi-14"].dropna()
        self.assertTrue((rsi >= 0).all())
        self.assertTrue((rsi <= 100).all())

    def test_volume_optional(self):
        df = _make_ohlcv(120).drop(columns=["volume"])
        feats = FeatureEngineer().populate_features(df)
        # No volume → no vol_ratio columns.
        self.assertEqual([c for c in feats.columns if "vol_ratio" in c], [])

    def test_requires_close(self):
        bad = pd.DataFrame({"open": [1, 2, 3]})
        with self.assertRaises(ValueError):
            FeatureEngineer().populate_features(bad)


class TestDataPreprocessor(unittest.TestCase):
    def test_replaces_inf_with_nan_and_ffills(self):
        df = pd.DataFrame({"a": [1.0, 2.0, np.inf, 4.0], "b": [10.0, np.nan, 30.0, 40.0]})
        out = DataPreprocessor(z_threshold=None).clean_data(df)
        self.assertFalse(np.isinf(out.to_numpy()).any())
        # The NaN in column b should be forward-filled (10.0).
        self.assertEqual(out.iloc[1]["b"], 10.0)

    def test_outlier_removal_drops_extreme_rows(self):
        # Build a frame where one row is a 20-sigma outlier.
        normal = np.random.default_rng(0).normal(0, 1, size=100)
        normal[50] = 20.0
        df = pd.DataFrame({"x": normal})
        out = DataPreprocessor(z_threshold=4.0).clean_data(df)
        self.assertEqual(len(out), len(df) - 1)

    def test_constant_column_does_not_drop_rows(self):
        df = pd.DataFrame({"x": [1.0] * 50, "y": np.linspace(0, 1, 50)})
        out = DataPreprocessor(z_threshold=4.0).clean_data(df)
        self.assertEqual(len(out), 50)


class TestMLExpertAgent(unittest.TestCase):
    def test_insufficient_data_path(self):
        agent = MLExpertAgent(model_path=None)
        result = agent.analyze(_make_ohlcv(MIN_BARS - 1))
        self.assertIsNone(result["signal"])
        self.assertEqual(result["mode"], "insufficient_data")
        self.assertEqual(result["reason"], "insufficient_data")

    def test_heuristic_returns_valid_shape(self):
        agent = MLExpertAgent(model_path=None)
        result = agent.analyze(_make_ohlcv(120))
        self.assertIn(result["signal"], {None, "buy", "sell"})
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)
        self.assertGreaterEqual(result["prediction"], -1.0)
        self.assertLessEqual(result["prediction"], 1.0)
        self.assertEqual(result["mode"], "heuristic")
        self.assertIsInstance(result["reason"], str)

    def test_heuristic_reacts_to_strong_uptrend(self):
        # Strongly trending up data → positive prediction (signal may or may
        # not fire depending on confidence threshold).
        rng = np.random.default_rng(1)
        n = 200
        close = np.linspace(100.0, 200.0, n) + rng.normal(0, 0.5, n)
        df = pd.DataFrame(
            {"open": close, "high": close * 1.001, "low": close * 0.999,
             "close": close, "volume": rng.integers(1000, 5000, n).astype(float)}
        )
        agent = MLExpertAgent(model_path=None)
        result = agent.analyze(df)
        self.assertGreater(result["prediction"], 0)

    def test_no_model_falls_back_quietly(self):
        # Pointing at a bogus model path must not raise.
        agent = MLExpertAgent(model_path="/no/such/file.pkl")
        result = agent.analyze(_make_ohlcv(120))
        self.assertEqual(result["mode"], "heuristic")


if __name__ == "__main__":
    unittest.main()
