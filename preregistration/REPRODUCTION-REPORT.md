# Reproduction report

## The one command

From the repository root, in a git clone or in the release archive (no `.git` needed), with Python >= 3.11:

    python3 -I reproduce.py

It runs every scripted analysis offline into a temporary directory and compares each regenerated output with the committed
one. It exits 0 when every check passes, 1 otherwise. (`python3 reproduce.py --tests` also runs the test suites; not part of
this report.)

## Without git history (reviewer item A13)

RQ1 reads three files as they are in the frame commit named in `preregistration/rq1/rq1-sample-manifest.json`
(`frame_commit`): the frame `rq1-frame.csv`, the sampler `sample_frame.py` and `estimate.py` (bound to the frame commit, D44).
`preregistration/rq1/frame-commit-pins.json` records the SHA-256 of each, computed with `git show <frame_commit>:<path>` from
the repository history. All three working-tree files are byte-identical to their frame-commit copies, so no byte copy is
shipped.

- With git history, the frame-commit copy is read and must equal its pin; otherwise the analysis stops.
- Without git history, the working-tree file is accepted only if its SHA-256 equals the pin (and, for the frame and the
  sampler, the hash in the sample manifest); otherwise the analysis stops (fails closed). A pin that contradicts the manifest
  also stops it.

The confirmatory logic and outputs are unchanged: the regenerated RQ1 outputs equal the committed ones in both settings.

## Expected outputs and their state

Run on 2026-11-01, once from a git clone (history present) and once from a copy of the tracked files without `.git`. Both runs
exited 0 and printed the same 22 OK lines, the same saved-result check and the same two private-data lines. The only
difference is the wording of the sample check: "frame from the frame commit" with history, and "frame from the working tree,
accepted by its recorded SHA-256" without it.

| RQ | Output (committed file) | State |
|---|---|---|
| RQ1 | primary analysis, JSON (`preregistration/runs/rq1-confirmatory-20261027T142818Z-rq1-analysis/RESULTS-RQ1.json`, without `run_dir`) | recomputed from public data |
| RQ1 | primary analysis, report (`.../RESULTS-RQ1.md`) | recomputed from public data |
| RQ1 | disagreement, exploratory D51, JSON (`.../EXPLORATORY-DISAGREEMENT.json`, without `run_dir`) | recomputed from public data |
| RQ1 | disagreement, exploratory D51, report (`.../EXPLORATORY-DISAGREEMENT.md`) | recomputed from public data |
| RQ1 | flag vs disagreement, two-sided Fisher exact test (`preregistration/rq1/fisher-flags.json`) | recomputed from public data |
| RQ1 | provenance of R0's labels (`.../R0-PROVENANCE.txt`) | recomputed from public data |
| RQ2 | matrix summary (`trusting-a-repo/evidence/q5-summary.md`) | recomputed from public data |
| RQ3 | primary analysis (`tool-change/evidence/primary-20261015/analysis/analysis.json`) | recomputed from public data |
| RQ3 | primary matrix (`.../analysis/matrix.csv`, without the `dir` column) | recomputed from public data |
| RQ3 | preregistered coder agreement (`.../coding/agreement.json`) | recomputed from public data |
| RQ3 | three-coder agreement (`.../coding/codex/agreement-three.json`) | recomputed from public data |
| RQ3 | positive control, exploratory D52 (`tool-change/evidence/positive-control-20261028/coded.csv`, without `dir`) | recomputed from public data |
| RQ3 | open-weight cells, exploratory D39 (`tool-change/evidence/open-weight-20261024/RESULTS.json`) | recomputed from public data |
| RQ4 | final census (`defence-coverage/results-20261024/final-census.csv`) | recomputed from public data |
| RQ4 | coverage, JSON (`.../coverage.json`, without `inputs_sha256`) | recomputed from public data |
| RQ4 | coverage, report (`.../COVERAGE.md`) | recomputed from public data |
| RQ5 | scores: author, second author, host (`telemetry/evidence/scores-20261024/scores-*.json`) | recomputed from public data |
| RQ5 | H5 verdict: author, second author (`.../h5-*.json`) | recomputed from public data |
| RQ5 | agreement of the two rule authors (`.../agreement.json`) | recomputed from public data |
| RQ1 | frame hash, seed and sample of 120 | compared with a saved result (the drand beacon value is the one stored in the manifest; it is checked online only with `verify_archive.py online`) |
| RQ4 | full readings behind `coverage.json` `inputs_sha256` | not regenerable from public inputs (private; the published CSVs are filtered to the six published servers) |
| RQ5 | the score inputs (`input-*.json`) themselves | not regenerable from public inputs (extracted from private log archives) |

The Fisher exact test that the paper used to call "computed outside the reproduction script" now has its own script,
`preregistration/rq1/fisher_flags.py` (standard library, exact fractions). It reads the regenerated D51 output and uses the
cases that have a model majority. The disagreement (four classes) between R0 and the majority is 10 of 71 flagged cases and
3 of 46 non-flagged cases, i.e. the table [[10, 61], [3, 43]]. The two-sided p is 0.243014, which rounds to 0.24 as in the paper.

Also outside these checks, as listed in the `reproduce.py` docstring: figures the paper reads directly from evidence tables
(RQ2 re-checks, the non-interactive and graphical cells, RQ3 graphical clients), and the values read by hand.

## What this is and is not

This reproduces the analyses: from the committed evidence, the scripts give the same numbers the paper reports. It is **not a
replication of client behaviour**. It does not re-run any agent client, VM, model or capture. Model-rater answers, human
labels and codings, client captures and the RQ5 log archives are taken as committed, and they cannot be regenerated from the
public inputs. Whether today's clients still behave as recorded is a separate question, which only a new run can answer.
