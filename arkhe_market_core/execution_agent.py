"""
execution_agent.py – Trade execution and logging expert.
"""

import os
from datetime import datetime, timezone
from typing import Optional

from arkhe_market_core.paper_engine import PaperEngine
from arkhe_market_core.fee_agent import estimate_trade_cost


class ExecutionAgent:
    def __init__(self, state_path: str, log_path: str, starting_cash: float, slippage_bps: float = 5.0):
        self.state_path = state_path
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)
        self.paper = PaperEngine(state_path=self.state_path, starting_cash=starting_cash, slippage_bps=slippage_bps)

        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write("timestamp,symbol,side,price,quantity,stop_loss,reason,regime,sentiment\n")

    def mark_price(self, price: float) -> None:
        self.paper.mark_price(price)

    def execute(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        reason: str = "",
        regime: str = "",
        sentiment: str = "",
    ) -> dict:
        if side == "buy":
            snapshot = self.paper.buy(quantity, price, symbol=symbol, reason=reason)
        elif side == "sell":
            snapshot = self.paper.sell(quantity, price, symbol=symbol, reason=reason)
        else:
            raise ValueError("side must be buy or sell")

        ts = datetime.now(timezone.utc).isoformat()
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"{ts},{symbol},{side},{price},{quantity},{stop_loss or ''},{reason},{regime},{sentiment}\n")

        return snapshot
