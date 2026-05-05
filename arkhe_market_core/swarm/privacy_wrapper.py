"""
privacy_wrapper.py — Privacy guards for swarm reports.

Inspired by HPE Swarm Learning: only aggregated, anonymous metrics ever
leave the local node. This module gives us two tools:

    scrub_sensitive(d)   — recursively drop disallowed keys from a dict.
    @privacy_safe(...)   — decorator that scrubs a function's dict return.

The list of allowed keys is *explicit* and conservative. Adding a new
field requires updating ALLOWED_KEYS — there is no implicit pass-through.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Iterable, Set


# Keys that are safe to include in a swarm report.
# Anything else is dropped by scrub_sensitive() at every nesting level.
ALLOWED_KEYS: Set[str] = {
    # report identity
    "report_id",
    "anonymous_node_id",
    "timestamp",
    "schema_version",
    "opt_in_swarm",
    "data_shared",
    # aggregated portfolio metrics (no raw trades, no positions, no symbols)
    "total_pnl",
    "sharpe",
    "win_rate",
    "profit_factor",
    "max_drawdown",
    "trade_count",
    "local_strategy_score",
    "key_decisions",
    # market-summary aggregates
    "market_summary",
    "total_symbols",
    "sharpe_ratio",
    # decision summary entries
    "decision_type",
    "regime",
    "outcome",
    "count",
}


def scrub_sensitive(value: Any, allowed: Iterable[str] = ALLOWED_KEYS) -> Any:
    """
    Recursively drop dict keys that aren't in `allowed`. Lists are walked,
    primitives pass through. Dicts ALWAYS get scrubbed — there is no
    implicit pass-through of unknown keys.
    """
    allowed_set = set(allowed)
    if isinstance(value, dict):
        return {
            k: scrub_sensitive(v, allowed_set)
            for k, v in value.items()
            if k in allowed_set
        }
    if isinstance(value, list):
        return [scrub_sensitive(item, allowed_set) for item in value]
    if isinstance(value, tuple):
        return tuple(scrub_sensitive(item, allowed_set) for item in value)
    return value


def privacy_safe(allowed: Iterable[str] = ALLOWED_KEYS) -> Callable:
    """
    Decorator: scrub the dict (or list-of-dicts) returned by `func`.

    Non-dict/list returns pass through unchanged. Use this on any function
    that produces data destined for the swarm coordinator.
    """
    allowed_set = set(allowed)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return scrub_sensitive(result, allowed_set)
        return wrapper

    return decorator
