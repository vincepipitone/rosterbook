"""Arizona Phil's Cubs 40-man roster page (thecubreporter.com, CC BY-ND 3.0) as a VALIDATION set.

We never republish his table; we parse it to score our own engine against it.

    python -m pipeline.fetch.azphil
"""
from __future__ import annotations

import csv
import datetime as dt
import html as htmllib
import re
import sys

import requests

from pipeline import config as C

URL = "https://www.thecubreporter.com/cubs-40-man-roster"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
COLS = ["name", "dob", "bt", "hw", "mls", "options", "assignments", "status", "contract"]


def strip(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    return htmllib.unescape(s).replace("\xa0", " ").strip()


def parse(text: str) -> tuple[str, list[dict]]:
    updated = re.search(r"LAST UPDATED:\s*([\d-]+)", text)
    updated = updated.group(1) if updated else ""
    table = re.search(r'<table class="table cubs-roster.*?</table>', text, re.S).group(0)
    rows, group = [], ""
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if 'colspan' in tr:
            group = strip(tds[0]); continue
        if len(tds) != len(COLS):
            continue
        cells = [strip(t) for t in tds]
        notes = re.findall(r'#note(\d+)', tds[5])
        rec = dict(zip(COLS, cells))
        rec["options_num"] = re.match(r"\s*(\d+|N/A)", rec["options"]).group(1)
        rec["notes"] = "+".join(notes)
        rec["group"] = group
        rows.append(rec)
    return updated, rows


def fetch() -> None:
    r = requests.get(URL, headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    updated, rows = parse(r.text)
    C.VALIDATION.mkdir(parents=True, exist_ok=True)
    out = C.VALIDATION / f"azphil_cubs_{dt.date.today().isoformat()}.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    (C.VALIDATION / "azphil_latest.txt").write_text(f"{out.name}\n{updated}\n")
    print(f"{len(rows)} rows, page updated {updated} -> {out.name}", file=sys.stderr)


if __name__ == "__main__":
    fetch()
