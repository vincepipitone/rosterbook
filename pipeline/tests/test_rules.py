import datetime as dt

import pandas as pd

from pipeline import config as C
from pipeline.rules import options as O, rule5 as R5, service as S

SEASONS = {2025: {"regularSeasonStartDate": "2025-03-27", "regularSeasonEndDate": "2025-09-28"},
           2026: {"regularSeasonStartDate": "2026-03-25", "regularSeasonEndDate": "2026-09-27"}}
ERA = C.CBA_ERAS[-1]
TODAY = dt.date(2026, 9, 8)


def tx(rows):
    df = pd.DataFrame(rows, columns=["date", "type", "subtype", "description"])
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["effective_date"] = df["date"]
    df["txn_id"] = range(len(df))
    df["season"] = pd.to_datetime(df["date"]).dt.year
    return df


def summarize(rows, season=2026):
    t = tx(rows)
    ivs = O.option_intervals(t, SEASONS, TODAY)
    by = O.option_seasons(ivs, SEASONS, ERA["option_day_threshold"])
    return O.summarize(by, season, ERA), by


def test_nineteen_days_does_not_burn():
    s, by = summarize([("2025-05-01", "optioned", "optioned", ""), ("2025-05-20", "recalled", "recalled", "")])
    assert by[2025].days == 19 and not by[2025].burned
    assert s["option_years_left_entering"] == 3


def test_twenty_days_burns():
    s, by = summarize([("2025-05-01", "optioned", "optioned", ""), ("2025-05-21", "recalled", "recalled", "")])
    assert by[2025].days == 20 and by[2025].burned
    assert s["option_years_left_entering"] == 2


def test_spring_training_days_excluded_and_exempt_from_cap():
    s, by = summarize([("2026-03-10", "optioned", "optioned", ""), ("2026-04-05", "recalled", "recalled", "")])
    assert by[2026].days == 11  # Mar 25 .. Apr 4
    assert by[2026].assignments == 0 and by[2026].assignments_exempt == 1
    assert s["assignments_available"] == 5


def test_il_placement_is_implicit_recall():
    s, by = summarize([("2025-03-24", "optioned", "optioned", ""), ("2025-04-04", "status_change", "il_60", "placed on 60-day IL")])
    assert by[2025].days == 8 and not by[2025].burned


def test_cumulative_days_and_assignment_count():
    s, by = summarize([("2026-04-01", "optioned", "optioned", ""), ("2026-04-11", "recalled", "recalled", ""),
                       ("2026-05-01", "optioned", "optioned", ""), ("2026-05-16", "recalled", "recalled", "")])
    assert by[2026].days == 25 and by[2026].burned
    assert s["assignments_used_this_season"] == 2 and s["assignments_available"] == 3


def test_implied_option_after_selection():
    s, by = summarize([("2026-06-08", "selected", "selected", ""), ("2026-07-31", "recalled", "recalled", "")])
    assert by[2026].intervals[0].source == "implied" and by[2026].days == 53


def test_rule5_age_cut():
    # signed July 2020 at 18 (born 2002-03-25) -> 5th draft after 2020 = 2024
    r = R5.evaluate(dt.date(2002, 3, 25), dt.date(2020, 7, 15), 2024, False, 0, ERA)
    assert r["age_june5"] == 18 and r["clock"] == 5 and r["first_eligible_year"] == 2024 and r["eligible_this_winter"]
    # college signee July 2021 at 21 -> 4th draft = 2024
    r = R5.evaluate(dt.date(2000, 1, 1), dt.date(2021, 7, 15), 2023, False, 0, ERA)
    assert r["clock"] == 4 and r["first_eligible_year"] == 2024 and r["eligible_this_winter"] is False
    # previously outrighted -> always eligible
    r = R5.evaluate(dt.date(2000, 1, 1), dt.date(2021, 7, 15), 2023, False, 1, ERA)
    assert r["eligible_this_winter"]


def test_season_accrual_walks_transactions():
    od, end = dt.date(2026, 3, 25), dt.date(2026, 9, 27)
    t = tx([("2026-06-08", "selected", "selected", ""), ("2026-08-01", "outrighted", "outrighted", "")])
    assert S.season_accrual(t, False, od, TODAY, end, 0) == (dt.date(2026, 8, 1) - dt.date(2026, 6, 8)).days
    assert S.season_accrual(tx([]), True, od, TODAY, end, 0) == (TODAY - od).days + 1


def test_mls_formatting():
    assert C.parse_mls("5+112") == 5 * 172 + 112 and C.fmt_mls(5 * 172 + 112, "+") == "5+112"
    assert C.parse_mls("n/a") is None
