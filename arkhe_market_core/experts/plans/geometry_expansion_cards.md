# Arkhe Constellation Interface System

## Core Design Rule
Wherever possible, Arkhe Market should represent complex systems as expanding constellations.

A card is not just a card.
A card is a collapsed system.

When the user hovers or opens it, the system expands into connected nodes.

## Primary Constellations

### Crypto Total
Collapsed: total crypto equity, PnL, active positions.
Expanded: currencies as connected nodes.

Nodes:
BTC, ETH, SOL, XRP, ADA, LINK, DOGE, AVAX.

Node data:
price, position value, PnL, signal, neural score, risk status.

### Stocks Total
Collapsed: total stock equity and PnL.
Expanded: tickers as connected nodes.

### Futures Total
Collapsed: total futures exposure.
Expanded: contracts as connected nodes.

### Strategy Health
Collapsed: current strategy score.
Expanded: strategy agents as connected nodes.

Nodes:
Technical, Regime, Volatility, Sentiment, Fee, Risk, Neural Gate.

### Risk Shield
Collapsed: risk status.
Expanded: drawdown, exposure, stop loss, cooldown, fee drag, blocked trades.

### Promotion Engine
Collapsed: promoted strategy count.
Expanded: candidate strategies as nodes moving from shadow validation into active use.

## Visual System
Dark glass panels.
Teal glow.
Shield geometry.
Thin network lines.
Subtle motion.
Nodes expand outward on hover.
High confidence nodes glow brighter.
Blocked or dangerous nodes pulse red.
Gold accents represent promoted or premium strategies.

## Phase 1
Build one reusable HTML/CSS Streamlit component:
ui/constellation_cards.py

Start with:
render_crypto_constellation_card()

## Phase 2
Use the same pattern for:
render_strategy_constellation_card()
render_risk_constellation_card()
render_market_constellation_card()

## Phase 3
Move to React and Three.js for true 3D constellations.
