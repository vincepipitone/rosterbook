# Rosterbook conventions

- Python is `python3.11`; run modules from the repo root (`python3.11 -m pipeline...`).
- Data and the code that produced it go in the same commit. Never write into another checkout from a job.
- Numbers shown on the site must have a validation path (`pipeline/validate/run.py`) or an honest
  "source" field. Do not add a derived column without one.
- Rule thresholds live in `pipeline/config.py:CBA_ERAS`, never inline in rule code. New CBA = new era entry.
- Arizona Phil's table is a validation set only (CC BY-ND). Paraphrase rules in `catalog.py`; link, don't copy.
- FanGraphs: one nightly pull per endpoint, cached under `data/raw/fg_*`. Never call it from the site.
- Site is fully static; every page reads `public/data` at build time. `npm run build` must exit 0 before pushing.
- Ship: sync `origin/main`, descriptive `<area>: <what>` commit, push `HEAD:main` (Vercel builds main).
