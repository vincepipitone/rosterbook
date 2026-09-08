"""Rule 5 eligibility.

Signed at 18 or younger (age on the June 5 preceding the signing): eligible at the 5th Rule 5 draft
after the first qualified season. 19 or older: the 4th. First qualified season = signing year, or the
next year if signed after the minor-league season. Previously outrighted players are always eligible.
"""
from __future__ import annotations

import datetime as dt
import re

MONTHS = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}


def parse_sign_date(signyear: str | None, draftyear: str | None, signing_date: str | None,
                    fallback_year: int | None) -> tuple[dt.date | None, str]:
    """Best available signing date and its source."""
    if signing_date:
        return dt.date.fromisoformat(signing_date[:10]), "draft_signing_date"
    for raw, src in ((signyear, "fg_signyear"), (draftyear, "fg_draftyear")):
        if not raw:
            continue
        s = str(raw).upper().strip()
        m = re.match(r"([A-Z]{3})\s+(\d{4})", s)
        if m:
            return dt.date(int(m.group(2)), MONTHS.get(m.group(1), 7), 15), src
        m = re.match(r"(\d{4})", s)
        if m:
            return dt.date(int(m.group(1)), 7, 15), src + "_yearonly"
    if fallback_year:
        return dt.date(fallback_year, 7, 15), "first_roster_entry"
    return None, "unknown"


def evaluate(birth: dt.date | None, sign: dt.date | None, season: int, on_forty: bool,
             prior_outrights: int, era: dict) -> dict:
    out = {"eligible_this_winter": None, "first_eligible_year": None, "age_june5": None, "clock": None,
           "reason": "", "always_eligible_outright": prior_outrights > 0}
    if sign is None or birth is None:
        out["reason"] = "signing date or birth date unknown"
        return out
    june5 = dt.date(sign.year if (sign.month, sign.day) >= (6, 5) else sign.year - 1, 6, 5)
    age = june5.year - birth.year - ((june5.month, june5.day) < (birth.month, birth.day))
    first_season = sign.year + (1 if sign.month >= 10 else 0)
    n = era["rule5_young_drafts"] if age <= era["rule5_age_cut"] else era["rule5_old_drafts"]
    first_eligible = first_season + n - 1
    out.update(age_june5=age, clock=n, first_eligible_year=first_eligible, first_season=first_season)
    if on_forty:
        out["eligible_this_winter"] = False
        out["reason"] = f"on a 40-man roster (would first be exposed after {first_eligible} otherwise)"
    elif prior_outrights > 0:
        out["eligible_this_winter"] = True
        out["reason"] = "previously outrighted, so eligible every year"
    elif first_eligible <= season:
        out["eligible_this_winter"] = True
        out["reason"] = (f"signed {sign.year} at age {age} on the prior June 5 -> eligible from the {n}th draft after "
                         f"{first_season} ({first_eligible})")
    else:
        out["eligible_this_winter"] = False
        out["reason"] = f"signed {sign.year} at age {age}: not eligible until the {first_eligible} draft"
    return out
