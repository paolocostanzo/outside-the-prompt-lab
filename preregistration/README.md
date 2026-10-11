# Preregistration companion files

- Frozen preregistration (v2, 11 October 2026): https://doi.org/10.5281/zenodo.23300369
- `DEVIATIONS.md` — dated deviations from that document, written before any confirmatory data.
- `classify.py` — model-rater script for RQ1 (standard library only; needs a local Ollama endpoint). Changes since the pilot are
  described in deviation D4.
- `pilot/` — the ten-case pilot of 10 October 2026, run before freezing: the v1 criteria text as used (`criteria-v1.txt`), the
  case summaries (`cases.json`), the author's labels written on 29 September 2026 (`human.json`), the raw answers of the three
  local models (three runs each) and the agreement table. Pilot inputs included date, product and title (see D4).

Confirmatory files (`rq1-frame.csv`, `rq1-r0.json`, model results) are added here in that order, each in its own commit.
