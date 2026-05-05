"""
ml_expert_agent.py — ML-flavored expert agent with an honest fallback.

Contract matches the existing experts (volatility, regime, sentiment):
    analyze(df) -> {"signal": "buy"|"sell"|None,
                    "confidence": float in [0, 1],
                    "prediction": float,
                    "reason": str,
                    "mode": "model"|"heuristic"|"insufficient_data"}

Behavior:
- If a model file is present at `model_path` AND joblib is importable,
  load the model and use its prediction.
- Otherwise, fall back to a transparent heuristic (multi-period ROC
  consensus). The `mode` field always tells the caller which path ran —
  no pretending a heuristic is a model.

This is intentionally conservative: a placeholder model masquerading as
the real thing is worse than no model at all.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from .data_preprocessor import DataPreprocessor
from .feature_engineer import FeatureEngineer
from arkhe_market_core.ml.config import model_path as _resolve_model_path

logger = logging.getLogger(__name__)


# Sentinel used to distinguish "caller passed nothing" (use canonical path)
# from "caller explicitly passed None" (force heuristic mode).
_USE_DEFAULT_MODEL = object()
MIN_BARS = 60  # need enough history for the longest feature period (55) plus margin


class MLExpertAgent:
    """
    Optional ML expert. Designed to be wired into SupervisorAgent as an
    additional advisor — never as a sole gate.

    Construct with `model_path=None` to force heuristic mode (useful in
    tests). Pass nothing to use the canonical path resolved by
    `arkhe_market_core.ml.config.model_path()`.
    """

    def __init__(
        self,
        model_path: Optional[Path] = _USE_DEFAULT_MODEL,  # type: ignore[assignment]
        confidence_threshold: float = 0.55,
        feature_engineer: Optional[FeatureEngineer] = None,
        preprocessor: Optional[DataPreprocessor] = None,
    ) -> None:
        if model_path is _USE_DEFAULT_MODEL:
            resolved = _resolve_model_path()
            self.model_path: Optional[Path] = resolved
        else:
            self.model_path = Path(model_path) if model_path else None
        self.confidence_threshold = float(confidence_threshold)
        self.feature_engineer = feature_engineer or FeatureEngineer()
        self.preprocessor = preprocessor or DataPreprocessor()
        self.model: Any = None
        self._mode: str = "heuristic"
        self._try_load_model()

    # ── model loading (optional, never raises) ─────────────────────
    def _try_load_model(self) -> None:
        if self.model_path is None or not self.model_path.exists():
            logger.info(
                "MLExpertAgent: no model at %s — using heuristic mode.",
                self.model_path,
            )
            return
        try:
            import joblib  # type: ignore
        except ImportError:
            logger.info("MLExpertAgent: joblib not installed — using heuristic mode.")
            return
        try:
            self.model = joblib.load(self.model_path)
            self._mode = "model"
            logger.info("MLExpertAgent: loaded model from %s", self.model_path)
        except Exception as e:  # noqa: BLE001 — broad on purpose: never crash startup
            logger.warning(
                "MLExpertAgent: failed to load %s (%s) — falling back to heuristic.",
                self.model_path,
                e,
            )

    # ── public api ─────────────────────────────────────────────────
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df is None or len(df) < MIN_BARS:
            return self._empty_result(reason="insufficient_data", mode="insufficient_data")

        try:
            feats = self.feature_engineer.populate_features(df)
            feats = self.preprocessor.clean_data(feats)
        except Exception as e:  # noqa: BLE001
            logger.warning("MLExpertAgent: feature pipeline failed (%s)", e)
            return self._empty_result(reason="feature_pipeline_error", mode=self._mode)

        if feats.empty:
            return self._empty_result(reason="no_clean_features", mode=self._mode)

        if self._mode == "model" and self.model is not None:
            return self._predict_with_model(feats)
        return self._predict_with_heuristic(feats)

    # ── prediction paths ───────────────────────────────────────────
    def _predict_with_model(self, feats: pd.DataFrame) -> Dict[str, Any]:
        feature_cols = self.feature_engineer.feature_columns(feats)
        if not feature_cols:
            return self._empty_result(reason="no_features", mode="model")

        latest_row = feats[feature_cols].iloc[[-1]].to_numpy(dtype=float)
        try:
            # Many sklearn-style models expose predict_proba; fall back to predict.
            proba = getattr(self.model, "predict_proba", None)
            if callable(proba):
                p = proba(latest_row)[0]
                # Assume binary {0=down, 1=up} unless the model specifies otherwise.
                up = float(p[-1])
                prediction = (up - 0.5) * 2.0  # → [-1, 1]
                confidence = float(abs(prediction))
            else:
                pred = float(self.model.predict(latest_row)[0])
                prediction = float(np.clip(pred, -1.0, 1.0))
                confidence = float(abs(prediction))
        except Exception as e:  # noqa: BLE001
            logger.warning("MLExpertAgent: model.predict failed (%s) — heuristic fallback.", e)
            return self._predict_with_heuristic(feats)

        signal = self._signal_from_score(prediction, confidence)
        return {
            "signal": signal,
            "confidence": confidence,
            "prediction": prediction,
            "reason": "ml_model",
            "mode": "model",
        }

    def _predict_with_heuristic(self, feats: pd.DataFrame) -> Dict[str, Any]:
        """
        Heuristic: average the latest ROC values across periods, normalize
        to roughly [-1, 1] by dividing by 5% (a typical strong move).
        """
        roc_cols = [c for c in feats.columns if c.startswith("%-roc-")]
        if not roc_cols:
            return self._empty_result(reason="no_roc_features", mode="heuristic")

        latest_roc = feats[roc_cols].iloc[-1].astype(float)
        # ROC is in percent (e.g. 1.5 = +1.5%). Normalize ~5% → 1.0.
        score = float(latest_roc.mean()) / 5.0
        prediction = float(max(-1.0, min(score, 1.0)))
        confidence = float(min(abs(prediction), 1.0))
        signal = self._signal_from_score(prediction, confidence)

        return {
            "signal": signal,
            "confidence": confidence,
            "prediction": prediction,
            "reason": "ml_heuristic_roc_consensus",
            "mode": "heuristic",
        }

    # ── helpers ────────────────────────────────────────────────────
    def _signal_from_score(self, prediction: float, confidence: float) -> Optional[str]:
        if confidence < self.confidence_threshold:
            return None
        if prediction > 0:
            return "buy"
        if prediction < 0:
            return "sell"
        return None

    def _empty_result(self, *, reason: str, mode: str) -> Dict[str, Any]:
        return {
            "signal": None,
            "confidence": 0.0,
            "prediction": 0.0,
            "reason": reason,
            "mode": mode,
        }
