from arkhe_market_core.fee_agent import get_cost_profile, estimate_trade_cost

def simulate_fill(symbol: str, side: str, requested_price: float, qty: float):
    est = estimate_trade_cost(symbol, side, requested_price, qty, mode="test")
    return {
        "asset_class": est["asset_class"],
        "requested_price": est["requested_price"],
        "exec_price": est["estimated_exec_price"],
        "qty": est["qty"],
        "notional": est["notional"],
        "spread_cost": est["spread_cost"],
        "slippage_cost": est["slippage_cost"],
        "commission": est["commission"],
        "total_cost": est["total_cost"],
    }
