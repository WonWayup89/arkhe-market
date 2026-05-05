"""
daily_report_generator.py — Build the anonymous daily swarm report.

The report is the *only* thing that ever leaves a node when swarm mode
is opted in. It contains aggregated metrics and a small bounded summary
of recent decisions — never raw trades, symbols, balances, or API keys.

Anonymous node IDs are stable across runs: generated once and persisted
to states/swarm_node_id.json so the swarm coordinator can track a
node's score over time without knowing who the operator is.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .privacy_wrapper import scrub_sensitive
from .swarm_logic import calculate_strategy_score

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1.0"
NODE_ID_PATH = Path("states/swarm_node_id.json")
DEFAULT_REPORT_PATH = Path("logs/daily_swarm_report.json")
MAX_DECISION_SUMMARY_ITEMS = 5


def _load_or_create_node_id(path: Path = NODE_ID_PATH) -> str:
    """
    Return a stable anonymous node ID. Generated once, cached on disk.

    The ID is a short prefix of a UUID4 — enough for the coordinator to
    distinguish nodes, not enough to identify a person.
    """
    try:
        if path.exists():
            data = json.loads(path.read_text())
            node_id = data.get("anonymous_node_id")
            if isinstance(node_id, str) and node_id:
                return node_id
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Could not load existing node id (%s); regenerating.", e)

    node_id = f"arkhe_node_{uuid.uuid4().hex[:8]}"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"anonymous_node_id": node_id}))
    except OSError as e:
        logger.warning("Could not persist node id to %s: %s", path, e)
    return node_id


def _summarize_decisions(decisions: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """
    Bounded, anonymized summary of recent decisions.

    Keeps only `decision_type`, `regime`, `outcome` — drops symbol, price,
    quantity, P&L, reason strings, and anything else that could leak data.
    """
    out: List[Dict[str, Any]] = []
    for d in list(decisions)[-MAX_DECISION_SUMMARY_ITEMS:]:
        if not isinstance(d, Mapping):
            continue
        entry = {
            "decision_type": str(d.get("decision_type", d.get("side", "unknown"))),
            "regime": str(d.get("regime", "unknown")),
            "outcome": str(d.get("outcome", "unknown")),
        }
        out.append(entry)
    return out


def generate_anonymous_daily_report(
    portfolio_state: Mapping[str, Any],
    performance: Mapping[str, Any],
    decisions: Optional[Iterable[Mapping[str, Any]]] = None,
    *,
    node_id_path: Path = NODE_ID_PATH,
) -> Dict[str, Any]:
    """
    Build the anonymous daily swarm report.

    Inputs are local — they may contain anything. The function is
    responsible for emitting only allow-listed fields. The output is
    scrubbed through `privacy_wrapper.scrub_sensitive` before return,
    so any future regression that adds an unsafe field is dropped, not
    leaked.
    """
    node_id = _load_or_create_node_id(node_id_path)

    perf = dict(performance) if performance else {}
    local_score = perf.get("local_strategy_score")
    if local_score is None:
        local_score = calculate_strategy_score(perf)

    raw_report: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "report_id": str(uuid.uuid4()),
        "anonymous_node_id": node_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "opt_in_swarm": True,
        "data_shared": ["aggregated_metrics", "decision_summary"],
        "market_summary": {
            "total_symbols": int(len(portfolio_state.get("positions", []) or [])),
            "total_pnl": float(perf.get("total_pnl", 0.0)),
            "sharpe_ratio": float(perf.get("sharpe", 0.0)),
            "win_rate": float(perf.get("win_rate", 0.0)),
            "profit_factor": float(perf.get("profit_factor", 1.0)),
            "max_drawdown": float(perf.get("max_drawdown", 0.0)),
            "trade_count": int(perf.get("trade_count", 0)),
        },
        "local_strategy_score": float(local_score),
        "key_decisions": _summarize_decisions(decisions or []),
    }

    return scrub_sensitive(raw_report)


def save_daily_report(
    report: Mapping[str, Any],
    path: Path = DEFAULT_REPORT_PATH,
) -> Path:
    """Write the report to disk and return the resolved path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True))
    logger.info("Anonymous daily swarm report saved: %s", path)
    return path
