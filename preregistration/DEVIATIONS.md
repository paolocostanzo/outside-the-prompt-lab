# Deviations from the preregistration

Preregistration v2, frozen 11 October 2026: https://doi.org/10.5281/zenodo.23300369 (section 8 says deviations are logged with
date and reason). This file is that log, made public so that the date of each entry is fixed by the repository history.
Every entry below was written **before any confirmatory data** for RQ1, RQ3 or RQ5 was collected. Each one is listed again
in the paper's threats to validity.

Format: ID · date · section of the preregistration · what changes · why · effect on confirmatory claims.

---

### D1 · 11 Oct 2026 · §3 dataset — sampling frame for RQ1
**Change.** The frame is the union of the two event timelines kept by the author for the window 26 June – 24 September 2026,
identified by their SHA-256 at freeze time:

- `01-timeline.md` (main) — `8cb3ea33b42e771f8fa910c9dc52ee5382e2d16236634ce0026d978c2ee2ae17`
- `01-timeline.md` (second compilation, cross-check) — `db72c6ffa48fee3c718ac7114261e19f01139d19fda17d4b6380f4bf89970750`

plus one dated query of the GitHub Advisory Database and NVD for the same window (keywords: MCP, Model Context Protocol, AI
agent, coding agent, Copilot, Claude Code, Cursor, Gemini CLI, Codex). The query date and raw results are recorded. The
resulting case list (ID, date, product, primary source, include/exclude with reason) is committed to this folder as
`rq1-frame.csv` **before** R0 classifies any new case.
**Why.** §3 names one file; a second compilation exists, and a file kept by the author is not an independent frame. The
database query adds an external, reproducible source.
**Effect.** None on the hypotheses; the frame can only grow, and every exclusion is listed with its reason.

### D2 · 11 Oct 2026 · §1 H1 — strength of the test
**Change.** No change to H1 (share in classes 1–3 ≥ 60%). Added note: in the ten-case pilot the share was 70% for all raters,
so H1 is a weak test; the paper reports the share with a 95% Wilson interval and does not present H1 alone as evidence for the
taxonomy. The informative quantities are the interval and agreement (H1a).
**Why.** A threshold close to an already observed value says little.
**Effect.** Interpretation only.

### D3 · 11 Oct 2026 · §3–§4 — independence of R0
**Change.** R0 (the author) classifies every confirmatory case from primary sources and commits the labels (file
`rq1-r0.json`, with commit hash recorded in the paper) before any model rater is run on any confirmatory case. The ten pilot
cases are excluded from the confirmatory set's agreement statistics and reported separately.
**Why.** The author saw model outputs on the pilot; committing labels first is the only verifiable protection.
**Effect.** Agreement statistics are computed on the confirmatory set only.

### D4 · 11 Oct 2026 · §4 — model rater inputs and records
**Change.** (a) The pilot sent date, product and title together with the summary; §4 says "one case summary". From now on the
model raters receive the summary only (`classify.py`, user message `Summary: …`). (b) The class-word check matches whole words
("class" and "classes"), as listed in §3. (c) Each result file records the model's full SHA-256 digest from the engine, of which
the 12-character ids in §4 are the prefix. (d) Note on seeds: at temperature 0 the three runs test determinism, not sampling
variability; they are reported as such.
**Why.** Product names and CVE titles can cue the class; the pilot's inputs did not match the text of §4.
**Effect.** Pilot κ values (§7) were obtained with the richer input and the v1 criteria; they are reported as pilot only.
The v1 criteria text and raw pilot outputs are in `pilot/`.

### D5 · 11 Oct 2026 · §6 Q3 protocol — size of the matrix
**Change.** Primary (confirmatory) design: 6 terminal clients (Claude Code, Codex CLI, Gemini CLI, Qwen Code, Cursor CLI,
Goose) × change signal {none, `notifications/tools/list_changed`} × change = description only × transport stdio × vendor-hosted
engine × 5 repetitions. VS Code + Copilot and Cursor IDE are run by hand on the same primary cells with 5 repetitions where
feasible; fewer repetitions are reported as such. Secondary (exploratory, 1 repetition): schema change, name change, Streamable
HTTP, local engine (only for clients that accept a custom model endpoint).
**Why.** The full factorial (2 × 2 × 3 × 2 levels × 5 repetitions per client) is not feasible in the planned week; H3 concerns
the default behaviour on a definition change, which the primary cells test directly.
**Effect.** H3 is tested on the primary cells only. Secondary cells are labelled exploratory.

### D6 · 11 Oct 2026 · §1 RQ5/H5 and Q4 protocol — detection metric
**Change.** Operational definition: the baseline (two hours of scripted normal use per terminal client) is split into
1-minute windows; a rule's false-positive rate is the share of baseline windows in which it fires, and "distinguishable" means
the rule fires on every event run and on ≤ 5% of baseline windows. RQ5 confirmatory analysis uses only event runs recorded after
the freeze, under the Q4 telemetry configuration; earlier Q5 captures are exploratory.
**Why.** "Below 5% per hour" was ambiguous for a two-hour baseline (two observations).
**Effect.** H5 becomes measurable; threshold unchanged.

### D7 · 11 Oct 2026 · §5 — aggregation rules
**Change.** H3: a client's outcome is the modal outcome over its primary cells; ties are reported as mixed and counted against
H3's "at most one client" clause only if one of the tied outcomes is re-approval. H1: "majority class of the model raters" is the
per-case majority of R1–R3 (R4 if run); a case with no majority counts as **not** in classes 1–3 (against H1).
**Why.** §5 did not say how cells and raters are combined.
**Effect.** Conservative for both hypotheses.

### D8 · 11 Oct 2026 · §5–§6 — wording of the scope
**Change.** "Systems owned by the author" reads: systems controlled by the author, including the author's own vendor accounts
and a rented GPU instance.
**Why.** Vendor-hosted engines and the cloud GPU are not owned but are under the author's control.
**Effect.** None.

### D9 · 11 Oct 2026 · §5 RQ4 (exploratory) — summary statistic
**Change.** The headline figure for RQ4 is the mean of per-server coverage on the primary count, 61% (median 57%), as in the
Q2 protocol.
**Why.** An earlier draft quoted a different summary.
**Effect.** Exploratory question; reporting only.

### D10 · 11 Oct 2026 · §5 RQ2 (exploratory) — Q5 protocol statement on Codex
**Correction.** The Q5 protocol (28 Sep 2026) states that Codex reads only a global MCP configuration. Measurement showed that
Codex CLI reads a project `.codex/config.toml` after the trust decision. The protocol keeps the original text with a dated
correction note; results always reflected the measured behaviour.
**Effect.** None on results.

### D11 · 12 Oct 2026 · header — target journal
**Change.** The target journal named in the preregistration header, *Transactions on Machine Learning Research* (TMLR), is replaced
by *Empirical Software Engineering* (Springer).
**Why.** The study is an empirical measurement of developer tools (configuration, approval dialogs, connectors) and does not
address learning methods, which is TMLR's stated scope; it falls squarely within the scope of *Empirical Software Engineering*.
**Effect.** None on research questions, hypotheses, classification criteria, dataset, raters, measurements or analysis plan.
Review becomes single-blind instead of double-blind, so the paper cites the preregistration with the author's name.
