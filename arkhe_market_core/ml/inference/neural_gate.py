"""
arkhe_market_core/ml/inference/neural_gate.py

Pure-Python gate evaluator. Does NOT import streamlit; reads thresholds
from arkhe_market_core.ml.config so the engine can be used in CI, scripts,
workers, and minimal deploys without Streamlit installed.

The audit identified two critical failure modes in the prior version:

  1. `import streamlit as st` at module top blocked headless imports.
  2. A missing model produced score=None → gate="unknown" → allow=False,
     i.e. the gate silently fail-CLOSED and blocked every entry.

This implementation:

  * has no Streamlit dependency,
  * returns a structured dict with explicit `allow` and `reason` so callers
    log *why* a gate did or didn't fire,
  * fails OPEN when no score is available (missing model, transient error)
    by default. The behavior is configurable via the gate config; it is
    intentionally NOT controlled by ad-hoc session state.
"""

from __future__ import annotations

from typing import Optional

from arkhe_market_core.ml.config import (
    fail_open,
    get_entry_threshold,
    get_exit_threshold,
)


def _threshold_for(mode: str) -> float:
    return get_entry_threshold() if mode == "entry" else get_exit_threshold()


def neural_gate(score: Optional[float], mode: str = "entry") -> str:
    """
    Backward-compatible string verdict: "allow" | "block" | "unknown".

    "unknown" is returned only for diagnostic purposes; callers should rely
    on `evaluate_gate()` for an actual allow/block decision because
    "unknown" alone does NOT determine policy.
    """
    if score is None:
        return "unknown"
    threshold = _threshold_for(mode)
    return "allow" if float(score) >= threshold else "block"


def evaluate_gate(score: Optional[float], mode: str = "entry") -> dict:
    """
    Structured evaluation. Always returns:

        {
          "score":     float | None,
          "gate":      "allow" | "block" | "unknown",
          "threshold": float,
          "allow":     bool,
          "reason":    str,
        }

    Policy:
      * score >= threshold       → allow=True,  gate="allow"
      * score <  threshold       → allow=False, gate="block"
      * score is None and fail_open → allow=True,  gate="unknown",
                                       reason="no_score_fail_open"
      * score is None otherwise  → allow=False, gate="unknown",
                                       reason="no_score_fail_closed"
    """
    threshold = _threshold_for(mode)
    if score is None:
        if fail_open():
            return {
                "score": None,
                "gate": "unknown",
                "threshold": threshold,
                "allow": True,
                "reason": "no_score_fail_open",
            }
        return {
            "score": None,
            "gate": "unknown",
            "threshold": threshold,
            "allow": False,
            "reason": "no_score_fail_closed",
        }

    s = float(score)
    if s >= threshold:
        return {
            "score": s,
            "gate": "allow",
            "threshold": threshold,
            "allow": True,
            "reason": "score_above_threshold",
        }
    return {
        "score": s,
        "gate": "block",
        "threshold": threshold,
        "allow": False,
        "reason": "score_below_threshold",
    }
