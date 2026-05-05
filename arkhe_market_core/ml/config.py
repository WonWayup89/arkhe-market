"""
arkhe_market_core/ml/config.py — Plain-Python config for the ML inference path.

Lives at the engine layer so nothing in arkhe_market_core/* needs to import
streamlit. The UI is allowed to mutate the threshold values here at runtime
(via `set_entry_threshold` / `set_exit_threshold`); everything else just
reads them.

Defaults can also come from environment variables:

    ARKHE_ENTRY_THRESHOLD   default 0.75
    ARKHE_EXIT_THRESHOLD    default 0.25
    ARKHE_GATE_FAIL_OPEN    default "1" (truthy → fail-open when no model)
    ARKHE_MODEL_PATH        default arkhe_market_core/ml/models/arkhe_market_model.pkl
                            (with fallback to .../amber_model.pkl)
"""

from __future__ import annotations

import os
from pathlib import Path


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


# ── Mutable runtime config ───────────────────────────────────────────
GATE_CONFIG = {
    "entry_threshold": _env_float("ARKHE_ENTRY_THRESHOLD", 0.75),
    "exit_threshold":  _env_float("ARKHE_EXIT_THRESHOLD",  0.25),
    # CRITICAL: when no model is loaded, gate must NOT silently block trades.
    # The audit found this was the root cause of the "buy flow can be silently
    # blocked" issue. Default behavior is fail-open: missing/None score is
    # treated as "no opinion" and lets the rest of the strategy decide.
    "fail_open_when_no_model": _env_bool("ARKHE_GATE_FAIL_OPEN", True),
}


# ── Canonical model artifact path ────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_FILENAME = "arkhe_market_model.pkl"
LEGACY_MODEL_FILENAME  = "amber_model.pkl"
MODELS_DIR = PROJECT_ROOT / "arkhe_market_core" / "ml" / "models"


def model_path() -> Path:
    """
    Single source of truth for "which model file should everything load?".

    Resolution order:
      1. ARKHE_MODEL_PATH env var (absolute or repo-relative).
      2. arkhe_market_core/ml/models/arkhe_market_model.pkl (canonical).
      3. arkhe_market_core/ml/models/amber_model.pkl (legacy, kept so an
         existing on-disk model isn't silently orphaned by the rename).
    """
    env = os.environ.get("ARKHE_MODEL_PATH")
    if env:
        p = Path(env)
        return p if p.is_absolute() else (PROJECT_ROOT / p)

    canonical = MODELS_DIR / DEFAULT_MODEL_FILENAME
    if canonical.exists():
        return canonical

    legacy = MODELS_DIR / LEGACY_MODEL_FILENAME
    if legacy.exists():
        return legacy

    # Return canonical even if it doesn't exist — load_model() must handle
    # "missing model" cleanly, and reporting the canonical path makes the
    # error message useful.
    return canonical


# ── Setters (used by UI, kept here so engine never reaches into UI) ──
def set_entry_threshold(value: float) -> None:
    try:
        GATE_CONFIG["entry_threshold"] = float(value)
    except (TypeError, ValueError):
        pass


def set_exit_threshold(value: float) -> None:
    try:
        GATE_CONFIG["exit_threshold"] = float(value)
    except (TypeError, ValueError):
        pass


def get_entry_threshold() -> float:
    return float(GATE_CONFIG.get("entry_threshold", 0.75))


def get_exit_threshold() -> float:
    return float(GATE_CONFIG.get("exit_threshold", 0.25))


def fail_open() -> bool:
    return bool(GATE_CONFIG.get("fail_open_when_no_model", True))
