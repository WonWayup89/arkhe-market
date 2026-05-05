"""
arkhe_market_core/ml/inference/neural_decision.py

Wraps the symbol scorer + structured gate evaluator into the
`neural_entry_ok` / `neural_exit_ok` pair the SupervisorAgent calls.

Both helpers always return a dict with:

    {
      "score":     float | None,
      "gate":      "allow" | "block" | "unknown",
      "threshold": float,
      "allow":     bool,
      "reason":    str,
    }

`allow` is the only field a caller should branch on — it already accounts
for the fail-open policy in `neural_gate.evaluate_gate`.
"""

from __future__ import annotations

from typing import Any, Dict

from arkhe_market_core.ml.inference.symbol_scorer import score_symbol
from arkhe_market_core.ml.inference.neural_gate import evaluate_gate


def _evaluate(
    symbol: str,
    price: float,
    asset_class: str,
    volatility: float,
    mode: str,
) -> Dict[str, Any]:
    try:
        score = score_symbol(
            symbol, {"price": price, "volatility": volatility}, asset_class
        )
    except Exception as exc:  # noqa: BLE001 — never crash the trading loop
        result = evaluate_gate(None, mode=mode)
        # Surface that we failed-open due to an exception, not a missing model.
        result["reason"] = f"scorer_error:{type(exc).__name__}"
        return result

    return evaluate_gate(score, mode=mode)


def neural_entry_ok(symbol, price, asset_class="unknown", volatility=0.1):
    return _evaluate(symbol, price, asset_class, volatility, mode="entry")


def neural_exit_ok(symbol, price, asset_class="unknown", volatility=0.1):
    return _evaluate(symbol, price, asset_class, volatility, mode="exit")
