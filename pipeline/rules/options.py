"""Minor-league option reconstruction from the transaction log.

Rules encoded (thresholds from config.CBA_ERAS):
- An option *year* is used when a player spends >= 20 cumulative days on optional assignment during
  the regular season. Spring-training and postseason days never count.
- Each OPT opens an interval; CU (recall), SE, DES, OUT, REL, TR, CLW or another OPT closes it. The
  day of the option counts, the day of recall does not (mirrors MLS accrual). A placement on the MLB
  injured list while optioned is an implicit recall (the log carries no CU row in that case).
- Two OPT rows within a day of each other are one assignment (re-assignment between affiliates).
- SE (contract selected) followed by CU without an OPT means the player was selected and kept on
  optional assignment; the SE date is an implied option (source="implied").
- 5 optional assignments per season (2022+). Exempt: options before Opening Day (spring training)
  and an option within 24h of acquisition by trade of a 40-man player. 27th-man doubleheader
  returns are not detectable from the log and are counted (known limitation).
- 4th option: a player who has used 3 option years but has fewer than 5 "full seasons" (>= 90 days
  on an active list) gets a 4th. Minor-league IL days are not in the log, so full seasons are
  approximated from roster stints; a FanGraphs/AZ Phil value can override with its source recorded.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import pandas as pd

from pipeline import config as C

CLOSERS = {"recalled", "selected", "designated", "outrighted", "released", "traded", "optioned",
           "claimed", "declared_fa", "retired"}
IL_SUBTYPES = {"il_7", "il_10", "il_15", "il_60", "il_60_transfer"}


@dataclass
class Interval:
    season: int
    start: dt.date
    end: dt.date | None      # None = still open
    close_type: str | None
    source: str = "OPT"      # OPT | implied
    days: int = 0            # regular-season days counted
    exempt: bool = False     # does not count toward the 5-per-season cap
    exempt_reason: str = ""


@dataclass
class OptionSeason:
    season: int
    days: int = 0
    burned: bool = False
    assignments: int = 0
    assignments_exempt: int = 0
    intervals: list[Interval] = field(default_factory=list)


def _season_window(seasons: dict, season: int) -> tuple[dt.date, dt.date]:
    s = seasons[season]
    return C.d(s["regularSeasonStartDate"]), C.d(s["regularSeasonEndDate"])


def option_intervals(tx: pd.DataFrame, seasons: dict, today: dt.date) -> list[Interval]:
    """tx: one player's transactions (columns: date, effective_date, type, subtype, txn_id)."""
    out: list[Interval] = []
    open_iv: Interval | None = None
    prev_type, prev_date = None, None
    for r in tx.sort_values(["date", "txn_id"]).itertuples():
        day: dt.date = r.effective_date if (r.type == "optioned" and r.effective_date) else r.date
        season = day.year
        if season not in seasons:
            continue
        if r.type == "optioned":
            if open_iv is not None and (day - open_iv.start).days <= 1 and open_iv.season == season:
                # re-assignment / duplicate row: same assignment
                prev_type, prev_date = r.type, day
                continue
            if open_iv is not None:
                open_iv.end, open_iv.close_type = day, "optioned"
                out.append(open_iv)
            open_iv = Interval(season, day, None, None, "OPT")
            if prev_type == "traded" and prev_date and 0 <= (day - prev_date).days <= 1:
                open_iv.exempt, open_iv.exempt_reason = True, "within 24h of trade"
        elif r.type == "recalled" and open_iv is None and prev_type == "selected" and prev_date and prev_date.year == season:
            out.append(Interval(season, prev_date, day, "recalled", "implied"))
        elif open_iv is not None and (r.type in CLOSERS or r.subtype in IL_SUBTYPES):
            open_iv.end = day
            open_iv.close_type = r.type if r.type in CLOSERS else "il"
            out.append(open_iv)
            open_iv = None
        prev_type, prev_date = r.type, day
    if open_iv is not None:
        out.append(open_iv)
    for iv in out:
        od, end_reg = _season_window(seasons, iv.season)
        start = max(iv.start, od)
        end = iv.end if iv.end is not None else min(today, end_reg) + dt.timedelta(days=1)
        end = min(end, end_reg + dt.timedelta(days=1))
        iv.days = max(0, (end - start).days)
        if iv.start < od and not iv.exempt:
            iv.exempt, iv.exempt_reason = True, "spring training"
    return out


def option_seasons(ivs: list[Interval], seasons: dict, threshold: int = 20) -> dict[int, OptionSeason]:
    by: dict[int, OptionSeason] = {}
    for iv in ivs:
        os_ = by.setdefault(iv.season, OptionSeason(iv.season))
        os_.days += iv.days
        os_.intervals.append(iv)
        if iv.exempt:
            os_.assignments_exempt += 1
        else:
            os_.assignments += 1
    for os_ in by.values():
        os_.burned = os_.days >= threshold
    return by


def approx_full_seasons(roster_entries: list[dict], seasons: dict, before_season: int) -> int | None:
    """Seasons with >= 90 days of roster stints (any level) between the season's regular-season
    bounds. Minor-league IL time is invisible here, so this over-counts for injured players."""
    if not roster_entries:
        return None
    n = 0
    for s in range(min(seasons), before_season):
        if s not in seasons or s == 2020:
            continue
        od, end = _season_window(seasons, s)
        days = 0
        covered: set[dt.date] = set()
        for e in roster_entries:
            st, en = C.d(e.get("start")), C.d(e.get("end")) or dt.date.today()
            if not st:
                continue
            lo, hi = max(st, od), min(en, end)
            if lo <= hi:
                for k in range((hi - lo).days + 1):
                    covered.add(lo + dt.timedelta(days=k))
        days = len(covered)
        if days >= 90:
            n += 1
    return n


def summarize(by: dict[int, OptionSeason], asof_season: int, era: dict,
              full_seasons: int | None = None, external_left: int | None = None) -> dict:
    burned_before = sorted(s for s, o in by.items() if o.burned and s < asof_season)
    burned_this = bool(by.get(asof_season) and by[asof_season].burned)
    used_before = len(burned_before)
    left = max(0, era["option_years"] - used_before)
    fourth = {"eligible": False, "source": None, "full_seasons_approx": full_seasons}
    if used_before >= era["option_years"]:
        # Minor-league IL days are not public, so the full-season test is only a hint; the number
        # shown follows FanGraphs when it carries a value, otherwise no 4th option is assumed.
        if external_left is not None and external_left >= 1:
            fourth = {"eligible": True, "source": "fangraphs", "full_seasons_approx": full_seasons}
            left = 1
        elif external_left is None and full_seasons is not None and full_seasons < era["fourth_option_full_seasons"]:
            fourth = {"eligible": False, "source": "approx_hint", "full_seasons_approx": full_seasons}
    cap = era.get("optional_assignments_per_season")
    used_assign = by[asof_season].assignments if asof_season in by else 0
    return {
        "option_seasons_burned": burned_before + ([asof_season] if burned_this else []),
        "option_years_used_entering": used_before,
        "option_years_left_entering": left,
        "fourth_option": fourth,
        "burning_this_season": burned_this,
        "option_days_this_season": by[asof_season].days if asof_season in by else 0,
        "assignments_used_this_season": used_assign,
        "assignments_available": (None if cap is None or left == 0 else max(0, cap - used_assign)),
        "seasons": {s: {"days": o.days, "burned": o.burned, "assignments": o.assignments,
                        "intervals": [{"start": i.start.isoformat(), "end": i.end.isoformat() if i.end else None,
                                       "close": i.close_type, "days": i.days, "source": i.source,
                                       "exempt": i.exempt_reason or None} for i in o.intervals]}
                    for s, o in sorted(by.items())},
    }
