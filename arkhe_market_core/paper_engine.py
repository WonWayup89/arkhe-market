"""
paper_engine.py
Paper trading ledger with market specific cost simulation.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

from arkhe_market_core.test_cost_agent import simulate_fill, get_cost_profile
# Atomic state writes — see services/atomic_io.py for rationale.
# The audit identified torn JSON writes / lost cooldowns as a real risk
# when the run loop, Streamlit UI, and manual actions all touch the
# same state files concurrently.
from services.atomic_io import atomic_write_json, file_lock


class PaperEngine:
    def __init__(
        self,
        state_path: str,
        starting_cash: float,
        slippage_bps: float = 5.0,
    ) -> None:
        self.state_path = state_path
        self.starting_cash = float(starting_cash)
        self.slippage_bps = float(slippage_bps)
        os.makedirs(os.path.dirname(self.state_path) or ".", exist_ok=True)
        self.state = self._load_state()

    def _default_state(self) -> Dict[str, Any]:
        return {
            "cash": self.starting_cash,
            "asset_qty": 0.0,
            "avg_entry": 0.0,
            "last_price": 0.0,
            "realized_pnl": 0.0,
            "gross_realized_pnl": 0.0,
            "total_fees": 0.0,
            "total_commission": 0.0,
            "total_spread_cost": 0.0,
            "total_slippage_cost": 0.0,
            "total_execution_drag": 0.0,
            "trade_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "trades": [],
        }

    def _load_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.state_path):
            state = self._default_state()
            self._save_state(state)
            return state
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            for k, v in self._default_state().items():
                state.setdefault(k, v)
            return state
        except Exception:
            state = self._default_state()
            self._save_state(state)
            return state

    def _save_state(self, state: Dict[str, Any]) -> None:
        # Atomic write under a coarse advisory lock so concurrent writers
        # can't tear the JSON file. Reads do NOT take the lock — they
        # tolerate seeing the previous version of the file.
        with file_lock(self.state_path):
            atomic_write_json(self.state_path, state)

    def mark_price(self, price: float) -> None:
        self.state["last_price"] = float(price)
        self._save_state(self.state)

    def buy(self, qty: float, price: float, symbol: str = "", reason: str = "") -> Dict[str, Any]:
        qty = float(qty)
        price = float(price)

        if qty <= 0:
            raise ValueError("Buy quantity must be positive")

        fill = simulate_fill(symbol or "UNKNOWN", "buy", price, qty)
        exec_price = float(fill["exec_price"])
        commission = float(fill["commission"])
        spread_cost = float(fill["spread_cost"])
        slippage_cost = float(fill["slippage_cost"])

        gross_cost = qty * exec_price
        total_debit = gross_cost + commission

        if total_debit > float(self.state["cash"]):
            raise ValueError("Not enough cash")

        old_qty = float(self.state["asset_qty"])
        old_avg = float(self.state["avg_entry"])
        new_qty = old_qty + qty

        effective_unit_cost = total_debit / qty
        new_avg = ((old_qty * old_avg) + (qty * effective_unit_cost)) / new_qty if new_qty > 0 else 0.0

        self.state["cash"] = float(self.state["cash"]) - total_debit
        self.state["asset_qty"] = new_qty
        self.state["avg_entry"] = new_avg
        self.state["last_price"] = exec_price
        self.state["total_fees"] = float(self.state["total_fees"]) + commission
        self.state["total_commission"] = float(self.state["total_commission"]) + commission
        self.state["total_spread_cost"] = float(self.state["total_spread_cost"]) + spread_cost
        self.state["total_slippage_cost"] = float(self.state["total_slippage_cost"]) + slippage_cost
        self.state["total_execution_drag"] = float(self.state["total_execution_drag"]) + float(fill["total_cost"])
        self.state["trade_count"] = int(self.state["trade_count"]) + 1

        self.state["trades"].append({
            "time": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "side": "buy",
            "qty": qty,
            "requested_price": price,
            "price": exec_price,
            "value": gross_cost,
            "commission": commission,
            "spread_cost": spread_cost,
            "slippage_cost": slippage_cost,
            "total_cost": float(fill["total_cost"]),
            "fee_profile": get_cost_profile(symbol or "UNKNOWN"),
            "reason": reason,
        })

        self._save_state(self.state)
        return self.snapshot()

    def sell(self, qty: float, price: float, symbol: str = "", reason: str = "") -> Dict[str, Any]:
        qty = float(qty)
        price = float(price)

        if qty <= 0:
            raise ValueError("Sell quantity must be positive")
        if qty > float(self.state["asset_qty"]):
            raise ValueError("Not enough asset quantity")

        fill = simulate_fill(symbol or "UNKNOWN", "sell", price, qty)
        exec_price = float(fill["exec_price"])
        commission = float(fill["commission"])
        spread_cost = float(fill["spread_cost"])
        slippage_cost = float(fill["slippage_cost"])

        gross_proceeds = qty * exec_price
        net_proceeds = gross_proceeds - commission
        cost_basis = float(self.state["avg_entry"]) * qty
        gross_realized = gross_proceeds - cost_basis
        net_realized = net_proceeds - cost_basis

        self.state["cash"] = float(self.state["cash"]) + net_proceeds
        self.state["asset_qty"] = float(self.state["asset_qty"]) - qty
        self.state["gross_realized_pnl"] = float(self.state["gross_realized_pnl"]) + gross_realized
        self.state["realized_pnl"] = float(self.state["realized_pnl"]) + net_realized
        self.state["last_price"] = exec_price
        self.state["total_fees"] = float(self.state["total_fees"]) + commission
        self.state["total_commission"] = float(self.state["total_commission"]) + commission
        self.state["total_spread_cost"] = float(self.state["total_spread_cost"]) + spread_cost
        self.state["total_slippage_cost"] = float(self.state["total_slippage_cost"]) + slippage_cost
        self.state["total_execution_drag"] = float(self.state["total_execution_drag"]) + float(fill["total_cost"])
        self.state["trade_count"] = int(self.state["trade_count"]) + 1

        if net_realized > 0:
            self.state["win_count"] = int(self.state["win_count"]) + 1
        elif net_realized < 0:
            self.state["loss_count"] = int(self.state["loss_count"]) + 1

        if float(self.state["asset_qty"]) <= 1e-12:
            self.state["asset_qty"] = 0.0
            self.state["avg_entry"] = 0.0

        self.state["trades"].append({
            "time": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "side": "sell",
            "qty": qty,
            "requested_price": price,
            "price": exec_price,
            "value": gross_proceeds,
            "net_value": net_proceeds,
            "commission": commission,
            "spread_cost": spread_cost,
            "slippage_cost": slippage_cost,
            "total_cost": float(fill["total_cost"]),
            "gross_realized_pnl": gross_realized,
            "realized_pnl": net_realized,
            "fee_profile": get_cost_profile(symbol or "UNKNOWN"),
            "reason": reason,
        })

        self._save_state(self.state)
        return self.snapshot()

    def snapshot(self) -> Dict[str, Any]:
        qty = float(self.state["asset_qty"])
        last_price = float(self.state["last_price"])
        avg_entry = float(self.state["avg_entry"])
        unrealized = (last_price - avg_entry) * qty if qty > 0 and last_price > 0 else 0.0
        equity = float(self.state["cash"]) + (qty * last_price)

        wins = int(self.state.get("win_count", 0))
        losses = int(self.state.get("loss_count", 0))
        win_rate = wins / max(wins + losses, 1) * 100

        return {
            "cash": float(self.state["cash"]),
            "asset_qty": qty,
            "avg_entry": avg_entry,
            "last_price": last_price,
            "gross_realized_pnl": float(self.state.get("gross_realized_pnl", 0)),
            "realized_pnl": float(self.state["realized_pnl"]),
            "unrealized_pnl": unrealized,
            "equity": equity,
            "total_fees": float(self.state.get("total_fees", 0)),
            "total_commission": float(self.state.get("total_commission", 0)),
            "total_spread_cost": float(self.state.get("total_spread_cost", 0)),
            "total_slippage_cost": float(self.state.get("total_slippage_cost", 0)),
            "total_execution_drag": float(self.state.get("total_execution_drag", 0)),
            "trade_count": int(self.state.get("trade_count", 0)),
            "win_count": wins,
            "loss_count": losses,
            "win_rate": round(win_rate, 1),
            "trades": list(self.state["trades"]),
        }
