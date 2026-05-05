"""
swarm_client.py — Sends the anonymous daily report to Arkhe Main.

For now, "sending" means writing to disk and emitting a log line. A real
network transport (HTTP POST, WebSocket, or HPE Swarm Learning hook)
plugs into `SwarmClient._dispatch` later without changing callers.

Opt-in is enforced here: if `opt_in=False`, `send()` returns the report
locally without dispatching it anywhere.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from .daily_report_generator import (
    DEFAULT_REPORT_PATH,
    generate_anonymous_daily_report,
    save_daily_report,
)

logger = logging.getLogger(__name__)


def _opt_in_from_env() -> bool:
    """Honor the ARKHE_SWARM_OPT_IN env var (default off)."""
    raw = os.environ.get("ARKHE_SWARM_OPT_IN", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


class SwarmClient:
    """
    Thin client that builds and (optionally) dispatches the daily report.
    """

    def __init__(
        self,
        opt_in: Optional[bool] = None,
        report_path: Path = DEFAULT_REPORT_PATH,
    ) -> None:
        self.opt_in = _opt_in_from_env() if opt_in is None else bool(opt_in)
        self.report_path = Path(report_path)

    def build_report(
        self,
        portfolio_state: Mapping[str, Any],
        performance: Mapping[str, Any],
        decisions: Optional[Iterable[Mapping[str, Any]]] = None,
    ) -> Dict[str, Any]:
        return generate_anonymous_daily_report(portfolio_state, performance, decisions)

    def send(
        self,
        portfolio_state: Mapping[str, Any],
        performance: Mapping[str, Any],
        decisions: Optional[Iterable[Mapping[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Build the anonymous report, save it locally, and dispatch IF opted in.

        Always returns the (scrubbed) report so callers can log/inspect it.
        """
        report = self.build_report(portfolio_state, performance, decisions)
        save_daily_report(report, self.report_path)

        if not self.opt_in:
            logger.info(
                "Swarm opt-in is OFF (set ARKHE_SWARM_OPT_IN=1 to share). "
                "Report saved locally only."
            )
            return report

        self._dispatch(report)
        return report

    def _dispatch(self, report: Mapping[str, Any]) -> None:
        """
        Override or replace this method to wire a real network transport.

        Default: log only. Even when opt-in is true, no network request is
        made until a real coordinator endpoint is configured.
        """
        logger.info(
            "[SwarmClient] Dispatch placeholder — report %s (node %s) NOT sent over network "
            "(no coordinator endpoint configured).",
            report.get("report_id"),
            report.get("anonymous_node_id"),
        )
