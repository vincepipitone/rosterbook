"""MLB Stats API fetchers (free, keyless; non-commercial use per gdx.mlb.com/components/copyright.txt).

    python -m pipeline.fetch.statsapi seasons
    python -m pipeline.fetch.statsapi transactions [--years 2011-2026]
    python -m pipeline.fetch.statsapi rosters   [--years 2011-2026] [--dates snapshot|today]
    python -m pipeline.fetch.statsapi people    (everyone seen in transactions + rosters)
    python -m pipeline.fetch.statsapi draft     [--years 2005-2026]
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from pipeline import config as C

BASE = "https://statsapi.mlb.com/api/v1"
S = requests.Session()
S.headers["User-Agent"] = "rosterbook/0.1 (non-commercial research; github.com/vincepipitone/rosterbook)"


def get(path: str, **params) -> dict:
    for attempt in range(4):
        try:
            r = S.get(f"{BASE}{path}", params=params, timeout=60)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
        except requests.RequestException:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"failed {path} {params}")


def dump(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        with gzip.open(path, "wt") as f:
            json.dump(obj, f, separators=(",", ":"))
    else:
        path.write_text(json.dumps(obj, separators=(",", ":")))


def load(path: Path):
    if path.suffix == ".gz":
        with gzip.open(path, "rt") as f:
            return json.load(f)
    return json.loads(path.read_text())


def years_arg(s: str | None, default: str) -> list[int]:
    s = s or default
    a, _, b = s.partition("-")
    return list(range(int(a), int(b or a) + 1))


# ---------------------------------------------------------------- seasons
def fetch_seasons(years: list[int]) -> dict:
    out = {}
    for y in years:
        out[y] = get("/seasons", sportId=1, season=y)["seasons"][0]
    dump(out, C.RAW / "seasons.json")
    return out


# ---------------------------------------------------------------- transactions
def fetch_transactions(year: int) -> list[dict]:
    rows = get("/transactions", startDate=f"{year}-01-01", endDate=f"{year}-12-31", sportId=1).get("transactions", [])
    dump(rows, C.RAW / "transactions" / f"{year}.json.gz")
    return rows


# ---------------------------------------------------------------- rosters
def snapshot_dates(year: int, seasons: dict) -> list[dt.date]:
    """As-of dates per season: Opening Day, Jun 1, Jul 1, day after deadline, Sep 1, last day,
    reserve-list filing, tender day, Rule 5 draft day, Dec 31."""
    s = seasons[year]
    dl = C.DEADLINES.get(year, {})
    cands = [s["regularSeasonStartDate"], f"{year}-06-01", f"{year}-07-01", s["regularSeasonEndDate"],
             f"{year}-09-01", dl.get("reserve_filing"), dl.get("tender"), dl.get("rule5"), f"{year}-12-31"]
    if dl.get("trade_deadline"):
        cands.append((dt.date.fromisoformat(dl["trade_deadline"]) + dt.timedelta(days=1)).isoformat())
    today = dt.date.today()
    dates = sorted({dt.date.fromisoformat(c) for c in cands if c})
    return [x for x in dates if x <= today]


def fetch_roster(team_id: int, date: dt.date, roster_type: str = "40Man") -> list[dict]:
    p = C.RAW / "rosters" / str(date.year) / f"{date.isoformat()}_{team_id}.json"
    if p.exists():
        return load(p)
    rows = get(f"/teams/{team_id}/roster", rosterType=roster_type, date=date.isoformat()).get("roster", [])
    slim = [{"id": r["person"]["id"], "name": r["person"]["fullName"], "pos": r["position"]["abbreviation"],
             "status": r.get("status", {}).get("code"), "status_desc": r.get("status", {}).get("description"),
             "note": r.get("note")} for r in rows]
    dump(slim, p)
    return slim


def fetch_rosters(years: list[int], mode: str) -> None:
    seasons = C.load_seasons()
    jobs = []
    if mode == "today":
        today = dt.date.today()
        jobs = [(t, today) for t in C.TEAMS]
    else:
        for y in years:
            for date in snapshot_dates(y, seasons):
                jobs += [(t, date) for t in C.TEAMS]
    print(f"{len(jobs)} roster snapshots", file=sys.stderr)
    with ThreadPoolExecutor(6) as ex:
        for i, _ in enumerate(ex.map(lambda j: fetch_roster(*j), jobs)):
            if i % 200 == 0:
                print(i, file=sys.stderr)


# ---------------------------------------------------------------- people
PEOPLE_STORE = C.RAW / "people.json.gz"   # one consolidated file so the nightly action only fetches new ids


def load_people() -> dict[int, dict]:
    if not PEOPLE_STORE.exists():
        return {}
    return {int(k): v for k, v in load(PEOPLE_STORE).items()}


def fetch_people(ids: list[int]) -> None:
    store = load_people()
    todo = sorted(i for i in set(ids) - set(store) if i and i > 0)
    print(f"{len(todo)} people to fetch ({len(store)} cached)", file=sys.stderr)
    for k in range(0, len(todo), 100):
        chunk = todo[k:k + 100]
        data = get("/people", personIds=",".join(map(str, chunk)), hydrate="rosterEntries")
        for p in data.get("people", []):
            slim = {f: p.get(f) for f in ["id", "fullName", "birthDate", "birthCountry", "mlbDebutDate", "draftYear", "active"]}
            slim["pos"] = (p.get("primaryPosition") or {}).get("abbreviation")
            slim["bats"] = (p.get("batSide") or {}).get("code")
            slim["throws"] = (p.get("pitchHand") or {}).get("code")
            slim["height"] = p.get("height"); slim["weight"] = p.get("weight")
            slim["rosterEntries"] = [
                {"team": (e.get("team") or {}).get("id"), "teamName": (e.get("team") or {}).get("name"),
                 "parentOrg": e.get("parentOrgId"), "status": (e.get("status") or {}).get("code"),
                 "start": e.get("startDate"), "end": e.get("endDate"), "forty": e.get("isActiveFortyMan"),
                 "active": e.get("isActive")}
                for e in p.get("rosterEntries", [])]
            store[p["id"]] = slim
        time.sleep(0.2)
    if todo:
        dump({str(k): v for k, v in store.items()}, PEOPLE_STORE)


def refresh_people(ids: list[int]) -> None:
    """Re-fetch rosterEntries for the players we display (current 40-man pool), since stints change."""
    store = load_people()
    ids = [i for i in ids if i and i > 0]
    for k in range(0, len(ids), 100):
        chunk = ids[k:k + 100]
        data = get("/people", personIds=",".join(map(str, chunk)), hydrate="rosterEntries")
        for p in data.get("people", []):
            if p["id"] in store:
                store[p["id"]]["rosterEntries"] = [
                    {"team": (e.get("team") or {}).get("id"), "teamName": (e.get("team") or {}).get("name"),
                     "parentOrg": e.get("parentOrgId"), "status": (e.get("status") or {}).get("code"),
                     "start": e.get("startDate"), "end": e.get("endDate"), "forty": e.get("isActiveFortyMan"),
                     "active": e.get("isActive")}
                    for e in p.get("rosterEntries", [])]
        time.sleep(0.2)
    dump({str(k): v for k, v in store.items()}, PEOPLE_STORE)


def all_known_ids() -> list[int]:
    ids = set()
    for p in (C.RAW / "transactions").glob("*.json.gz"):
        for r in load(p):
            if r.get("person"):
                ids.add(r["person"]["id"])
    for p in (C.RAW / "rosters").rglob("*.json"):
        for r in load(p):
            ids.add(r["id"])
    for d in (C.RAW / "fg_roster").glob("*"):
        for p in d.glob("*.json"):
            ids |= {r["mlbamid"] for r in load(p) if r.get("mlbamid")}
    return sorted(ids)


# ---------------------------------------------------------------- season stats (league-wide, one call per season/group)
HIT_KEYS = ["gamesPlayed", "plateAppearances", "avg", "obp", "slg", "ops", "strikeOuts", "baseOnBalls", "homeRuns", "stolenBases"]
PIT_KEYS = ["gamesPlayed", "gamesStarted", "inningsPitched", "era", "whip", "strikeOuts", "baseOnBalls", "battersFaced", "saves", "homeRuns"]


def fetch_stats(year: int) -> None:
    for group, keys in (("hitting", HIT_KEYS), ("pitching", PIT_KEYS)):
        p = C.RAW / "stats" / f"{year}_{group}.json.gz"
        if p.exists() and year < C.CURRENT_SEASON:
            continue
        data = get("/stats", stats="season", group=group, season=year, sportId=1, playerPool="all", limit=5000)
        rows = []
        for s in (data.get("stats") or [{}])[0].get("splits", []):
            st = s.get("stat", {})
            rows.append({"id": s["player"]["id"], "team": (s.get("team") or {}).get("id"), **{k: st.get(k) for k in keys}})
        dump(rows, p)
        print(year, group, len(rows), file=sys.stderr)


# ---------------------------------------------------------------- draft
def fetch_draft(year: int) -> None:
    data = get(f"/draft/{year}")
    rows = []
    for rnd in data.get("drafts", {}).get("rounds", []):
        for pk in rnd.get("picks", []):
            person = pk.get("person") or {}
            rows.append({"year": year, "round": pk.get("pickRound"), "pick": pk.get("pickNumber"),
                         "id": person.get("id"), "name": person.get("fullName"), "signed": pk.get("isSigned"),
                         "signingDate": pk.get("signingDate"), "bonus": pk.get("signingBonus"),
                         "school": (pk.get("school") or {}).get("name"),
                         "schoolClass": (pk.get("school") or {}).get("schoolClass"),
                         "team": (pk.get("team") or {}).get("id")})
    dump(rows, C.RAW / "draft" / f"{year}.json.gz")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["seasons", "transactions", "rosters", "people", "people-refresh", "draft", "stats"])
    ap.add_argument("--years")
    ap.add_argument("--dates", default="snapshot")
    a = ap.parse_args()
    if a.what == "seasons":
        fetch_seasons(years_arg(a.years, "2005-2026"))
    elif a.what == "transactions":
        for y in years_arg(a.years, f"{C.FIRST_SEASON - 1}-{C.CURRENT_SEASON}"):
            n = len(fetch_transactions(y)); print(y, n, file=sys.stderr)
    elif a.what == "rosters":
        fetch_rosters(years_arg(a.years, f"{C.FIRST_SEASON}-{C.CURRENT_SEASON}"), a.dates)
    elif a.what == "people":
        fetch_people(all_known_ids())
    elif a.what == "people-refresh":
        latest = max(d for d in (C.RAW / "fg_roster").glob("*") if d.is_dir())
        ids = sorted({r["mlbamid"] for p in latest.glob("*.json") for r in load(p) if r.get("mlbamid")})
        refresh_people(ids)
    elif a.what == "stats":
        for y in years_arg(a.years, f"{C.FIRST_SEASON - 1}-{C.CURRENT_SEASON}"):
            fetch_stats(y)
    elif a.what == "draft":
        for y in years_arg(a.years, "2005-2026"):
            fetch_draft(y); print(y, file=sys.stderr)
