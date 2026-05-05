from arkhe_market_core.ml.inference.symbol_scorer import score_symbol
from arkhe_market_core.ml.inference.neural_gate import neural_gate

def neural_entry_ok(symbol, price, asset_class="unknown", volatility=0.1):
    score = score_symbol(symbol, {"price": price, "volatility": volatility}, asset_class)
    gate = neural_gate(score, mode="entry")
    return {
        "score": score,
        "gate": gate,
        "allow": gate == "allow",
    }

def neural_exit_ok(symbol, price, asset_class="unknown", volatility=0.1):
    score = score_symbol(symbol, {"price": price, "volatility": volatility}, asset_class)
    gate = neural_gate(score, mode="exit")
    return {
        "score": score,
        "gate": gate,
        "allow": gate == "allow",
    }
