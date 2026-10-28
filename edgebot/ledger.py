"""CSV record of every signal and every price snapshot.

Closing line value (CLV) — did you beat the final fair price before the game? —
is the fastest honest test of whether the edge is real; win/loss takes thousands
of bets to mean anything.
"""

import csv
from dataclasses import asdict, fields
from datetime import datetime, timezone
from pathlib import Path

from .strategy import Signal

SNAPSHOT_FIELDS = ["ts", "market", "team", "commence_time", "fair_prob"]
SIGNAL_FIELDS = ["ts", "status"] + [f.name for f in fields(Signal)]


def _append(path: Path, fieldnames: list[str], rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if new:
            writer.writeheader()
        writer.writerows(rows)


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


class Ledger:
    def __init__(self, data_dir: str):
        self.dir = Path(data_dir)
        self.signals_path = self.dir / "signals.csv"
        self.snapshots_path = self.dir / "snapshots.csv"

    def log_signal(self, signal: Signal, status: str):
        now = datetime.now(timezone.utc).isoformat()
        _append(self.signals_path, SIGNAL_FIELDS, [{"ts": now, "status": status, **asdict(signal)}])

    def log_snapshots(self, rows: list[dict]):
        now = datetime.now(timezone.utc).isoformat()
        _append(self.snapshots_path, SNAPSHOT_FIELDS, [{"ts": now, **r} for r in rows])

    def signals(self) -> list[dict]:
        return _read(self.signals_path)

    def already_bet(self, market: str, team: str) -> bool:
        """True once a signal was acted on or alerted, so cron runs do not repeat it."""
        return any(s["market"] == market and s["team"] == team and s["status"] in ("placed", "paper", "alert")
                   for s in self.signals())

    def open_exposure(self) -> float:
        now = datetime.now(timezone.utc).isoformat()
        return sum(float(s["stake"]) for s in self.signals()
                   if s["status"] in ("placed", "paper") and s["commence_time"] > now)

    def closing_fair(self) -> dict[tuple[str, str], float]:
        """Last fair probability seen before each game started."""
        closing = {}
        for row in _read(self.snapshots_path):
            if row["ts"] < row["commence_time"]:
                closing[(row["market"], row["team"])] = float(row["fair_prob"])
        return closing

    def clv_report(self) -> list[dict]:
        closing = self.closing_fair()
        out = []
        for s in self.signals():
            if s["status"] not in ("placed", "paper") or s["kind"] == "arb":
                continue
            close = closing.get((s["market"], s["team"]))
            if close is None:
                continue
            # price paid as an implied probability vs the closing fair probability
            paid = float(s["price"]) if s["kind"] == "kalshi" else 1 / float(s["price"])
            out.append({**s, "closing_fair": close, "clv": round(close / paid - 1, 4)})
        return out
