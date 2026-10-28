"""Minimal Kalshi Trade API v2 client (RSA-PSS request signing)."""

import base64
import time
import uuid
from urllib.parse import urlparse

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class KalshiClient:
    def __init__(self, base_url: str, key_id: str = "", private_key_path: str = ""):
        self.base_url = base_url.rstrip("/")
        self.key_id = key_id
        self.private_key = None
        if private_key_path:
            with open(private_key_path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(f.read(), password=None)
        self.session = requests.Session()

    def _auth_headers(self, method: str, path: str) -> dict:
        if not self.private_key:
            return {}
        ts = str(int(time.time() * 1000))
        message = (ts + method.upper() + path).encode()
        signature = self.private_key.sign(
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
            hashes.SHA256(),
        )
        return {
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-TIMESTAMP": ts,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode(),
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        url = self.base_url + endpoint
        path = urlparse(url).path  # signature covers the path without the query string
        resp = self.session.request(method, url, headers=self._auth_headers(method, path), timeout=15, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def open_markets(self, series_ticker: str) -> list[dict]:
        markets, cursor = [], None
        while True:
            params = {"series_ticker": series_ticker, "status": "open", "limit": 1000}
            if cursor:
                params["cursor"] = cursor
            data = self._request("GET", "/markets", params=params)
            markets.extend(data.get("markets", []))
            cursor = data.get("cursor")
            if not cursor:
                return markets

    def market(self, ticker: str) -> dict:
        return self._request("GET", f"/markets/{ticker}")["market"]

    def balance(self) -> float:
        return self._request("GET", "/portfolio/balance")["balance"] / 100

    def buy_yes(self, ticker: str, count: int, limit_price: float) -> dict:
        """Limit order: never pays more than `limit_price`, so slippage cannot eat the edge."""
        body = {
            "ticker": ticker,
            "action": "buy",
            "side": "yes",
            "type": "limit",
            "count": count,
            "yes_price": round(limit_price * 100),
            "client_order_id": str(uuid.uuid4()),
        }
        return self._request("POST", "/portfolio/orders", json=body)


def yes_ask(market: dict) -> float | None:
    """Best YES ask in dollars, handling both the cents and *_dollars field styles."""
    if market.get("yes_ask_dollars") not in (None, ""):
        price = float(market["yes_ask_dollars"])
    elif market.get("yes_ask") is not None:
        price = market["yes_ask"] / 100
    else:
        return None
    return price if 0 < price < 1 else None
