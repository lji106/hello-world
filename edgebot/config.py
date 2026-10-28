"""Loads config.toml. Every decision threshold lives here, not in someone's head."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# Kalshi game-winner series -> The Odds API sport key
DEFAULT_LEAGUES = {
    "KXNFLGAME": "americanfootball_nfl",
    "KXNBAGAME": "basketball_nba",
    "KXMLBGAME": "baseball_mlb",
    "KXNHLGAME": "icehockey_nhl",
    "KXNCAAFGAME": "americanfootball_ncaaf",
}


@dataclass
class Config:
    # credentials
    odds_api_key: str = ""
    kalshi_key_id: str = ""
    kalshi_private_key_path: str = ""
    kalshi_base_url: str = "https://api.elections.kalshi.com/trade-api/v2"

    # where "true" probability comes from: sharp books, in priority order.
    # If none of them lists a game, the median de-vigged price of all books is used.
    sharp_books: list[str] = field(default_factory=lambda: ["pinnacle", "circasports", "betonlineag"])
    devig_method: str = "power"  # "power" or "multiplicative"
    min_books_for_consensus: int = 4

    # sportsbooks you can bet manually (alerts only, no automation)
    retail_books: list[str] = field(default_factory=lambda: ["espnbet", "thescorebet", "draftkings", "fanduel"])

    # entry rules
    min_edge: float = 0.03           # 3% EV after fees
    min_fair_prob: float = 0.20      # skip longshots: fair-price error is biggest there
    max_fair_prob: float = 0.85
    max_minutes_to_start: int = 24 * 60
    min_minutes_to_start: int = 10   # lines move sharply near kickoff

    # sizing
    bankroll: float = 1000.0         # used when Kalshi balance is not fetched
    kelly_multiplier: float = 0.25   # quarter Kelly
    max_bet_fraction: float = 0.02   # never more than 2% of bankroll on one game
    max_open_exposure_fraction: float = 0.15
    kalshi_fee_rate: float = 0.07

    leagues: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_LEAGUES))
    data_dir: str = "data"
    kill_switch_file: str = "STOP"   # create this file to halt all live orders


def load(path: str | Path = "config.toml") -> Config:
    path = Path(path)
    if not path.exists():
        return Config()
    raw = tomllib.loads(path.read_text())
    cfg = Config()
    for key, value in raw.items():
        if not hasattr(cfg, key):
            raise ValueError(f"unknown config key: {key}")
        setattr(cfg, key, value)
    return cfg
