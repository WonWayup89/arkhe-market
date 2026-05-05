from typing import Dict

MINIMUMS = {
    "crypto": {
        "unsafe": 500.0,
        "eligible": 1500.0,
        "healthy": 3000.0,
        "recommended": 5000.0,
    },
    "stocks": {
        "unsafe": 1000.0,
        "eligible": 2500.0,
        "healthy": 5000.0,
        "recommended": 10000.0,
    },
    "futures": {
        "unsafe": 2500.0,
        "eligible": 10000.0,
        "healthy": 15000.0,
        "recommended": 20000.0,
    },
}

# Defensive alias map — the audit found a `"stock"` vs `"stocks"` key
# mismatch that silently bypassed live-account minimums for stock
# accounts. Normalizing here means a single misnamed call site can never
# again silently miss the MINIMUMS table.
_ASSET_CLASS_ALIASES = {
    "stock":    "stocks",
    "stocks":   "stocks",
    "equity":   "stocks",
    "equities": "stocks",
    "crypto":   "crypto",
    "cryptos":  "crypto",
    "futures":  "futures",
    "future":   "futures",
}


def _canonical_asset_class(asset_class: str) -> str:
    if asset_class is None:
        return ""
    return _ASSET_CLASS_ALIASES.get(str(asset_class).strip().lower(), str(asset_class))


def capital_health(asset_class: str, balance: float) -> str:
    rules = MINIMUMS.get(_canonical_asset_class(asset_class), {})
    b = float(balance or 0)

    if b < float(rules.get("unsafe", 0)):
        return "unsafe"
    if b < float(rules.get("eligible", 0)):
        return "limited"
    if b < float(rules.get("healthy", 0)):
        return "eligible"
    return "healthy"

def live_market_status(asset_class: str, connected: bool, balance: float, override_minimum: bool = False, market_enabled: bool = True, market_paused: bool = False) -> Dict[str, object]:
    canonical = _canonical_asset_class(asset_class)
    health = capital_health(canonical, balance)
    recommended = float(MINIMUMS.get(canonical, {}).get("recommended", 0))
    eligible_min = float(MINIMUMS.get(canonical, {}).get("eligible", 0))

    under_minimum = float(balance or 0) < eligible_min
    live_eligible = bool(connected) and (not under_minimum or bool(override_minimum))

    if not market_enabled:
        mode = "off"
    elif market_paused:
        mode = "paused"
    else:
        mode = "live" if live_eligible else "paper"

    reason = "ok"
    if not market_enabled:
        reason = "disabled"
    elif market_paused:
        reason = "paused"
    elif not connected:
        reason = "not_connected"
    elif under_minimum and not override_minimum:
        reason = "under_minimum"
    elif under_minimum and override_minimum:
        reason = "override_under_minimum"

    return {
        "asset_class": asset_class,
        "connected": bool(connected),
        "balance": float(balance or 0),
        "health": health,
        "live_eligible": live_eligible,
        "mode": mode,
        "minimum_live_balance": eligible_min,
        "recommended_balance": recommended,
        "override_minimum": bool(override_minimum),
        "market_enabled": bool(market_enabled),
        "market_paused": bool(market_paused),
        "reason": reason,
    }
