"""
metrics.py – Portfolio performance metrics.
"""

import math
from typing import List, Dict


def compute_equity_curve(
    trades: List[Dict], current_equity: float, starting_equity: float,
) -> List[float]:
    curve = [float(starting_equity)]
    equity = float(starting_equity)
    for t in trades:
        if t.get("side") == "sell":
            equity += float(t.get("realized_pnl", 0.0))
            curve.append(equity)
    if not curve or curve[-1] != float(current_equity):
        curve.append(float(current_equity))
    return curve


def compute_max_drawdown(curve: List[float]) -> float:
    if not curve:
        return 0.0
    peak = curve[0]
    max_dd = 0.0
    for v in curve:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0.0
        max_dd = max(max_dd, dd)
    return max_dd


def compute_simple_return(start: float, current: float) -> float:
    if start <= 0:
        return 0.0
    return (float(current) - float(start)) / float(start)


def compute_sharpe_like(curve: List[float]) -> float:
    if len(curve) < 3:
        return 0.0
    rets = [(curve[i] - curve[i-1]) / curve[i-1] for i in range(1, len(curve)) if curve[i-1] > 0]
    if len(rets) < 2:
        return 0.0
    mu = sum(rets) / len(rets)
    var = sum((r - mu) ** 2 for r in rets) / (len(rets) - 1)
    std = math.sqrt(var)
    return mu / std if std > 0 else 0.0


def compute_sortino(curve: List[float]) -> float:
    if len(curve) < 3:
        return 0.0
    rets = [(curve[i] - curve[i-1]) / curve[i-1] for i in range(1, len(curve)) if curve[i-1] > 0]
    if len(rets) < 2:
        return 0.0
    mu = sum(rets) / len(rets)
    downside = [r for r in rets if r < 0]
    if not downside:
        return 999.0
    ds_var = sum(r ** 2 for r in downside) / len(downside)
    ds_std = math.sqrt(ds_var)
    return mu / ds_std if ds_std > 0 else 0.0


def compute_calmar(curve: List[float]) -> float:
    if len(curve) < 3:
        return 0.0
    total_ret = (curve[-1] - curve[0]) / curve[0] if curve[0] > 0 else 0.0
    max_dd = compute_max_drawdown(curve)
    return total_ret / max_dd if max_dd > 0 else 0.0


def compute_profit_factor(trades: List[Dict]) -> float:
    gross_profit = sum(float(t.get("realized_pnl", 0)) for t in trades if float(t.get("realized_pnl", 0)) > 0)
    gross_loss = abs(sum(float(t.get("realized_pnl", 0)) for t in trades if float(t.get("realized_pnl", 0)) < 0))
    return gross_profit / gross_loss if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)
