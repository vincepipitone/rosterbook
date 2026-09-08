"""MLB service time reconstruction.

MLS accrues for every regular-season day a player is on an MLB club's 40-man reserve list (active,
any injured list, paternity/bereavement, DFA in-season) EXCEPT days on optional assignment in a
season where the optional-assignment days total >= 20 (those seasons' option days are excluded
entirely; a season with <= 19 option days keeps them). 172 days = one year; a season caps at 172.

Inputs: Stats API rosterEntries (per-club stints with an `forty` flag) + option seasons from
rules.options. Postseason days never count.
"""
from __future__ import annotations

import datetime as dt

from pipeline import config as C

MLB_IDS = set(C.TEAMS)


def forty_man_days(entries: list[dict], seasons: dict, season: int, today: dt.date) -> int:
    s = seasons[season]
    od, end = C.d(s["regularSeasonStartDate"]), C.d(s["regularSeasonEndDate"])
    end = min(end, today)
    covered: set[int] = set()
    for e in entries:
        if e.get("team") not in MLB_IDS or not e.get("forty"):
            continue
        st, en = C.d(e.get("start")), C.d(e.get("end")) or today
        lo, hi = max(st, od), min(en, end)
        if lo <= hi:
            covered.update(range((lo - od).days, (hi - od).days + 1))
    return len(covered)


def mls_by_season(entries: list[dict], option_seasons: dict, seasons: dict, first: int, last: int,
                  today: dt.date, cap: int = 172, threshold: int = 20) -> dict[int, int]:
    out = {}
    for season in range(first, last + 1):
        if season not in seasons:
            continue
        days = forty_man_days(entries, seasons, season, today)
        if days == 0:
            continue
        os_ = option_seasons.get(season)
        if os_ is not None and os_.days >= threshold:
            days -= os_.days
        out[season] = max(0, min(cap, days))
    return out


def total(mls: dict[int, int]) -> int:
    return sum(mls.values())


ON_TYPES = {"selected", "rule5_selected", "purchased", "claimed"}
OFF_TYPES = {"outrighted", "released", "declared_fa", "retired"}


def season_accrual(tx_season, on40_at_od: bool, od: dt.date, today: dt.date, reg_end: dt.date,
                   option_days_excluded: int, cap: int = 172) -> int:
    """Days of MLB service this season: on a 40-man (or DFA'd in-season) between Opening Day and
    today, walking the season's transactions from the Opening Day snapshot state."""
    end = min(today, reg_end)
    if end < od:
        return 0
    on = on40_at_od
    cur = od
    days = 0
    for r in tx_season.sort_values(["date", "txn_id"]).itertuples():
        d = r.date
        if d < od:
            # pre-season moves set the starting state
            if r.type in ON_TYPES or (r.type == "signed_fa" and "minor league" not in r.description.lower()):
                on = True
            elif r.type in OFF_TYPES:
                on = False
            continue
        if d > end:
            break
        if on:
            days += (d - cur).days
        cur = d
        if r.type in ON_TYPES or (r.type == "signed_fa" and "minor league" not in r.description.lower()):
            on = True
        elif r.type in OFF_TYPES:
            on = False
    if on:
        days += (end - cur).days + 1
    return max(0, min(cap, days - option_days_excluded))
