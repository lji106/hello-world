"""Turns prices into decisions. No opinions: a bet exists only if the numbers say so."""

from dataclasses import dataclass
from datetime import datetime, timezone

from . import oddsmath
from .config import Config


@dataclass
class Signal:
    kind: str            # "kalshi" (auto-tradable), "book" (manual alert) or "arb"
    venue: str
    market: str          # Kalshi ticker or "<book>:<event id>"
    team: str
    game: str
    commence_time: str
    fair_prob: float
    fair_source: str
    price: float         # cost per $1 payout (Kalshi) or decimal odds (book)
    edge: float          # expected profit per $1 staked
    stake: float         # dollars, after Kelly and caps
    contracts: int = 0
    limit_price: float = 0.0  # raw Kalshi ask the order is capped at


def minutes_to_start(commence_time: str, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    start = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
    return (start - now).total_seconds() / 60


def passes_filters(cfg: Config, fair_prob: float, commence_time: str, now=None) -> bool:
    mins = minutes_to_start(commence_time, now)
    return (cfg.min_fair_prob <= fair_prob <= cfg.max_fair_prob
            and cfg.min_minutes_to_start <= mins <= cfg.max_minutes_to_start)


def size(cfg: Config, bankroll: float, full_kelly: float) -> float:
    return round(bankroll * min(full_kelly * cfg.kelly_multiplier, cfg.max_bet_fraction), 2)


def evaluate_kalshi(cfg: Config, bankroll: float, ticker: str, team: str, game: str,
                    commence_time: str, fair_prob: float, fair_source: str, ask: float, now=None):
    if not passes_filters(cfg, fair_prob, commence_time, now):
        return None
    # size first at the raw price, then recompute with the real fee for that order size
    rough = size(cfg, bankroll, oddsmath.kelly_binary(fair_prob, ask))
    contracts = int(rough // ask)
    if contracts < 1:
        return None
    cost = oddsmath.kalshi_cost_per_contract(ask, contracts, cfg.kalshi_fee_rate)
    edge = oddsmath.ev_binary(fair_prob, cost)
    if edge < cfg.min_edge:
        return None
    stake = size(cfg, bankroll, oddsmath.kelly_binary(fair_prob, cost))
    contracts = int(stake // cost)
    if contracts < 1:
        return None
    # fees round up per order, so re-check the edge at the final size
    cost = oddsmath.kalshi_cost_per_contract(ask, contracts, cfg.kalshi_fee_rate)
    edge = oddsmath.ev_binary(fair_prob, cost)
    if edge < cfg.min_edge:
        return None
    return Signal("kalshi", "kalshi", ticker, team, game, commence_time, fair_prob, fair_source,
                  round(cost, 4), round(edge, 4), round(contracts * cost, 2), contracts, ask)


def evaluate_book(cfg: Config, bankroll: float, book: str, event_id: str, team: str, game: str,
                  commence_time: str, fair_prob: float, fair_source: str, american: float, now=None):
    if not passes_filters(cfg, fair_prob, commence_time, now):
        return None
    dec = oddsmath.american_to_decimal(american)
    edge = oddsmath.ev_decimal(fair_prob, dec)
    if edge < cfg.min_edge:
        return None
    stake = size(cfg, bankroll, oddsmath.kelly_fraction(fair_prob, dec))
    if stake <= 0:
        return None
    return Signal("book", book, f"{book}:{event_id}", team, game, commence_time, fair_prob,
                  fair_source, round(dec, 4), round(edge, 4), stake)


def evaluate_arb(cfg: Config, ticker: str, team: str, game: str, commence_time: str,
                 ask: float, book: str, other_team: str, other_american: float):
    """Kalshi YES on `team` + sportsbook bet on `other_team` covers both outcomes."""
    cost = oddsmath.kalshi_cost_per_contract(ask, 100, cfg.kalshi_fee_rate)
    dec = oddsmath.american_to_decimal(other_american)
    margin = oddsmath.arb_margin(cost, dec)
    if margin <= 0:
        return None
    return Signal("arb", f"kalshi+{book}", ticker, f"{team} / {other_team}", game, commence_time,
                  1.0, "arbitrage", round(cost, 4), round(margin, 4), 0.0)
