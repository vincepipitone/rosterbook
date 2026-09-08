"""FanGraphs RosterResource snapshots (options remaining, service time, contract acquisition).

One pull per team per night, cached forever under data/raw/fg_roster/{date}/. FanGraphs does not
publish this as an API; keep volume minimal and never call it from the site at runtime.

    python -m pipeline.fetch.fangraphs roster
    python -m pipeline.fetch.fangraphs tracker --years 2020-2026
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time

from curl_cffi import requests

from pipeline import config as C
from pipeline.fetch.statsapi import dump, years_arg

KEEP = ["teamid", "loaddate", "type", "role", "position", "jnum", "player", "playerNameRoute", "handed", "bats",
        "throws", "age", "acquired", "acquiredcode", "options", "servicetime", "signyear", "signround", "signpick",
        "draftyear", "draftround", "draftpick", "school", "country", "originalteam", "mlbamid", "playerid",
        "minormasterid", "roster40", "isNRI", "mlevel", "injurynotes", "injurydate", "notes", "eta",
        "proj_WAR", "actual_WAR", "actual_PT", "proj_PT"]


def get(url: str):
    for attempt in range(4):
        r = requests.get(url, impersonate="chrome", timeout=60)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("application/json"):
            return r.json()
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"FanGraphs blocked: {url} -> {r.status_code}")


def fetch_roster(date: dt.date | None = None) -> None:
    date = date or dt.date.today()
    out_dir = C.RAW / "fg_roster" / date.isoformat()
    for team_id, (abbr, _, fgid) in C.TEAMS.items():
        p = out_dir / f"{abbr}.json"
        if p.exists():
            continue
        rows = get(f"https://www.fangraphs.com/api/depth-charts/roster?teamid={fgid}")
        slim = [{k: r.get(k) for k in KEEP} for r in rows]
        for s in slim:
            s["team_id"] = team_id
        dump(slim, p)
        print(abbr, len(slim), sum(1 for s in slim if s.get("roster40") == "Y"), file=sys.stderr)
        time.sleep(1.5)


def fetch_contracts(season: int, date: dt.date | None = None) -> None:
    """Contract table per team (guaranteed years, club/mutual/player options, arb years, 2027 status)."""
    date = date or dt.date.today()
    out_dir = C.RAW / "fg_contracts" / date.isoformat()
    for team_id, (abbr, _, fgid) in C.TEAMS.items():
        p = out_dir / f"{abbr}.json.gz"
        if p.exists():
            continue
        data = get(f"https://www.fangraphs.com/api/roster-resource/contracts/team-2020?teamid={fgid}&season={season}")
        slim = []
        for c in data.get("players", []):
            s = c.get("contractSummary") or {}
            slim.append({
                "mlbamid": s.get("MLBAMID"), "name": s.get("playerName"), "servicetime": s.get("servicetime"),
                "contract_type": s.get("ContractType"), "no_trade": s.get("NoTradeNotes"), "description": c.get("description"),
                "start": s.get("startSeason"), "end": s.get("endSeason"), "end_all": s.get("endSeasonAll"),
                "total": s.get("ContractTotal"), "aav": s.get("AAV"), "years_total": s.get("YearsTotal"),
                "has_club_option": s.get("hasClubOption"), "has_mutual_option": s.get("hasMutualOption"),
                "has_vesting_option": s.get("hasVestingOption"),
                "years": [{"season": y.get("Season"), "type": y.get("Type"), "salary": y.get("Salary"),
                           "option_notes": y.get("OptionNotes"), "arb_year": y.get("ArbYear"),
                           "arb_proj": y.get("ArbSalaryProjection"), "status": y.get("Status")}
                          for y in c.get("contractYears", []) if y.get("Season")],
            })
        dump(slim, p)
        print(abbr, len(slim), file=sys.stderr)
        time.sleep(1.5)


def fetch_tracker(years: list[int]) -> None:
    for y in years:
        rows = get(f"https://www.fangraphs.com/api/roster-resource/transaction-tracker/data?season={y}")
        dump(rows, C.RAW / "fg_tracker" / f"{y}.json.gz")
        print(y, len(rows), file=sys.stderr)
        time.sleep(2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["roster", "tracker", "contracts"])
    ap.add_argument("--years")
    a = ap.parse_args()
    if a.what == "roster":
        fetch_roster()
    elif a.what == "contracts":
        fetch_contracts(C.CURRENT_SEASON)
    else:
        fetch_tracker(years_arg(a.years, "2020-2026"))
