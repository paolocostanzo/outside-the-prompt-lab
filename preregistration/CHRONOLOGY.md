# Chronology of decisions, per research question

**Read `chronology.csv` for the full register.** It has one row per decision: every deviation D1–D55 (D50 and D55 split
into their points, because they differ in timing), the pilot, the H1 threshold of 60%, the H1a threshold of 0.6, the
other choices made in preregistration v2, and the freezes of rules, frames, samples and labels. Each row gives the
decision, its date, its commit, where the timestamp can be checked, which data were visible, its effect on a verdict, and
whether it was prospective, made during collection or made after results. This page is a summary of that file.

## How to check a date

- **`origin/master (pushed …)`**: the commit is in the public repository. The push time comes from the local reflog of
  `origin/master`, which can be checked on the hosting service. Pushes before 15 Oct 2026 16:10 are older than the local
  reflog, so for those rows the time of the first Zenodo version is the check.
- **`Zenodo vX`**: the first archived release that holds the commit. These are external timestamps: v0.2.1 (13 Oct),
  v0.3.0 (17 Oct), v0.4.0–v0.4.2 (24 Oct), v0.4.3 (25 Oct). D45–D47, the RQ1 analysis script and the R0 labels are on
  `origin/master` (pushed 26 Oct) but are not in any Zenodo version before v0.5.0.
- **`local until v0.5.0`**: D48–D55, the RQ1 confirmatory run (3f13bef) and the D52 positive control. These dates rest on
  local commit times, which the author sets, until the v0.5.0 release is published. The paper's Appendix D says the same.
- **`external`**: the preregistration v2 deposit (Zenodo 10.5281/zenodo.23300369, 11 Oct), the blog post of 29 Sep, and
  drand round 6584246 (25 Oct 20:00 UTC) for the RQ1 sample. No Internet Archive capture of the blog post has been
  checked. The pilot (10 Oct) and the author's pilot labels (29 Sep) come before the repository (first commit 11 Oct),
  so no commit dates them.
- Two dates differ from the entries' own headers: D26 is dated 17 Oct but was first committed on 22 Oct (b1d6104, before
  any Q4 run), and D50 is headed 28 Oct but was committed on 27 Oct at 23:40 CET.

Timing is judged against the confirmatory data of the research question concerned. *Prospective*: none of that data
existed yet; exploratory or pilot data may have existed, and the "data visible" column names them. *During collection*:
some of that data had been collected, but no outcome had been read or scored. *After results*: outcomes were known. RQ2
and RQ4 are exploratory, so no decision on them can change a confirmatory verdict.

## Counts by timing (rows; a row on several RQs counts once for each)

| RQ | prospective | during collection | after results | rows |
|---|---|---|---|---|
| RQ1 | 22 | 2 | 7 | 31 |
| RQ2 (exploratory) | 0 | 0 | 3 | 3 |
| RQ3 | 10 | 1 | 9 | 20 |
| RQ4 (exploratory) | 0 | 0 | 11 | 11 |
| RQ5 | 11 | 8 | 6 | 25 |
| all | 2 | 0 | 2 | 4 |
| **unique rows** | **42** | **11** | **33** | **86** |

No decision made after results changed a confirmatory figure or verdict. All of them are reporting, corrections or
analyses labelled exploratory or post hoc (D50–D55).

## RQ1 (H1 share ≥ 60%, H1a Fleiss' κ ≥ 0.6). Verdict: H1 supported but not robust; H1a not supported

Decisions that could change or did change the verdict, from highest to lowest impact:
1. **D41 point 6** (prospective, 25 Oct, before the frame). Counting the contested cases against H1 gives a share of 32.6%,
   so this rule makes H1 *not robust*. **D44** (prospective, after the frame and before any summary) replaced the
   population with a probability sample of 120 cases from the 330-case frame.
2. **60% threshold** (11 Oct, set after the author's 7/10 on the pilot). A weak test (D2). The primary estimates are 90.1%
   for R0 and 92.6% for the model majority.
3. **H1a 0.6** (11 Oct, fixed with the pilot κ of 0.91 known). Observed κ is 0.458, so only a threshold of 0.45 or lower
   would reverse the result.
4. **D7 and D43**: no-majority cases count against H1, and R2 is not the preregistered build. Without R2 the majority falls
   to 73.4%, and H1 holds on the point estimate only; κ without R2 is 0.408.
5. **R0's input and calibration**: summaries written by AI (D42), read in Italian (D46), labelled through guided questions
   (D47), all prospective. The worked pilot examples shown before R0 (D50.1) were decided on 26 Oct but recorded only
   after the results.

Post hoc (D55.4, after results): with 28 ambiguous cases counted as class 4, the share is 69.3% for R0 and 71.0% for the
majority. Both lower bounds fall below 60%. This is reported, and the preregistered verdict does not change.

## RQ3 (H3: at most one client requires re-approval; no client acts on the server's notification). Verdict: clause 1 holds, clause 2 does not

1. **D12** (prospective, 13 Oct, no RQ3 data). It operationalised clause 2 as "notifies or asks". Under this reading clause
   2 fails, because Gemini CLI notifies in 5 of 5 repetitions. Under the frozen wording ("by asking") it would hold. This is
   the only decision in the register that changed a verdict compared with the frozen text.
2. **D16** (prospective): the delivery rule decides which legacy cells count for clause 2. **D5** (prospective): H3 is
   tested on the primary cells only.
3. **D19** (during collection: the matrix had ended, no outcome had been read). One repetition was excluded and re-run (1
   of 60).

The positive control was planned in D12 point 5, recorded as not run in D50.2, and run after the results in D52; it has
no effect on the verdict.

## RQ5 (H5: at least one event type not distinguishable with default client logs). Verdict: holds

1. **D27** (prospective, 22 Oct, no Q4 run). Threshold "< 5%" (at most 2 of 60 windows), aggregation per event type, and
   freezing of rules and scoring code. The freeze itself is 41f992f (24 Oct 08:57), before any holdout was opened. Scoring
   (8293052) came after it.
2. **D29** (prospective): Cursor CLI was deferred, so the verdict rests on five clients (restated in D50.3 and D54).
3. **D31 and D36** (during collection: event runs recorded, no holdout opened). D31 records that set-up sessions were used
   as rule-development material. D36 adds the H5 verdict code.
4. **D6 and D13** (prospective): the metric and the holdout design.

D32–D35 and D37 restarted the baseline during collection, without changing events, rules or thresholds. The coverage
threshold of D55.1 (at least 30 of 60 windows) was set after the coverage figures were known. It is post hoc and does not
change H5.

## RQ2 and RQ4 (exploratory)

RQ2 was measured before the freeze. RQ4's hypothesis was removed in v2 after its measurement. The RQ4 census rules (D17,
D23, D38) were fixed after the readings existed and changed the exploratory figures; no confirmatory verdict depends on
them. D23's removed server is not named, as in D23 and D54.

## Paper short view

Body of a compact table for the main text, listing only the decisions that could affect a confirmatory verdict. It
needs booktabs and the `L{}` column type, as Appendix D does.

```latex
\begin{tabular}{@{}l L{4.6cm} L{1.7cm} L{2.4cm} L{3.6cm}@{}}
\toprule
RQ & Decision & When & Data visible & Effect on verdict \\
\midrule
RQ3 & H3 clause 2 read as ``notifies or asks'' (D12) & Prospective & None & Changed: clause 2 fails (holds under frozen wording) \\
RQ1 & Contested cases counted against/for H1 (D41.6) & Prospective & None & Changed: H1 not robust (32.6\%) \\
RQ1 & Population: random sample of 120 from frozen frame (D44) & Prospective & Frame only & Changed: estimate for the frame \\
RQ1 & H1 threshold 60\% & Prospective & Pilot (7/10) & Could change; observed 90.1\%/92.6\% \\
RQ1 & H1a threshold $\kappa \ge 0.6$ & Prospective & Pilot ($\kappa$ 0.91) & Could change; observed 0.458 \\
RQ1 & No-majority against H1; R2 digest differs (D7, D43) & Prospective & None & Without R2: point estimate only (73.4\%) \\
RQ1 & R0 input: AI summaries, Italian, guided questions (D42, D46, D47) & Prospective & None & Could change H1, H1a \\
RQ1 & Pilot worked examples before R0 (D50.1) & Before labels; logged after & None at decision & Could change H1a \\
RQ3 & One repetition excluded and re-run (D19) & During collection & Runs, no outcome read & Could change (1/60) \\
RQ5 & Threshold $<5\%$, per-event aggregation, freeze (D27) & Prospective & None & Could change H5 \\
RQ5 & Cursor CLI deferred: five clients (D29) & Prospective & Set-up sessions & Could change H5 \\
RQ5 & Set-up sessions as rule material; verdict code (D31, D36) & During collection & Event runs, no holdout & Could change H5 \\
\bottomrule
\end{tabular}
```
