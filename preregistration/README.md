# Preregistration companion files

- Frozen preregistration (v2, 11 October 2026): https://doi.org/10.5281/zenodo.23300369
- `DEVIATIONS.md` — dated deviations from that document, written before any confirmatory data.
- `classify.py` — model-rater script for RQ1 (standard library only; needs a local Ollama endpoint). Changes since the pilot are
  described in deviations D4, D14 point 4, D41 and D42: strict answers, ties unresolved, undefined κ reported, a run manifest
  (models and digests, hashes of cases, criteria and R0), R0 required before a confirmatory run, a complete rater set required for
  agreement, an explicit context window with a truncation guard. Tests: `python3 -m unittest discover -s preregistration/test`.
- `pilot/` — the ten-case pilot of 10 October 2026, run before freezing: the v1 criteria text as used (`criteria-v1.txt`), the
  case summaries (`cases.json`), the author's labels written on 29 September 2026 (`human.json`), the raw answers of the three
  local models (three runs each) and the agreement table. Pilot inputs included date, product and title (see D4).

- `rq1/` — the RQ1 confirmatory set (D1, D41, D44): the dated query (`query_frame.py`, raw results; the two full GitHub advisory
  dumps are kept by the author, hashes in `raw-20261025/`), screening, grouping, eligibility ledger and first-disclosure dates,
  `FRAME-NOTES.md` (every rule and count), the frozen frame `rq1-frame.csv` (330 cases, commit e62676b), and the sample
  `rq1-sample.csv` with `rq1-sample-manifest.json` (120 cases, drand round 6584246). `sample_frame.py verify` (in a clone) or
  `verify_archive.py` (in a release archive, no git history) recomputes the sample; `estimate.py` is the stratified estimator of D44 point 6.

Next confirmatory files, each in its own commit and in this order: `rq1-r0.json` (the author's labels), then the model results.
