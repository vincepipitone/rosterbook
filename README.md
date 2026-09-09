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

Rules: the 2022-2026 Basic Agreement (MLBPA's published PDF, mirrored at `public/cba/`); every
catalog entry cites article and printed page and deep-links to the PDF page (Articles are offset
+14 from printed numbering, Attachments +16). Mechanics that live in the Major League Rules (Rule 5
eligibility, waiver order, option-year count, the 60-day IL calendar) cite the incorporating article
and name the rule. Data: MLB Stats API (non-commercial use), FanGraphs RosterResource (one
low-volume nightly snapshot; never called at runtime), The Cub Reporter (validation only, CC BY-ND),
Chadwick Bureau. Not affiliated with MLB, the MLBPA or any club.

## The model

`pipeline/model/build_panel.py` turns every dated 40-man snapshot since 2011 (~190k player-snapshot
rows) into as-of features plus the first club-driven event in the next 90 days (designated /
optioned / traded / released-or-non-tendered / none). `train.py` fits a multiclass LightGBM,
evaluates it leave-one-season-out (pooled log loss 0.550 vs 0.730 for a time-of-year base rate;
AUC designated .86, optioned .93, released .87, traded .72), publishes decile calibration and
feature gain on `/model`, and scores the current snapshot with built-in SHAP reasons. Features include
this season's line (for snapshots from September 1 on), whether the player was acquired by trade
or claim in the last 60 days, and positional depth on the 40-man. Outputs feed the board (cut /
option risk), each player page, and `/non-tender` (arbitration-eligible players ranked by cut risk
through the tender deadline, with ZiPS projected WAR, this year's WAR, acquisition and the club's
departing same-position free agents shown as context the model does not weigh).

Also on each player page: post-season eligibility as it stands (Major League Rule 40 mechanics)
and what an option, DFA/outright, release, trade or the offseason would mean for him.
