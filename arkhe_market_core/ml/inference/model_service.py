from pathlib import Path
import joblib
import pandas as pd

MODEL_PATH = Path("ml/models/arkhe_market_model.pkl")

_cached_model = None
_cached_scaler = None
_cached_feature_cols = None
_cache_loaded = False

def load_model():
    global _cached_model, _cached_scaler, _cached_feature_cols, _cache_loaded
    if _cache_loaded:
        return _cached_model, _cached_scaler, _cached_feature_cols
    if not MODEL_PATH.exists():
        _cache_loaded = True
        return None, None, None
    _cached_model, _cached_scaler, _cached_feature_cols = joblib.load(MODEL_PATH)
    _cache_loaded = True
    return _cached_model, _cached_scaler, _cached_feature_cols

def score_features(feature_dict: dict):
    model, scaler, feature_cols = load_model()
    if model is None:
        return None

    row = {}
    for col in feature_cols:
        row[col] = feature_dict.get(col, 0)

    X = pd.DataFrame([row])
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0)

    X_scaled = scaler.transform(X)
    raw = float(model.predict(X_scaled)[0])

    # clamp to 0..1 range
    score = max(0.0, min(1.0, raw))
    return score
