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
