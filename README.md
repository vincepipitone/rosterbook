# Rosterbook

Every MLB 40-man roster with the rules attached: option years left, optional assignments left this
season, service time, who can refuse an assignment, who is exposed to the Rule 5 draft, and the
plain-English reason for each, derived from the public transaction log and checked nightly against
the best human-maintained sources.

Deploy: import the repo at vercel.com/new (framework Next.js, no env vars); Vercel builds `main` on every push, including the nightly data commit.

## Why

Roster mechanics decide who is expendable, and the public tools mostly stop at "options: 1". This
site reproduces the columns Arizona Phil (@TheCubReporter) keeps by hand for the Cubs, for all 30
clubs, and explains each flag in the voice of his roster-rules guide: *he has an option left, but he
was outrighted once, so a second outright lets him walk.*

The 2022-2026 Basic Agreement expires December 1, 2026. Every threshold in the engine is keyed by
agreement (`pipeline/config.py:CBA_ERAS`), so the next CBA is a data change, not a rewrite.

## What is derived and how

| Field | Method |
|---|---|
| Option years left | Reconstructed from every option/recall/selection/DFA/outright/trade row in the MLB Stats API transaction log since 2010. An option year is used at 20+ regular-season days on optional assignment; spring-training and postseason days are excluded; an MLB injured-list placement while optioned is an implicit recall; a selection followed by a recall with no option row is an implied option. |
| Optional assignments left (5-per-season cap) | Options after Opening Day, minus those within 24h of a trade acquisition. 27th-man doubleheader returns cannot be seen in the log and are counted. |
| Fourth option | Follows FanGraphs when it carries a count, because minor-league IL days (needed for the "five full seasons" test) are not public. |
| Service time through last season | FanGraphs RosterResource. Our own stint-based reconstruction matched it exactly for only ~30% of players, so it is not displayed; the accuracy page says so. |
| Service time this season | Walked from the Opening Day 40-man snapshot through the season's transactions; option days are excluded in a season where they reach 20. |
| Article XIX-A / XX-D / XX-B / Super Two / 10-and-5 | From service time, prior outrights, contract data and the thresholds in `config.py`. |
| Rule 5 eligibility | Signing date (draft record, else FanGraphs signing year) and age on the June 5 before the first contract: 5th draft for 18-and-under, 4th for 19-and-older; previously outrighted players are always eligible. |
| Contract status next season | FanGraphs contract tables (guaranteed years, club/mutual/player options, arbitration years). |

## Accuracy (2026-09-08)

Against Arizona Phil's Cubs 40-man page (49 players): service time 100%, option years 95.9%,
assignments left 98.0%, roster status 98.0%, contract status 95.9%. Against FanGraphs option counts
for all 1,010 players with a value: 96.7% exact. The disagreements are listed on `/validation`
and on each player page. The nightly build fails if these drop.

## Pipeline (python 3.11)

```
python -m pipeline.fetch.statsapi seasons|transactions|rosters|people|people-refresh|draft
python -m pipeline.fetch.fangraphs roster|contracts|tracker
python -m pipeline.fetch.azphil                # Cubs validation set (CC BY-ND; never republished)
python -m pipeline.build.build_transactions    # -> data/processed/transactions.parquet
python -m pipeline.build.build_players         # rule engine for all 30 orgs -> players.json.gz
python -m pytest pipeline/tests -q
python -m pipeline.validate.run                # -> data/validation/validation.json
python -m pipeline.export.export_site_json     # -> public/data/*.json
npm run build                                  # Next.js 16, fully static (1,400 pages)
```

`.github/workflows/nightly-refresh.yml` runs the whole chain at 12:00 UTC and commits the data.

- `pipeline/rules/catalog.py` is the rule catalog (id, era, summary, citation).
- `pipeline/rules/options.py`, `service.py`, `rule5.py` hold the algorithms; `engine.py` turns them
  into flags with reasons.
- `app/` renders `/team/[abbr]`, `/player/[id]`, `/rules`, `/rule5`, `/out-of-options`, `/crunch`,
  `/validation`.

## Sources and terms

MLB Stats API (non-commercial use), FanGraphs RosterResource (one low-volume nightly snapshot;
never called at runtime), The Cub Reporter (CC BY-ND 3.0; rules paraphrased and linked, table used
only for validation), Chadwick Bureau. Not affiliated with MLB, the MLBPA or any club.

## Next

Phase 2 is the transaction-probability model: per player and as-of date, the probability of being
designated, optioned, traded, released, or selected in Rule 5 over the next window, trained on the
2011-2025 log with leave-one-season-out evaluation and SHAP reasons rendered as phrases. The labels,
snapshots and features are already in `data/`.
