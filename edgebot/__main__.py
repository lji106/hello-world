"""Command line entry point.

    python -m edgebot scan            # find edges, paper-trade them (default)
    python -m edgebot scan --live     # also place Kalshi limit orders
    python -m edgebot report          # closing line value of past signals
"""

import argparse
import logging
import sys
from pathlib import Path

from . import config as config_mod
from . import oddsapi, strategy
from .kalshi import KalshiClient, yes_ask
from .ledger import Ledger
from .matching import match_market

log = logging.getLogger("edgebot")


def scan(cfg, live: bool) -> list[strategy.Signal]:
    ledger = Ledger(cfg.data_dir)
    kalshi = KalshiClient(cfg.kalshi_base_url, cfg.kalshi_key_id, cfg.kalshi_private_key_path)
    bankroll = cfg.bankroll
    if live:
        bankroll = kalshi.balance()
        log.info("Kalshi balance: $%.2f", bankroll)

    signals, snapshots = [], []
    for series, sport in cfg.leagues.items():
        try:
            events = oddsapi.fetch_h2h(cfg.odds_api_key, sport)
            markets = kalshi.open_markets(series)
        except Exception as exc:  # one league failing should not stop the others
            log.warning("%s: fetch failed: %s", series, exc)
            continue

        fair_by_event = {}
        for ev in events:
            fair, source = oddsapi.fair_probabilities(ev, cfg.sharp_books, cfg.devig_method,
                                                      cfg.min_books_for_consensus)
            if fair:
                fair_by_event[ev["id"]] = (fair, source)

        for ev in events:
            if ev["id"] not in fair_by_event:
                continue
            fair, source = fair_by_event[ev["id"]]
            game = f"{ev['away_team']} @ {ev['home_team']}"
            for book, prices in oddsapi.book_prices(ev).items():
                if book not in cfg.retail_books:
                    continue
                for team, american in prices.items():
                    snapshots.append({"market": f"{book}:{ev['id']}", "team": team,
                                      "commence_time": ev["commence_time"], "fair_prob": fair[team]})
                    sig = strategy.evaluate_book(cfg, bankroll, book, ev["id"], team, game,
                                                 ev["commence_time"], fair[team], source, american)
                    if sig:
                        signals.append(sig)

        for m in markets:
            hit = match_market(m, events)
            ask = yes_ask(m)
            if not hit or ask is None or hit[0]["id"] not in fair_by_event:
                continue
            ev, team = hit
            fair, source = fair_by_event[ev["id"]]
            game = f"{ev['away_team']} @ {ev['home_team']}"
            snapshots.append({"market": m["ticker"], "team": team,
                              "commence_time": ev["commence_time"], "fair_prob": fair[team]})
            sig = strategy.evaluate_kalshi(cfg, bankroll, m["ticker"], team, game,
                                           ev["commence_time"], fair[team], source, ask)
            if sig:
                signals.append(sig)
            other = ev["away_team"] if team == ev["home_team"] else ev["home_team"]
            for book, prices in oddsapi.book_prices(ev).items():
                if book in cfg.retail_books and other in prices:
                    arb = strategy.evaluate_arb(cfg, m["ticker"], team, game, ev["commence_time"],
                                                ask, book, other, prices[other])
                    if arb:
                        signals.append(arb)

    ledger.log_snapshots(snapshots)
    act(cfg, ledger, kalshi, bankroll, signals, live)
    return signals


def act(cfg, ledger, kalshi, bankroll, signals, live):
    exposure = ledger.open_exposure()
    for sig in sorted(signals, key=lambda s: s.edge, reverse=True):
        if ledger.already_bet(sig.market, sig.team):
            continue
        line = (f"[{sig.kind}] {sig.venue:<12} {sig.game} | {sig.team} | fair {sig.fair_prob:.3f} "
                f"({sig.fair_source}) | price {sig.price} | edge {sig.edge:+.2%} | stake ${sig.stake:.2f}")
        if sig.kind != "kalshi":
            print("ALERT " + line)  # sportsbooks: place by hand, if at all
            ledger.log_signal(sig, "alert")
            continue
        if exposure + sig.stake > bankroll * cfg.max_open_exposure_fraction:
            print("SKIP (exposure cap) " + line)
            continue
        if live and Path(cfg.kill_switch_file).exists():
            print(f"HALTED: {cfg.kill_switch_file} exists. " + line)
            continue
        if live:
            # limit at the observed ask: fills only at the price the edge was computed on
            kalshi.buy_yes(sig.market, sig.contracts, sig.limit_price)
            print("PLACED " + line)
            ledger.log_signal(sig, "placed")
        else:
            print("PAPER " + line)
            ledger.log_signal(sig, "paper")
        exposure += sig.stake


def report(cfg):
    rows = Ledger(cfg.data_dir).clv_report()
    if not rows:
        print("No signals with closing prices yet.")
        return
    for r in rows:
        print(f"{r['ts'][:16]} {r['venue']:<12} {r['team']:<28} paid {r['price']:<7} "
              f"close {r['closing_fair']:.3f}  CLV {r['clv']:+.2%}")
    avg = sum(r["clv"] for r in rows) / len(rows)
    beat = sum(r["clv"] > 0 for r in rows) / len(rows)
    print(f"\n{len(rows)} bets | average CLV {avg:+.2%} | beat the close {beat:.0%}")
    print("Positive average CLV over 100+ bets is evidence of a real edge; negative means stop.")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="edgebot")
    parser.add_argument("--config", default="config.toml")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_scan = sub.add_parser("scan")
    p_scan.add_argument("--live", action="store_true", help="place real Kalshi orders")
    sub.add_parser("report")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = config_mod.load(args.config)
    if args.cmd == "scan":
        if not cfg.odds_api_key:
            sys.exit("odds_api_key missing from config")
        if args.live and not (cfg.kalshi_key_id and cfg.kalshi_private_key_path):
            sys.exit("--live needs kalshi_key_id and kalshi_private_key_path")
        signals = scan(cfg, args.live)
        print(f"{len(signals)} signal(s)")
    else:
        report(cfg)


if __name__ == "__main__":
    main()
