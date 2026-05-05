"""
arkhe_market_core.swarm — Distributed adaptive swarm intelligence layer.

Implements the Phase 1 critical rule:
    if local_strategy_score > global_strategy_score:
        use_local_strategy()
    else:
        consider_global_strategy()

Privacy: opt-in only (env var ARKHE_SWARM_OPT_IN=1), anonymous stable node ID,
no positions/API keys/raw trades shared.
"""

from .swarm_logic import apply_local_override, calculate_strategy_score
from .privacy_wrapper import privacy_safe, scrub_sensitive
from .daily_report_generator import generate_anonymous_daily_report, save_daily_report
from .swarm_client import SwarmClient
from .swarm_coordinator import SwarmCoordinator

__all__ = [
    "apply_local_override",
    "calculate_strategy_score",
    "privacy_safe",
    "scrub_sensitive",
    "generate_anonymous_daily_report",
    "save_daily_report",
    "SwarmClient",
    "SwarmCoordinator",
]
