from typing import Dict

FUTURES_SYMBOLS = {"ES", "NQ", "RTY", "YM", "CL", "NG"}

TEST_COSTS: Dict[str, Dict[str, float]] = {
    "crypto": {
        "commission_rate": 0.0060,
        "spread_bps": 8.0,
        "slippage_bps": 10.0,
        "min_notional": 25.0,
    },
    "stock": {
        "commission_rate": 0.0000,
        "spread_bps": 2.0,
        "slippage_bps": 3.0,
        "min_notional": 50.0,
    },
    "futures": {
        "commission_rate": 0.0000,
        "fee_per_contract": 2.50,
        "spread_bps": 2.0,
        "slippage_bps": 6.0,
        "min_notional": 100.0,
    },
}

LIVE_COSTS: Dict[str, Dict[str, float]] = {
    "crypto": {
        "commission_rate": 0.0060,
        "spread_bps": 6.0,
        "slippage_bps": 8.0,
    },
    "stock": {
        "commission_rate": 0.0000,
        "spread_bps": 1.5,
        "slippage_bps": 2.0,
    },
    "futures": {
        "commission_rate": 0.0000,
        "fee_per_contract": 2.50,
        "spread_bps": 1.5,
        "slippage_bps": 4.0,
    },
}

def infer_asset_class(symbol: str) -> str:
    if symbol in FUTURES_SYMBOLS:
        return "futures"
    if symbol.endswith("-USD"):
        return "crypto"
    return "stock"

def get_cost_profile(symbol: str, mode: str = "test") -> Dict[str, float]:
    asset_class = infer_asset_class(symbol)
    if mode == "live":
        return LIVE_COSTS[asset_class].copy()
    return TEST_COSTS[asset_class].copy()

def estimate_trade_cost(symbol: str, side: str, requested_price: float, qty: float, mode: str = "test") -> Dict[str, float]:
    profile = get_cost_profile(symbol, mode=mode)
    requested_price = float(requested_price)
    qty = float(qty)

    spread_bps = float(profile.get("spread_bps", 0.0))
    slippage_bps = float(profile.get("slippage_bps", 0.0))
    commission_rate = float(profile.get("commission_rate", 0.0))
    fee_per_contract = float(profile.get("fee_per_contract", 0.0))

    spread_per_unit = requested_price * (spread_bps / 10000.0)
    slip_per_unit = requested_price * (slippage_bps / 10000.0)

    if side == "buy":
        exec_price = requested_price + spread_per_unit + slip_per_unit
    else:
        exec_price = requested_price - spread_per_unit - slip_per_unit

    notional = exec_price * qty
    spread_cost = spread_per_unit * qty
    slippage_cost = slip_per_unit * qty

    if infer_asset_class(symbol) == "futures":
        commission = qty * fee_per_contract
    else:
        commission = notional * commission_rate

    total_cost = spread_cost + slippage_cost + commission

    return {
        "mode": mode,
        "asset_class": infer_asset_class(symbol),
        "requested_price": requested_price,
        "estimated_exec_price": exec_price,
        "qty": qty,
        "notional": notional,
        "spread_cost": spread_cost,
        "slippage_cost": slippage_cost,
        "commission": commission,
        "total_cost": total_cost,
        "cost_pct_of_notional": (total_cost / notional * 100.0) if notional > 0 else 0.0,
    }

def decision_after_cost(symbol: str, side: str, requested_price: float, qty: float, expected_edge_pct: float, mode: str = "test") -> Dict[str, float]:
    est = estimate_trade_cost(symbol, side, requested_price, qty, mode=mode)
    minimum_edge_buffer_pct = 0.10 if mode == "test" else 0.20
    net_edge_pct = float(expected_edge_pct) - float(est["cost_pct_of_notional"])
    allow = net_edge_pct > minimum_edge_buffer_pct
    est["expected_edge_pct"] = float(expected_edge_pct)
    est["net_edge_pct"] = net_edge_pct
    est["minimum_edge_buffer_pct"] = minimum_edge_buffer_pct
    est["allow"] = allow
    return est
