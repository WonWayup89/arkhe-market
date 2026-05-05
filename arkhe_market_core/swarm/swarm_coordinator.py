"""
swarm_coordinator.py — Local-side coordinator applying the critical rule.

Each node holds a SwarmCoordinator that remembers what global scores it
last heard for each symbol (or strategy id). When the supervisor asks
`should_use_local_strategy(symbol, local_metrics)`, the coordinator
computes a local score from `local_metrics` and consults
`apply_local_override` against the cached global score.

If no global score is known, the local strategy wins by default — the
node never blocks itself waiting for an outside opinion.
"""

from __future__ import annotations

import logging
from typing import Dict, Mapping, Optional

from .swarm_logic import (
    DEFAULT_OVERRIDE_THRESHOLD,
    apply_local_override,
    calculate_strategy_score,
)

logger = logging.getLogger(__name__)


class SwarmCoordinator:
    """
    Tracks the most recent global score per symbol/strategy id and
    applies the local-vs-global decision rule.
    """

    def __init__(self, override_threshold: float = DEFAULT_OVERRIDE_THRESHOLD) -> None:
        self.override_threshold = float(override_threshold)
        self._global_scores: Dict[str, float] = {}

    # ── global scores ──────────────────────────────────────────────
    def update_global_consensus(self, key: str, global_score: float) -> None:
        """Store a global score for a symbol/strategy id."""
        self._global_scores[str(key)] = float(global_score)

    def update_many(self, scores: Mapping[str, float]) -> None:
        for k, v in scores.items():
            self.update_global_consensus(k, v)

    def get_global_score(self, key: str) -> Optional[float]:
        return self._global_scores.get(str(key))

    # ── decision ───────────────────────────────────────────────────
    def should_use_local_strategy(
        self,
        key: str,
        local_metrics: Mapping[str, float],
    ) -> bool:
        """
        Decide whether to use the local strategy for `key`.

        Returns True if the node should keep doing what it's doing.
        Returns False to *consider* the global consensus (the supervisor
        is still free to ignore that suggestion — the coordinator does
        not directly act on the trade path).
        """
        local_score = calculate_strategy_score(local_metrics)
        global_score = self.get_global_score(key)
        use_local = apply_local_override(
            local_score, global_score, threshold=self.override_threshold
        )
        logger.info(
            "[Swarm] %s: local=%.3f global=%s → %s",
            key,
            local_score,
            "n/a" if global_score is None else f"{global_score:.3f}",
            "LOCAL" if use_local else "consider GLOBAL",
        )
        return use_local

    # ── introspection ──────────────────────────────────────────────
    def snapshot(self) -> Dict[str, float]:
        """Return a copy of the current global score table."""
        return dict(self._global_scores)
