"""
cooldown_store.py – Per-symbol trade-cooldown tracker.
"""

import json
import os
from datetime import datetime
from typing import Optional


class CooldownStore:
    def __init__(self, path: str = "states/cooldowns.json") -> None:
        self.path = path
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get_last_trade_time(self, symbol: str) -> Optional[datetime]:
        raw = self.data.get(symbol)
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except Exception:
            return None

    def set_last_trade_time(self, symbol: str, when: datetime) -> None:
        self.data[symbol] = when.isoformat()
        self._save()

    def clear(self) -> None:
        self.data = {}
        self._save()
