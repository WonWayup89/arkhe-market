"""
backtester.py – Walk-forward backtester for any asset class.

Feeds historical candles bar-by-bar through the TechnicalAgent and
records simulated trades via a fresh PaperEngine.
"""

import pandas as pd
import tempfile
import os
from typing import List, Dict

from arkhe_market_core.technical_agent import TechnicalAgent
from arkhe_market_core.paper_engine import PaperEngine
from arkhe_market_core.metrics import (
    compute_equity_curve,
    compute_max_drawdown,
    compute_simple_return,
    compute_sharpe_like,
    compute_sortino,
    compute_profit_factor,
)


class Backtester:
    def __init__(
        self,
        market_type: str = "stable",
        starting_cash: float = 1000.0,
        risk_pct: float = 0.01,
    ) -> None:
        self.market_type = market_type
        self.starting_cash = starting_cash
        self.risk_pct = risk_pct

    def run(self, df: pd.DataFrame, symbol: str = "BACKTEST") -> Dict:
        """Walk through df bar-by-bar and return performance results."""
        tech = TechnicalAgent(market_type=self.market_type)
        paper = PaperEngine(state_path=os.path.join(tempfile.gettempdir(), "bt_state.json"), starting_cash=self.starting_cash)

        results: List[Dict] = []
        min_bars = 50

        for i in range(min_bars, len(df)):
            window = df.iloc[:i + 1].copy()
            window = tech.calculate_indicators(window)

            price = float(window.iloc[-1]["close"])
            paper.mark_price(price)
            snap = paper.snapshot()
            has_pos = float(snap["asset_qty"]) > 0

            signal, stop_dist, reason = tech.generate_signal(window, has_pos)

            if signal == "buy" and stop_dist and not has_pos:
                risk_amt = float(snap["equity"]) * self.risk_pct
                qty = risk_amt / stop_dist
                max_afford = float(snap["cash"]) / price * 0.95
                qty = min(qty, max_afford)
                if qty > 0:
                    try:
                        paper.buy(qty, price, symbol=symbol, reason=reason)
                    except Exception:
                        pass

            elif signal == "sell" and has_pos:
                qty = float(snap["asset_qty"])
                try:
                    paper.sell(qty, price, symbol=symbol, reason=reason)
                except Exception:
                    pass

            snap = paper.snapshot()
            results.append({"bar": i, "price": price, "equity": snap["equity"], "signal": signal or "hold"})

        final = paper.snapshot()
        curve = [r["equity"] for r in results]

        return {
            "results": results,
            "final_snapshot": final,
            "total_return": compute_simple_return(self.starting_cash, final["equity"]),
            "max_drawdown": compute_max_drawdown(curve),
            "sharpe": compute_sharpe_like(curve),
            "sortino": compute_sortino(curve),
            "profit_factor": compute_profit_factor(final["trades"]),
            "trade_count": final["trade_count"],
            "win_rate": final["win_rate"],
        }
