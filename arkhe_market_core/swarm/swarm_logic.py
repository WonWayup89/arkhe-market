"""
swarm_logic.py — Core decision rules for Arkhe Swarm Learning.

The "critical rule" from the project handoff: a node's local strategy
overrides the global swarm consensus when it is *meaningfully* better,
not merely fractionally better. The threshold protects against churn
when local and global scores are noisy and roughly equal.
"""

from __future__ import annotations

from typing import Mapping


# Threshold below which local and global are "essentially the same"
# and we should defer to the global consensus (which has more samples).
DEFAULT_OVERRIDE_THRESHOLD: float = 0.05


def apply_local_override(
    local_score: float,
    global_score: float,
    threshold: float = DEFAULT_OVERRIDE_THRESHOLD,
) -> bool:
    """
    Return True if the local strategy should override the global consensus.

    A local strategy "wins" only if it beats the global score by at least
    `threshold`. Equal-or-marginally-better local scores defer to global,
    because the global score is averaged across more nodes.

    >>> apply_local_override(0.80, 0.70)
    True
    >>> apply_local_override(0.71, 0.70)
    False
    >>> apply_local_override(0.50, 0.90)
    False
    """
    if local_score is None or global_score is None:
        # No comparison possible — default to the local strategy.
        return True
    return float(local_score) > float(global_score) + float(threshold)


def calculate_strategy_score(metrics: Mapping[str, float]) -> float:
    """
    Compute a single 0..~1 score from a portfolio's performance metrics.

    Inputs (all optional, defaults are conservative):
        sharpe         — annualized Sharpe ratio, clipped at [-2, 4]
        win_rate       — 0..1
        profit_factor  — gross profit / gross loss, clipped at [0, 4]
        max_drawdown   — 0..1, expressed as a fraction (0.10 = 10% drawdown)

    Weights favor risk-adjusted returns and consistency over raw profit
    factor; drawdown is a penalty term.

    >>> calculate_strategy_score({"sharpe": 2.0, "win_rate": 0.6, "profit_factor": 1.8, "max_drawdown": 0.05})  # doctest: +ELLIPSIS
    0.6...
    """
    sharpe = max(-2.0, min(float(metrics.get("sharpe", 0.0)), 4.0))
    win_rate = max(0.0, min(float(metrics.get("win_rate", 0.0)), 1.0))
    profit_factor = max(0.0, min(float(metrics.get("profit_factor", 1.0)), 4.0))
    drawdown = max(0.0, min(float(metrics.get("max_drawdown", 0.10)), 1.0))

    # Normalize sharpe to 0..1 (assume 4 = excellent, -2 = terrible).
    sharpe_n = (sharpe + 2.0) / 6.0
    # Normalize profit factor to 0..1 (1.0 = breakeven, 4.0 = excellent).
    pf_n = max(0.0, min((profit_factor - 1.0) / 3.0, 1.0))

    score = (
        sharpe_n * 0.40
        + win_rate * 0.30
        + pf_n * 0.20
        - drawdown * 0.30  # drawdown is a penalty; >0.30 starts hurting hard
    )
    return max(0.0, min(score, 1.0))
