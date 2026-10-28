"""Links Kalshi game markets to sportsbook events.

Kalshi labels teams by city ("Kansas City") while sportsbooks use full names
("Kansas City Chiefs"). A market only matches when both teams and the date agree,
and anything ambiguous (two teams sharing a city) is skipped rather than guessed.
"""

import re
from datetime import datetime, timedelta

_MONTHS = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower().replace("&", " and ")).strip()


def label_matches_team(label: str, team: str) -> bool:
    """True when Kalshi's label is a whole-word prefix or suffix of the full team name."""
    label, team = _norm(label), _norm(team)
    if not label:
        return False
    return team == label or team.startswith(label + " ") or team.endswith(" " + label)


def event_date(event_ticker: str):
    """KXNFLGAME-25NOV02KCBUF -> date(2025, 11, 2)."""
    m = re.search(r"-(\d{2})([A-Z]{3})(\d{2})", event_ticker)
    if not m or m.group(2) not in _MONTHS:
        return None
    return datetime(2000 + int(m.group(1)), _MONTHS[m.group(2)], int(m.group(3))).date()


def match_market(market: dict, events: list[dict]):
    """Returns (event, team_name) for the team this market's YES side pays on, or None."""
    label = market.get("yes_sub_title", "")
    title = market.get("title", "")
    date = event_date(market.get("event_ticker", ""))
    hits = []
    for ev in events:
        teams = [ev["home_team"], ev["away_team"]]
        if date:
            commence = datetime.fromisoformat(ev["commence_time"].replace("Z", "+00:00")).date()
            if abs(commence - date) > timedelta(days=1):  # UTC vs US-local date
                continue
        yes_teams = [t for t in teams if label_matches_team(label, t)]
        if len(yes_teams) != 1:
            continue
        other = teams[1] if yes_teams[0] == teams[0] else teams[0]
        if not _title_mentions(title, other):
            continue
        hits.append((ev, yes_teams[0]))
    return hits[0] if len(hits) == 1 else None


def _title_mentions(title: str, team: str) -> bool:
    title_words = set(_norm(title).split())
    team_words = _norm(team).split()
    # any leading or trailing run of the team name ("New York", "Giants") appearing in the title
    for i in range(1, len(team_words) + 1):
        for chunk in (team_words[:i], team_words[-i:]):
            if set(chunk) <= title_words:
                return True
    return False
