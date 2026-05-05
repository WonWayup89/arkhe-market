Arkhe Market clean rebuild

What this contains:
- Streamlit UI
- Paper trading engine
- Stable sleeve plus alt sleeve
- Cooldown logic
- Volatility filter
- Position aware signals
- Live price based manual test trades
- Reset support

How to run:
1. cd Arkhe Market
2. python3 -m venv venv
3. source venv/bin/activate
4. pip install -r requirements.txt
5. streamlit run app.py

If replacing an old project root, copy these files into the root and let them overwrite the current versions.
