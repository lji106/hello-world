"""Sportsbook odds from The Odds API (https://the-odds-api.com), plus fair-price estimation."""

import statistics

import requests

from . import oddsmath

BASE_URL = "https://api.the-odds-api.com/v4"


def fetch_h2h(api_key: str, sport: str) -> list[dict]:
    resp = requests.get(
        f"{BASE_URL}/sports/{sport}/odds",
        params={"apiKey": api_key, "regions": "us,us2,eu", "markets": "h2h", "oddsFormat": "american"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def book_prices(event: dict) -> dict[str, dict[str, float]]:
    """{bookmaker_key: {team_name: american_price}} for two-way moneylines."""
    out = {}
    for book in event.get("bookmakers", []):
        for market in book.get("markets", []):
            if market["key"] != "h2h" or len(market["outcomes"]) != 2:
                continue  # skip three-way (draw) markets
            out[book["key"]] = {o["name"]: o["price"] for o in market["outcomes"]}
    return out


def _devig(prices: dict[str, float], method: str) -> dict[str, float]:
    teams = list(prices)
    implied = [oddsmath.american_to_implied(prices[t]) for t in teams]
    fair = oddsmath.devig_power(implied) if method == "power" else oddsmath.devig_multiplicative(implied)
    return dict(zip(teams, fair))


def fair_probabilities(event: dict, sharp_books: list[str], method: str, min_books: int):
    """Returns ({team: prob}, source) or (None, None) when no trustworthy price exists."""
    books = book_prices(event)
    for key in sharp_books:
        if key in books:
            return _devig(books[key], method), key
    if len(books) < min_books:
        return None, None
    per_book = [_devig(p, method) for p in books.values()]
    teams = [event["home_team"], event["away_team"]]
    medians = {t: statistics.median(b[t] for b in per_book if t in b) for t in teams}
    total = sum(medians.values())
    return {t: p / total for t, p in medians.items()}, f"consensus({len(books)})"
