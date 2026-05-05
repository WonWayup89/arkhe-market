"""
services/market_controls.py — Plain-Python market-control state.

Holds per-asset-class flags (enabled / paused / override_minimum / connected)
that the trading engine consults. Lives in `services/` so the engine layer
can read it without importing Streamlit; the Streamlit sidebar mutates the
same dict from the UI side via the setters below.

Audit reference: removing `import streamlit as st` from inside
SupervisorAgent._market_control_state, which had bound execution logic to
the UI runtime and broke headless / CI usage.
"""

from __future__ import annotations

from typing import Dict


# Default per-asset-class control state. Keys mirror the canonical
# asset_class strings used everywhere else in the codebase.
def _default() -> Dict[str, bool]:
    return {
        "enabled":          True,
        "paused":           False,
        "override_minimum": False,
        "connected":        False,
    }


_MARKET_CONTROL: Dict[str, Dict[str, bool]] = {
    "crypto":  _default(),
    "stocks":  _default(),
    "futures": _default(),
}


def _normalize(asset_class: str) -> str:
    """Accept the legacy "stock" key as a synonym for "stocks"."""
    if asset_class == "stock":
        return "stocks"
    return asset_class


def get_market_control(asset_class: str) -> Dict[str, bool]:
    key = _normalize(asset_class)
    state = _MARKET_CONTROL.setdefault(key, _default())
    # Return a shallow copy so callers can't mutate via reference.
    return dict(state)


def set_market_control(asset_class: str, **fields) -> None:
    key = _normalize(asset_class)
    state = _MARKET_CONTROL.setdefault(key, _default())
    for name, value in fields.items():
        if name not in state:
            continue
        state[name] = bool(value)


def reset_market_controls() -> None:
    """Test-only helper."""
    for k in list(_MARKET_CONTROL.keys()):
        _MARKET_CONTROL[k] = _default()
