"""Roster-aware tender model.

For a player at a September / season-end snapshot, the question is whether the club has a job for
him at his role next season. We rebuild each club's *returning* depth at his role (40-man players at
the role minus that offseason's departing free agents), rank everyone by a Marcel-style WAR
projection built from FanGraphs WAR history, and record where he lands: rank among returners, the
projection of the player at the last job slot for that role, and his margin over that bar. A
binary LightGBM is trained on those features (plus his own mechanics) to predict "kept through the
offseason" (not designated or released within 90 days), leave-one-season-out, and compared with the
same model without the roster-fit features.

Role job counts (last slot that normally survives a winter): SP 8, RP 9, C 3, IF 8, OF 7.

    python -m pipeline.model.roster_fit          # train + evaluate + score the current snapshot
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from collections import defaultdict

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score

from pipeline import config as C
from pipeline.fetch.statsapi import dump, load, load_people

ROLES = ["SP", "RP", "C", "IF", "OF"]
JOBS = {"SP": 8, "RP": 9, "C": 3, "IF": 8, "OF": 7}
PRIOR_PA, PRIOR_IP = 400.0, 120.0   # regression toward 0 WAR
FIT_FEATS = ["fit_rank", "fit_returners", "fit_bar", "fit_margin", "fit_above", "fit_proj", "fit_role", "fit_departing", "fit_share_of_jobs"]
OWN_FEATS = ["age", "yrs_since_debut", "status_code", "options_left_est", "opt_days_this_season", "war_prev", "war_cur", "war_prev2",
             "il_days_this_season", "n40", "n60", "prior_outrights", "recent_trade", "recent_claim", "mls_start", "phase"]
PARAMS = dict(objective="binary", learning_rate=0.04, num_leaves=15, min_data_in_leaf=80, feature_fraction=0.8, bagging_fraction=0.8,
              bagging_freq=1, lambda_l2=5.0, verbose=-1, seed=7)
ROUNDS = 300


def load_war() -> dict:
    war = {}
    for p in (C.RAW / "fg_war").glob("*.json.gz"):
        y, grp = p.stem.replace(".json", "").split("_")
        for r in load(p):
            d = war.setdefault((r["xMLBAMID"], int(y)), {})
            if grp == "bat":
                d.update(bwar=r.get("WAR") or 0.0, pa=r.get("PA") or 0)
            else:
                d.update(pwar=r.get("WAR") or 0.0, ip=r.get("IP") or 0.0, g=r.get("G") or 0, gs=r.get("GS") or 0)
    return war


def marcel(war: dict, pid: int, season: int, through_current: bool) -> float:
    """3/2/1-weighted WAR over the last three seasons (incl. the current one when through_current),
    regressed toward 0 by a playing-time prior. Season = the season just played / being played."""
    ys = [season, season - 1, season - 2] if through_current else [season - 1, season - 2, season - 3]
    wts = [3, 2, 1]
    num = den = 0.0
    is_pitcher = False
    for y, w in zip(ys, wts):
        d = war.get((pid, y))
        if not d:
            continue
        pt = (d.get("pa") or 0) + 4.3 * (d.get("ip") or 0)   # PA-equivalents
        tot = (d.get("bwar") or 0.0) + (d.get("pwar") or 0.0)
        num += w * tot; den += w * pt
        if (d.get("ip") or 0) > (d.get("pa") or 0) / 4.3:
            is_pitcher = True
    if den == 0:
        return 0.0
    prior = 4.3 * PRIOR_IP if is_pitcher else PRIOR_PA
    rate = num / den                     # WAR per PA-equivalent
    full = 600.0                          # a full season in PA-equivalents
    return rate * full * (den / (den + prior))


def role_of(war: dict, pid: int, pos: str | None, season: int, date: dt.date) -> str:
    p = (pos or "").upper()
    if p == "C":
        return "C"
    if p in ("1B", "2B", "3B", "SS", "IF", "DH", "UT"):
        return "IF"
    if p in ("LF", "CF", "RF", "OF"):
        return "OF"
    if p not in ("P", "SP", "RP", "LHP", "RHP", "TWP", "CL"):
        return "IF"
    if p == "SP":
        return "SP"
    if p in ("RP", "CL"):
        return "RP"
    for y in ((season, season - 1) if date >= dt.date(season, 9, 1) else (season - 1, season - 2)):
        d = war.get((pid, y))
        if d and d.get("g"):
            return "SP" if (d.get("gs") or 0) / d["g"] >= 0.5 else "RP"
    return "RP"


def fit_features(roster: list[dict], departing: set, war: dict, season: int, date: dt.date, proj_override: dict | None = None) -> dict[int, dict]:
    """Per player: rank among returning players at his role by projection, bar, margin."""
    roles = {r["id"]: role_of(war, r["id"], r.get("pos"), season, date) for r in roster}
    proj = {r["id"]: (proj_override or {}).get(r["id"], marcel(war, r["id"], season, date >= dt.date(season, 9, 1))) for r in roster}
    by_role: dict[str, list] = defaultdict(list)
    for r in roster:
        if r["id"] not in departing:
            by_role[roles[r["id"]]].append((proj[r["id"]], r["id"]))
    out = {}
    for r in roster:
        pid = r["id"]; role = roles[pid]
        returners = sorted(by_role[role], reverse=True)
        ids = [i for _, i in returners]
        rank = ids.index(pid) + 1 if pid in ids else len(ids) + 1
        jobs = JOBS[role]
        bar = returners[jobs - 1][0] if len(returners) >= jobs else (returners[-1][0] if returners else 0.0)
        out[pid] = {"fit_role": ROLES.index(role), "fit_proj": proj[pid], "fit_rank": rank, "fit_returners": len(ids),
                    "fit_bar": bar, "fit_margin": proj[pid] - bar, "fit_above": sum(1 for p_, i in returners if p_ > proj[pid] and i != pid),
                    "fit_departing": sum(1 for r2 in roster if roles[r2["id"]] == role and r2["id"] in departing),
                    "fit_share_of_jobs": rank / jobs, "role": role, "departing": pid in departing,
                    "returners": [(i, round(p_, 2)) for p_, i in returners]}
    return out


def build_training(panel: pd.DataFrame, war: dict) -> pd.DataFrame:
    seasons = C.load_seasons()
    tx = pd.read_parquet(C.PROCESSED / "transactions.parquet")
    departing: dict[tuple[int, int], set] = defaultdict(set)
    for y, s in seasons.items():
        ws = C.d(s.get("postSeasonEndDate"))
        if not ws:
            continue
        fa = tx[(tx["type"] == "declared_fa") & (tx["date"] >= ws - dt.timedelta(days=3)) & (tx["date"] <= ws + dt.timedelta(days=10))]
        for r in fa.itertuples():
            team = r.from_team if not pd.isna(r.from_team) else r.to_team
            if not pd.isna(team):
                departing[(int(team), y)].add(int(r.mlbam_id))
    rows = []
    keep = panel[panel["phase"].isin([4, 5])]   # Sep 1 and season-end snapshots
    for (date, team_id), g in keep.groupby(["date", "team_id"]):
        date = pd.Timestamp(date).date() if not isinstance(date, dt.date) else date
        season = date.year
        roster = [{"id": int(r.mlbam_id), "pos": None, "_pos_group": int(r.pos_group)} for r in g.itertuples()]
        for r in roster:   # panel keeps only the coarse group; map back to a position token the role function accepts
            r["pos"] = {0: "P", 1: "C", 2: "IF", 3: "OF"}[r["_pos_group"]]
        ff = fit_features(roster, departing.get((team_id, season), set()), war, season, date)
        for r in g.itertuples():
            f = ff[int(r.mlbam_id)]
            rows.append({**{k: getattr(r, k) for k in OWN_FEATS + ["mlbam_id", "team_id", "date", "season", "label", "censored"]},
                         **{k: f[k] for k in FIT_FEATS}})
    df = pd.DataFrame(rows)
    df["kept"] = (~df["label"].isin(["designated", "released"])).astype(int)
    return df


def loso(df: pd.DataFrame, feats: list[str]) -> tuple[dict, np.ndarray]:
    oof = np.zeros(len(df))
    for s in sorted(df["season"].unique()):
        if s < 2013:
            continue
        tr, te = (df["season"] != s).values, (df["season"] == s).values
        m = lgb.train(PARAMS, lgb.Dataset(df.loc[tr, feats], df.loc[tr, "kept"]), ROUNDS)
        oof[te] = m.predict(df.loc[te, feats])
    mask = (df["season"] >= 2013).values
    y = df.loc[mask, "kept"].values
    return {"logloss": round(float(log_loss(y, oof[mask])), 4), "auc": round(float(roc_auc_score(y, oof[mask])), 4), "n": int(mask.sum()),
            "base_rate_kept": round(float(y.mean()), 4)}, oof


def main():
    war = load_war()
    panel = pd.read_parquet(C.PROCESSED / "model_panel.parquet")
    df = build_training(panel, war)
    train = df[(df["censored"] == 0) & (df["yrs_since_debut"] >= 2.0)].reset_index(drop=True)   # tender-relevant population
    res_own, _ = loso(train, OWN_FEATS)
    res_fit, oof = loso(train, OWN_FEATS + FIT_FEATS)
    print("own-features only:", res_own, file=sys.stderr)
    print("own + roster fit :", res_fit, file=sys.stderr)
    # stratified read-out: kept rate by rank bucket among returners, starters only
    sp = train[train["fit_role"] == 0]
    strat = sp.groupby(pd.cut(sp["fit_rank"], [0, 5, 8, 10, 13, 40])).agg(kept=("kept", "mean"), n=("kept", "size")).round(3)
    print(strat, file=sys.stderr)
    model = lgb.train(PARAMS, lgb.Dataset(train[OWN_FEATS + FIT_FEATS], train["kept"]), ROUNDS)
    imp = dict(sorted(zip(OWN_FEATS + FIT_FEATS, model.feature_importance("gain").round(0).tolist()), key=lambda kv: -kv[1]))
    # ---- score the current snapshot with live departing set (contract free agents) and live rosters
    players = load(C.PROCESSED / "players.json.gz")["players"]
    today = dt.date.today(); season = today.year
    # system projections (ZiPS / Steamer average) for a second, forward-looking ranking of the live rosters
    sysproj = {}
    pdirs = sorted(d for d in (C.RAW / "fg_proj").glob("*") if d.is_dir()) if (C.RAW / "fg_proj").exists() else []
    if pdirs:
        acc = defaultdict(list)
        for f in pdirs[-1].glob("*.json.gz"):
            for r in load(f):
                if r.get("WAR") is not None:
                    acc[r["xMLBAMID"]].append(float(r["WAR"]))
        sysproj = {k: sum(v) / len(v) for k, v in acc.items()}
    cur = panel[panel["date"] == panel["date"].max()]
    cur_by_team = {t: g for t, g in cur.groupby("team_id")}
    live = {}
    for team_id, (abbr, _, _) in C.TEAMS.items():
        g = cur_by_team.get(team_id)
        if g is None:
            continue
        tp = {p["id"]: p for p in players if p["team"] == abbr and p["on_forty"]}
        dep = {pid for pid, p in tp.items() if (p.get("contract_status") or "").startswith("FREE AGENT") or any(f["rule"] == "mls.xx_b" and f["status"] == "yes" for f in p["flags"])}
        roster = [{"id": int(r.mlbam_id), "pos": (tp.get(int(r.mlbam_id)) or {}).get("pos")} for r in g.itertuples()]
        ff = fit_features(roster, dep, war, season, today)
        ff2 = fit_features(roster, dep, war, season, today, proj_override={r["id"]: sysproj[r["id"]] for r in roster if r["id"] in sysproj})
        X = pd.DataFrame([{**{k: getattr(r, k) for k in OWN_FEATS}, **{k: ff[int(r.mlbam_id)][k] for k in FIT_FEATS}} for r in g.itertuples()])
        X2 = pd.DataFrame([{**{k: getattr(r, k) for k in OWN_FEATS}, **{k: ff2[int(r.mlbam_id)][k] for k in FIT_FEATS}} for r in g.itertuples()])
        P, P2 = model.predict(X), model.predict(X2)
        for r, pk, pk2 in zip(g.itertuples(), P, P2):
            f, f2 = ff[int(r.mlbam_id)], ff2[int(r.mlbam_id)]
            live[int(r.mlbam_id)] = {"p_kept": round(float(pk), 4), "role": f["role"], "rank": f["fit_rank"], "returners": f["fit_returners"],
                                     "bar": round(f["fit_bar"], 2), "proj": round(f["fit_proj"], 2), "margin": round(f["fit_margin"], 2),
                                     "departing": f["fit_departing"], "jobs": JOBS[f["role"]],
                                     "returner_list": [{"id": i, "name": (tp.get(i) or {}).get("name"), "proj": p_} for i, p_ in f["returners"][:12]],
                                     "sys": {"p_kept": round(float(pk2), 4), "rank": f2["fit_rank"], "bar": round(f2["fit_bar"], 2), "proj": round(f2["fit_proj"], 2),
                                             "margin": round(f2["fit_margin"], 2), "has_proj": int(r.mlbam_id) in sysproj,
                                             "returner_list": [{"id": i, "name": (tp.get(i) or {}).get("name"), "proj": p_} for i, p_ in f2["returners"][:12]]}}
    out_dir = C.PROCESSED / "model"; out_dir.mkdir(exist_ok=True)
    report = {"trained_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "n_train": int(len(train)),
              "own_only": res_own, "with_roster_fit": res_fit, "importance": imp,
              "sp_kept_by_rank": {str(k): {"kept": float(v.kept), "n": int(v.n)} for k, v in strat.iterrows()}, "jobs": JOBS}
    dump({"report": report, "live": live}, out_dir / "roster_fit.json.gz")
    print(json.dumps(report, indent=1, default=str)[:1500], file=sys.stderr)


if __name__ == "__main__":
    main()
