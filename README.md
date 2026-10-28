# edgebot

A rules-only betting scanner for **Kalshi** sports markets and sportsbooks
(theScore Bet, formerly ESPN Bet, and others). It never asks who you think will
win. It only asks whether a price is wrong compared with the sharpest market in
the world, and by how much after fees.

## The strategy

1. **Fair price comes from sharp books.** Pinnacle and similar books take big
   bets from professionals and move their lines fast, so their de-vigged price is
   the best public estimate of the true probability. The bot removes the vig
   with the *power* method, which corrects the favourite/longshot bias. If no
   sharp book lists a game, the median of 4+ books is used. Otherwise the game is skipped.
2. **Bet only when price < fair probability by at least 3% after fees.** On Kalshi
   the fee is `ceil(0.07 × contracts × P × (1−P))`, and it is included before any
   edge is counted. Thin edges usually disappear once the fee is applied.
3. **Size with quarter Kelly, capped.** At most 2% of bankroll per game and 15%
   open in total. Full Kelly is mathematically optimal only when your
   probabilities are exact, which they never are.
4. **Hard filters remove the noisy spots.** No longshots under 20% or heavy
   favourites over 85%, where fair-price error is largest. No bets in the final
   10 minutes before start, when lines move sharply.
5. **Measure with closing line value (CLV), not wins.** Every scan saves a
   snapshot of the fair price. `report` compares what you paid with the last fair
   price before the game started. If average CLV stays negative after 100+ bets,
   there is no edge, so stop. It takes thousands of bets before win/loss tells you anything.
6. **Arbitrage check.** If buying Kalshi YES on team A plus a sportsbook bet on team
   B costs less than $1 per $1 payout, it is flagged as a locked-in profit.

### What is automated and what is not

| Venue | Automation |
|---|---|
| Kalshi | Fully automated through its official API (limit orders only, never above the ask the edge was computed on). |
| Sportsbooks (theScore Bet / ESPN Bet, DraftKings, …) | **Alerts only.** Their terms of service ban bots and automated betting, and accounts that win get limited fast. Place these by hand, if at all. |

## Setup

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp config.example.toml config.toml   # add your keys
```

You need an [Odds API](https://the-odds-api.com) key, which has a free tier. For live trading
you also need a Kalshi API key: download the private key `.pem` and set its path in the config.

```bash
python -m edgebot scan            # paper trade: logs what it would do
python -m edgebot scan --live     # real Kalshi orders
python -m edgebot report          # closing line value so far
python -m unittest                # tests
```

Run paper mode for a few weeks and check `report` before you use `--live`.

## Running it on a schedule

On any always-on Linux box (a $5 VPS works), run `crontab -e`:

```
*/10 * * * * cd /path/to/edgebot && .venv/bin/python -m edgebot scan >> data/scan.log 2>&1
```

Each run makes one Odds API request per league, so check the request count against
your plan's quota. Add `--live` once paper results justify it.
**Kill switch:** `touch STOP` in the project folder halts all live orders immediately.

State is stored in `data/signals.csv` (every signal and its status) and `data/snapshots.csv`
(fair-price history for CLV).

## Honest caveats

- Most bettors lose. Sharp-vs-soft pricing is the most reliable public edge, but
  books and Kalshi market makers know about it, so edges are rare, small, and short-lived.
- Team matching between Kalshi and sportsbooks is conservative. Ambiguous games
  (for example, two teams from the same city) are skipped rather than guessed.
- Check Kalshi's current fee schedule and API field names. Both have changed
  before, and the fee rate is set in the config.
- Only bet money you can afford to lose. Help: 1-800-GAMBLER.
