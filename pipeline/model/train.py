"""Train and evaluate the transaction-probability model; predict for the current snapshot.

Multiclass LightGBM over {none, designated, optioned, traded, released} in the next 90 days.
Evaluation: leave-one-season-out 2013-2025 on uncensored rows, multiclass log loss against a
phase-conditional base-rate model, one-vs-rest AUC per class, decile calibration for designated.
Reasons: LightGBM's built-in SHAP (pred_contrib) rendered as phrases.

    python -m pipeline.model.train
"""
from __future__ import annotations

import datetime as dt
import json
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score

from pipeline import config as C
from pipeline.fetch.statsapi import dump, load
from pipeline.model.build_panel import LABELS

FEATURES = ["phase", "status_code", "pos_group", "age", "yrs_since_debut", "n40", "n60", "in_season", "days_to_end", "day_of_year",
            "prior_outrights", "prior_dfa", "prior_claims", "prior_trades", "prior_options", "prior_releases", "n_txn",
            "days_with_club", "join_type", "opts_this_season", "il_this_season", "opt_years_used", "opt_days_this_season",
            "options_left_est", "p_pa", "p_ops", "p_k", "p_bb", "p_hr", "p_ip", "p_era", "p_whip", "p_gs", "p_pk", "p_pbb", "mls_start"]
CATS = ["phase", "status_code", "pos_group", "join_type"]
PARAMS = dict(objective="multiclass", num_class=len(LABELS), learning_rate=0.05, num_leaves=31, min_data_in_leaf=200,
              feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=5.0, verbose=-1, seed=7)
ROUNDS = 400

PHRASES = {
    "options_left_est": "option years left", "opt_years_used": "option years used", "opt_days_this_season": "option days this season",
    "opts_this_season": "times optioned this season", "status_code": "roster status", "phase": "time of year", "age": "age",
    "yrs_since_debut": "years since debut", "n40": "club's 40-man count", "n60": "club's 60-day IL count", "prior_outrights": "prior outrights",
    "prior_dfa": "prior DFAs", "prior_claims": "prior waiver claims", "prior_trades": "prior trades", "prior_options": "career options",
    "days_with_club": "time with the club", "join_type": "how he was acquired", "p_ops": "last season's OPS", "p_era": "last season's ERA",
    "p_pa": "last season's plate appearances", "p_ip": "last season's innings", "p_k": "last season's strikeout rate",
    "p_pk": "last season's strikeout rate", "p_bb": "last season's walk rate", "p_pbb": "last season's walk rate", "p_whip": "last season's WHIP",
    "p_gs": "last season's starts", "p_hr": "last season's home runs", "mls_start": "service time", "pos_group": "position",
    "il_this_season": "IL stints this season", "prior_releases": "prior releases", "n_txn": "transaction history length",
    "in_season": "in-season", "days_to_end": "days left in the season", "day_of_year": "calendar", "p_pa": "last season's plate appearances",
}


def prep(df: pd.DataFrame) -> pd.DataFrame:
    X = df[FEATURES].copy()
    for c in CATS:
        X[c] = X[c].astype("category")
    return X


def base_rates(train: pd.DataFrame) -> pd.DataFrame:
    return train.groupby("phase")["y"].value_counts(normalize=True).unstack().reindex(columns=range(len(LABELS))).fillna(0)


def evaluate(df: pd.DataFrame) -> dict:
    res = {"seasons": {}, "features": FEATURES}
    oof = np.zeros((len(df), len(LABELS)))
    base = np.zeros_like(oof)
    for s in sorted(df["season"].unique()):
        if s < 2013:
            continue
        tr, te = df["season"] != s, df["season"] == s
        m = lgb.train(PARAMS, lgb.Dataset(prep(df[tr]), df.loc[tr, "y"], categorical_feature=CATS), ROUNDS)
        oof[te.values] = m.predict(prep(df[te]))
        br = base_rates(df[tr])
        base[te.values] = br.reindex(df.loc[te, "phase"]).fillna(0).values
        ll = log_loss(df.loc[te, "y"], oof[te.values], labels=list(range(len(LABELS))))
        llb = log_loss(df.loc[te, "y"], np.clip(base[te.values], 1e-6, 1), labels=list(range(len(LABELS))))
        aucs = {}
        for k, lab in enumerate(LABELS):
            yk = (df.loc[te, "y"] == k).astype(int)
            aucs[lab] = round(float(roc_auc_score(yk, oof[te.values][:, k])), 3) if 0 < yk.sum() < len(yk) else None
        res["seasons"][int(s)] = {"n": int(te.sum()), "logloss": round(ll, 4), "logloss_base": round(llb, 4), "auc": aucs}
        print(s, int(te.sum()), round(ll, 4), round(llb, 4), aucs, file=sys.stderr)
    mask = df["season"] >= 2013
    res["pooled"] = {"n": int(mask.sum()),
                     "logloss": round(log_loss(df.loc[mask, "y"], oof[mask.values], labels=list(range(len(LABELS)))), 4),
                     "logloss_base": round(log_loss(df.loc[mask, "y"], np.clip(base[mask.values], 1e-6, 1), labels=list(range(len(LABELS)))), 4),
                     "auc": {lab: round(float(roc_auc_score((df.loc[mask, "y"] == k).astype(int), oof[mask.values][:, k])), 3) for k, lab in enumerate(LABELS)}}
    # calibration by decile, per event class
    cal = {}
    for k, lab in enumerate(LABELS[1:], start=1):
        p = oof[mask.values][:, k]; y = (df.loc[mask, "y"] == k).astype(int).values
        q = pd.qcut(pd.Series(p), 10, labels=False, duplicates="drop")
        g = pd.DataFrame({"p": p, "y": y, "q": q}).groupby("q").agg(pred=("p", "mean"), actual=("y", "mean"), n=("y", "size"))
        cal[lab] = [{"pred": round(float(r.pred), 4), "actual": round(float(r.actual), 4), "n": int(r.n)} for r in g.itertuples()]
    res["calibration"] = cal
    return res


def explain(model: lgb.Booster, X: pd.DataFrame, k: int, top: int = 3) -> list[list[dict]]:
    contrib = model.predict(X, pred_contrib=True)
    n_feat = X.shape[1]
    block = contrib[:, k * (n_feat + 1): (k + 1) * (n_feat + 1)][:, :n_feat]
    out = []
    for i in range(len(X)):
        order = np.argsort(-np.abs(block[i]))[:top]
        out.append([{"feature": FEATURES[j], "label": PHRASES.get(FEATURES[j], FEATURES[j]), "value": _val(X.iloc[i, j]),
                     "contrib": round(float(block[i, j]), 3)} for j in order if abs(block[i, j]) > 0.02])
    return out


def _val(v):
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return float(v) if isinstance(v, (int, float, np.floating, np.integer)) else str(v)


def main(do_eval: bool = True):
    df = pd.read_parquet(C.PROCESSED / "model_panel.parquet")
    df["y"] = df["label"].map({l: i for i, l in enumerate(LABELS)})
    train = df[df["censored"] == 0].reset_index(drop=True)
    prev = C.PROCESSED / "model" / "predictions.json.gz"
    if do_eval or not prev.exists():
        report = evaluate(train)
        report["evaluated_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    else:
        report = load(prev)["report"]   # weekly evaluation carried forward; nightly run only refits
    model = lgb.train(PARAMS, lgb.Dataset(prep(train), train["y"], categorical_feature=CATS), ROUNDS)
    out_dir = C.PROCESSED / "model"; out_dir.mkdir(exist_ok=True)
    model.save_model(str(out_dir / "model.txt"))
    imp = dict(zip(FEATURES, model.feature_importance("gain").round(0).tolist()))
    report["importance"] = dict(sorted(imp.items(), key=lambda kv: -kv[1])[:20])
    # predictions for the latest snapshot
    latest = df["date"].max()
    cur = df[df["date"] == latest].reset_index(drop=True)
    X = prep(cur)
    P = model.predict(X)
    reasons_dfa = explain(model, X, LABELS.index("designated"))
    reasons_opt = explain(model, X, LABELS.index("optioned"))
    preds = {}
    for i, r in cur.iterrows():
        preds[int(r["mlbam_id"])] = {"team_id": int(r["team_id"]), **{f"p_{lab}": round(float(P[i, k]), 4) for k, lab in enumerate(LABELS)},
                                     "reasons_designated": reasons_dfa[i], "reasons_optioned": reasons_opt[i]}
    meta = {"trained_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "asof": str(latest), "horizon_days": 90,
            "n_train": int(len(train)), "seasons": f"{int(train['season'].min())}-{int(train['season'].max())}", "labels": LABELS,
            "base_rates": train["label"].value_counts(normalize=True).round(4).to_dict()}
    dump({"meta": meta, "report": report, "predictions": preds}, out_dir / "predictions.json.gz")
    print(json.dumps({"pooled": report["pooled"], "importance": report["importance"]}, indent=1), file=sys.stderr)


if __name__ == "__main__":
    import sys as _s
    main(do_eval="--no-eval" not in _s.argv)
