"""
Read-only Binance client. Never places trades or touches withdrawals.
Uses account endpoint (needs API key) for balances, and public endpoints
(no key needed) for historical price data.
"""

import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

BASE_URL = "https://api.binance.com"


class BinanceReadOnlyClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def _signed_request(self, path: str, params: dict = None):
        params = params or {}
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        query_string += f"&signature={signature}"
        headers = {"X-MBX-APIKEY": self.api_key}
        url = f"{BASE_URL
