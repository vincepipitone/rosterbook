"""Training panel for the transaction-probability model.

Unit: one row per (40-man player, roster snapshot date). Snapshots are the dated 40-man pulls in
data/raw/rosters (Opening Day, Jun 1, Jul 1, day after the deadline, Sep 1, season end, reserve-list
filing, tender day, Rule 5 draft, Dec 31) plus today's. Label: the first club-driven event in the
next HORIZON days among designated (incl. a direct outright), optioned, traded, released
(incl. a non-tender), else none. Features use only information dated before the snapshot.

    python -m pipeline.model.build_panel
"""
from __future__ import annotations

import bisect
import datetime as dt
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

from pipeline import config as C
from pipeline.fetch.statsapi import load, load_people
from pipeline.rules import options as O

HORIZON = 90
LABELS = ["none", "designated", "optioned", "traded", "released"]
JOIN_TYPES = {"selected", "claimed", "traded", "signed_fa", "rule5_selected", "purchased"}
PHASES = {"od": 0, "jun": 1, "jul": 2, "deadline": 3, "sep": 4, "end": 5, "filing": 6, "tender": 7, "rule5": 8, "dec": 9, "today": 10}


def phase_of(date: dt.date, seasons: dict) -> str:
    y = date.year
    s = seasons.get(y)
    if s is None:
        return "today"
    od, end = C.d(s["regularSeasonStartDate"]), C.d(s["regularSeasonEndDate"])
    dl = C.DEADLINES.get(y, {})
    if date == od:
        return "od"
    if date == end:
        return "end"
    for k, v in (("filing", dl.get("reserve_filing")), ("tender", dl.get("tender")), ("rule5", dl.get("rule5"))):
        if v and date == C.d(v):
            return k
    if dl.get("trade_deadline") and date == C.d(dl["trade_deadline"]) + dt.timedelta(days=1):
        return "deadline"
    if date.month == 6 and date.day == 1:
        return "jun"
    if date.month == 7 and date.day == 1:
        return "jul"
    if date.month == 9 and date.day == 1:
        return "sep"
    if date.month == 12 and date.day == 31:
        return "dec"
    return "today"


def pos_group(pos: str | None) -> int:
    p = (pos or "").upper()
    if p in ("P", "SP", "RP", "LHP", "RHP", "TWP"):
        return 0
    if p == "C":
        return 1
    if p in ("1B", "2B", "3B", "SS", "IF", "DH"):
        return 2
    return 3


def main() -> pd.DataFrame:
    seasons = C.load_seasons()
    today = dt.date.today()
    tx = pd.read_parquet(C.PROCESSED / "transactions.parquet")
    tx = tx.sort_values(["mlbam_id", "date", "txn_id"])
    people = load_people()
    # season stats keyed by (id, year)
    stats: dict[tuple[int, int], dict] = {}
    for p in (C.RAW / "stats").glob("*.json.gz"):
        y, grp = p.stem.replace(".json", "").split("_")
        for r in load(p):
            d = stats.setdefault((r["id"], int(y)), {})
            if grp == "hitting":
                d.update(pa=r.get("plateAppearances"), ops=_f(r.get("ops")), k_pct=_rate(r.get("strikeOuts"), r.get("plateAppearances")),
                         bb_pct=_rate(r.get("baseOnBalls"), r.get("plateAppearances")), hr=r.get("homeRuns"))
            else:
                d.update(ip=_f(r.get("inningsPitched")), era=_f(r.get("era")), whip=_f(r.get("whip")), gs=r.get("gamesStarted"),
                         pk_pct=_rate(r.get("strikeOuts"), r.get("battersFaced")), pbb_pct=_rate(r.get("baseOnBalls"), r.get("battersFaced")))
    # FanGraphs tracker season-start service time 2020+
    fg_mls: dict[tuple[int, int], int] = {}
    for p in (C.RAW / "fg_tracker").glob("*.json.gz"):
        y = int(p.stem.replace(".json", ""))
        for r in load(p):
            if r.get("mlbamid") and r.get("servicetime"):
                v = C.parse_mls(str(r["servicetime"]))
                if v is not None and (r["mlbamid"], y) not in fg_mls:
                    fg_mls[(r["mlbamid"], y)] = v
    # per-player transaction arrays and option intervals
    ptx = {pid: g for pid, g in tx.groupby("mlbam_id")}
    opt_cache: dict[int, list] = {}

    def opt_ivs(pid):
        if pid not in opt_cache:
            g = ptx.get(pid)
            opt_cache[pid] = O.option_intervals(g, seasons, today) if g is not None and len(g) else []
        return opt_cache[pid]

    rows = []
    files = sorted((C.RAW / "rosters").rglob("*.json"))
    print(len(files), "snapshots", file=sys.stderr)
    for k, f in enumerate(files):
        date = dt.date.fromisoformat(f.name[:10]); team_id = int(f.stem.split("_")[1])
        if date.year not in seasons:
            continue
        roster = load(f)
        n40 = sum(1 for r in roster if r.get("status") != "D60"); n60 = sum(1 for r in roster if r.get("status") == "D60")
        phase = phase_of(date, seasons)
        season = date.year
        od = C.d(seasons[season]["regularSeasonStartDate"]); end = C.d(seasons[season]["regularSeasonEndDate"])
        horizon_end = date + dt.timedelta(days=HORIZON)
        for r in roster:
            pid = r["id"]
            g = ptx.get(pid)
            person = people.get(pid, {})
            birth = C.d(person.get("birthDate")); debut = C.d(person.get("mlbDebutDate"))
            # ---- history before date
            feat = dict(mlbam_id=pid, team_id=team_id, date=date, season=season, phase=PHASES[phase],
                        status=r.get("status") or "A", pos_group=pos_group(r.get("pos")),
                        age=(date - birth).days / 365.25 if birth else np.nan,
                        yrs_since_debut=(date - debut).days / 365.25 if debut and debut <= date else (0.0 if debut is None else -1.0),
                        n40=n40, n60=n60, in_season=int(od <= date <= end), days_to_end=(end - date).days,
                        day_of_year=date.timetuple().tm_yday)
            if g is not None and len(g):
                before = g[g["date"] < date]
                vc = before["type"].value_counts()
                feat.update(prior_outrights=int(vc.get("outrighted", 0)), prior_dfa=int(vc.get("designated", 0)),
                            prior_claims=int(vc.get("claimed", 0)), prior_trades=int(vc.get("traded", 0)),
                            prior_options=int(vc.get("optioned", 0)), prior_releases=int(vc.get("released", 0)),
                            n_txn=len(before))
                joins = before[before["type"].isin(JOIN_TYPES) & ~((before["type"] == "signed_fa") & before["description"].str.contains("minor league", case=False))]
                if len(joins):
                    j = joins.iloc[-1]
                    feat.update(days_with_club=(date - j["date"]).days, join_type={"selected": 0, "claimed": 1, "traded": 2, "signed_fa": 3, "rule5_selected": 4, "purchased": 5}[j["type"]])
                else:
                    feat.update(days_with_club=np.nan, join_type=-1)
                sb = before[before["season"] == season]
                feat.update(opts_this_season=int((sb["type"] == "optioned").sum()), il_this_season=int(sb["subtype"].str.startswith("il_").sum()))
                # option years used before this season and days this season before date
                ivs = opt_ivs(pid)
                used = len({iv.season for iv in ivs if iv.season < season and iv.days >= 20})
                days_this = 0
                for iv in ivs:
                    if iv.season == season and iv.start < date:
                        e = iv.end if iv.end is not None and iv.end < date else date
                        days_this += max(0, (min(e, end + dt.timedelta(days=1)) - max(iv.start, od)).days)
                feat.update(opt_years_used=used, opt_days_this_season=days_this, options_left_est=max(0, 3 - used))
                # ---- label: first event in the horizon
                after = g[(g["date"] >= date) & (g["date"] <= horizon_end)]
                label = "none"; label_days = np.nan
                for e in after.itertuples():
                    t = e.type
                    lab = None
                    if t in ("designated", "outrighted"):
                        lab = "designated"
                    elif t == "optioned":
                        lab = "optioned"
                    elif t == "traded":
                        lab = "traded"
                    elif t == "released":
                        lab = "released"
                    elif t == "declared_fa":
                        tender = C.d(C.DEADLINES.get(season, {}).get("tender"))
                        if tender and abs((e.date - tender).days) <= 2:
                            lab = "released"
                    if lab:
                        label, label_days = lab, (e.date - date).days
                        break
                feat.update(label=label, label_days=label_days)
            else:
                feat.update(prior_outrights=0, prior_dfa=0, prior_claims=0, prior_trades=0, prior_options=0, prior_releases=0, n_txn=0,
                            days_with_club=np.nan, join_type=-1, opts_this_season=0, il_this_season=0, opt_years_used=0,
                            opt_days_this_season=0, options_left_est=3, label="none", label_days=np.nan)
            # ---- prior-season performance (leak-free)
            ps = stats.get((pid, season - 1), {})
            feat.update(p_pa=ps.get("pa"), p_ops=ps.get("ops"), p_k=ps.get("k_pct"), p_bb=ps.get("bb_pct"), p_hr=ps.get("hr"),
                        p_ip=ps.get("ip"), p_era=ps.get("era"), p_whip=ps.get("whip"), p_gs=ps.get("gs"), p_pk=ps.get("pk_pct"), p_pbb=ps.get("pbb_pct"),
                        mls_start=fg_mls.get((pid, season)))
            rows.append(feat)
        if k % 500 == 0:
            print(k, file=sys.stderr)
    df = pd.DataFrame(rows)
    df["status_code"] = df["status"].map({"A": 0, "D10": 1, "D15": 1, "D7": 1, "D60": 2, "RM": 3, "RA": 1}).fillna(4).astype(int)
    df["censored"] = (df["date"] + pd.to_timedelta(HORIZON, "D") > pd.Timestamp(today).date()).astype(int) if False else ((pd.to_datetime(df["date"]) + pd.Timedelta(days=HORIZON)) > pd.Timestamp(today)).astype(int)
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(C.PROCESSED / "model_panel.parquet", index=False)
    print(len(df), "rows;", df["label"].value_counts(normalize=True).round(3).to_dict(), file=sys.stderr)
    return df


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _rate(a, b):
    try:
        return float(a) / float(b) if b else None
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
