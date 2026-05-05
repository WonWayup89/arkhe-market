import json
import os
from datetime import datetime, timezone

DATA_PATH = "ml/data/market_log.jsonl"

def log_market_state(symbol, asset_class, features, agent_outputs, action=None):
    try:
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "asset_class": asset_class,
            "features": features,
            "agents": agent_outputs,
            "action": action
        }

        with open(DATA_PATH, "a") as f:
            f.write(json.dumps(record) + "\n")

    except Exception as e:
        print("LOGGING ERROR:", e)
