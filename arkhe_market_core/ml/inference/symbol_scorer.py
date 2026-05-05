from arkhe_market_core.ml.inference.model_service import score_features

def build_symbol_features(symbol, snapshot, asset_class="unknown"):
    return {
        "feature_equity_crypto_cash": 0,
        "feature_equity_crypto_equity": 0,
        "feature_equity_futures_cash": 0,
        "feature_equity_futures_equity": 0,
        "feature_equity_stocks_cash": 0,
        "feature_equity_stocks_equity": 0,
        "feature_ok": 1,
        "feature_price": float(snapshot.get("price", 0) or 0),
        "feature_volatility": float(snapshot.get("volatility", 0.1) or 0.1),
    }

def score_symbol(symbol, snapshot, asset_class="unknown"):
    features = build_symbol_features(symbol, snapshot, asset_class)
    return score_features(features)
