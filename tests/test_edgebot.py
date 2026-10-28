import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from edgebot import oddsapi, oddsmath, strategy
from edgebot.config import Config
from edgebot.ledger import Ledger
from edgebot.matching import event_date, label_matches_team, match_market

NOW = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
START = (NOW + timedelta(hours=5)).isoformat().replace("+00:00", "Z")


def event(home="Buffalo Bills", away="Kansas City Chiefs", books=None):
    books = books or {"pinnacle": {home: -150, away: 130}}
    return {
        "id": "ev1", "home_team": home, "away_team": away, "commence_time": START,
        "bookmakers": [{"key": k, "markets": [{"key": "h2h", "outcomes": [
            {"name": t, "price": p} for t, p in prices.items()]}]} for k, prices in books.items()],
    }


class OddsMath(unittest.TestCase):
    def test_conversions(self):
        self.assertAlmostEqual(oddsmath.american_to_decimal(150), 2.5)
        self.assertAlmostEqual(oddsmath.american_to_decimal(-200), 1.5)
        self.assertAlmostEqual(oddsmath.american_to_implied(-110), 0.5238, places=4)

    def test_devig_sums_to_one(self):
        implied = [oddsmath.american_to_implied(-150), oddsmath.american_to_implied(130)]
        for fair in (oddsmath.devig_multiplicative(implied), oddsmath.devig_power(implied)):
            self.assertAlmostEqual(sum(fair), 1.0, places=8)
            self.assertGreater(fair[0], fair[1])

    def test_power_devig_shades_longshot_more(self):
        implied = [oddsmath.american_to_implied(-400), oddsmath.american_to_implied(300)]
        mult = oddsmath.devig_multiplicative(implied)
        power = oddsmath.devig_power(implied)
        self.assertLess(power[1], mult[1])

    def test_kalshi_fee_rounds_up_to_cent(self):
        # 0.07 * 10 * 0.5 * 0.5 = 0.175 -> 0.18
        self.assertEqual(oddsmath.kalshi_fee(0.50, 10), 0.18)
        self.assertEqual(oddsmath.kalshi_fee(0.50, 100), 1.75)

    def test_kelly(self):
        self.assertAlmostEqual(oddsmath.kelly_fraction(0.55, 2.0), 0.10)
        self.assertEqual(oddsmath.kelly_fraction(0.45, 2.0), 0.0)

    def test_arb(self):
        self.assertGreater(oddsmath.arb_margin(0.45, 2.0), 0)   # 0.45 + 0.50 < 1
        self.assertLess(oddsmath.arb_margin(0.55, 2.0), 0)


class FairPrice(unittest.TestCase):
    def test_prefers_sharp_book(self):
        ev = event(books={"draftkings": {"Buffalo Bills": -200, "Kansas City Chiefs": 170},
                          "pinnacle": {"Buffalo Bills": -150, "Kansas City Chiefs": 130}})
        fair, src = oddsapi.fair_probabilities(ev, ["pinnacle"], "power", 4)
        self.assertEqual(src, "pinnacle")
        self.assertAlmostEqual(sum(fair.values()), 1.0)

    def test_no_sharp_and_too_few_books(self):
        ev = event(books={"draftkings": {"Buffalo Bills": -200, "Kansas City Chiefs": 170}})
        self.assertEqual(oddsapi.fair_probabilities(ev, ["pinnacle"], "power", 4), (None, None))


class Matching(unittest.TestCase):
    def test_labels(self):
        self.assertTrue(label_matches_team("Kansas City", "Kansas City Chiefs"))
        self.assertTrue(label_matches_team("Chiefs", "Kansas City Chiefs"))
        self.assertFalse(label_matches_team("Kansas Ci", "Kansas City Chiefs"))

    def test_event_date(self):
        self.assertEqual(str(event_date("KXNFLGAME-26NOV01KCBUF")), "2026-11-01")

    def test_match(self):
        m = {"event_ticker": "KXNFLGAME-26NOV01KCBUF", "title": "Kansas City at Buffalo Winner?",
             "yes_sub_title": "Kansas City"}
        ev, team = match_market(m, [event()])
        self.assertEqual(team, "Kansas City Chiefs")

    def test_wrong_date_or_ambiguous_city_skipped(self):
        m = {"event_ticker": "KXNFLGAME-26NOV09KCBUF", "title": "Kansas City at Buffalo Winner?",
             "yes_sub_title": "Kansas City"}
        self.assertIsNone(match_market(m, [event()]))
        m = {"event_ticker": "KXNFLGAME-26NOV01NYGNYJ", "title": "New York at New York Winner?",
             "yes_sub_title": "New York"}
        self.assertIsNone(match_market(m, [event("New York Jets", "New York Giants")]))
        m = {"event_ticker": "KXNCAAFGAME-26NOV01KUKSU", "title": "Kansas at Kansas State Winner?",
             "yes_sub_title": "Kansas"}
        self.assertIsNone(match_market(m, [event("Kansas State Wildcats", "Kansas Jayhawks")]))


class Strategy(unittest.TestCase):
    cfg = Config()

    def test_kalshi_signal_when_ask_below_fair(self):
        sig = strategy.evaluate_kalshi(self.cfg, 1000, "T", "Bills", "g", START, 0.60, "pinnacle", 0.52, NOW)
        self.assertIsNotNone(sig)
        self.assertGreaterEqual(sig.edge, self.cfg.min_edge)
        self.assertLessEqual(sig.stake, 1000 * self.cfg.max_bet_fraction)
        self.assertEqual(sig.limit_price, 0.52)
        self.assertGreater(sig.price, 0.52)  # fee included

    def test_fee_kills_thin_edge(self):
        self.assertIsNone(strategy.evaluate_kalshi(self.cfg, 1000, "T", "Bills", "g", START,
                                                   0.55, "pinnacle", 0.53, NOW))

    def test_filters(self):
        late = (NOW + timedelta(minutes=5)).isoformat()
        self.assertIsNone(strategy.evaluate_kalshi(self.cfg, 1000, "T", "x", "g", late, 0.6, "p", 0.5, NOW))
        self.assertIsNone(strategy.evaluate_kalshi(self.cfg, 1000, "T", "x", "g", START, 0.1, "p", 0.05, NOW))

    def test_book_signal(self):
        sig = strategy.evaluate_book(self.cfg, 1000, "espnbet", "ev1", "Chiefs", "g", START, 0.45, "p", 150, NOW)
        self.assertAlmostEqual(sig.edge, 0.125)
        self.assertIsNone(strategy.evaluate_book(self.cfg, 1000, "espnbet", "ev1", "Chiefs", "g",
                                                 START, 0.40, "p", 140, NOW))


class LedgerTest(unittest.TestCase):
    def test_clv(self):
        with tempfile.TemporaryDirectory() as d:
            led = Ledger(d)
            commence = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
            sig = strategy.Signal("kalshi", "kalshi", "T", "Bills", "g", commence, 0.6, "p", 0.50, 0.2, 10, 20, 0.49)
            led.log_signal(sig, "paper")
            led.log_snapshots([{"market": "T", "team": "Bills", "commence_time": commence, "fair_prob": 0.55}])
            self.assertTrue(led.already_bet("T", "Bills"))
            self.assertEqual(led.open_exposure(), 10)
            (row,) = led.clv_report()
            self.assertAlmostEqual(row["clv"], 0.10)


if __name__ == "__main__":
    unittest.main()
