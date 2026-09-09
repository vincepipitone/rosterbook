"""Feature-group ablation for the transaction model: add each candidate group to the current
feature set and score held-out (leave-one-season-out) log loss, overall and on the tender-window
snapshots (reserve-list filing and tender day), plus one-vs-rest AUC for designated / released.

    python -m pipeline.model.ablate
"""
from __future__ import annotations

import json
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score

from pipeline import config as C
from pipeline.model.build_panel import LABELS
import pipeline.model.train as T

GROUPS = {
    "war": ["war_prev", "war_prev2", "war_cur", "wrc_prev", "fip_prev", "xfip_prev", "sv_prev", "war_delta"],
    "role": ["gs_share_prev"],
    "rank": ["war_rank_group", "war_rank_pct", "war_gap_group"],
    "injury": ["il_days_this_season", "on_il60"],
    "recency": ["dfa_365", "claims_365", "outrights_365", "moves_365", "days_since_txn", "rule5_pick"],
    "team": ["team_pct", "team_rd"],
    # positional supply (2026-09-09): starter/reliever split from games-started share, counts per role, departing FAs per role
    "supply": ["role", "role_n", "role_vets", "sp_n"],
    "supply+departing": ["role", "role_n", "role_vets", "sp_n", "role_departing", "role_net", "sp_departing"],
}


def run(df: pd.DataFrame, feats: list[str]) -> dict:
    T.FEATURES = feats  # prep() reads the module global
    oof = np.zeros((len(df), len(LABELS)))
    for s in sorted(df["season"].unique()):
        if s < 2013:
            continue
        tr, te = df["season"] != s, df["season"] == s
        m = lgb.train(T.PARAMS, lgb.Dataset(T.prep(df[tr]), df.loc[tr, "y"], categorical_feature=T.CATS), T.ROUNDS)
        oof[te.values] = m.predict(T.prep(df[te]))
    mask = (df["season"] >= 2013).values
    tender = mask & df["phase"].isin([6, 7]).values
    y = df["y"].values
    out = {"logloss": log_loss(y[mask], oof[mask], labels=list(range(5))),
           "logloss_tender": log_loss(y[tender], oof[tender], labels=list(range(5))),
           "auc_designated": roc_auc_score((y[mask] == 1).astype(int), oof[mask, 1]),
           "auc_released": roc_auc_score((y[mask] == 4).astype(int), oof[mask, 4]),
           "auc_released_tender": roc_auc_score((y[tender] == 4).astype(int), oof[tender, 4]),
           "auc_designated_tender": roc_auc_score((y[tender] == 1).astype(int), oof[tender, 1])}
    return {k: round(float(v), 4) for k, v in out.items()}


def main(only: list[str] | None = None):
    df = pd.read_parquet(C.PROCESSED / "model_panel.parquet")
    df["y"] = df["label"].map({l: i for i, l in enumerate(LABELS)})
    df = df[df["censored"] == 0].reset_index(drop=True)
    base = list(T.FEATURES)
    out_p = C.PROCESSED / "model" / "ablation.json"
    results = json.loads(out_p.read_text()) if out_p.exists() else {}
    configs = {"base": base, **{"+" + g: base + [c for c in cols if c not in base] for g, cols in GROUPS.items()},
               "+all": base + [c for cols in GROUPS.values() for c in cols if c not in base]}
    for name, cols in configs.items():
        if only and name not in only:
            continue
        results[name] = run(df, cols)
        print(name, results[name], file=sys.stderr, flush=True)
        out_p.parent.mkdir(exist_ok=True)
        out_p.write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:] or None)
