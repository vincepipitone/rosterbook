"""Write public/data/*.json for the Next.js site from data/processed/players.json.gz.

    python -m pipeline.export.export_site_json
"""
from __future__ import annotations

import datetime as dt
import json
import shutil
import sys

from pipeline import config as C
from pipeline.fetch.statsapi import load
from pipeline.rules.catalog import RULES

SUMMARY_KEYS = ["id", "name", "team", "pos", "bats", "throws", "age", "on_forty", "roster_status", "status_code", "on_option",
                "il", "injury", "mls_prior", "mls_prior_days", "mls_now", "mls_this_season_days", "mls_end_proj", "options_left",
                "options_left_source", "fangraphs_options", "burning_this_season", "option_days_this_season",
                "assignments_used", "assignments_available", "prior_outrights", "prior_dfa", "acquired", "acquired_code",
                "contract_status", "contract_status_source", "fourth_option"]


def slim(p: dict) -> dict:
    d = {k: p.get(k) for k in SUMMARY_KEYS}
    d["flags"] = [{k: f.get(k) for k in ("rule", "title", "status", "value", "why", "since")} for f in p["flags"]]
    d["contract"] = p.get("contract", {}).get("description")
    return d


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, separators=(",", ":"), default=str))


def main():
    data = load(C.PROCESSED / "players.json.gz")
    meta, players = data["meta"], data["players"]
    today = dt.date.today(); season = today.year
    seasons = C.load_seasons(); dl = C.DEADLINES.get(season, {})
    ws_end = C.d(seasons[season]["postSeasonEndDate"])
    deadlines = {
        "regular_season_end": seasons[season]["regularSeasonEndDate"],
        "world_series_end_scheduled": seasons[season]["postSeasonEndDate"],
        "il60_reinstate_by": (ws_end + dt.timedelta(days=5)).isoformat(),
        "xxb_free_agency": (ws_end + dt.timedelta(days=1)).isoformat(),
        "reserve_list_filing": dl.get("reserve_filing"), "tender": dl.get("tender"), "rule5_draft": dl.get("rule5"),
        "cba_expires": C.CBA_ERAS[-1]["effective_to"],
    }
    out = C.SITE_DATA
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    teams = []
    for team_id, (abbr, name, _) in C.TEAMS.items():
        roster = [p for p in players if p["team"] == abbr and p["on_forty"]]
        pool = [p for p in players if p["team"] == abbr and not p["on_forty"]]
        r5_exposed = [p for p in pool if p["rule5"].get("eligible_this_winter")]
        team = {
            "abbr": abbr, "name": name, "id": team_id,
            "counts": {"forty": sum(1 for p in roster if p["status_code"] != "D60"), "il60": sum(1 for p in roster if p["status_code"] == "D60"),
                       "optioned": sum(1 for p in roster if p["on_option"]), "out_of_options": sum(1 for p in roster if p["options_left"] == 0 and (p["mls_prior_days"] or 0) < 860),
                       "xxb_fa": sum(1 for p in roster if any(f["rule"] == "mls.xx_b" and f["status"] == "yes" for f in p["flags"])),
                       "arb": sum(1 for p in roster if (p["contract_status"] or "").startswith("SALARY ARBITRATION")),
                       "rule5_exposed": len(r5_exposed), "pool": len(pool)},
            "players": [slim(p) for p in sorted(roster, key=lambda p: ((p["pos"] or "") not in ("SP", "RP", "P", "LHP", "RHP"), p["name"].split()[-1]))],
            "rule5_pool": [{k: p.get(k) for k in ("id", "name", "pos", "age", "acquired", "signyear")} | {"level": None, "rule5": p["rule5"], "prior_outrights": p["prior_outrights"]}
                           for p in sorted(r5_exposed, key=lambda p: p["name"].split()[-1])],
        }
        write(out / "teams" / f"{abbr}.json", team)
        write(out / "players" / f"{abbr}.json", {p["id"]: p for p in roster})
        teams.append({k: team[k] for k in ("abbr", "name", "id", "counts")})
    write(out / "teams.json", {"meta": meta, "deadlines": deadlines, "teams": teams})
    write(out / "rules.json", {"meta": meta, "cba_eras": [{k: v for k, v in e.items() if k in ("id", "effective_from", "effective_to")} for e in C.CBA_ERAS], "rules": RULES})
    ooo = [slim(p) for p in players if p["on_forty"] and p["options_left"] == 0 and (p["mls_prior_days"] or 0) < 860]
    write(out / "out_of_options.json", {"meta": meta, "players": sorted(ooo, key=lambda p: (p["team"], p["name"].split()[-1]))})
    r5 = [{"team": p["team"], **{k: p.get(k) for k in ("id", "name", "pos", "age", "acquired", "signyear", "prior_outrights")}, "rule5": p["rule5"]}
          for p in players if not p["on_forty"] and p["rule5"].get("eligible_this_winter")]
    write(out / "rule5.json", {"meta": meta, "deadlines": deadlines, "players": r5})
    shutil.copy(C.VALIDATION / "validation.json", out / "validation.json")
    print(f"{len(teams)} teams, {len(ooo)} out of options, {len(r5)} Rule 5 exposed -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
