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

---

The four entries below follow an external critical review of the project (13 Oct 2026), whose points were checked one by one
against the code, the specifications and the primary sources before being accepted. All four were written **before any
confirmatory data** for RQ1, RQ3 or RQ5.

### D12 · 13 Oct 2026 · §6 Q3 protocol — conformance with MCP 2026-07-28 and outcome coding
**Problem.** The frozen Q3 protocol records the protocol revision "from the handshake" and sends `notifications/tools/list_changed`
unconditionally. Under the 2026-07-28 specification the modern path has no negotiation handshake (servers implement
`server/discover`), a server must not send notification types the client has not requested (subscription with acknowledgement),
and `tools/list` results carry a cache lifetime (`ttlMs`). A notification the client never subscribed to is not evidence that the
client "ignores" it; a call after the toggle is not evidence that the client saw definition B (it may still use cached A). The four
outcome categories also overlap and miss outcomes (stale cache, error, timeout).
**Change.**
1. A dedicated Q3 server replaces the Q5 canary: legacy path (current legacy revision, `initialize`, `tools.listChanged: true`) and
   modern path (`server/discover`, `subscriptions/listen` with acknowledgement, `ttlMs: 0` on `tools/list`). It logs every message
   with a timestamp and which definition (A or B) each `tools/list` served. Revision recorded from the request metadata or the
   `MCP-Protocol-Version` header.
2. Delivery check: the list_changed level counts as delivered only if the client subscribed (modern) or declared the capability
   (legacy); otherwise the cell is coded "signal not deliverable" and excluded from H3's second clause.
3. Outcomes, coded with this precedence: (1) refused or disconnected; (2) re-approval required; (3) notified without re-approval;
   (4) silent accept — B served by a `tools/list` after the toggle, the call succeeded, nothing shown to the user; (5) stale — no
   refetch after the toggle, A still in use; (6) error, no call or timeout.
4. Aggregation: per-cell counts are always reported. H3 first clause: D7 unchanged (client outcome = modal outcome over primary
   cells). H3 second clause is evaluated on delivered list_changed cells only; a client "acts on the notification" if it notifies
   or asks for re-approval in at least 1 of 5 repetitions.
5. A positive control per client (a change the client is known to surface, where one exists) precedes the primary cells.
**Effect.** Prevents false "ignored" and "silent accept" results. H3 second clause can only be tested for clients where the signal
is deliverable; the others are reported as such.

### D13 · 13 Oct 2026 · §1 RQ5/H5 and Q4 protocol — holdout and reporting
**Change.** (1) Baseline: at least two hours per terminal client (≥ 12 h for six clients), repeated with the local engine where
supported. (2) Detection rules are written on a development part of the baseline and their files' SHA-256 committed **before**
they are scored on a separate holdout session (different session and time). (3) Reported per rule: true positives on event runs,
false-positive windows on the holdout with counts, Wilson 95% intervals and alerts per hour; "≤ 5%" (D6) is an observed rate on
the holdout, not a population estimate, and consecutive one-minute windows are autocorrelated. (4) H5 is judged on default client
logging only; added host telemetry is reported separately. (5) Without a holdout, RQ5 is reported as exploratory.
**Effect.** Separates rule development from rule evaluation; threshold unchanged.

### D14 · 13 Oct 2026 · §2–§3 RQ1 — case C01, disclosure date, summaries, classifier
**Problem.** Pilot case C01 (CVE-2026-55607, GHSA-7835-87q9-rgvv) was labelled class 1 by R0 and by one model. The vendor advisory
states that reliable exploitation required a repository containing prompt-injection content run with the agent: under the
decision rule of §2 the case is class 4. The case summary given to the raters omitted this precondition. The class-1 clarification
added after the pilot (§2, §7) was motivated by the disagreement on C01, so it was influenced by the author's label. The advisory
was published on 25 June, one day before the window (26 June); the pilot used the CVE date (29 June).
**Change.** (1) C01 is relabelled class 4 in all reporting; the pilot share becomes 6/10 (6/9 if C01 is dropped by date). Pilot
κ values, computed on the original labels, are reported as such and recomputed with the correction. (2) Disclosure date = first
public advisory or researcher write-up; advisory, CVE and fix dates are recorded separately in `rq1-frame.csv`. (3) Case summaries
must state every precondition of exploitation, paraphrased without class words (e.g. "instructions planted in files the agent
reads"); a second human reader checks the summaries of contested cases against the sources where available. (4) The classifier
(`classify.py`) parses answers as strict JSON, counts invalid answers, treats ties as unresolved, refuses mismatched case sets,
reports undefined κ as undefined, aborts without a model digest, and writes each run to its own directory; covered by tests.
**Effect.** H1 is evaluated on the confirmatory set with the corrected rules; the pilot is reported separately with the correction.

### D15 · 13 Oct 2026 · §5 RQ4 (exploratory) — summary statistic, correcting D9
**Correction.** D9 called the 61% mean "the primary count … as in the Q2 protocol"; the protocol defines neither a primary count
nor the exclusion of the two small servers (MSSQL, Oracle). **Change.** RQ4 is reported as a range with its inclusion rules: mean
per-repository coverage 61% over the five servers analysed (partial coverage counted; median 57%), 60–72% depending on including the
two small servers and on counting partial coverage, and the pooled per-tool share; denominators that are estimates (GitHub, Sentry)
are marked. The unit of count is the registered tool name; results are given separately per defence mechanism (nonce delimiting,
character hygiene, provenance marking), which are not equivalent. Azure DevOps is 28/28 read tools at the pinned commit, text
success paths only. The Q2 protocol's ">95%" for spotlighting refers to Nasr et al.'s adaptive search attack on AgentDojo (one model
47%) and is quoted that way from now on.
**Effect.** Exploratory question; reporting only.

### D16 · 15 Oct 2026 · §6 Q3 protocol — delivery rule (corrects D12 point 2) and cell procedure
**Problem.** (a) D12 point 2 counts the legacy list_changed level as delivered if "the client declared the capability". In the
legacy revisions `tools.listChanged` is a **server** capability (returned in the `initialize` result); clients do not declare it.
Read literally, legacy cells in which the notification was correctly sent would be excluded as "signal not deliverable". (b) The
frozen procedure does not say where the server is configured, which answer is given to a client's per-tool permission question,
how the in-session outcome is coded from the records, or how exploratory set-up runs are separated from the primary ones.
**Change.**
1. Delivery (replaces D12 point 2). Legacy: the server declared `tools.listChanged: true` in its `initialize` result and sent
   `notifications/tools/list_changed` on that initialized connection after the change. Modern (2026-07-28): the client opened
   `subscriptions/listen` with `toolsListChanged: true`, the server acknowledged it first, and the notification carried that
   subscription ID. The server records which applied (`signal-delivered`, with the channel) or `signal-not-deliverable`; only the
   latter codes the cell "signal not deliverable" as in D12.
2. Configuration. The Q3 server is added to each client's **user-level** MCP configuration, the usual way a user installs a server,
   and is not declared by the test repository, whose folder is trusted beforehand. This keeps the decision measured here (a changed
   tool) apart from the repository-trust decision measured in Q5 (RQ2). Goose reads user-level configuration only.
3. First approval. At the first call the runner gives the client's persistent per-tool approval where one exists ("always allow
   this tool" or the nearest equivalent), recorded verbatim; otherwise the per-call approval, and the cell is marked "no persistent
   approval". Outcome 2 of D12 (re-approval required) means the client asks again for the changed tool despite that approval.
4. One server for both signal levels: `tools.listChanged: true` declared on both paths and `ttlMs: 0` on every modern `tools/list`;
   the levels differ only in whether the notification is sent after the change.
5. "Silent accept" (D12 outcome 4) is a protocol-level outcome: B served by a `tools/list` after the change, the call succeeded,
   nothing shown to the user. That B reached the model is claimed only in local-engine cells, from the recording proxy.
6. Reopen phase (exploratory). After the in-session call the client is closed, reopened and asked to call the tool once more; coded
   with the same categories, reported separately and not used for H3.
7. Coding. A rule-based coder over the server log and the screen captures gives a provisional outcome per repetition; its rules
   are committed under `tool-change/` before the primary runs. The two preregistered coders (author; one local model on the
   captures) classify independently of it and of each other. κ is reported between the two preregistered coders; agreement with the
   rule-based coder is reported separately.
8. Set-up runs. Exploratory runs used to fix each client's key sequence and positive control are published but excluded from all
   counts. Every primary repetition restores a clean snapshot taken before any Q3 run, set-up runs included.
**Effect.** H3's second clause can be evaluated on legacy cells where the notification was in fact delivered; outcome categories
and precedence are those of D12. No RQ3 data of any kind existed when this entry was written.
