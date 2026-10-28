"""Pure math: odds conversion, vig removal, fees, expected value and Kelly sizing.

Every number the bot acts on comes from these functions, so they are kept free of
I/O and covered by unit tests.
"""

import math


def american_to_decimal(american: float) -> float:
    if american >= 100:
        return 1 + american / 100
    if american <= -100:
        return 1 + 100 / -american
    raise ValueError(f"invalid American odds: {american}")


def decimal_to_implied(decimal_odds: float) -> float:
    return 1 / decimal_odds


def american_to_implied(american: float) -> float:
    return decimal_to_implied(american_to_decimal(american))


def devig_multiplicative(implied: list[float]) -> list[float]:
    """Scale implied probabilities so they sum to 1 (removes the bookmaker margin)."""
    total = sum(implied)
    return [p / total for p in implied]


def devig_power(implied: list[float], tol: float = 1e-10) -> list[float]:
    """Find k so that sum(p_i ** k) == 1.

    Corrects favourite/longshot bias better than the multiplicative method,
    because books shade longshots more heavily than favourites.
    """
    lo, hi = 1.0, 10.0
    if sum(implied) < 1:  # no margin (or negative): fall back
        return devig_multiplicative(implied)
    for _ in range(200):
        k = (lo + hi) / 2
        s = sum(p ** k for p in implied)
        if abs(s - 1) < tol:
            break
        if s > 1:
            lo = k
        else:
            hi = k
    return [p ** k for p in implied]


def kalshi_fee(price: float, contracts: int, rate: float = 0.07) -> float:
    """Kalshi trading fee in dollars: ceil_to_cent(rate * C * P * (1 - P)).

    0.07 is the published taker rate for most markets; check Kalshi's current fee
    schedule, since maker rates and per-series rates differ.
    """
    raw = rate * contracts * price * (1 - price)
    return math.ceil(round(raw * 100, 6)) / 100


def kalshi_cost_per_contract(price: float, contracts: int, rate: float = 0.07) -> float:
    """All-in cost of one $1-payout contract, including the fee spread over the order."""
    return price + kalshi_fee(price, contracts, rate) / contracts


def ev_binary(fair_prob: float, cost: float) -> float:
    """Expected profit per $1 staked on a contract that pays $1 and costs `cost`."""
    return fair_prob / cost - 1


def ev_decimal(fair_prob: float, decimal_odds: float) -> float:
    """Expected profit per $1 staked at sportsbook decimal odds."""
    return fair_prob * decimal_odds - 1


def kelly_fraction(fair_prob: float, decimal_odds: float) -> float:
    """Full-Kelly fraction of bankroll; 0 when the bet has no edge."""
    b = decimal_odds - 1
    f = (fair_prob * b - (1 - fair_prob)) / b
    return max(0.0, f)


def kelly_binary(fair_prob: float, cost: float) -> float:
    """Full-Kelly fraction for a $1-payout contract bought at `cost` (fees included)."""
    return kelly_fraction(fair_prob, 1 / cost)


def arb_margin(cost_a: float, decimal_b: float) -> float:
    """Guaranteed return when buying side A at `cost_a` (per $1 payout) and betting
    the opposite side B at sportsbook decimal odds. Positive means a true arbitrage."""
    return 1 / (cost_a + 1 / decimal_b) - 1
