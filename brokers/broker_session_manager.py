from datetime import datetime, timezone


class BrokerSessionManager:
    def __init__(self):
        self.sessions = {
            "crypto": {
                "connected": False,
                "source": "test",
                "broker": "Coinbase",
                "last_sync": None,
                "balances": {},
                "positions": [],
            },
            "stocks": {
                "connected": False,
                "source": "test",
                "broker": "Broker",
                "last_sync": None,
                "balances": {},
                "positions": [],
            },
            "futures": {
                "connected": False,
                "source": "test",
                "broker": "Broker",
                "last_sync": None,
                "balances": {},
                "positions": [],
            },
        }

    def _mark_sync(self, market: str):
        self.sessions[market]["last_sync"] = datetime.now(timezone.utc).isoformat()

    def connect_market(self, market: str, broker: str):
        self.sessions[market]["connected"] = True
        self.sessions[market]["source"] = "connected"
        self.sessions[market]["broker"] = broker
        self._mark_sync(market)

    def disconnect_market(self, market: str):
        self.sessions[market]["connected"] = False
        self.sessions[market]["source"] = "test"
        self.sessions[market]["balances"] = {}
        self._mark_sync(market)

    def update_balances(self, market: str, balances: dict):
        self.sessions[market]["balances"] = balances or {}
        if balances:
            self.sessions[market]["connected"] = True
            self.sessions[market]["source"] = "connected"
        self._mark_sync(market)

    def update_positions(self, market: str, positions: list):
        self.sessions[market]["positions"] = positions or []
        self._mark_sync(market)

    def snapshot(self, market: str) -> dict:
        return self.sessions[market]
