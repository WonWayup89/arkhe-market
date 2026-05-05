"""
arkhe_market_core/ml/inference/model_service.py

Loads the unified neural-stats / system-level scoring model. The path is
resolved through `arkhe_market_core.ml.config.model_path()` so the entire
codebase agrees on which artifact is in play.
"""

from __future__ import annotations

from typing import Optional, Tuple

import joblib
import pandas as pd

from arkhe_market_core.ml.config import model_path

_cached_model = None
_cached_scaler = None
_cached_feature_cols = None
_cache_loaded = False


def load_model() -> Tuple[Optional[object], Optional[object], Optional[list]]:
    """
    Load (model, scaler, feature_cols). Returns (None, None, None) if no
    model is on disk — callers must handle that explicitly.
    """
    global _cached_model, _cached_scaler, _cached_feature_cols, _cache_loaded
    if _cache_loaded:
        return _cached_model, _cached_scaler, _cached_feature_cols

    path = model_path()
    if not path.exists():
        _cache_loaded = True
        return None, None, None

    try:
        loaded = joblib.load(path)
    except Exception:  # noqa: BLE001 — corrupt model must not crash startup
        _cache_loaded = True
        return None, None, None

    if isinstance(loaded, tuple) and len(loaded) == 3:
        _cached_model, _cached_scaler, _cached_feature_cols = loaded
    else:
        # Single-object pickle (legacy ml_expert format) — not usable for
        # score_features which expects (model, scaler, feature_cols).
        _cache_loaded = True
        return None, None, None

    _cache_loaded = True
    return _cached_model, _cached_scaler, _cached_feature_cols


def reset_cache() -> None:
    """Test-only helper — drop cached artifacts so a new model is re-read."""
    global _cached_model, _cached_scaler, _cached_feature_cols, _cache_loaded
    _cached_model = None
    _cached_scaler = None
    _cached_feature_cols = None
    _cache_loaded = False


def score_features(feature_dict: dict) -> Optional[float]:
    """
    Returns score in [0, 1] or None if no model is available. Callers must
    treat None as "no opinion" — the gate layer's fail-open policy then
    decides whether to allow or block.
    """
    model, scaler, feature_cols = load_model()
    if model is None or scaler is None or not feature_cols:
        return None

    row = {col: feature_dict.get(col, 0) for col in feature_cols}
    X = pd.DataFrame([row])
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

    try:
        X_scaled = scaler.transform(X)
        raw = float(model.predict(X_scaled)[0])
    except Exception:  # noqa: BLE001
        return None

    return max(0.0, min(1.0, raw))
