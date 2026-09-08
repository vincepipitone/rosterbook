"""Static configuration: teams, season calendar, CBA-era thresholds.

Everything a rule needs as a *number* lives here, keyed by CBA era, so the 2027 CBA is a data
change and not a code branch.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
VALIDATION = ROOT / "data" / "validation"
SITE_DATA = ROOT / "public" / "data"

FIRST_SEASON = 2011  # Stats API rosters/transactions are reliable from here
CURRENT_SEASON = 2026

# MLBAM team id -> (abbr, name, FanGraphs RosterResource teamid)
TEAMS: dict[int, tuple[str, str, int]] = {
    108: ("LAA", "Los Angeles Angels", 1),
    109: ("AZ", "Arizona Diamondbacks", 15),
    110: ("BAL", "Baltimore Orioles", 2),
    111: ("BOS", "Boston Red Sox", 3),
    112: ("CHC", "Chicago Cubs", 17),
    113: ("CIN", "Cincinnati Reds", 18),
    114: ("CLE", "Cleveland Guardians", 5),
    115: ("COL", "Colorado Rockies", 19),
    116: ("DET", "Detroit Tigers", 6),
    117: ("HOU", "Houston Astros", 21),
    118: ("KC", "Kansas City Royals", 7),
    119: ("LAD", "Los Angeles Dodgers", 22),
    120: ("WSH", "Washington Nationals", 24),
    121: ("NYM", "New York Mets", 25),
    133: ("ATH", "Athletics", 10),
    134: ("PIT", "Pittsburgh Pirates", 27),
    135: ("SD", "San Diego Padres", 29),
    136: ("SEA", "Seattle Mariners", 11),
    137: ("SF", "San Francisco Giants", 30),
    138: ("STL", "St. Louis Cardinals", 28),
    139: ("TB", "Tampa Bay Rays", 12),
    140: ("TEX", "Texas Rangers", 13),
    141: ("TOR", "Toronto Blue Jays", 14),
    142: ("MIN", "Minnesota Twins", 8),
    143: ("PHI", "Philadelphia Phillies", 26),
    144: ("ATL", "Atlanta Braves", 16),
    145: ("CWS", "Chicago White Sox", 4),
    146: ("MIA", "Miami Marlins", 20),
    147: ("NYY", "New York Yankees", 9),
    158: ("MIL", "Milwaukee Brewers", 23),
}
ABBR_TO_ID = {v[0]: k for k, v in TEAMS.items()}
FG_TO_ID = {v[2]: k for k, v in TEAMS.items()}
# Aliases seen in FanGraphs "originalteam"/AZ Phil text
ABBR_ALIASES = {"OAK": "ATH", "ARI": "AZ", "WSN": "WSH", "SFG": "SF", "SDP": "SD", "TBR": "TB",
                "KCR": "KC", "CHW": "CWS", "ANA": "LAA"}


def load_seasons() -> dict[int, dict]:
    """Season calendar from the Stats API `/seasons` endpoint, cached in data/raw/seasons.json."""
    p = RAW / "seasons.json"
    return {int(k): v for k, v in json.loads(p.read_text()).items()}


def d(s: str | None) -> dt.date | None:
    return dt.date.fromisoformat(s) if s else None


# Hand-maintained dates the Stats API does not publish. Sources: MLB.com / MLBTR annual coverage.
# trade_deadline = last day trades were allowed; tender = contract-tender deadline;
# rule5 = Rule 5 draft date; reserve_filing = 40-man protection deadline for the Rule 5 draft.
DEADLINES: dict[int, dict[str, str | None]] = {
    2011: {"trade_deadline": "2011-07-31", "tender": "2011-12-12", "rule5": "2011-12-08", "reserve_filing": "2011-11-18"},
    2012: {"trade_deadline": "2012-07-31", "tender": "2012-11-30", "rule5": "2012-12-06", "reserve_filing": "2012-11-20"},
    2013: {"trade_deadline": "2013-07-31", "tender": "2013-12-02", "rule5": "2013-12-12", "reserve_filing": "2013-11-20"},
    2014: {"trade_deadline": "2014-07-31", "tender": "2014-12-02", "rule5": "2014-12-11", "reserve_filing": "2014-11-20"},
    2015: {"trade_deadline": "2015-07-31", "tender": "2015-12-02", "rule5": "2015-12-10", "reserve_filing": "2015-11-20"},
    2016: {"trade_deadline": "2016-08-01", "tender": "2016-12-02", "rule5": "2016-12-08", "reserve_filing": "2016-11-18"},
    2017: {"trade_deadline": "2017-07-31", "tender": "2017-12-01", "rule5": "2017-12-14", "reserve_filing": "2017-11-20"},
    2018: {"trade_deadline": "2018-07-31", "tender": "2018-11-30", "rule5": "2018-12-13", "reserve_filing": "2018-11-20"},
    2019: {"trade_deadline": "2019-07-31", "tender": "2019-12-02", "rule5": "2019-12-12", "reserve_filing": "2019-11-20"},
    2020: {"trade_deadline": "2020-08-31", "tender": "2020-12-02", "rule5": "2020-12-10", "reserve_filing": "2020-11-20"},
    2021: {"trade_deadline": "2021-07-30", "tender": "2021-11-30", "rule5": None, "reserve_filing": "2021-11-19"},  # no Rule 5 draft (lockout)
    2022: {"trade_deadline": "2022-08-02", "tender": "2022-11-18", "rule5": "2022-12-07", "reserve_filing": "2022-11-15"},
    2023: {"trade_deadline": "2023-08-01", "tender": "2023-11-17", "rule5": "2023-12-06", "reserve_filing": "2023-11-14"},
    2024: {"trade_deadline": "2024-07-30", "tender": "2024-11-22", "rule5": "2024-12-11", "reserve_filing": "2024-11-19"},
    2025: {"trade_deadline": "2025-07-31", "tender": "2025-11-21", "rule5": "2025-12-10", "reserve_filing": "2025-11-18"},
    2026: {"trade_deadline": "2026-08-03", "tender": "2026-11-20", "rule5": "2026-12-09", "reserve_filing": "2026-11-17"},
}

# CBA eras. Thresholds that rules read. `effective_to` None = current.
CBA_ERAS: list[dict] = [
    {
        "id": "2017-2021",
        "effective_from": "2017-01-01",
        "effective_to": "2022-03-09",
        "active_max": 26, "active_max_sept": 28, "pitcher_max": 13, "pitcher_max_sept": 14,  # 26/13 from 2020
        "reserve_max": 40,
        "option_years": 3, "option_day_threshold": 20, "optional_assignments_per_season": None,
        "fourth_option_full_seasons": 5, "full_season_active_days": 90,
        "recall_min_days_position": 10, "recall_min_days_pitcher": 10,
        "dfa_days": 7, "outright_waiver_price": 50_000,
        "xix_a_years": 5, "xx_d_years": 3, "xx_b_years": 6, "ten_and_five": (10, 5),
        "service_year_days": 172, "super_two_pct": 0.22, "super_two_prior_days": 86,
        "rule5_price_ml": 100_000, "rule5_price_aaa": 24_000, "rule5_offer_back": 50_000,
        "rule5_active_days": 90, "rule5_age_cut": 18, "rule5_young_drafts": 5, "rule5_old_drafts": 4,
        "rule9_seasons": 7, "xxb_retention_bonus": 100_000,
        "min_salary": {2017: 535_000, 2018: 545_000, 2019: 555_000, 2020: 563_500, 2021: 570_500},
    },
    {
        "id": "2022-2026",
        "effective_from": "2022-03-10",
        "effective_to": "2026-12-01",
        "active_max": 26, "active_max_sept": 28, "pitcher_max": 13, "pitcher_max_sept": 14,
        "reserve_max": 40,
        "option_years": 3, "option_day_threshold": 20, "optional_assignments_per_season": 5,
        "fourth_option_full_seasons": 5, "full_season_active_days": 90,
        "recall_min_days_position": 10, "recall_min_days_pitcher": 15,
        "dfa_days": 7, "outright_waiver_price": 50_000,
        "xix_a_years": 5, "xx_d_years": 3, "xx_b_years": 6, "ten_and_five": (10, 5),
        "service_year_days": 172, "super_two_pct": 0.22, "super_two_prior_days": 86,
        "rule5_price_ml": 100_000, "rule5_price_aaa": 24_000, "rule5_offer_back": 50_000,
        "rule5_active_days": 90, "rule5_age_cut": 18, "rule5_young_drafts": 5, "rule5_old_drafts": 4,
        "rule9_seasons": 7, "xxb_retention_bonus": None,  # eliminated 2023
        "min_salary": {2022: 700_000, 2023: 720_000, 2024: 740_000, 2025: 760_000, 2026: 780_000},
        "qualifying_offer": {2022: 19_650_000, 2023: 20_325_000, 2024: 21_050_000, 2025: 22_025_000},
        "cbt_threshold": {2022: 230e6, 2023: 233e6, 2024: 237e6, 2025: 241e6, 2026: 244e6},
    },
]

# Super Two cutoffs (years.days) actually announced each offseason, keyed by the season just played.
SUPER_TWO_CUTOFF = {2017: "2.123", 2018: "2.134", 2019: "2.115", 2020: "2.125", 2021: "2.116",
                    2022: "2.128", 2023: "2.118", 2024: "2.132", 2025: "2.140"}


def era_for(asof: dt.date) -> dict:
    for e in CBA_ERAS:
        lo = d(e["effective_from"]); hi = d(e["effective_to"]) or dt.date.max
        if lo <= asof <= hi:
            return e
    return CBA_ERAS[-1]


def parse_mls(s: str | None) -> int | None:
    """'5.112' / '5+112' / '5.000' -> total days (172-day years). None if blank/'n/a'."""
    if not s or str(s).strip().lower() in ("n/a", "na", "", "-"):
        return None
    s = str(s).replace("+", ".")
    y, _, dd = s.partition(".")
    return int(y) * 172 + int(dd or 0)


def fmt_mls(days: int | None, sep: str = ".") -> str:
    if days is None:
        return "n/a"
    return f"{days // 172}{sep}{days % 172:03d}"
