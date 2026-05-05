"""
cooldown_store.py – Per-symbol trade-cooldown tracker.

Persists timestamps to a small JSON file. Audit-driven changes:

  * Writes go through services.atomic_io.atomic_write_json so a torn
    write can never leave the file partially serialized.
  * Mutations are wrapped in services.atomic_io.file_lock so the run
    loop, the Streamlit UI, and manual actions can't race on the same
    file.
  * Reads tolerate a missing or corrupt file — they return {} rather
    than crashing the supervisor's run_once().
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

from services.atomic_io import atomic_write_json, file_lock


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
                loaded = json.load(f)
                # Defensive: only accept dict shape.
                return loaded if isinstance(loaded, dict) else {}
        except Exception:
            return {}

    def _save(self) -> None:
        with file_lock(self.path):
            atomic_write_json(self.path, self.data)

    def get_last_trade_time(self, symbol: str) -> Optional[datetime]:
        raw = self.data.get(symbol)
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except Exception:
            return None

    def set_last_trade_time(self, symbol: str, when: datetime) -> None:
        with file_lock(self.path):
            # Re-read under the lock so we don't clobber another writer's
            # update for a different symbol that landed since we loaded.
            self.data = self._load()
            self.data[symbol] = when.isoformat()
            atomic_write_json(self.path, self.data)

    def clear(self) -> None:
        with file_lock(self.path):
            self.data = {}
            atomic_write_json(self.path, self.data)
