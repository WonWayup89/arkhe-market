"""
coinbase_client.py – Placeholder for authenticated Coinbase client.

Currently unused; all data flows through data_feeds.py public endpoints.
"""


class CoinbaseClient:
    def __init__(self, api_key: str = "", api_secret: str = ""):
        self.api_key = api_key
        self.api_secret = api_secret

    def status(self):
        return "placeholder – use data_feeds.py"
