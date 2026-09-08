"""Validation: engine vs Arizona Phil (Cubs), vs FanGraphs options (all 40-man), transaction sanity.

Writes data/validation/validation.json (published on /validation).

    python -m pipeline.validate.run
"""
from __future__ import annotations

import csv
import datetime as dt
import glob
import json
import re
import sys

import pandas as pd

from pipeline import config as C
from pipeline.fetch.statsapi import load
from pipeline.ids.names import key

# Each type is compared to the mean of the three prior seasons (current season scaled by the fraction
# of the regular season elapsed). Rule 5 rows only exist in the Stats API from 2024.
SANITY_TYPES = {"designated": 0.5, "traded": 0.5, "optioned": 0.5, "outrighted": 0.5, "released": 0.6, "selected": 0.5}


def norm_status(s: str) -> str:
    s = (s or "").upper()
    s = re.sub(r"\(.*?\)", "", s).strip()
    return {"OPTIONED": "OPTIONED", "ACTIVE": "ACTIVE"}.get(s, s)


def norm_contract(s: str) -> str:
    s = (s or "").upper().replace("PRE-ARBITRTATION", "PRE-ARBITRATION").replace("FREE-AGENT", "FREE AGENT")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def vs_azphil(players: list[dict]) -> dict:
    files = sorted(glob.glob(str(C.VALIDATION / "azphil_cubs_*.csv")))
    if not files:
        # No fresh snapshot (the page blocks some networks): carry the last committed comparison forward.
        prev = C.VALIDATION / "validation.json"
        if prev.exists():
            old = json.loads(prev.read_text())["azphil"]
            old["stale"] = True
            old["note"] = "Arizona Phil's page could not be fetched on this run; comparison carried forward from the last successful one."
            return old
        raise SystemExit("no Arizona Phil snapshot and no previous validation.json")
    az = list(csv.DictReader(open(files[-1])))
    updated = (C.VALIDATION / "azphil_latest.txt").read_text().splitlines()[1]
    ours = {key(p["name"]): p for p in players if p["team"] == "CHC" and p["on_forty"]}
    cols = {"mls": 0, "options": 0, "assignments": 0, "status": 0, "contract": 0}
    rows, n = [], 0
    for r in az:
        p = ours.get(key(r["name"]))
        if not p:
            rows.append({"name": r["name"], "matched": False}); continue
        n += 1
        ours_asg = "N/A" if p["assignments_available"] is None else str(p["assignments_available"])
        cmp = {
            "mls": (r["mls"], p["mls_prior"]),
            "options": (r["options_num"], str(p["options_left"])),
            "assignments": (r["assignments"], ours_asg),
            "status": (norm_status(r["status"]), norm_status(p["roster_status"])),
            "contract": (norm_contract(r["contract"]), norm_contract(p["contract_status"])),
        }
        agree = {k: v[0] == v[1] for k, v in cmp.items()}
        # contract: accept our label as a prefix match either way (his labels carry extra options text)
        a, b = cmp["contract"]
        agree["contract"] = agree["contract"] or a.startswith(b) or b.startswith(a) or (a.startswith("SALARY ARB") and b.startswith("SALARY ARB"))
        for k in cols:
            cols[k] += agree[k]
        rows.append({"name": r["name"], "matched": True, **{k: {"azphil": v[0], "ours": v[1], "agree": agree[k]} for k, v in cmp.items()}})
    return {"source": "thecubreporter.com/cubs-40-man-roster", "page_updated": updated, "compared_on": dt.date.today().isoformat(), "stale": False, "n_rows": len(az), "n_matched": n,
            "agreement": {k: {"n": v, "pct": round(100 * v / n, 1)} for k, v in cols.items()}, "rows": rows}


def vs_fangraphs(players: list[dict]) -> dict:
    n = ok = 0
    conf = {}
    dis = []
    for p in players:
        if not p["on_forty"]:
            continue
        fg = p.get("fangraphs_options")
        if fg is None or not str(fg).isdigit():
            continue
        n += 1
        a, b = int(fg), p["options_left"]
        conf[f"{a}->{b}"] = conf.get(f"{a}->{b}", 0) + 1
        if a == b:
            ok += 1
        else:
            dis.append({"name": p["name"], "team": p["team"], "fangraphs": a, "ours": b, "burned": list(map(str, p["option_history"].keys()))})
    return {"source": "FanGraphs RosterResource options (current snapshot)", "n": n, "exact": ok, "pct": round(100 * ok / n, 1),
            "confusion": conf, "disagreements": dis[:80]}


def txn_sanity() -> dict:
    tx = pd.read_parquet(C.PROCESSED / "transactions.parquet")
    by = tx.groupby(["season", "type"]).size().unstack().fillna(0).astype(int)
    out = {"years": {}, "ok": True}
    seasons = C.load_seasons()
    for y in range(2015, C.CURRENT_SEASON + 1):
        row = {}
        for t, tol in SANITY_TYPES.items():
            v = int(by.loc[y, t]) if t in by.columns and y in by.index else 0
            prior = [int(by.loc[k, t]) for k in (y - 1, y - 2, y - 3) if k in by.index and k != 2020 and t in by.columns]
            base = sum(prior) / len(prior) if prior else v
            scale = 1.0
            if y == C.CURRENT_SEASON:
                od, end = C.d(seasons[y]["regularSeasonStartDate"]), C.d(seasons[y]["regularSeasonEndDate"])
                scale = min(1.0, max(0.1, (dt.date.today() - dt.date(y, 1, 1)).days / (dt.date(y, 12, 31) - dt.date(y, 1, 1)).days))
            ok = y == 2020 or abs(v - base * scale) <= tol * base * scale
            row[t] = {"n": v, "expected": round(base * scale), "ok": ok}
            if y >= C.CURRENT_SEASON - 2:
                out["ok"] &= ok
        out["years"][y] = row
    return out


def main():
    data = load(C.PROCESSED / "players.json.gz")
    players = data["players"]
    res = {"generated_at": data["meta"]["generated_at"], "azphil": vs_azphil(players), "fangraphs": vs_fangraphs(players),
           "transactions": txn_sanity(),
           "service_time_note": ("Service time through the prior season is taken from FanGraphs RosterResource. Our own "
                                 "reconstruction from Stats API roster stints matched FanGraphs exactly for only ~30% of "
                                 "players (52% within 10 days) because stint flags are unreliable before ~2022 and the 2021 "
                                 "option log has gaps, so it is not used for display yet.")}
    C.VALIDATION.mkdir(parents=True, exist_ok=True)
    (C.VALIDATION / "validation.json").write_text(json.dumps(res, indent=1, default=str))
    a = res["azphil"]["agreement"]; f = res["fangraphs"]
    print(f"AZ Phil: matched {res['azphil']['n_matched']}/{res['azphil']['n_rows']}; " + ", ".join(f"{k} {v['pct']}%" for k, v in a.items()), file=sys.stderr)
    print(f"FanGraphs options: {f['exact']}/{f['n']} = {f['pct']}%  confusion {f['confusion']}", file=sys.stderr)
    print("txn sanity ok:", res["transactions"]["ok"], file=sys.stderr)
    for r in res["azphil"]["rows"]:
        if not r.get("matched"):
            print("  unmatched:", r["name"], file=sys.stderr)
        else:
            bad = [k for k in ("mls", "options", "assignments", "status", "contract") if not r[k]["agree"]]
            if bad:
                print("  ", r["name"], {k: (r[k]["azphil"], r[k]["ours"]) for k in bad}, file=sys.stderr)
    return res


if __name__ == "__main__":
    main()
