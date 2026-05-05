# Arkhe Market v2

Multi-market paper-trading workspace with live data and expert agents.

## What changed from v1

### Live data for every market
- **Crypto**: Coinbase Exchange public REST (ticker + candles)
- **Stocks**: Yahoo Finance via `yfinance` (live prices, OHLCV)
- **Futures**: Yahoo Finance continuous-contract tickers (ES=F, NQ=F, GC=F, …)
- 15-second in-memory cache to avoid hammering APIs
- Auto-refresh option in the UI (configurable interval)

### Expert agent panel
Every symbol now gets analysed by five specialised experts before any trade:

| Expert           | Role                                                        |
|------------------|-------------------------------------------------------------|
| TechnicalAgent   | RSI, MACD, Stochastic, Bollinger, ATR%, OBV, VWAP, volume  |
| VolatilityAgent  | Vol-regime (normal/elevated/high/compressed), size factor   |
| RegimeAgent      | Trend detection (trending/ranging/mixed), R², slope, bias   |
| SentimentAgent   | Momentum score (-100…+100), ROC, streaks, divergence        |
| RiskAgent        | Position sizing, drawdown gate, market-hours filter         |

The **SupervisorAgent** orchestrates all five, resolves conflicts:
- Blocks entries in high-vol on stable/stock assets
- Blocks buys when regime is trending-down with high confidence
- Scales position size by vol-factor and sentiment score

### Full workspaces for stocks and futures
- Separate portfolio balances and risk parameters per market
- Paper trading with the same engine (slippage model, win/loss tracking)
- Expert scan per symbol
- Live price tables with position data

### Enhanced metrics
- Sharpe-like, Sortino, Calmar, Profit Factor, Win Rate
- Equity curves per sleeve and per symbol

### Improved paper engine
- Configurable slippage (basis points)
- Win/loss counting
- Total fee tracking
- Trade count

### Functional backtester
- Walk-forward simulation through any OHLCV DataFrame
- Uses the same TechnicalAgent signal logic
- Returns full performance stats

### Command Center
- Cross-market overview at the top level
- Full Sweep button runs all markets in one click
- Risk dashboard shows all open positions

## How to run

```bash
cd Arkhe Market
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Headless mode

```bash
python run_loop.py
```

## Architecture

```
app.py                    Streamlit UI
├── multi_portfolio_agent.py   Orchestrates all markets
│   ├── supervisor_agent.py    Per-symbol expert coordinator
│   │   ├── data_feeds.py      Unified data gateway
│   │   ├── technical_agent.py Indicator + signal expert
│   │   ├── volatility_agent.py Vol-regime expert
│   │   ├── regime_agent.py    Trend-detection expert
│   │   ├── sentiment_agent.py Momentum expert
│   │   ├── risk_agent.py      Sizing + drawdown expert
│   │   └── execution_agent.py Paper fill + logging
│   │       └── paper_engine.py Ledger with slippage
│   └── cooldown_store.py      Per-symbol cooldown
├── metrics.py                 Sharpe, Sortino, Calmar, PF
├── backtester.py              Walk-forward simulator
└── agent_prompts.py           Expert role definitions
```
