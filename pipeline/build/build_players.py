"""Assemble per-player input records and run the rule engine for every organization.

Output: data/processed/players.json.gz (list of engine outputs; 40-man + 60-day IL + Rule 5 pool).

    python -m pipeline.build.build_players
"""
from __future__ import annotations

import datetime as dt
import sys

import pandas as pd

from pipeline import config as C
from pipeline.fetch.statsapi import dump, load, load_people
from pipeline.rules import engine

STATUS_LABEL = {"A": "ACTIVE", "D7": "7-DAY IL", "D10": "10-DAY IL", "D15": "15-DAY IL", "D60": "60-DAY IL",
                "RM": "OPTIONED", "RA": "REHAB", "PL": "PATERNITY", "BRV": "BEREAVEMENT", "RST": "RESTRICTED",
                "SU": "SUSPENDED", "DEC": "DECEASED", "FA": "FREE AGENT", "TR": "TRADED", "ASG": "ASSIGNED"}


def latest_dir(base) -> dt.date:
    return max(dt.date.fromisoformat(p.name) for p in base.iterdir() if p.is_dir())


def main() -> list[dict]:
    today = dt.date.today()
    seasons = C.load_seasons(); era = C.era_for(today)
    ctx = {"today": today, "seasons": seasons, "era": era}
    tx = pd.read_parquet(C.PROCESSED / "transactions.parquet")
    tx_by = {pid: g for pid, g in tx.groupby("mlbam_id")}
    fg_date = latest_dir(C.RAW / "fg_roster"); ct_date = latest_dir(C.RAW / "fg_contracts")
    roster_year_dir = C.RAW / "rosters" / str(today.year)
    snap_dates = sorted({p.name[:10] for p in roster_year_dir.glob("*.json")})
    snap_date = snap_dates[-1]
    od = seasons[today.year]["regularSeasonStartDate"]
    on40_at_od = set()
    for tid in C.TEAMS:
        p_od = roster_year_dir / f"{od}_{tid}.json"
        if p_od.exists():
            on40_at_od |= {r["id"] for r in load(p_od)}
    people = load_people()
    drafts = {}
    for p in (C.RAW / "draft").glob("*.json.gz"):
        for r in load(p):
            if r.get("id") and r.get("signed"):
                drafts[r["id"]] = r
    out, n40 = [], 0
    for team_id, (abbr, _, _) in C.TEAMS.items():
        fg = load(C.RAW / "fg_roster" / fg_date.isoformat() / f"{abbr}.json")
        # a player can have several contracts (old deal + extension): rank by what next season looks like
        def rank(c):
            y = next((y for y in c["years"] if y["season"] == today.year + 1), None)
            t = ((y or {}).get("type") or "").upper()
            return 3 if t == "GUARANTEED" or "OPTION" in t else 2 if t.startswith("ARB") else 1 if t.startswith("PRE") else 0
        contracts = {}
        for c in load(C.RAW / "fg_contracts" / ct_date.isoformat() / f"{abbr}.json.gz"):
            if c.get("mlbamid") and (c["mlbamid"] not in contracts or rank(c) > rank(contracts[c["mlbamid"]])):
                contracts[c["mlbamid"]] = c
        sa = {r["id"]: r for r in load(roster_year_dir / f"{snap_date}_{team_id}.json")}
        forty_count = sum(1 for f in fg if f.get("roster40") == "Y")
        for f in fg:
            pid = f.get("mlbamid")
            if not pid:
                continue
            on_forty = f.get("roster40") == "Y" or f.get("role") == "60IL" or pid in sa
            is_pool = not on_forty and f.get("mlevel") in ("AAA", "AA", "A+", "A", None) and not f.get("isNRI")
            if not on_forty and not is_pool:
                continue
            person = people.get(pid) or {}
            entries = person.get("rosterEntries") or []
            sa_row = sa.get(pid) or {}
            code = sa_row.get("status") or ("D60" if f.get("role") == "60IL" else None)
            fg_type = f.get("type") or ""
            on_option = on_forty and (code == "RM" or (code is None and fg_type.split("-")[0] in ("aaa", "aa", "ha", "la", "ss")))
            if on_forty and code is None:
                code = "RM" if on_option else "A"
            label = STATUS_LABEL.get(code, code or "")
            if on_forty and not on_option and fg_type.startswith("il") and code == "A":
                label = f"{f.get('role')} (FG)"
            club_since = None
            mlb_entries = [e for e in entries if e.get("team") == team_id and e.get("forty")]
            if mlb_entries:
                club_since = C.d(min(e["start"] for e in mlb_entries if e.get("start")))
            first_pro_year = min((int(e["start"][:4]) for e in entries if e.get("start")), default=None)
            d = drafts.get(pid) or {}
            rec = {
                "id": pid, "name": f.get("player") or person.get("fullName"), "team_abbr": abbr, "team_id": team_id,
                "pos": f.get("position") or person.get("pos"), "bats": person.get("bats") or f.get("bats"),
                "throws": person.get("throws") or f.get("throws"), "birth": C.d(person.get("birthDate")),
                "on_forty": on_forty, "on_option": on_option, "on_forty_at_od": pid in on40_at_od, "status_code": code, "status_label": label,
                "il": f.get("role") if fg_type.startswith("il") else None, "injury": f.get("injurynotes") or None,
                "mls_prior": C.parse_mls(f.get("servicetime")), "fg_options": f.get("options"),
                "acquired": f.get("acquired"), "acquired_code": f.get("acquiredcode"), "originalteam": f.get("originalteam"),
                "signyear": f.get("signyear"), "draftyear": f.get("draftyear"), "draft_signing_date": d.get("signingDate"),
                "first_pro_year": first_pro_year, "rosterEntries": entries, "club_since": club_since,
                "contract": contracts.get(pid), "tx": tx_by.get(pid, tx.iloc[0:0]),
                "mlevel": f.get("mlevel"), "fg_type": fg_type, "fg_role": f.get("role"), "age_fg": f.get("age"),
                "club_forty_count": forty_count,
            }
            try:
                out.append(engine.evaluate(rec, ctx))
            except Exception as e:  # keep the build alive, surface the row
                print("ENGINE ERROR", abbr, rec["name"], repr(e), file=sys.stderr)
                raise
            n40 += on_forty
        print(abbr, "done", file=sys.stderr)
    meta = {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "fg_snapshot": fg_date.isoformat(),
            "contracts_snapshot": ct_date.isoformat(), "statsapi_snapshot": snap_date, "season": today.year,
            "cba_era": era["id"], "n_players": len(out), "n_forty": n40}
    dump({"meta": meta, "players": out}, C.PROCESSED / "players.json.gz")
    print(meta, file=sys.stderr)
    return out


if __name__ == "__main__":
    main()
