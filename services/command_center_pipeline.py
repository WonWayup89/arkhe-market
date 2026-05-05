from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List
import streamlit as st

MAX_ACTIVITY = 200

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def ensure_command_center_state() -> None:
    if "cc_activity" not in st.session_state:
        st.session_state.cc_activity = []
    if "cc_last_run" not in st.session_state:
        st.session_state.cc_last_run = None
    if "cc_summary" not in st.session_state:
        st.session_state.cc_summary = {
            "total_actions": 0,
            "buys": 0,
            "sells": 0,
            "holds": 0,
            "waits": 0,
            "entry_blocks": 0,
            "exit_blocks": 0,
            "cooldowns": 0,
        }

def classify_message(msg: str) -> str:
    m = (msg or "").lower()
    if "✅ buy" in m:
        return "buy"
    if "✅ sell" in m:
        return "sell"
    if "entry_gate:block" in m:
        return "entry_block"
    if "exit_gate:block" in m:
        return "exit_block"
    if "cooldown" in m:
        return "cooldown"
    if "wait" in m:
        return "wait"
    if "hold" in m:
        return "hold"
    return "other"

def log_market_outputs(market: str, outputs: List[str]) -> None:
    ensure_command_center_state()
    summary = st.session_state.cc_summary

    for raw in outputs or []:
        msg = str(raw)
        kind = classify_message(msg)
        symbol = msg.split(":")[0].strip() if ":" in msg else "UNKNOWN"

        row = {
            "ts": _now(),
            "market": market,
            "symbol": symbol,
            "kind": kind,
            "message": msg,
        }
        st.session_state.cc_activity.insert(0, row)

        summary["total_actions"] += 1
        if kind == "buy":
            summary["buys"] += 1
        elif kind == "sell":
            summary["sells"] += 1
        elif kind == "hold":
            summary["holds"] += 1
        elif kind == "wait":
            summary["waits"] += 1
        elif kind == "entry_block":
            summary["entry_blocks"] += 1
        elif kind == "exit_block":
            summary["exit_blocks"] += 1
        elif kind == "cooldown":
            summary["cooldowns"] += 1

    st.session_state.cc_activity = st.session_state.cc_activity[:MAX_ACTIVITY]
    st.session_state.cc_last_run = _now()

def get_recent_activity(limit: int = 20) -> List[Dict[str, Any]]:
    ensure_command_center_state()
    return st.session_state.cc_activity[:limit]

def get_summary() -> Dict[str, Any]:
    ensure_command_center_state()
    return st.session_state.cc_summary
