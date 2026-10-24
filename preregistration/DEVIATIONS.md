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

### D17 · 15 Oct 2026 · §5 RQ4 (exploratory) — per-tool census replaces the 9 October reading; D15's figure withdrawn
**Problem.** The 9 October reading counted tools approximately (GitHub ~40 and Sentry ~28 were estimates; GitHub's sub-methods were
counted as separate surfaces; the Azure DevOps denominator was every read tool), classified borderline cases differently from server
to server, and did not separate partial from full protection. D15's 60–72% range rests on those counts.
**Change.** (1) RQ4 is computed from a per-tool census at the same pinned commits: one row per registered tool name, with class,
protection (full / partial / none), mechanism and file:line evidence; the tables will be published under `defence-coverage/`.
(2) A tool is class A if it returns free prose written by third parties (titles, descriptions, bodies, comments, messages, file
contents, logs); names and identifier-like strings do not make it A. (3) Coverage is reported twice: full protection only, and full
plus partial. (4) Tools whose prose is only vendor-written (documentation, curated advisories) are reported with and without.
(5) Monorepos: every package is screened for an output-side defence and every server that has one is included; a package whose
mechanism is unclear is reported as such. (6) Summaries: per-server values, mean and median over servers, and the pooled per-tool
share, computed by a published script. The 60–72% figure of D15 is withdrawn. (7) The census was made by AI agents of the same model
family as the 9 October reading (not an independent second reader); the coordinator checked a sample of claims against the source,
and the author re-checks a sample before any figure is published.
**Effect.** Exploratory question; reporting only. The 9 October reading is kept for traceability.

### D18 · 15 Oct 2026 · §6 Q3 protocol — set-up runs before the snapshot, snapshot type, models for Gemini CLI and Qwen Code
**Problem.** (a) D16 point 8 says the clean snapshot is taken before any Q3 run, set-up runs included. The client logins had to be renewed
after the set-up runs had started (Claude Code's OAuth session had expired), so the snapshot could not precede them. (b) Restoring a
powered-off snapshot means booting the VM for every repetition; on the host, loading the VM's AppArmor profile failed when memory was
fragmented (kernel log: page allocation failure, order 6). (c) The free daily quota of the Gemini API key used by Gemini CLI and Qwen Code
was exhausted on the default model (gemini-3.8-flash, 20 requests per day) during the set-up runs.
**Change.** (1) The clean snapshot is taken after the set-up runs, once their residue has been removed by `tool-change/scripts/cleanup_setup.py`
(tool approvals for q3-lab, server log, control file, set-up outputs, and the session histories those runs wrote); the script's output and a
listing of every file changed since the configuration step are published with the evidence. Kept on purpose: folder-trust markers (given by
hand before the runs, D16 point 2) and logins. Left as they are and declared: Codex's SQLite state and prompt-history databases, caches and debug logs, Claude Code's account-synced
skills and plugins (they come with the login), and `~/.claude/settings.json` = `{"tui": "default"}` (written when an accidental opt-in to
the full-screen renderer during a set-up run was undone; equal to the default). Client background processes are stopped before the snapshot.
(2) The snapshot is a running snapshot (memory included); after each restore the guest clock is set to the host's time.
(3) Gemini CLI and Qwen Code run on `gemini-flash-lite-latest` (the model Goose already used), fixed for all repetitions; the engine is still the
vendor's (D5). (4) Clients without a persistent per-tool approval: Gemini CLI offers only session approvals by default ("Allow tool for this
session" is used, D16 point 3); Goose (`auto`) and Qwen Code ("Auto mode") ask no question by default and are marked "no persistent approval".
For clients with session-only approvals the reopen phase (exploratory, D16 point 6) cannot distinguish a definition change from an expired
approval and is reported as such.
(5) Snapshot `q3-base-20261015`, taken 15 Oct 2026 17:51 CEST; client versions at the snapshot: Claude Code 2.1.300, Codex CLI 0.162.1,
Gemini CLI 0.64.0, Qwen Code 0.25.1, Cursor CLI 2026.10.14-941492e, Goose 1.54.0. Default permission modes observed: Claude Code "auto mode"
and Qwen Code "Auto mode" ask no question; Codex CLI ("Always allow"), Cursor CLI ("Allowlist MCP Tool") and Gemini CLI (session only)
ask at the first call.
**Effect.** No change to outcomes, precedence or aggregation. No primary repetition had been run when this entry was written.

### D19 · 15 Oct 2026 · §6 Q3 protocol — a client's own classifier unavailable; unexpected questions
**Event.** In primary repetition `qwen / none / r4` (48th of 60), after the change Qwen Code asked for permission with the message "Auto Mode
couldn't classify this action (Classifier stage 1 unavailable). Review it manually." Qwen Code's default "Auto mode" decides tool calls with a
classifier that uses the same rate-limited API key; when the classifier is unavailable it falls back to asking. The runner had no key sequence
for a Qwen question (none was expected, D18 point 4) and stopped; no outcome was recorded. No other capture of the 60 repetitions contains
such a message. This entry was written after the matrix ended and **before any outcome of the primary matrix was read**.
**Change.** (1) A repetition in which the client shows that its own permission classifier was unavailable is coded `invalid-external` and
excluded, like `invalid-setup`: the question is caused by the classifier's availability, not by the change. It is listed with the reason.
(2) An invalid repetition is run again once from the clean snapshot; the failed attempt is kept and published. (3) When a client asks a
question the runner has no answer for, the runner records it (`unexpected_approval`) and accepts the pre-selected answer instead of stopping.
**Effect.** One repetition re-run (Qwen Code, signal none, repetition 4). Outcome definitions and aggregation unchanged.

### D20 · 15 Oct 2026 · §5 RQ3 — coders
**Problem.** §5 asks two coders, the author and one local model, to classify each repetition independently, and reports Cohen's κ between
them. On 15 October the author read the rule-based coder's results table before looking at the evidence, so a coding by the author done
afterwards would not be independent of it.
**Change.** (1) The author's role is verification: the author checked the repetitions against the rule-based outcomes and reported no
disagreement (recorded verbatim with the evidence). (2) The independent, blind coding is the local model's (`qwen3.8:27b-q8_0`, digest
recorded, temperature 0, packets without the rule-based outcome and with shuffled identifiers). (3) κ is reported between the local model and
the rule-based coder; every disagreement is resolved by re-reading the capture and the server log, and the resolution is published.
(4) The paper states that no blind human coding was done. This entry was written before any answer of the local model was read.
**Effect.** The reported agreement is model versus rule-based coder instead of author versus model; outcome definitions and precedence unchanged.

### D21 · 15 Oct 2026 · §5 RQ3 and D17 — correction of D20: author coding restored
**Correction.** D20 assumed that the author had read the rule-based coder's results before examining the evidence. The author states that he
examined the evidence first and then compared it with the results, finding agreement on every repetition (and on every row of the Q2 spot
check). D20's premise was the coordinator's assumption, not a fact.
**Change.** (1) §5 as preregistered applies: the two coders are the author and the local model, and Cohen's κ between them is reported;
κ of each with the rule-based coder is reported as well. (2) The author did not write a label per packet: his labels are recorded from his
declaration of agreement on every packet (each row of the coding sheet says so), and the paper states this. (3) Q2 (D17): author spot check of
the seeded ten-row sample, no disagreement; agreement reported as 10/10 with κ on the protection label. This entry was written before any
answer of the local model was read.
**Effect.** Reporting as in §5; D20 is superseded.

### D22 · 17 Oct 2026 · §5 RQ3 and RQ4 (D17) — an independent additional coder from another model family (post hoc)
**Problem.** (1) RQ3: the preregistered agreement between the author and the local model (D21) is κ = 0.115 (14/60). 45 of the 46
disagreements share one cause, a packet line ("definition in force at the call: B") that gives the server's state and that the model
read as "B was served". The author's labels were recorded from his declaration of agreement after he examined the evidence, not on
blind forms (D21). (2) RQ4: the per-tool census (D17) was made by AI agents of one model family, with the coordinator's sample check
and the author's 10/10 spot check; it has no independent second reader (D17 point 7).
**Change.** A coder from a different model family is added, post hoc: OpenAI Codex CLI 0.162.0, model `gpt-6.1-sol`, reasoning effort
`medium`, read-only sandbox, apps, plugins and MCP servers disabled. It replaces no preregistered coder and no preregistered analysis:
the author-versus-local-model κ stays the primary agreement statistic and is reported first, with its cause.
(1) RQ3. Codex codes the same 60 blind packets as the local model, without any change to their wording (packet set SHA-256
`2aa0e318fee2db8b1832840553e4d6cc9e1cdff31cae325e8b960e60537825e6`), with the same instruction text, the same closing request and
the same answer schema (`outcome` from the six labels, `reason`) as `scripts/code_q3_llm.py`. One difference in delivery is
declared as a limitation of the comparison: `codex exec` takes a single prompt, so the instruction that the local model received
as a separate system message is placed at the top of the same prompt as the packet, below the CLI's own built-in instructions.
The comparison therefore changes both the model family and where the instruction sits. One fresh session per packet, packet
order P001–P060, the packet text inside the prompt, the working directory an empty folder. Reported: Cohen's κ Codex vs author and
Codex vs local model, Fleiss' κ over the three, the confusion tables, and how many of the 46 earlier disagreements Codex resolves
like the author.
(2) RQ4. Codex reads the eight servers of the census at the pinned commits (`defence-coverage/pinned-commits.csv`), one session per
repository, and returns one row per tool name the server exposes, i.e. registered with the SDK or reachable through a dispatcher
or catalog tool, deprecated aliases not counted separately, as in the first reading: class (A or not A), protection (full / partial / none / n-a), mechanism,
a vendor-only-prose flag, and file:line evidence for each. The rules are given verbatim and in advance: D17 points 2–4 and the
operational rule of the census (`lab/results/q2/census/REVIEW.md`, "Regola di coerenza"): class A = returns free prose written by
third parties (titles, descriptions, bodies, comments, messages, file contents, logs), not names or identifier-like strings;
**full** = all third-party prose the tool can return passes through the server's defence; **partial** = only part of it does,
including the case where error or secondary branches return third-party text outside the defence; **none** = none of it does;
**n-a** = not class A; **vendor-only prose** = the only prose is written by the vendor itself (documentation, curated advisories).
Vendor-only prose **counts as qualifying prose** for class and protection in the inclusive reading: such a tool is class A and gets
a protection label like any other. The vendor-only flag is used only to drop those rows from the second variant ("without
vendor-only prose"). A tool that returns both vendor and third-party prose is not flagged and stays in both variants. The working directory contains only the clones at the pinned commits.
**Comparison baseline:** before Codex starts, the first reading is frozen as one canonical table, i.e. the agents' CSVs after the
documented corrections that `aggregate.py` applies (`load()` and `FULLY_CONTESTED`): 324 rows, 135 of class A, written to a CSV
whose SHA-256 is `709d27601ab33fd820e19681a9fcd4cb1677a2bf4fa1e52fc02a1cbf7f78dc8c`; the table is published with the census evidence. The two readings are joined by server and registered tool name, and missing or duplicate tools on either
side are reported. Agreement (Cohen's κ and raw agreement) is computed on class, on protection and on the vendor-only flag, using
Codex's untouched labels: no correction of the first reading is applied to the second. Every disagreement on a class-A tool is
then adjudicated by the author against the source, with file:line, before any coverage figure from the second reading is
published; the independent results are reported before the adjudicated ones.
(3) Blindness and isolation. Every coding session is new: never resumed, never a session used for reviewing this project. Each
session runs inside a bubblewrap (`bwrap`) container whose filesystem holds only read-only system directories (`/usr`, `/etc` and
their links), a private `/tmp`, the Codex executable, a separate `CODEX_HOME` with only a copy of the authentication file and a
minimal configuration (model, effort), and the working directory: empty for RQ3, the pinned clones for RQ4. The real home
directory, the project, earlier Codex sessions, global `AGENTS.md`, memories and hooks are not mounted, so they cannot be read by
the CLI or any child process, whatever the command or symlink. Before each batch a probe inside the same container lists the
paths of the project and of the real `~/.codex` and must fail; the probe output and the exact `bwrap` argument list are kept. For
each session we keep the complete prompt, the session rollout (initial context), the packet or repository hashes, model,
effort, the `--json` event stream and the answer. Allowed initial context: the CLI's own built-in instructions and tool
definitions, the minimal configuration, and our prompt; no user or project instruction file. The CLI's own blocks are fixed
for each batch by a reference session on a synthetic prompt, run first in the same container; every coding session's developer
blocks must be byte-identical to the reference ones, with exactly one environment block (working directory `/work`) and exactly one
user message equal to the prompt sent. A coding is valid only if the probe failed as required and the rollout passes this check.
Any violation is reported and that session's coding is excluded.
(4) Order. This deviation is committed and pushed before Codex receives any packet or repository. The scripts, with their prompts
and schemas, are committed with it: `tool-change/scripts/isolated_codex.py` (container, probe, context check),
`tool-change/scripts/code_q3_codex.py` (RQ3), `defence-coverage/scripts/census_codex.py` (RQ4 second reading) and
`defence-coverage/scripts/compare_census.py` (RQ4 agreement) and `tool-change/scripts/agreement_q3_three.py` (RQ3 agreement),
with their tests. Before this commit they were run only on synthetic
inputs: one invented packet and one invented repository.
**Effect.** Adds a robustness check from an independent model family. Preregistered analyses and their reporting order are unchanged.
Codex belongs to the vendor of one measured client (Codex CLI); its role is coding captures and reading server code, not judging
products.

### D23 · 17 Oct 2026 · §5 RQ4 (D17 point 5) — what counts as an output-side defence
**Problem.** D17 point 5 puts every server that has an output-side defence against untrusted content into the RQ4 set, but it does
not say what counts as a defence. In one server of the census the only candidate is a pair of delimiter lines that one tool places
around uploaded content. Those lines present the content as workflow guidance for the agent to follow, subject to the agent's
safety guidelines and tool policies, not as untrusted data. A source check on 17 October 2026 found no sanitiser, untrusted-data boundary or provenance marking anywhere else in
that server. The first reading coded that tool as fully protected, which brought the server into the set. The second reading (D22)
coded it as partially protected.
**Change.** For RQ4, an output-side defence is a mechanism that marks or neutralises third-party content as data that the model
should not follow: delimitation together with an instruction to treat the delimited text as untrusted data, character hygiene, or
provenance marking. Delimiters that present the content as instructions to follow do not count. The server above therefore has no
output-side defence: it moves to the servers without one, and its tools leave the coverage figures. The set of servers with a defence
goes from eight to seven. Agreement between the readings (D22) is computed on the original labels of both readings, as they were
frozen and returned, without the recoding of this deviation: on the eight-server set and, filtering the same labels, on the
seven-server set, so the change cannot hide a disagreement. The rule applies to the coverage figures only; labels recoded under it
are kept in separate derived files, and the original tables and their SHA-256 are unchanged.
**Effect.** Exploratory question; the rule is fixed before any coverage figure from the per-tool census (D17) is published. The
server is named, with file and line evidence, in the census evidence when it is released. Decided by the author.

### D24 · 17 Oct 2026 · §1 RQ5/H5, Q4 protocol, D6, D13 — default client logs, new event runs, baseline and holdout
**Problem.** The Q4 protocol lists each client's own logs, at default and at maximum verbosity, among its data sources, and D13
point 4 judges H5 on default client logging only. The Q3 primary runs exported host telemetry (audit, journal, nftables rules) but
not the clients' own logs. The virtual machine returns to a clean snapshot after every repetition, so those logs are lost: the Q3
primary runs cannot serve the H5 judgement. No baseline session has been recorded yet.

**Change.**
1. *Export.* After every event run and every baseline session, the runner stops every client and then, before the snapshot is
   restored, copies:
   - each client's default log locations; SQLite databases together with their write-ahead-log files, opened from a private
     copy (never the original), checked and also saved as a consolidated copy, so that committed records still in the log are
     kept;
   - the host telemetry, as in the Q3 runs.
   The default log locations are fixed by an inventory on the clean snapshot before any new run. The inventory, with each
   source's format, retention and how its record times are read, is committed with this deviation's implementation
   (`telemetry/inventory/`).
   Raw client logs, and the paths of some of them, can name services connected to the lab accounts. They stay in the private
   evidence, with the full collection records; the public evidence holds the inventory counts, the manifests' SHA-256, a public
   collection record per session (counts per frozen location, no file path, failure reasons by category only) and the derived
   detection records. The list of locations is the one committed with the harness; no other list can be used.
2. *Collection check, independent of detection.* For every session the runner records:
   - the client's logging configuration at collection time (hashes of its settings files, names of logging variables);
   - for every frozen location, whether it is absent or was looked at, how many files it held and any error met while reading
     it, and every exported file with size and SHA-256;
   - the time range of the exported records, compared with the session's start and end, where record times can be read, and
     "unknown" otherwise.

   An export fails when the archive or its manifest cannot be read, the manifest does not account for every frozen location of
   the client or was made from another list of locations, a location or file could not be read, a file is missing or differs
   from its hash, or a database cannot be opened from its copy. An absent location is not a failure.

   Whether an event happened is established only by ground truth: the canary's log (Q5 events) or the lab server's log (Q3
   events), never by the client's log. An event that does not appear in the client's default logs is a valid negative observation
   and is kept. A client that does not log a kind of event by default is distinguished from a failed export. No session is
   excluded because the event is missing from its logs; a session is excluded only if its export failed, with the reason.
   A run in which the ground truth shows that the event did not happen (for example Goose, which does not start servers
   declared by a repository) is reported as "no event": it enters neither the true positives nor the misses.
3. *New event runs.* Before the baseline, we run a series of event runs on the six terminal clients, from the clean snapshot,
   with the export above:
   - Q5 events: a repository-declared server starts after the folder is trusted;
   - Q3 events: an approved tool's definition changes, with the notification (one event type) and without it (another).

   There are two runs per event type and client (three types, 36 runs), in a random order fixed by a seed and written, with the
   hashes of the inventory, of the list of locations and of the harness commit, before the first run. A restart executes that
   plan and refuses other inputs. The ground-truth log of every run is copied and checked before the next restore: every record
   must be well formed and timed; a Q3 run needs exactly one A-to-B change record for its own cell, and a Q5 run a canary log,
   which may be empty (no event). If the check fails, the attempt is kept and does not count, and the runs stop until the cause
   is fixed. They are the
   confirmatory events of RQ5 (D6), recorded after the freeze under the Q4 telemetry configuration. Earlier Q3 and Q5 captures
   remain exploratory for RQ5.
4. *Baseline and holdout* (D13 points 1–3). For each terminal client:
   - scripted normal use for at least two hours with the vendor's engine, split into a development part (the first hour) and a
     holdout part (the second hour);
   - the holdout part runs as a separate session, at least six hours after the development part;
   - the scripts are fixed in advance: open the test repository, ask for an explanation of a file, run the tests, edit a file,
     approve a known server; command and edit questions are answered "allow once";
   - a session counts only if the normal use happened: at least 80% of the prompted tasks completed with evidence that the action
     took place (the tests ran, the edit is in the file, the known server logged the call; a refused action does not count) and
     at least 0.8 calls per cycle to the known server, whose definition stays the same for the whole session; and only if its
     client logs were exported. A session that fails these checks is kept as an attempt, does not count toward the two hours,
     and stops the baseline until it is looked at. A holdout session needs a counted development session of the same client.

   Detection rules are written on the development part only. Their files' SHA-256 are committed before they are scored on the
   holdout. The local-engine repetition of the baseline (D13 point 1) is not implemented at the time of this deviation; it is
   reported as not done unless a later, reviewed change adds it.
5. *Reporting* (D6, D13 point 3).
   - H5 is judged on default client logs only; host telemetry is reported separately.
   - A rule detects an event run if it fires between the ground-truth time of the event and the end of the run, when the
     logs are copied; hits before the event do not count. Holdout windows start at the session's start; a trailing window
     shorter than one minute is dropped. Latency from the event to the first hit is reported.
   - For each rule: true positives on the event runs; false-positive one-minute windows on the holdout, with counts, Wilson 95%
     intervals and alerts per hour.
   - "≤ 5%" is an observed rate on the holdout, not a population estimate.
   - Without a holdout, RQ5 is reported as exploratory.

**Effect.** RQ5 keeps its confirmatory status, on new event runs and a held-out baseline. Q3 primary results (RQ3) are unaffected.
The order is fixed: this deviation and the exporter are published before any new run.

### D25 · 17 Oct 2026 · D24 points 3–4 — seeds, set-up sessions and pipeline check before the Q4 campaign
**Problem.** D24 fixes the order of the new event runs and of the baseline sessions with a seed, but does not give the seeds. The
orchestrators and the baseline driver have never run against the virtual machine. The patterns for command and edit questions in
`telemetry/baseline/clients.json`, and the lines that identify the lab tool's MCP approval dialog, are provisional: Claude Code
never asked a question in Q3, so its dialog has not been seen.
**Change.**
1. *Seeds.* Event runs: 20261018. Baseline: 20261019. Both are fixed here, before any run, and were not chosen by looking at the
   order they produce. The orchestrators generate the plans from them and write them to `plan.json` before the first run.
2. *Set-up sessions (exploratory).* One six-minute session of scripted use per terminal client (`q4_baseline.py --parts setup
   --minutes 6`), in a separate folder, before the baseline. They serve only to see each client's permission questions and to
   correct `baseline/clients.json`. A set-up session whose only problem is that the scripted use did not work is recorded and the
   set-up goes on to the next client; any quota, copy, export or telemetry problem stops it, as in the baseline. Each revision of
   `baseline/clients.json` gets its own folder (`setup-r1`, `setup-r2`, …) with its own frozen plan, and re-runs only the
   clients whose questions changed. No folder is reused or overwritten. `setup-lineage.md` records, for each folder, the commit
   and the SHA-256 of `clients.json` it used, and why the next revision was made. The final file is then frozen in a commit,
   with its SHA-256, before the first baseline session. These sessions are not part of the baseline and are published as set-up
   evidence.
3. *Pipeline check (exploratory).* One run per event type on Gemini CLI (`q4_events.py --clients gemini --reps 1`: three runs), in a
   separate folder, before the 36 event runs. It checks end to end:
   - the client-log export and its check;
   - the copy of the ground truth;
   - the host telemetry.

   These runs are not part of RQ5 and are published as set-up evidence. A code change that follows is reviewed and committed
   before the campaign, whose plan freezes the new commit.
4. *Snapshot.* If a client's login in `q3-base-20261015` has expired, the logins are renewed and a new clean snapshot is taken,
   after the clean-up of D18 point 1, with its listing published. The campaign then uses that snapshot, and its name is in the
   frozen plan.
5. *Quotas.* The clients use the author's accounts. Next to every run and session, an observer (`telemetry/scripts/quota_watch.py`)
   reads the client's terminal every second, read-only, and records any quota or rate-limit message, even one the client recovers
   from before the next saved screen. It also records a heartbeat every ten seconds, any failure to read the terminal, and an
   orderly end. Any quota message stops the campaign, and so does an observer that did not watch the whole run: no record, no
   orderly end, a gap of more than 30 seconds, or a read failure. The attempt is kept and does not count. The Q3 and Q5 runners
   are used as they ran.

**Effect.** RQ5 stays confirmatory. The set-up sessions and the pipeline check are exploratory and excluded, like the set-up runs of
Q3 (D16 point 8).

### D26 · 17 Oct 2026 · D25 point 4 — logins for the Q4 snapshot, and a gate that keeps every secret out of the published evidence
**Problem.** The VM check of 17 October, made before any Q4 session or run, found Claude Code's access token in `q3-base-20261015`
expired since 15 October. One minimal non-interactive call, without MCP servers, renewed it: the stored refresh token changed and
the new access token lasts eight hours. Claude Code therefore replaces its refresh token at every renewal; the vendor's
troubleshooting page describes an earlier client bug in which two renewals with the same token revoked the saved login. From a snapshot, Claude Code can run only
within about eight hours of the snapshot's last renewal. After that, the first restored run renews and replaces the token, and the
next run, restored from the same snapshot, reuses a token that is no longer valid. The baseline of D24 point 4 runs from one
snapshot for more than twelve hours: development sessions, at least six hours, held-out sessions. Codex CLI's login was last renewed
on 9 October and its access token expires on 19 October, inside the campaign. A long-lived token solves this, but the lab publishes
captures, host telemetry and records derived from the clients' logs, and the author's rule is that no secret may ever be published.
Default client logs can also hold token-shaped data of their own, such as short-lived session tokens: the check of the clean
snapshot found some in one client's default diagnostic log, all expired.
**Change.**
1. *Claude Code.* It authenticates with a one-year OAuth token of the same subscription, which the author creates with
   `claude setup-token` on the host and writes into a file in the VM that only the lab user can read.
   - A shell function in the lab user's login profile passes the token, as `CLAUDE_CODE_OAUTH_TOKEN`, to Claude Code's process
     only. The runners start every client in a login shell, so no runner code changes, and no other client has it in its
     environment.
   - The interactive login file is moved out of `~/.claude/`. The token is then the only credential Claude Code can use, and a
     missing token shows as "not logged in" rather than as a fall-back to the other login.
   - By the vendor's documentation the token can only make model requests: claude.ai connectors and Remote Control are not
     available (the lab uses neither), and locally configured MCP servers work. Files synced from the account on 15 October stay
     as D18 point 1 left them.
2. *Codex CLI.* A fresh ChatGPT login of the same account (`codex login --device-auth`), just before the snapshot.
3. *Other clients.* No change: Gemini CLI, Qwen Code and Goose use an API key; Cursor CLI's token is valid until 27 November.
4. *Secret gate* (`telemetry/scripts/secret_gate.py`). It never prints, logs or writes a secret's value.
   - Inside the VM, it takes a fingerprint of every secret in the clients' known stores: length, first four characters and
     SHA-256. In login files only the fields that name a secret (tokens, keys, passwords) count: the account data stored next to
     them, such as the names and addresses of the account's MCP connectors, is not a secret.
   - On the host, it scans files, folders and archives, nested archives included, two ways: by those exact values, and by the
     formats of known tokens and keys. File names and archive member names are scanned too, and every name it reports is
     redacted first. A fingerprint set that is missing, malformed, or lacks one of the expected stores stops the scan.
   - After every run and session, every copy out of the VM is completed first, with only exit codes in the campaign log. The
     orchestrators then refresh the fingerprints into the host's private state and scan the copied folder, before any other
     check reads it.
   - A lab secret found by exact value, anywhere, stops the campaign: the attempt is kept as "secret-found" and never
     published. So do token-shaped data anywhere outside the raw client-log archive, a secret store that cannot be read, and a
     file or folder that cannot be scanned.
   - Inside the raw client-log archive, which D24 point 1 already keeps in the private evidence, token-shaped data that matches no
     lab secret is counted by kind in the run's `secret-marks.json` (no value, no file name) and does not stop the run. That
     archive is never published.
   - Right after the gate, a redacted copy of that archive is made and checked clean, with the SHA-256 of both in
     `secret-marks.json`; every later reader (a person, a script or a model) uses the copy. Redaction replaces each match with
     characters of the same length, so databases stay readable; JSON stays parseable; archives are rebuilt member by member,
     names and tar metadata included. An archive it cannot rebuild unambiguously, with data after its end for instance, stops
     the run. The only reader of the raw archive is the collection check of D24 point 2, which compares file hashes with the
     manifest; the records it writes are redacted first and scanned after.
   - A pre-push hook in the lab and site repositories scans every file, file name and commit message in the tree of every
     commit a push would publish, merges included. A finding, or a missing fingerprint set, blocks the push; a new branch is
     checked against its whole history. Before this deviation, the whole published history of both repositories was scanned, by
     format and by exact value: no finding.
5. *Checks before the snapshot.*
   - `claude auth status` names the token as the method in use, after the move of the login file.
   - One minimal non-interactive call without MCP servers succeeds, and the moved login file is not modified by it.
   - No fragment of the token is found in Claude Code's own files.
   - Codex reports a ChatGPT login renewed on the day.
6. *Snapshot.* What the checks wrote is removed, as in D18 point 1. Client processes are stopped and a running snapshot
   `q4-base-<date>` is taken (D18 point 2). The checks, the clean-up output and a list of the files changed since the VM check (paths
   only) pass the secret gate and are published as set-up evidence.
7. *Before the event runs.* Claude Code's set-up session (D25 point 2) runs before the event runs. If its default mode or its
   questions differ from Q3 ("auto mode", no question at the first tool call, D18 point 5), the campaign stops and a deviation is
   written before any event run.
8. *After the lab.* Every lab secret is revoked or rotated: the Claude Code token, the Codex login and the Gemini API key.
**Effect.** None on outcomes, rules or analysis: every Q4 session and run uses the same logins, and `q3-base-20261015` is not used
for Q4. Limitation: an interactively logged-in Claude Code renews its login every few hours; our runs do not. Any trace of that
renewal in default logs or in network traffic is therefore absent from both the event runs and the baseline. An attempt stopped by
the secret gate is reported by its file names and the kinds of secret found.


### D27 · 22 Oct 2026 · §1 RQ5/H5, D6, D13, D24 points 4–5 — rule development, threshold, aggregation and freezing, fixed before any Q4 run
**Problem.** Before the Q4 campaign, a red-team review of the plan found six gaps.
1. *Rule development.* D24 point 4 says detection rules are written on the development part of the baseline only, but a rule
   cannot be written for an event it has never seen. Writing it on the 36 event runs would make the true positives in-sample.
2. *Threshold.* The preregistration says "below 5% per hour"; D6 wrote "≤ 5%" and called the threshold unchanged.
3. *Window count.* The number of holdout windows, and the clock they are counted on, is not fixed.
4. *Aggregation.* H5 ("at least one event type is not distinguishable with default client logging alone") does not say how results
   per client combine into a verdict per event type, nor what happens to a client where an event type cannot occur.
5. *What is frozen.* Only the rule files are frozen; the code that applies and scores them is not.
6. *Lab artefacts.* Nothing stops a rule from matching names that exist only because of the lab's own design.

**Change.**
1. *Rule-development event runs (exploratory).* Before the 36 event runs of D24 point 3, one run per event type and terminal client
   (18 runs, `q4_events.py --reps 1`, seed 20261022, in their own folder) is recorded from the same snapshot, with the same export
   and checks. These runs, the pipeline check of D25 point 3 and the development part of the baseline are the only material on
   which rules are written. The 36 event runs and the holdout sessions are used only to score frozen rules. The development runs
   are published as development evidence and are not part of RQ5.
2. *Threshold.* We return to the preregistered wording: a rule passes on a holdout if its false-positive windows are **below** 5%
   (k/n < 0.05). This replaces "≤ 5%" in D6 and D24 point 5. With 60 windows a rule passes with at most two.
3. *Windows.* Holdout windows are cut from `t_start` to `t_end` of the session's `session.json`, written by `baseline_session.py`
   on the VM clock. The VM clock is set from the host at every restore, and the remaining skew is recorded. The count is
   n = floor((t_end − t_start) / 60), whatever the session's real length. Client-log times are read on the same clock.
4. *Aggregation.*
   - A (client, event type) pair is **measurable** if it has at least one counted event run in which the ground truth shows the
     event. Pairs where the event cannot happen (for example Goose and repository-declared servers) are "not measurable", are
     listed, and do not enter the verdict.
   - An event type is **distinguishable** if, for every measurable pair of that type, the pair's frozen rule detects every
     counted event run and passes on that client's counted holdout.
   - **H5 holds** if at least one event type with at least one measurable pair is not distinguishable.
   - The table per pair is reported next to the verdict.
   - Failed sessions and runs are retried for every client, in plan order, until they count. No client is retried selectively.
   - If a client's confirmatory data are incomplete when results are first reported, the verdict is given with and without that
     client, and the client is marked as preliminary.
5. *Freezing.* One rule per measurable pair on default client logs, and separately one rule per event type on host telemetry
   (reported apart, D13 point 4). Before any holdout session is opened for scoring, one commit is pushed. It contains:
   - the rule files;
   - `score.py`;
   - the script that applies the rules to the logs;
   - this window definition;
   - the versions of the tools used;
   - a single SHA-256 list of all these files.

   Every candidate rule tried during development is logged with the material it was tried on and why it was kept or dropped
   (`rule-development-log.md`). Until that commit, failed holdout attempts are inspected only through `attempt.json`, the
   campaign log and the secret-gate summaries; any other access to holdout material is logged.
6. *No lab artefacts.* Rules on client logs may not use these literals:
   - the lab's names and paths (`q3-lab`, `q3_noop`, `q3-repo`, `q4-out`, the lab user's home), the lab ports and addresses;
   - the canary's names and content;
   - the text of definitions A and B, and the names of the lab server's tools.

   A rule must describe the class of event: a server declared by the project starts; a tool list changes after approval, with or
   without a notification.
7. *Second rule author (exploratory).* A second set of rules is written by a separate model session that starts with no
   conversation history. Its inputs are a package assembled for it:
   - redacted copies of the development material only (rule-development runs, pipeline check, development sessions);
   - a description of the three event classes;
   - the forbidden literals.

   What is kept: the package (with SHA-256), the exact prompt, the model and session identity, and the session's full transcript.
   The transcript is checked: a read of any file outside the package (design notes, deviations, harness code, confirmatory
   folders) invalidates the session, which is then reported and not replaced. Its rules are frozen in the same commit and scored
   the same way. They are reported for agreement only; H5 is judged on the author's rules.
8. *Quota stops.* A stop for a quota or rate limit is always handled the same way: wait for the reset, then resume the same frozen
   plan with the same length.

9. *Acquisition and analysis checkouts.* The orchestrators freeze the repository commit in every plan and refuse to resume under
   another. All acquisition, meaning the rule-development runs, the event runs and the baseline, therefore runs from a separate
   worktree fixed at the campaign commit and never changed. It resumes, if needed, after any later commit. The rules, the scoring
   code and the analysis are committed from the main checkout. The campaign commit is named in every plan and in the report.
10. *Failed exports.* An event run whose client-log export fails is kept as an attempt and retried, like a baseline session; it is
   never recorded as complete (this corrects the event orchestrator before any run).

**Why.** To keep the true positives and the false-positive rate out of sample, restore the preregistered threshold, and make the H5
verdict a rule written before any confirmatory data rather than a reading of them.
**Effect.**
- RQ5 stays confirmatory, with rules developed on exploratory runs and the development baseline only.
- The baseline is unchanged at D24's two hours per client.
- Limitation, reported: the baseline has no benign server starts or benign definition changes, so the false-positive rate measures
  normal use, not benign look-alikes. With two confirmatory runs per pair, detection rates are imprecise. The local-engine
  repetition remains not done.

### D28 · 22 Oct 2026 · D24 point 4, D25 point 2 — the baseline driver after the set-up sessions
**Problem.** The six exploratory set-up sessions (D25 point 2, folder `setup-r1`, 22 October, six minutes each, harness `b1d6104`)
found four faults in the baseline driver. None of them was in a client.
1. *A busy client taken for a ready one.* The driver declared a task over when the client's ready pattern was on screen and the
   screen had not changed for eight seconds.
   - Goose keeps its start-up banner ("goose is ready") on screen while it works. Every "explain" task was declared done while
     Goose was still working ("… (Ctrl+C to interrupt)"). The next prompts were typed while Goose was busy, and they queued.
   - In cycles 3 and 4 there was no provider error, yet every task after "explain" failed.
   - In cycles 1 and 2 the provider also answered "503 Service Unavailable … experiencing high demand".
   - Gemini CLI and Qwen Code have the same weakness: their input line ("Type your message") is drawn under the spinner.
2. *A notice taken for a question.* Claude Code's screen said "Allowed by auto mode classifier": auto mode was on and no question
   was asked, as in Q3. The generic question pattern contained "Allow" without word boundaries. The driver pressed Enter for
   four minutes, until the task's timeout. Nothing was submitted: the input stayed empty and the timeline has no extra prompt.
3. *An unsent prompt.* In Codex CLI's last cycle, an account notice ("Set up security …", already in Q3's list of unrelated
   notices) was drawn just after the client opened. The prompt was typed and stayed unsent in the composer. The driver sent Escape
   at every poll, because the notice matched anywhere on the screen, and the notice stayed. The task timed out after four
   minutes.
4. *Cut cycles.* The session's end cut the last cycle of Codex CLI, Gemini CLI and Cursor CLI before the known-server task. Their
   calls per cycle (D24 point 4: "at least 0.8 calls per cycle to the known server") were then 0.75, 0.5 and 0.75, although
   every cycle that reached that task made its call. Gemini CLI and Cursor CLI did every task they were given (7/7, 15/15);
   Codex CLI did 12 of 13, because of fault 3.

**Change** (`telemetry/scripts/baseline_session.py`, `telemetry/scripts/q4_baseline.py`, `telemetry/baseline/clients.json`):
1. *Busy means not over.* A task is over only when all four of these hold:
   - the ready pattern is on screen;
   - the screen has not changed for the idle time;
   - the prompt was submitted (point 4);
   - the client is not working. A working line ("Ctrl+C to interrupt", "esc to cancel", "esc to interrupt", "ctrl+c to stop")
     counts only if it is in the bottom fifteen lines with no end-of-turn line after it (Goose's elapsed time, "… for Ns",
     "Worked for"). Old working lines above an ended turn do not count.

   Before typing a prompt, the driver waits for the same condition, for at most 90 seconds. If the client never settles,
   nothing is typed (`not-settled`).
2. *An error is not an answer.* The current turn's outcome is read once, after the prompt's echo:
   - "error": a model or API error (a fixed list, `ANSWER_ERROR`) is drawn with no answer text after it;
   - "answered": answer text is drawn after the last error;
   - "empty": anything else.

   Screen furniture (footers, input boxes, progress lines, elapsed-time lines) is not answer text. The "answered" evidence needs
   "answered". Every task exit records whether its turn ended on an error: done, no evidence, timeout, unsent, not settled,
   question limit, quota. `session.json` counts these once per task (`error_replies`).
3. *Notices and questions.*
   - A notice from the unchanged Q3 list is answered only while it is drawn in the bottom twelve lines and the client is not
     working. It is answered once before a prompt and at most once while a task runs. Its screen is kept before the keys are
     sent.
   - The generic question pattern matches "Allow" and "Approve" as whole words (`clients.json`, a revision in the sense of D25
     point 2).
   - At most three unexpected questions are answered per task. A fourth fails the task (`question-limit`).
4. *Submitted prompts.* The screen is read after the prompt's text is typed and before Enter. A task can be over only after the
   screen differs from that reading, or after a working line has appeared. If neither happens for 60 seconds, the task is
   recorded as `prompt-not-submitted` and fails at once, not at its timeout.
5. *A failed task ends the cycle.* A task can fail without completing: not settled, not submitted, question limit, timeout. When
   that happens, nothing more is typed in that cycle. The client is closed, and the cycle's remaining tasks count as prompted and
   failed, the known-server task included. A cycle whose client never gets ready counts all its tasks the same way, even when the
   session's time is over.
6. *Calls per cycle.*
   - D24 point 4's "at least 0.8 calls per cycle to the known server" becomes "at least 0.8 calls per cycle that reached the
     known-server task". Cycles counted under point 5 also count. The threshold is unchanged.
   - This relaxes a preregistered rule after exploratory set-up data and before any baseline session. In a sixty-minute session
     it can turn a failing session into a passing one only through its last cycle.
   - We had first decided to keep the rule (set-up log, 16:18), and reversed that when the same cut appeared in three clients.
7. *Provider unavailable.* Goose, Gemini CLI and Qwen Code use the same model on one free key.
   - A development or holdout session that fails its workload check with at least one error reply is a "provider unavailable"
     attempt. The driver makes no in-session retries.
   - The baseline orchestrator (`q4_baseline.py`) enforces the rest:
     - before running that session again, it waits until one hour has passed since the last such attempt;
     - after three such attempts, it records the client in `incomplete-clients.json` (written by the runner, never by hand) and
       skips the client's remaining sessions, its holdout included;
     - the frozen plan goes on with the other clients.
   - RQ5 for an incomplete client is exploratory (D13 point 5, D27 point 4).
   - Error replies in counted sessions stay in the data: they are part of the normal use against which the rules are scored.
8. *Set-up, second round.* All six clients run again in `setup-r2`, with the same seed, snapshot and length, and with the harness
   at the commit that carries this deviation. The corrections apply to every client, and Qwen Code's only valid session ran a
   single cycle. `setup-lineage.md` records each round's commit, the SHA-256 of `clients.json` and the reason for the next round.
   `clients.json` is frozen, with its SHA-256, after the last set-up round and before the first event run.

**Why.** Fault 1 counted unfinished and failed work as normal use. Faults 2–4 discarded sessions in which normal use happened. All
four were found on exploratory sessions, before any confirmatory data.

**Check on the recorded screens.** The new working-line and outcome rules were applied to every task end recorded in `setup-r1`:
- the 49 tasks that really ended in the five clients other than Goose all read "not working" and "answered";
- Goose's four wrong "done" read "working";
- Codex CLI's unsent prompt reads "empty".

**Effect.**
- No change to the events, the detection rules, the threshold of D6/D27 or the baseline's length.
- The validity rule of D24 point 4 is stricter for busy, unsent and error screens (points 1, 2, 4, 5), and amended for cut cycles
  (point 6).
- The `setup-r1` sessions are published as set-up evidence, except the Cursor CLI screens of MCP approval dialogs, which stay
  private (D27, plan of 22 October).

### D29 · 22 Oct 2026 · D24 points 3–4, D25 points 2 and 4, D26 point 8, D27 points 1, 4, 5, 7, 8 and 9, D28 point 8 — Cursor CLI without quota, Goose's ready pattern, longer set-up sessions
**Problem.** The second set-up round (`setup-r2`, harness `4b6be4c`, 22 October) counted Codex CLI, Qwen Code and Claude Code.
Three problems remained.
1. *Cursor CLI.* It stopped at its first task with "You've hit your usage limit". The author's Cursor account is on the free plan,
   and its included usage resets when the monthly cycle ends, on 15 November 2026. The stop was handled as D25 point 5 and D27
   point 8 require. Before that date, Cursor CLI cannot run event runs or baseline sessions. The frozen plans of D24 run over all
   clients in one order. Waiting as D27 point 8 says would hold the whole campaign until 15 November, after the blog post of
   27 October and the preprint of the week of 2 November.
2. *Goose's ready pattern.*
   - The baseline used the frozen Q3 ready patterns.
   - Goose's pattern ("goose is ready", "( O)>", or a line ending in ">") matched while its start-up banner was on screen.
   - Once the banner had scrolled away, the input line read "> Enter to send · Ctrl+J newline". Goose had made the requested
     edit and ended its turn, and the task timed out.
3. *Slow cycles in a six-minute set-up.* Gemini CLI did 3/3 tasks, with three correct "allow once" answers and no error. Each task
   took about 2.5 minutes ("This is taking a bit longer, we're still on it"), so the session ended before the known-server task.

**Change.**
1. *RQ5's confirmatory data are the five clients'; Cursor CLI becomes an exploratory addendum.*
   - The rule-development runs (D27 point 1, now 15), the event runs (D24 point 3, now 30) and the baseline (D24 point 4) run with
     `--clients claude-code,codex,gemini,qwen,goose` and the seeds of D25 and D27. The plans shuffle the five clients' runs: they
     are not the six-client order with Cursor CLI's runs removed. The orders are fixed below, before any run.
   - D27 point 4 is unchanged in substance. Its aggregation and the H5 judgement are made on these five clients, and that
     judgement is the confirmatory one.
   - H5 can only become true, never false, when a client is added: a type that fails on one measurable pair stays failed. If
     Cursor CLI's data entered the judgement after the five-client results were known, its rules, written by an author who knows
     those results, could decide H5. Cursor CLI therefore never changes the confirmatory judgement.
   - D27 point 8 ("wait for the reset, then resume the same frozen plan") is replaced, for Cursor CLI only, by this point.
     D27 point 4's "no client is retried selectively" still holds within each plan.
2. *Cursor CLI's addendum (exploratory).*
   - Schedule: its own set-up session (`setup-cursor`) on 15–16 November 2026, after the reset. Then, straight after: its 3
     rule-development runs, its 6 event runs, and its baseline (development, at least six hours' gap, holdout).
   - It uses `--clients cursor-agent`, the seeds of D25 and D27, and its own folders.
   - Usage estimate: about 10 prompts for the runs and about 140 for the baseline (about 35 cycles of 4 prompts). Several model
     requests per prompt.
   - If the free allowance stops a session, the author decides between one paid month and stopping; the decision and its date
     are recorded.
   - It runs from the same acquisition worktree and commit as the five clients (D27 point 9). A fix that only Cursor CLI needs,
     found in `setup-cursor`, gets its own deviation, a diff limited to the `cursor-agent` entry or code paths and a new commit
     named in Cursor CLI's plans. The five clients' data and plans are not touched. Any such difference is reported as a
     limitation.
   - If its snapshot login has expired (the Cursor CLI token of D26 point 3 is renewed by 27 November), it is renewed as D25 point
     4 says, in a Cursor-only snapshot named in its plans.
   - Rules for Cursor CLI are written only on its own development material and frozen before its holdout is opened. The freeze
     commit adds only Cursor CLI's rule files and its line in the SHA list. A script checks that every other frozen hash (scorer,
     applier, window definition, tool versions) equals the five-client freeze. The blind second author (D27 point 7) also writes
     rules for Cursor CLI, from a Cursor-only package.
   - Results: reported per pair, with the same metrics, as exploratory, next to the confirmatory five-client judgement. If not
     complete by 31 December 2026, the addendum reports what exists. A stop outside the author's control (quota, provider,
     login) is logged with its date.
   - The blog post of 27 October and the first preprint say only that Cursor CLI's test could not be completed for lack of
     quota. Its MCP approval screens stay private, as for every Cursor CLI run (plan of 22 October).
3. *Goose's ready pattern for the baseline.*
   - `baseline/clients.json` may give a client a ready pattern for the baseline. The driver then uses it in place of the frozen
     Q3 pattern when a cycle opens and when a task ends.
   - Goose's pattern adds its input line, "Enter to send · Ctrl+J newline", to the Q3 alternatives.
   - A ready pattern alone never ends a task: D28 still requires a submitted prompt, an unchanged screen and no working line.
     For Goose the input line is present at every turn end, so this rests on the working-line check.
   - The four Goose task ends of `setup-r2` show the input line only at turn ends. `setup-r3` keeps the screens of every Goose
     task end, and its lineage entry reports any input line seen on a working screen.
   - The Q3 pattern and Q3's results are unchanged.
4. *Longer set-up sessions.* D25 point 2 is amended in two ways:
   - a set-up session may last up to fifteen minutes, so that a slow client shows a complete cycle;
   - a client may be run again when its earlier session did not show a complete cycle, not only when its questions changed.

   `setup-r3` runs Goose and Gemini CLI, fifteen minutes each. It must show:
   - for each client, at least one complete cycle, including the known-server task;
   - a duration for every task;
   - no timeout caused by the driver.

   Goose and Gemini CLI share one free API key, so a quota or provider stop is handled as D27 point 8 and D28 point 7 say. Set-up
   sessions remain exploratory. The baseline's sixty-minute parts are unchanged.
5. *Logins for the five-client campaign.* Codex CLI's login in `q4-base-20261017` lasts until about 27 October.
   - If Codex CLI's sessions are not complete by then, the login is renewed in a new snapshot as D25 point 4 and D26 say.
   - A further deviation, written before Codex CLI's next run, then names that snapshot for Codex CLI's remaining runs and
     sessions.
   - D26 point 8, the rotation of the lab's secrets, waits until Cursor CLI's addendum is over.

**Frozen orders** (`--dry-run`, five clients, before any run):
- Rule-development runs (seed 20261022, one repetition): gemini q3-announced, goose q3-silent, goose q3-announced, gemini
  q5-start, qwen q3-silent, goose q5-start, claude-code q3-announced, gemini q3-silent, codex q5-start, claude-code q5-start,
  claude-code q3-silent, codex q3-announced, qwen q5-start, codex q3-silent, qwen q3-announced.
- Event runs (seed 20261018, two repetitions):
  - r1: goose q3-silent, codex q3-announced, qwen q3-silent, claude-code q3-silent, claude-code q5-start, qwen q5-start, gemini
    q5-start, qwen q3-announced, gemini q3-silent, gemini q3-announced, claude-code q3-announced, codex q3-silent, codex q5-start,
    goose q5-start, goose q3-announced;
  - r2: qwen q3-announced, goose q3-silent, qwen q5-start, codex q3-silent, gemini q5-start, gemini q3-announced, codex
    q3-announced, goose q5-start, claude-code q3-announced, claude-code q3-silent, codex q5-start, claude-code q5-start, goose
    q3-announced, gemini q3-silent, qwen q3-silent.
- Baseline (seed 20261019): development codex, claude-code, qwen, gemini, goose; then the holdouts in the same order.
- Cursor CLI: rule development q5-start, q3-announced, q3-silent; events r1 q3-silent, q3-announced, q5-start, then r2 in the same
  order; baseline development, then holdout.

**Why.**
- Point 1: the campaign can go on, and Cursor CLI's later rules cannot decide the confirmatory judgement.
- Points 3 and 4: a client must not fail for reasons that belong to the driver or to the set-up's length.

**Effect.**
- RQ5 is confirmatory on five clients. Cursor CLI's Q4 result is exploratory, about three weeks later. The snapshot holds the same
  version, but Cursor CLI can update itself when it starts; the version of every run is recorded and reported.
- The event and baseline orders are those fixed above.
- The preregistered six-client scope of RQ5 is reduced to five, and this is reported as a limitation.

### D30 · 22 Oct 2026 · D28 points 1, 2, 4 and 5, D29 points 3 and 4 — the end of Goose's turn; Gemini CLI's footer
**Problem.**
1. *Goose.* In `setup-r3` (harness `5c0d878`, fifteen minutes) Goose completed 6 of 14 tasks and never called the known server.
   - With the slow model of D18, Goose stayed still in the middle of a turn, between a tool's output and the model's reply, for
     longer than the idle time. It drew no working line in that session; in `setup-r1` it did.
   - The driver declared turns over too early. "Explain" was over at 47 seconds of a turn that took 73 seconds ("⏱ 1m 13s"). Of
     the 13 task ends that were not timeouts, 11 came too early.
   - The next prompt was then typed while Goose was working. Goose drew it as a plain line, queued it, and ran it after the
     current turn, echoing it only then ("> prompt"). The driver stayed one turn behind, and the following tasks ended without
     their evidence: the test ran during the "edit" task, for example.
   - D28's checks did not catch this. The screen was still, the ready pattern of D29 point 3 matched, and no working line was
     drawn.
2. *Gemini CLI's footer.*
   - In `setup-r3` (fifteen minutes) Gemini CLI meets D29 point 4: its second cycle is complete, with the known-server call after
     the frozen MCP approval, and every task has a duration.
   - Its one timeout is not the driver's. The edit of cycle 1 was made. Then the model returned an empty response, and Gemini CLI
     kept retrying on its own, past the task's 240-second limit ("This is taking a bit longer", 2 min 47 s, working line drawn).
   - The session is "not valid" by the workload rule: 7 of 9 tasks (0.78) and 0.5 calls per cycle, against 0.8 for both.
   - The timeout was recorded with `error_reply` false, because a line of Gemini CLI's footer ("workspace (…)") was read as
     answer text after the error.

**Change.**
1. *Turn-end line.* `baseline/clients.json` may give a client:
   - a turn-end line, which the client prints only when a turn is over. For Goose, its elapsed-time line ("⏱" and a number);
   - the format of its prompt echo. For Goose, "> " at the start of the line.

   For such a client, a turn is over only when a turn-end line is drawn after the prompt's echo. These cases are not over:
   - a plain queued copy of the prompt, with no echo;
   - an echo that is the last drawn line (its turn has just started).

   If neither the echo nor a copy is on screen, the echo has scrolled away, and any turn-end line counts. This is required in
   addition to D28's checks.
2. *The next prompt waits.* Before the next prompt, the driver waits for the previous prompt's turn to end, as part of D28 point
   1's 90-second wait. The previous prompt is forgotten when the client is launched again for a new cycle.
3. *Other clients.* They have no turn-end line, and their behaviour is unchanged.
4. *Screen furniture.* A line that starts with "workspace (" is added to D28's list of screen furniture.

Applied to every recorded task end, the turn-end rule changes only Goose's results:
- In `setup-r3` it reads "over" only on the two task ends that had really ended; it reads "not over" on the 11 early ones and on
  the timeout.
- In `setup-r2` it reads "over" on all four task ends, which had ended.

Applied to every recorded task end of all clients in `setup-r1` to `setup-r3`, the screen-furniture change alters one outcome
only: Gemini CLI's timeout, which now reads "error".

`setup-r4` runs Goose again for fifteen minutes. As D29 point 4 requires, it must show at least one complete cycle with the
known-server call, a duration for every task, and no timeout caused by the driver.

**Why.** Goose does not always draw a working line while it works, but it always prints its elapsed time at the end of a turn,
after its answer or its error.

**Effect.**
- None on events, rules, thresholds or other clients' task ends.
- Goose's baseline tasks are judged over only at Goose's own end-of-turn line.
- Gemini CLI's provider errors are now counted for D28 point 7.
- Risk, reported: slow provider answers may make Gemini CLI's sixty-minute sessions fail the workload rule. D28 point 7 then
  applies.

### D31 · 22 Oct 2026 · D25 point 2, D27 points 1, 4 and 5 — set-up sessions as rule-development material, window coverage, rule tooling
**Problem.**
- D27 point 1 names the material on which rules are written: the rule-development runs, the pipeline check and the development
  part of the baseline.
- The author also used the exploratory set-up sessions of D25 point 2 (`setup-r1` to `setup-r4`, normal use on the same snapshot)
  to check candidate rules for false alarms and to drop candidates. D27 did not list that material.
- Every archive also carries the snapshot's history, meaning records older than the run, from earlier lab work. "Changed" and
  "new name" rules read that history as the past.
- An adversarial review found two further problems:
  - Goose keeps only its last ten model requests, so most one-minute windows of a long session hold no record a Goose rule could
    fire on;
  - the tools that read the logs and apply the rules were not described in any deviation.

**Change.**
1. *Material.* Rule development may use the exploratory set-up sessions (D25 point 2) and the history carried by every archive, in
   addition to the material of D27 point 1. The confirmatory event runs and the holdout sessions remain excluded until the rules
   are frozen. Each use is recorded in `telemetry/rules/rule-development-log.md`.
2. *Coverage.* For every rule, the report gives, next to the false-positive windows, the number of holdout windows that hold at
   least one record of the rule's source. The threshold of D27 point 2 and the window count of D27 point 3 are unchanged.
3. *Tools.* Two scripts are frozen with the rules (D27 point 5):
   - `telemetry/rules/normalize.py` reads a client's default logs, from the redacted archive and only the client's frozen
     locations, as time-ordered records. Record times are read as the exporter reads them, with three additions: a time without a
     zone is read as UTC; Codex CLI's `ts_nanos` is added; colour codes before a time are ignored. A file with no timed record is
     dated by its file time and marked, and only a rule that says so may use such records.
   - `telemetry/rules/apply.py` applies rules of five types: match, changed, unannounced, new name, none. A pair whose rule is
     "none" is not distinguishable.
   - Lab literals are refused anywhere in a rule. A name hidden in regular-expression syntax is left to the reviews.

**Why.** The set-up sessions were the only normal use available before the baseline. They were used openly, and they contain no
confirmatory data.

**Effect.**
- No change to the events, the threshold, the windows or the aggregation of D27.
- The rules' false-positive check on development material covers more normal use than D27 foresaw.
- Coverage makes visible where a false-positive rate of zero only reflects absent records.

### D32 · 23 Oct 2026 · D25 point 5, D27 points 1 and 9, D29 point 2 — a quota stop without a limit message, an observer race, and a fresh start of the baseline
**Problem.**
1. *A quota stop without a limit message.*
   - The first baseline session was Codex CLI's development part, run on harness `be9317c`. After 40 of its 60 minutes, at the start
     of its sixteenth cycle, Codex CLI 0.162.1 showed a new notice: "You have 2 usage limit resets available. Run /usage to use
     one."
   - The notice was absent from the fifteen earlier cycles and from all six Codex CLI event runs. What makes it appear is not
     documented; third-party guides describe these resets as a way to continue after a limit is hit.
   - The generic pattern "usage limit" in `telemetry/scripts/quota.py` matched the notice, and the session was stopped. No screen of
     that session holds a limit message ("You've hit your usage limit", "try again at"), and Codex CLI went on working after the
     notice.
   - Whether the account was close to a limit at that moment is unknown.
2. *Observer race.*
   - Twice the observer found the tmux session present, and its screen capture then failed with "no server running", because the
     runner had just closed tmux.
   - Once was in the event runs (`qwen__q5-start__r1`, attempt 1, kept and repeated on 22 October). The other was in this session,
     2 s before a cycle closed.
   - D25 point 5 counts every read failure as a stop.

**Change.**
1. *The pattern.* The generic pattern no longer matches "usage limit" when the next words are "resets available". Real limit
   messages still match, including those that say when a limit resets: "Your usage limit resets in 3h", "Usage limit reached for
   …", "You've hit your usage limit".
2. *The observer (D25 point 5 amended).* When a screen capture fails, the observer checks the session again. If the session no
   longer exists, it writes a "vanished" record with its time, and counts it apart from read errors and from absent sessions. A
   failure while the session still exists remains an error and a stop. A client that dies mid-cycle is still caught by the
   driver, which records the failed tasks.
3. *Before restarting.* Codex CLI's account usage (five-hour and weekly) is read outside any measured session, on the vendor's
   usage page, and written in the campaign log. If either window is nearly used up, the baseline waits for it to reset, in the
   spirit of D27 point 8.
4. *Fresh start of the baseline.*
   - The orchestrators freeze the harness commit in each plan, so the baseline cannot resume under the corrected code. It starts
     again in a new folder, `baseline-r2`, with the same seed (20261019), the same five clients and order, the same lengths and
     gap, and the same snapshot.
   - Its acquisition commit is `be9317c` plus only the two corrections of this deviation, on a branch of its own (`acq-baseline`),
     so the rule files of D31 are not copied into the VM. D27 point 9 is amended: the event runs used `be9317c`, and the baseline
     uses that branch's commit.
   - D29 point 2 is amended: Cursor CLI's later phases (set-up, rule-development runs, event runs and baseline) use that branch's
     commit too.
5. *The first folder.* `baseline/` is kept and published as an attempt: one Codex CLI development session, not counted. It is
   excluded from rule development, and its client-log archives stay closed.

**Why.**
- A notice that offers resets is not a limit message.
- A session that ends between two reads is not a broken observer.
- Neither stop came from the clients' normal use.

**Effect.**
- No change to events, rules, thresholds or lengths.
- The baseline starts about two hours later than planned.

### D33 · 23 Oct 2026 · D28 point 8, D29 point 3, D32 point 4 — Qwen Code's ready pattern when a suggestion replaces its placeholder; a third start of the baseline
**Problem.**
- `baseline-r2` (acquisition commit `3481e6f`) counted Codex CLI's and Claude Code's development sessions. Qwen Code's development
  session then failed its workload check, with 35 of 56 tasks and 5 calls in 14 cycles.
- Its "edit" task timed out in 8 of 13 cycles, although the edit had been made and Qwen Code had answered ("I have appended …").
- After those turns, Qwen Code drew a suggested next prompt ("> run the tests") in its input line instead of its placeholder,
  "Type your message …". The placeholder was its only ready pattern (the frozen Q3 pattern), so the driver never saw it ready.
- Among the recorded screens, Qwen Code showed this in 9 of 61 (set-up rounds and this attempt). Gemini CLI never showed it, in
  32 screens, and Goose has its own pattern (D29).

**Change.**
1. *The ready pattern.*
   - `baseline/clients.json` gives Qwen Code a baseline ready pattern: its placeholder, or its idle footer line, which begins with
     "Auto mode (shift + tab to cycle)".
   - While Qwen Code works, that footer begins with "Enter to steer", which the pattern does not match.
   - D28's checks still apply: a submitted prompt, an unchanged screen and no working line.
   - On the recorded screens, the new pattern reads all 9 screens with a suggestion as ready and loses none of the screens the old
     pattern read as ready.
   - This revises `clients.json` after its freeze (D28 point 8). The revision is limited to Qwen Code's entry.
2. *A check before the restart (exploratory).*
   - The recorded screens never show a prompt typed while a suggestion is drawn: every such screen ended its cycle.
   - One fifteen-minute set-up session of Qwen Code (`setup-r5`, D25 point 2, D29 point 4) runs on the corrected commit before the
     baseline. It must show at least one task typed after a suggestion was drawn, with the typed prompt alone echoed and its
     evidence present.
   - If it does not, the baseline does not start and the cause is examined.
3. *Other clients.*
   - Gemini CLI: no suggestion appears in its 32 recorded screens, and no idle-only footer line exists to use instead.
   - Goose: its pattern (D29) matched 43 of 44 screens. The one miss is the queued-prompt case handled by D30.
   - Their patterns are not changed without evidence.
4. *A third start of the baseline.*
   - The plan freezes the harness commit, so the baseline starts again in a new folder, `baseline-r3`. The seed (20261019), clients,
     order, lengths, gap and snapshot are the same as before.
   - The acquisition commit is that of `baseline-r2` (`3481e6f`) plus only this revision, on the same branch (`acq-baseline`).
   - D32 point 4 is amended accordingly, and Cursor CLI's later phases (D29 point 2, D32 point 4) use this commit.
   - `baseline-r2` is kept and published as an attempt: two counted development sessions (Codex CLI, Claude Code) and one failed
     one (Qwen Code), none of them counted in `baseline-r3`.
   - Its development sessions remain rule-development material (D27 point 1, D31). Codex CLI's and Claude Code's client logs had
     already been read for their candidate rules before this deviation; no candidate changed.
   - This differs from D32, which kept `baseline/` closed and excluded, because that material had not been read.
   - Any rule-development round on `baseline-r3`'s development hours reports the `baseline-r2` results next to them.
5. *Limitation.* The pattern depends on Qwen Code's footer text for its default approval mode. If that mode or the text changes,
   the old failure can return.

**Why.** A suggestion drawn in the input line is not a sign of work. The driver must recognise an idle client by a line the client
draws whenever it is idle.

**Effect.**
- No change to events, rules, thresholds or lengths.
- The baseline restarts about four hours after its first start.
- Codex CLI's and Claude Code's development hours are recorded again.

### D34 · 23 Oct 2026 · D18 point 3, D25 point 2, D27 point 8, D28 points 3 and 7, D33 — Qwen Code's feedback survey, a check of the typed prompt before Enter, and a paid tier for the Gemini API key
**Problem.**
1. *The survey.*
   - Qwen Code sometimes shows a feedback survey under its last answer: "How is Qwen doing this session? (optional) 1: Good 2:
     Bad 3: Fine 0: Dismiss". While it is open, a digit typed into the next prompt answers it and vanishes from the prompt.
   - Three prompts were altered, all of the known-server task: in `setup-r2`, `setup-r5` and Qwen Code's development session of
     `baseline-r2`, each in its first cycle. "Call the q3_noop tool of the q3-lab MCP server" arrived as "Call the q_noop tool of
     the q-lab MCP server". The model still called the right tool.
   - The survey was also drawn once without altering a prompt (`setup-r1`, the cycle ended right after).
   - The survey can be drawn up to about 16 s after a turn ends, after the driver's idle check, so answering it once before
     typing is not enough.
   - Each altered prompt answered the survey ("Fine") from the lab's Qwen Code account.
   - Q3 is not affected: all 50 Qwen Code prompts of the Q3 primary runs are intact, and no survey appears there.
   - Codex CLI draws a card that also takes digits ("Press a number to choose"). The frozen Q3 notice list closes it (D28 point 3);
     no prompt was altered by it.
2. *Quota.*
   - The free tier of the Gemini API key used by Gemini CLI, Qwen Code and Goose (D18 point 3) ran out twice: on 22 October during
     the event runs, and on 23 October during `setup-r5`, with "exceeded your current quota".
   - The baseline needs about six hours of these three clients. The free tier allows about one and a half to two hours a day. The
     baseline would end after the blog post of 27 October.

**Change.**
1. *Baseline notices.*
   - `baseline/clients.json` may list a client's own notices, with the keys that close them. The frozen Q3 list of notices (D28
     point 3) is unchanged.
   - Qwen Code's survey is closed with "0" (Dismiss), under the rules of D28 point 3: only at the bottom of the screen, never while
     the client works, with the screen kept before and after the key.
2. *Right before typing (all clients).* A prompt is typed only on a screen that is ready, idle, past the previous turn and free
   of notices. A notice drawn after the ready marker is answered, at most twice, and the client must then settle again. If it does
   not within the settle time, or a notice is still drawn after two answers, nothing is typed and the task ends as `not-settled`
   (D28 point 7).
3. *Before Enter (all clients).*
   - The driver compares the screen before typing with the screen after typing, line by line. Among the lines that typing drew
     or changed, the input must be the prompt alone, after white space, box borders and scroll bars are dropped: it may run over
     line ends, only an input marker may stand before it on its first line, and nothing may follow it on its last.
   - Otherwise Enter is not pressed, and the task ends with a new hard failure, `prompt-mangled`: the cycle ends and the client
     is closed, as for the other hard failures (D28 point 7).
   - The comparison ignores an earlier cycle's echo of the same prompt.
   - On the recorded set-up and development screens, the normalisation reads all 1,031 echoed prompts of the six clients as whole.
4. *Paid tier.*
   - The author enables billing on the Google project of the same API key. The key, the model (`gemini-flash-lite-latest`, D18
     point 3), the clients and their settings are unchanged; only the quota changes.
   - The time of the change is logged, with the project name and never the key. The author sets a spending cap on the project.
   - Runs and sessions recorded before the change keep their place: the event runs ran on the free tier.
   - `gemini-flash-lite-latest` is an alias. The model version that served each session is reported where the clients' own logs
     record it, and is otherwise a limitation.
   - Differences that the tier could make, such as latency, provider errors and Google's data-use terms, are reported as a
     limitation.
5. *Check before the baseline.*
   - One more fifteen-minute set-up session of Qwen Code (`setup-r6`, D25 point 2) runs on the corrected commit and the paid tier.
   - A script decides it: no task ends `prompt-mangled`; no echoed prompt on any screen is altered; after every answered notice,
     the screen after the keys is kept and the notice (from the frozen Q3 list or the client's own) is gone from the bottom of
     the screen; the session meets its workload with no quota stop. The script uses the driver's own definitions.
   - On the recorded sessions, the script flags exactly the four screens of the three altered prompts, and nothing else.
   - If it fails, the baseline does not start.
6. *Commit.*
   - The acquisition commit becomes D33's commit plus only this change, on `acq-baseline`. `baseline-r3` starts from it.
   - D32 point 4 and D33 point 4 are amended, and so are Cursor CLI's later phases.

**Why.**
- A prompt that loses characters is not the scripted normal use, and a check on the screen is the only one the driver has before
  the prompt is sent.
- A quota that lasts two hours a day would push three clients' baseline past the date of the first report.

**Effect.**
- No change to events, rules, thresholds or lengths.
- The three Gemini-backed clients' baseline runs on the paid tier.
- A cycle can now end with `prompt-mangled`; such cycles are counted and reported like the other hard failures.
- Cursor CLI's later phases use the new commit.

### D35 · 23 Oct 2026 · D18 point 3, D25 point 4, D27 point 8, D32 point 1, D34 points 2–6 — Qwen Code's cursor character, Claude Code's usage notices, a prepaid Gemini API key, and checks of every client's input line without sending
**Problem.**
1. *`setup-r6`.*
   - It ran on D34's commit (`1c18719`). Every cycle ended at its first task with `prompt-mangled`: 19 cycles, 0 tasks done.
   - The prompt was whole each time. Qwen Code 0.25.1 draws its cursor as a zero-width space (U+200B) after the typed text, and
     D34's check allowed nothing after the prompt.
   - Enter was never pressed: no prompt was sent. The lab server saw only start-up calls (19 of each list and initialize call),
     and no tool call. The check of the `setup-r6` screens covers the typed screens only: the driver kept no screen from before.
   - D34's check had been validated on echoed prompts, which carry no cursor.
2. *Claude Code's usage notice.* In a check after one real turn, Claude Code 2.1.300 drew "You've used 76% of your weekly limit
   · resets Oct 24, 10pm" in its footer. The pattern "weekly limit" in `telemetry/scripts/quota.py` matched it, and the task was
   stopped as a quota stop. The notice is not a stop.
3. *The Gemini key.*
   - D34 point 4 planned a paid tier on the Google project of the lab's key. On 23 October at about 17:45 that key answered with
     "Quota exceeded for metric … generate_content_free_tier_requests, limit: 500, model: gemini-3.5-flash-lite": it was still on
     the free tier. Whether billing had been set on another project is not known; the key is replaced.
   - At 18:04 the author installed a new key of another project of his, with prepaid billing. With no credit it answered "Your
     prepayment credits are depleted"; after the author's top-up, at 18:07, it answered (`modelVersion` `gemini-3.5-flash-lite`,
     `serviceTier` standard).

**Change.**
1. *Folding of the input line.* Zero-width characters (U+200B–U+200D, U+2060, U+FEFF) are allowed only at the very end of the
   input, after the last character of the prompt. Anywhere inside it, a line end of a wrapped prompt included, they fail. The rule is unchanged: the input must be the prompt alone. As in D34, white space and box borders inside the
   input are ignored, so a space inside a word, or a character wrapped onto its own line, would not be seen; `tmux send-keys -l`
   with the ASCII prompts cannot produce either.
2. *Reading the input line again.* When the check fails, the driver reads the screen again, 0.6 s apart, up to five reads in
   all, and stops early when two reads are equal. Enter is pressed only if the last read passes; otherwise the task ends
   `prompt-mangled`. The number of reads is logged with the prompt.
3. *Usage notices.*
   - For Claude Code, "You've used N% of your … limit" is removed from the screen text before the quota patterns are applied
     (white space and a line break tolerated). "You've hit your … limit", "Claude usage limit reached" and "… weekly limit" (any
     other wording) still match.
   - "Your prepayment credits are depleted" is a quota stop for every client (D27 point 8).
   - On the recorded screens (1,150 across the six clients, events and holdouts excluded) the patterns match only the screens
     already recorded as quota stops.
4. *The Gemini key (D34 point 4 replaced).*
   - The three Gemini-backed clients (D18 point 3) use the new key, with the same model, clients and settings.
   - The key is set by the author in `~/.agentlab_secrets` of a new snapshot, `q4-base-20261023b` (D25 point 4): the snapshot
     `q4-base-20261017` plus only the new key, in both variables of that file (`GEMINI_API_KEY` for Gemini CLI and Qwen Code,
     `GOOGLE_API_KEY` for Goose). An intermediate snapshot, `q4-base-20261023`, had only the first line changed: in the check after
     a turn, Goose still used the old key and met its free-tier limit. It is not used. All baseline sessions, of every client,
     use `q4-base-20261023b`. The event runs used
     `q4-base-20261017` and the old key on its free tier.
   - The prepaid credit is the spending cap: when it is used up, requests are refused and the session stops as a quota stop.
   - The key is never logged or published; the project is named only in the author's private notes.
   - Differences the tier could make (latency, rate limits, Google's data-use terms) are a limitation. The lab's content is
     synthetic.
5. *Checks without sending (23 October).* A script opens each client in the VM, restored to its snapshot, types prompts and
   checks the input line with the driver's `composer_holds` and its re-read rule. The SHA-256 of the driver and of `quota.py`
   in the VM are recorded with each folder. After the checks, the driver changed only in where a zero-width character is
   allowed (point 1); every saved screen pair was replayed with the final driver, with the same results.
   - Into a freshly started client, all four prompts, Enter never pressed: 20 of 20 read as whole (5 clients). D34's version
     read 16 of 20; the 4 failures were Qwen Code's.
   - After one real "explain" turn (Enter pressed for that task only), the test, edit (cycle 10) and known-server prompts, never
     sent: 15 of 15 (5 clients), with the driver and `quota.py` of SHA-256 `761dbb34…` and `d22125bb…`. Goose
     first met the old key's free-tier limit on the intermediate snapshot and was checked again on `q4-base-20261023b`.
   - Six synthetic alterations of each typed prompt (a dropped letter, a zero-width character inside, a "0" before or after, a
     "/" before, a soft hyphen inside), replayed with the corrected driver on every saved screen pair, are all rejected: 366 of
     366.
   - Cursor CLI was not checked. The same checks run before its phase (D29).
6. *`setup-r7`, then `baseline-r3`.*
   - `setup-r7` (Qwen Code, fifteen minutes, D34 point 5) runs on the corrected commit and the new snapshot. It is decided by
     `check_setup_r6.py` (SHA-256 `519581fb…`), which loads the harness's own driver and its folding, and also requires the
     host's acceptance of the session (its `run.json`, written after the quota observer, the copies and the export).
   - `baseline-r3` starts only if `setup-r7` passes, with the plan of D33 (seed 20261019, the five clients in the order Codex
     CLI, Claude Code, Qwen Code, Gemini CLI, Goose, development then holdout, 60 minutes, six hours' gap), on the new snapshot.
   - If a check fails and needs a code change, the baseline starts again in a new folder from the next commit.
   - `setup-r6` is kept and published as an attempt.
7. *Other clients' quota on the author's accounts.* Claude Code's account was at 76% of its weekly limit on 23 October (reset
   24 October, 22:00). A stop at the limit is a quota stop under D27 point 8.
8. *Commit.* The acquisition commit becomes D34's commit plus only this change, on `acq-baseline`.

**Why.** A check that stops a whole prompt, and a notice read as a stop, are faults of the driver, not of the clients. Typing
without sending tests every client's input line at almost no cost. The free tier could not carry three clients' baseline before
the blog post of 27 October; a prepaid key gives the quota with a hard spending cap.

**Effect.**
- No change to events, rules, thresholds or lengths.
- The baseline runs on a snapshot that differs from the events' only by the Gemini key.
- Gemini requests are paid from the author's prepaid credit.

### D36 · 23 Oct 2026 · D13 point 4, D24 points 2 and 5, D27 points 2–6, D28 point 6, D31 points 2–3 — rules on host telemetry, the start time of a repository-declared server, and the scoring tools
**Problem.**
1. *Host-telemetry rules.* D27 point 5 asks for one rule per event type on host telemetry, frozen with the client-log rules and
   reported apart. None had been written. Exploration on development material only (the rule-development runs, the pipeline
   check, the set-up sessions and the development sessions of `baseline-r2`) found:
   - the audit log records the start of a repository-declared server: the AI client starts an interpreter or runner in the
     project folder at its own start-up;
   - nothing in the audit log, the journal or the outgoing-connection lines changes when an approved server changes its tool
     definition, with or without a notification: the change happens inside a process that is already running, over stdio.
2. *The start time of a repository-declared server.* The ground truth of Q5 is the "start" record that the server process writes
   itself. The audit log records that process's exec 0.06 to 0.22 s earlier, on the same clock. Under D24 point 5 ("hits before
   the event do not count"), a rule that sees the start would be scored as a miss.
3. *The audit log rotates.* Only the current `/var/log/audit/audit.log` is copied (D24). In hour-long sessions it rotates: in the
   development sessions of `baseline-r2`, 39 and 19 of 60 one-minute windows hold any process-start record, and the client's
   start-up at the beginning of the session is lost. The event runs are short and keep their whole log.
4. *Tools.* D27 point 5 freezes the scripts that apply and score the rules. Two were missing: the one that turns rule hits and
   ground truth into the scorer's input, and the one that computes the verdict of D27 point 4.

**Change.**
1. *Host rules.*
   - `host/q5-start` (H-Q5): an AI client process (public product names: claude, codex, gemini, qwen, goose, cursor-agent,
     cursor) directly starts an MCP launcher (an interpreter or runner such as node, npx, python, uvx or docker, not a shell),
     with its working directory in a project folder (a folder inside a home folder that is not hidden), within 30 s of the
     client's own start; and the launcher's command line, digits replaced by N, has not been seen before as a child of an AI
     client on this host.
   - "Seen before" means in a learning set, or earlier inside the same run or session. The learning set holds the commands that
     AI clients started inside the windows of development sessions: the set-up sessions and the development sessions of the
     baseline, never the event runs, the holdout sessions or the log's older history. It is computed by `host.py learn`,
     published and frozen with the rules. It is data drawn from normal use, not text written into a rule (D27 point 6).
   - `host/q3-announced` and `host/q3-silent`: none. Host telemetry cannot tell these events apart.
   - Two other candidates were tried and dropped, with their results, in the rule-development log: a write to a trust or approval
     store long after the writing process started (never after the event; 5.2% of normal one-minute windows), and the same server
     launched again by the same client (it fires only because the harness restarts the client, equally for both Q3 events).
   - Each host rule is scored over all five clients' event runs of its type and all five holdout sessions, and also per client.
2. *Start time of a repository-declared server (all rules).* The event time of a Q5 run is the time of the audit log's last
   successful exec, at or before the canary's "start" record and within 60 s of it, of the process whose pid that record names;
   without such an exec record, the "start" record's time. Whether the event happened is still decided by the "start" record of
   the run's client. The definition is the same for client-log and host rules; it can only add hits in the fraction of a second
   between the two records. On development material the pid matched in every run.
3. *Coverage of host holdouts.* For every host holdout the report gives the windows that hold at least one process-start record
   (as D31 point 2 does for client logs), and the host false-positive share is given both over all windows and over the covered
   ones. The acquisition is not changed: the host results are reported apart from H5, and `baseline-r3` is already running on a
   frozen commit.
4. *Tools, frozen with the rules (D27 point 5).*
   - `telemetry/rules/scores_input.py`: the input of `score.py`. Event times come from the ground-truth logs only: for Q3 the lab
     server's single change of definition to B for the run's cell, as in `q4_events.py`; for Q5 point 2. Hits count from 5 s
     before the run's t0. A run ends 120 s after its t1, the moment its scripted session returned: the clients are then stopped
     and the logs copied (D24 point 5, "until the logs are copied"), which took 3.2 to 4.5 s in the 18 rule-development and
     pipeline runs; the copied archive holds nothing written after the copy. Holdout windows are cut from `t_start` to `t_end`
     of the session's `session.json` (D27 point 3), with coverage per rule. Every run and holdout of the plans must be there and
     usable: an absent or unusable one (a failed export, a missing audit log for host rules) is listed under "missing" with its
     client; a planned pair without a rule stops the build.
   - `telemetry/rules/h5.py`: the verdict of D27 point 4, on client-log rules only. A pair is measurable if at least one counted
     run shows the event; an event type is distinguishable if every measurable pair's rule tells it apart; H5 holds if some event
     type with a measurable pair is not distinguishable. A client whose confirmatory data are incomplete (the runner's
     provider-incomplete clients of D28 point 6, and every client with something listed as missing) is marked preliminary, and the
     verdict is given with and without those clients; otherwise a measurable pair with no holdout windows does not pass.
   - `telemetry/rules/host.py`: the host rules, the learning set, the exec lookup of point 2 and the coverage of point 3.
   - `telemetry/scripts/score.py` (D24 point 5) also reports, for each rule, the covered windows (total and per session) and the
     false-positive share over them; the threshold stays on all windows.
   - On development material the whole chain runs: client-log rules on the rule-development runs, with the development sessions
     of `baseline-r2` in place of holdouts; host rules with a learning set of 5 commands. `host/q5-start` detects 3 of 3 rule-
     development runs where the event happened (and the pipeline check's), at the exec.

**Why.** D27 point 5 requires the host rules and the scoring tools to be frozen before any holdout is opened; the start time must
be fixed now, before any rule is scored.

**Effect.**
- No change to the client-log rules, the threshold or the windows. The H5 verdict rests on client logs only.
- Host results are reported apart, per event type and per client.
- Limits of the Q5 host rule: it misses a repository-declared server whose command line was already seen on the host; it assumes
  the repository is opened when the client starts; it sees only the lab user's processes; and in the holdout it is tested mostly
  on the harness's own commands, which the learning set already holds, over windows the rotating log only partly covers.

### D37 · 23 Oct 2026 · D27 point 8, D32 points 1 and 3, D33 point 4, D35 points 3 and 6 — a tip read as a quota stop; a fourth start of the baseline
**Problem.**
- `baseline-r3` (acquisition commit `cf77407`, snapshot `q4-base-20261023b`) stopped in its first session, Codex CLI's development
  part, after about 49 minutes (48.8 minutes from `t_start` to `t_end`) and 19 cycles: 74 of 75 prompted tasks done, and the
  known server called in each of the 18 cycles that reached its task.
- Under an answer, Codex CLI 0.162.1 drew a tip: "Tip: When signed in with ChatGPT, use /usage to check your account usage and
  access available usage limit resets." The generic pattern "usage limit" matched it; D32's exception covered only "usage limit
  resets available". The quota observer and the driver flagged it within half a second and the session was stopped.
- The tip is not a limit. Codex CLI had finished its turn (the edit was made, the input line was idle), and no limit message
  appears on any screen or in the observer's record. The one task counted as not done is that last edit, stopped with the session.
- The tips change at random: the recorded screens hold 32 different Codex CLI tips and 8 of Cursor CLI.

**Change.**
1. *Patterns (`telemetry/scripts/quota.py`, SHA-256 `ad064cb4…`).*
   - For Codex CLI only, the recorded phrase "available usage limit resets" (also across a line break) is removed before the
     patterns are applied. The rest of the tip's line is still read, so a failure on the same line still matches.
   - No general rule on tips: a tip never recorded that names a limit could stop a session again. That would be a false stop,
     handled as this one, never a missed one.
   - Real limit messages still match ("You've hit your usage limit", "Your usage limit resets in 3h", "Usage limit reached for …").
   - On all recorded screen files (1,462, copies included; events and holdouts excluded), the new patterns change the result of
     only the two screens of this stop.
2. *Records of `baseline-r3`.* Its attempt keeps the records as written (the problems in `attempt.json`, `quota_exhausted` in
   `session.json`, the observer's `quota-watch.jsonl`); this deviation reclassifies the stop as a false alarm in its text only.
   Because it was not a quota stop, D27 point 8 (wait for the reset and resume the same plan) does not apply.
3. *A fourth start of the baseline.*
   - As in D32 and D33, the plan freezes the harness commit, so the baseline starts again in a new folder, `baseline-r4`, from the
     corrected commit, with the plan of D33 (seed 20261019, the same five clients and order, 60 minutes, six hours' gap) and the
     snapshot of D35 (`q4-base-20261023b`). The `baseline-r3` folder is not rerun.
   - Before the restart, Codex CLI's account usage (five-hour and weekly) is read on the vendor's usage page and written in the
     campaign log (D32 point 3); if either is nearly used up, the restart waits for it. Read by the author on 23 October in the
     evening: 1% used.
   - `baseline-r3` is kept and published as an attempt. Its Codex CLI development session is development material (D27 point 1,
     D31), as `baseline-r2`'s were; any rule-development round reports it next to `baseline-r4`'s.
   - The acquisition commit becomes D35's commit plus only this change, on `acq-baseline`.

**Why.** A tip is not a quota message, and the stop did not come from the client's normal use.

**Effect.**
- No change to events, rules, thresholds or lengths.
- The baseline restarts about three hours after `baseline-r3`'s start.

### D38 · 24 Oct 2026 · D17 point 7, D21, D22 — the author's adjudication of RQ4, helped by a third reading that proposes
**Problem.** D22 has every disagreement between the two readings on a tool decided by the author against the source, with
file:line. There were 91 such tools in the servers whose figures are published. The adjudication sheet showed both readings and the
cited code; deciding 91 cases from it alone proved slow for the author.

**Change.**
1. A third reading, by AI-model sessions (the coordinator's model, Claude Opus 5.5) that saw only the adjudication pages (both
   readings and the cited code) and the rules of D17 points 2–4, proposed for each case a class, a protection and a vendor-only flag,
   with a short reason, the line that settles it and a confidence; where the cited code was not enough it proposed the reading with
   less protection.
2. The author decided each case in a guided page that showed the disputed fields, the cited lines and the proposal, and could accept
   it or choose otherwise. For each case the exported sheet records whether the proposal was taken as it was or the author chose
   otherwise.
3. The proposals and the sheet are published with the census (`defence-coverage/results-20261024/`), for the published servers
   only. The guided page is not: it also carried rows of servers whose figures are not published. Agreement between the two original readings is still
   measured before any decision, on their original labels (D22).
4. The three AWS servers' figures are unchanged from those agreed with AWS.
5. After the Codex review of this deviation, the author decided one case again: Sentry's `find_dashboards` returns dashboard titles,
   which D17 point 2 counts as third-party prose, and the cited code has no defence (A, none). The sheet records it.

**Why.** The decision stays the author's and is checked against the source; the proposal makes the cited code readable for a
non-programmer and is kept with the record.

**Effect.** The final labels are the author's. The third reading may have influenced them; the sheet shows, case by case, where the
author followed it.

### D39 · 24 Oct 2026 · D5 (secondary cells, local engine), D16 points 5–6 — the open-weight cells, run after part 4's confirmatory results
**Problem.** D5 lists a secondary, exploratory cell per client with a local engine, and D16 point 5 says that B reached the model
is claimed only in local-engine cells, from a recording proxy. Part 2 announced these runs in public ("Clients that accept a custom
endpoint will also run against open-weight models on a GPU instance we control"). Neither the cells nor the proxy were made before
part 3 or part 4.

**Change.**
1. Exploratory cells, one repetition (D5): client × signal {none, `notifications/tools/list_changed`}, description change only,
   stdio, the server and the three phases of D16 (call, change, call; the reopen phase reported apart, D16 point 6).
2. Clients: only those whose own documented options point them at another model endpoint; each is checked in the VM before the
   cells. Candidates: Qwen Code (OpenAI-compatible endpoint), Goose (Ollama provider), Codex CLI (`--oss --local-provider ollama`
   or a configured provider), Claude Code only if the endpoint offers an Anthropic-compatible API. A client that cannot be pointed
   at the endpoint is listed with the reason. The launch command of every phase, reopening included, comes from a separate file
   (`tool-change/scripts/q3-clients-open-weight.json`), never from `q3-clients.json`.
3. Model: `qwen3.8:27b-q8_0` served by Ollama on our GPU instance; tag and digest are recorded. Other open-weight models only as
   single control cells, named as such.
4. A recording proxy (`tool-change/scripts/record_proxy.py`) runs in the VM between the client and the endpoint, forwards every
   request and response unchanged and writes, per request, the time, the model and each tool's name, a SHA-256 of its description
   and the revision (A/B) it names; prompts and replies are not recorded.
5. A cell is valid only if the proxy shows, for that client, requests to the intended model carrying revision A before the change;
   otherwise it is discarded with the reason. Results are given per phase: phase 2 (requests with A after the change; the first
   request with B and its delay, or "B not seen before the session closed"; whether the call succeeded) and phase 3 apart.

6. *Added on 24 October, after the routing checks and before any cell* (commit after `ebc4bd3`). Two clients hand MCP tools to the
   model in ways point 4 did not cover: Codex CLI groups them in a `namespace` entry of `tools[]` (recorded as
   `<namespace>/<tool>`), and Qwen Code passes them through a tool search, so the definition reaches the model inside the
   messages. The proxy therefore also counts, per request, how many times each revision is named outside `tools[]` (counts only,
   no text). The VM reaches the model through a reverse SSH tunnel opened from the host after each restore
   (`q3_open_weight_host.py`), because the host firewall does not accept connections from the VM and is left unchanged.

**Why.** It is the only way to see which definition a client hands to the model, which the vendors' hosted models do not show, and
it keeps the promise made in part 2.

**Effect.** Exploratory. It cannot change H3, H5 or any confirmatory result, and it is reported as an addendum to part 3 and part 4.
