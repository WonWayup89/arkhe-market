from datetime import datetime, timezone
import requests
import pandas as pd
from arkhe_market_core.data_feeds import FUTURES_YF_MAP

try:
    import yfinance as yf
except Exception:
    yf = None


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_crypto_quote(symbol: str) -> dict:
    try:
        url = f"https://api.coinbase.com/v2/prices/{symbol}/spot"
        r = requests.get(url, timeout=6)
        r.raise_for_status()
        raw = r.json()
        return {
            "symbol": symbol,
            "price": float(raw["data"]["amount"]),
            "source": "coinbase_public",
            "timestamp": _now_iso(),
            "ok": True,
        }
    except Exception as exc:
        return {
            "symbol": symbol,
            "price": 0.0,
            "source": "coinbase_public",
            "timestamp": _now_iso(),
            "ok": False,
            "error": str(exc),
        }


def get_crypto_quotes(symbols: list[str]) -> pd.DataFrame:
    rows = [get_crypto_quote(symbol) for symbol in symbols]
    return pd.DataFrame(rows)


def _yf_symbol_for_futures(symbol: str) -> str:
    """Use canonical mapping from data_feeds module."""
    return FUTURES_YF_MAP.get(symbol, f"{symbol}=F")


def get_yf_quotes(symbols: list[str], market: str) -> pd.DataFrame:
    rows = []
    if yf is None:
        return pd.DataFrame([{
            "symbol": s,
            "price": 0.0,
            "source": "yfinance",
            "timestamp": _now_iso(),
            "ok": False,
            "error": "yfinance not installed",
        } for s in symbols])

    for symbol in symbols:
        lookup = _yf_symbol_for_futures(symbol) if market == "futures" else symbol
        try:
            ticker = yf.Ticker(lookup)
            hist = ticker.history(period="2d", interval="1m")
            info = ticker.fast_info if hasattr(ticker, "fast_info") else {}
            price = 0.0
            if hist is not None and not hist.empty:
                price = float(hist["Close"].dropna().iloc[-1])
            elif info and info.get("lastPrice") is not None:
                price = float(info["lastPrice"])

            rows.append({
                "symbol": symbol,
                "lookup": lookup,
                "price": round(price, 6),
                "source": "yfinance",
                "timestamp": _now_iso(),
                "ok": True,
            })
        except Exception as exc:
            rows.append({
                "symbol": symbol,
                "lookup": lookup,
                "price": 0.0,
                "source": "yfinance",
                "timestamp": _now_iso(),
                "ok": False,
                "error": str(exc),
            })
    return pd.DataFrame(rows)


def get_stock_quotes(symbols: list[str]) -> pd.DataFrame:
    return get_yf_quotes(symbols, market="stocks")


def get_futures_quotes(symbols: list[str]) -> pd.DataFrame:
    return get_yf_quotes(symbols, market="futures")
