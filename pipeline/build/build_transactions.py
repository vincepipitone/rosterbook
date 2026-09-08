"""Normalize raw Stats API transactions into data/processed/transactions.parquet.

    python -m pipeline.build.build_transactions
"""
from __future__ import annotations

import re
import sys

import pandas as pd

from pipeline import config as C
from pipeline.fetch.statsapi import load

MLB_TEAM_IDS = set(C.TEAMS)

# Stats API typeCode -> our label. NOTE: 'DFA' in the API means DECLARED FREE AGENCY.
TYPE_MAP = {
    "OPT": "optioned", "CU": "recalled", "SE": "selected", "DES": "designated", "OUT": "outrighted",
    "CLW": "claimed", "REL": "released", "TR": "traded", "R5": "rule5_selected", "RTN": "rule5_returned",
    "DFA": "declared_fa", "SFA": "signed_fa", "SGN": "signed", "ASG": "assigned", "SC": "status_change",
    "NUM": "number", "RET": "retired", "DEI": "ineligible", "SU": "suspended", "PUR": "purchased",
}

IL_RE = re.compile(r"placed .*? on the (\d+)-day injured list|placed .*? on the (\d+)-day disabled list", re.I)
IL60_RE = re.compile(r"transferred .*? to the 60-day (injured|disabled) list", re.I)
ACT_RE = re.compile(r"activated .*? from the (\d+)-day (injured|disabled) list|activated .*?\.$", re.I)
REHAB_RE = re.compile(r"rehab assignment", re.I)
OUTRIGHT_RE = re.compile(r"outrighted", re.I)


def classify_sc(desc: str) -> str:
    """Sub-classify 'status change' rows from the description text."""
    if not desc:
        return "sc_other"
    d = desc.lower()
    if IL60_RE.search(d):
        return "il_60_transfer"
    m = IL_RE.search(d)
    if m:
        return f"il_{m.group(1) or m.group(2)}"
    if "activated" in d and ("injured list" in d or "disabled list" in d):
        return "il_activated"
    if "activated" in d:
        return "activated"
    if "paternity" in d:
        return "paternity"
    if "bereavement" in d:
        return "bereavement"
    if "restricted list" in d:
        return "restricted"
    if "roster status changed" in d:
        return "sc_status"
    return "sc_other"


def main() -> pd.DataFrame:
    rows = []
    for p in sorted((C.RAW / "transactions").glob("*.json.gz")):
        for r in load(p):
            person = r.get("person") or {}
            if not person.get("id"):
                continue
            rows.append({
                "txn_id": r.get("id"), "mlbam_id": person["id"], "name": person.get("fullName"),
                "date": r.get("date"), "effective_date": r.get("effectiveDate"), "resolution_date": r.get("resolutionDate"),
                "type_code": r.get("typeCode"), "type": TYPE_MAP.get(r.get("typeCode"), r.get("typeCode")),
                "from_team": (r.get("fromTeam") or {}).get("id"), "to_team": (r.get("toTeam") or {}).get("id"),
                "description": r.get("description") or "",
            })
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["effective_date"] = pd.to_datetime(df["effective_date"]).dt.date
    df["season"] = pd.to_datetime(df["date"]).dt.year
    df["subtype"] = df["type"]
    sc = df["type"] == "status_change"
    df.loc[sc, "subtype"] = df.loc[sc, "description"].map(classify_sc)
    asg = df["type"] == "assigned"
    df.loc[asg & df["description"].str.contains("rehab", case=False), "subtype"] = "rehab"
    df = df.drop_duplicates(subset=["mlbam_id", "date", "type_code", "description"])
    df = df.sort_values(["mlbam_id", "date", "txn_id"]).reset_index(drop=True)
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(C.PROCESSED / "transactions.parquet", index=False)
    print(len(df), "rows;", df["type"].value_counts().head(12).to_dict(), file=sys.stderr)
    return df


if __name__ == "__main__":
    main()
