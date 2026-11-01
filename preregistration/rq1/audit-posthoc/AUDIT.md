# RQ1 audit of the 120 sampled cases (post hoc, exploratory)

**Status.** Written on 31 October 2026, after the RQ1 confirmatory results (run `rq1-confirmatory-20261027T142818Z`).
It is post hoc and exploratory. It changes no label, no summary, no flag, no confirmatory estimate and no verdict, and it does
not change the taxonomy. The frozen criteria (`classify.py`, `CRITERIA`, SHA-256 `1dbc3906…b8700b8`, checked unchanged) are the only
yardstick. Each alternative count below is a separate exploratory variant, not a replacement for the primary analysis.

**Who did it.** An AI assistant (Claude) did the audit, reading files only. No second human checked it. The mechanism coding
and the categories are one coder's judgement; the per-case file gives the reason for each.

**Inputs** (first 16 hex digits of SHA-256): `rq1-frame.csv` 5fe33295abf0a529 (= manifest), `rq1-sample.csv` 2ae5f0389faeb407,
`rq1-r0.json` 06ef87a02908090a, `rq1-summary-records.json` d0a2b62728cd9868, `summary-checks.csv` 7bf8de3374699333,
`rq1-flags.json` c4282b4b9524b6cb, the three model result files of the run, and `criteria-it.txt` 69fdf30991da2fe6. Part (b)
uses the saved copies of the primary sources (CVE records, GitHub advisories, reporter issues, vendor pages) that the summary
checker used. The author keeps these copies; they are not in the repository, for the reason given in `FRAME-NOTES.md`. Nothing
was fetched from the web. The stratified shares were computed with `analyze.share`, which gives the published primary values
again (R0 90.1%, model majority 92.6%).

**Per-case file:** `rq1-audit-cases.csv` (120 rows). Columns: labels (R0, each model's mode, majority), flag, summary-check
verdict, the triggering input recorded per finding, the mechanism, (a) the class-3 clause, (b) the source facts, (c) the flag
category.

## (a) R0 class-3 labels against the frozen class-3 definition

Under the frozen text, class 3 is "classic authentication, authorization or origin flaws in the services around the agent".
The decision rule then says that any case not needing the model to follow untrusted instructions "goes to the earliest step
that fails without any model decision", and lists class 3 as "the authentication and authorization of the services around the
agent". The rule has no fifth class and no "other" branch. A flaw outside the agent's startup machinery and the approval step
therefore goes to class 3, even when it is not an authentication, authorisation or origin flaw. Command injection, path
traversal and SSRF in a server, connector or SDK fall into this group when no model step is needed. The frozen rule treats
class 3 as the class for every remaining case. No deviation addresses this (`DEVIATIONS.md` has no ruling on the scope of class 3).

R0 put 100 of the 120 cases in class 3. For each case, the auditor recorded the clause it fits. For a bundle, this is the best
clause among its findings.

| Clause fitted | Cases |
|---|---|
| Authorisation (ownership, scope, permission, admin-only checks) | 21 |
| Authentication (missing or bypassed authentication, token/session binding, credential handling) | 15 |
| Origin (redirect, cross-origin forwarding, DNS rebinding, host-header checks) | 6 |
| **None of the three: class 3 only through the decision rule** | **58** |

The 58 cases that reach class 3 only through the decision rule:

| Mechanism | Cases |
|---|---|
| Unconfined file paths in tool arguments (path traversal) | 23 |
| Unrestricted request destinations (SSRF) | 12 |
| Attacker text reaching a shell command or process start (command injection) | 9 |
| Resource exhaustion or leak | 3 |
| SQL statement or filter/deny-list bypass | 3 |
| Vendor CWE-77 "command injection" with the mechanism not described (assistant records) | 3 |
| Isolation (cross-client state, container network) | 2 |
| Sandbox escape, template code generation, a bundle of filter bypasses | 1 each |

Of the 58: 45 are MCP servers or connectors, 10 agent clients and 3 SDKs. The model majority is 3 for 49 of them, 1 for 8,
and there is no majority for 1. 38 of the 58 are flagged. The 58 labels rest on reading the frozen decision rule as exhaustive (it offers no class beyond
1–4); the class-3 and step-3 wording (authentication, authorisation, origin) does not cover them, and no deviation rules on
this, so the labels are kept and flagged. The per-case violated property, a source paraphrase and the evidence reference are in
`rq1-class3-residual-map.csv` (built by `class3_residual.py`). Of the 58, 6 are `arguable_authorisation` (the source itself frames
the flaw as an access-control or permission bypass), 5 have a competing literal class 1 (all agent clients, of the 10), and for 4
the violated property is "not stated in the source". The per-case property was written by an AI coder (Claude) after all
results were known; it is exploratory. A second check (1 Nov 2026, `rq1-class3-second-check.csv`) was made by a model of
another provider (Codex, gpt-6.1-sol), blind to this map, from the same saved sources and the frozen wording only. The two
agree on all fields for 47 of the 58 cases. Both find an access or permission framing in the source for 4 cases (0006, 0124,
0279, 0292); one rater only for 3 more (0222, 0227, 0299). Both see class 1 as a competing reading for 3 agent clients (0096,
0130, 0131); one rater only for 2 more (0144, 0279), and the second rater also for 2 cases the frozen frame lists as services
(0016, 0039; scope follows the frame). For the 4 cases with no property stated, the second rater gives only a generic one
(confidentiality, privilege). Disagreements are recorded, not resolved by relabelling; no label changes.

*Exploratory variant (not a reinterpretation):* the share of the sample whose label matches a literal class clause (classes 1
and 2, plus class 3 only where the authentication, authorisation or origin clause fits) is 41.6% stratified (interval
28.8–55.2%; unweighted 50/120). It describes the composition of classes 1–3. It is not an estimate of class 4, because the 58
cases need no model step.

## (b) Residual ambiguity between classes 1–3 and class 4: source check

**Scope.** Cases that are ambiguous (flagged, or R0 and the majority differ, or there is no majority) **and** bear on the 1–3/4
boundary (some rater chose 4, or some finding's triggering input is not "direct attacker"). That gives **46 cases**. For each one,
the auditor read the saved primary sources and recorded two things. First, whether the sources attest who supplies the
triggering input. Second, whether model manipulation is required. Explicit source wording goes in `b_source_actor`. The
auditor's inference goes separately in `b_inference`.

| Source finding | Cases | R0 labels |
|---|---|---|
| Model manipulation required, stated explicitly | 5 | all 4 |
| A model-free route (direct caller, malicious server, authenticated upload) attested explicitly | 10 | all 3 |
| Rule interpretation: the attacker prompts the model directly, or "an attacker-controlled agent" is the actor | 3 | 2, 3, 4 |
| **Not established by the sources** | **28** | 22 × 3, 3 × 1, 3 × 4 |

Facts:
- Where the sources are explicit, R0 agrees with them in all 15 cases. In two of the five explicit class-4 cases, the model
  majority chose a class in 1–3: RQ1-0060 (majority 2) and RQ1-0325 (majority 3). Both sources say that the attack works only
  through the steered agent.
- In the 28 "not established" cases, the sources name only "a caller", "an MCP client", "user-controlled" input or "an
  (un)authorized attacker". Ten of the 28 are vendor records of one or two lines. None of these sources says whether a model
  step is needed.
- Eight are tool-argument path or SSRF cases with the same evidence pattern ("an MCP client / caller can …", no channel named):
  RQ1-0168, 0175, 0176, 0177, 0178, 0180, 0182 and 0193. R0 gave class 4 to two of them (0175, 0193) and class 3 to six. The frozen
  rule sets no default class when the triggering input is unknown, so both choices fit the text. The labels are inconsistent
  with each other, but neither breaks the rule.

Inference (not verified):
- In stdio deployments, the realistic caller of a tool is the agent host. A "direct MCP client" attacker there assumes local
  access, as the CVSS vectors (AV:L, PR:L) of several of these cases also suggest.

*Exploratory variants* (stratified, frame of 330, computed with `analyze.share`):

| Variant | R0 | Model majority |
|---|---|---|
| Primary (published) | 90.1% (77.9–95.8) | 92.6% (81.2–98.2) |
| The 28 "not established" cases as class 4 | 69.3% (55.2–79.7) | 71.0% (56.7–81.5) |
| The 28 cases plus the 3 rule-interpretation cases as class 4 | 67.7% (53.6–78.2) | 69.3% (55.2–79.4) |

Under these variants, the point estimates stay above 60% and the lower bounds fall below it. By the analysis plan's wording,
that is "supported on the point estimate only". The published contested-case variant (all 78 contested cases as class 4,
32.6%) remains the bound set in advance.

## (c) The 74 flagged cases

This part sorts each case by what its flag reason records (`c_flag_reason`), read against the frozen rule.

| Category | Cases | Of which summary corrected / verified |
|---|---|---|
| Resolved correction, or a remaining doubt that cannot change the class under the frozen rule (privileges, metrics, configuration, impact, a bundle finding that does not decide) | 39 | 35 / 4 |
| **Residual class-relevant uncertainty** | **32** | 15 / 17 |
| Bibliographic only (disclosure date, eligibility, source or reporter identity) | 3 | 0 / 3 |

The 32 residual cases break down as follows:
- **28** concern who supplies the triggering input, or whether a model step is needed (the 3/4 boundary).
- **2** are rule-interpretation cases where the attacker prompts the model directly (RQ1-0130, 0276), also on the 3/4 boundary.
- **1** is a class 2/4 case (RQ1-0119, "an attacker-controlled agent").
- **1** is a class 1/3 case (RQ1-0144, prerequisites for enabling the feature and placing the file).

The source check in (b) settles none of the 32. In four "resolved" cases, the source states explicitly that the case is
model-mediated (RQ1-0060, 0089, 0139, 0260). Two cases sorted as "resolved" by their flag reason (RQ1-0036, 0196) still have
an open trigger question at the source level (part b).

The manuscript's own split ("50 corrected, 24 uncertain, three of them date/identity") counts verdicts, not content. Of the 50
corrected summaries, 15 still carry a class-relevant doubt. Of the 24 verified ones, 4 carry only a doubt that does not
change the class.

## (d) Scope of the RQ1 claims

The sampled population is the D44 frame: advisory-database disclosures (GitHub Advisory Database, NVD, plus one timeline event)
first disclosed from 26 June to 24 September 2026. They concern tool-using AI agents and their connectors: 210 MCP servers or
connectors, 100 agent clients and 20 SDKs, out of 330. The recall of the D1 keyword query is unknown. Claims about RQ1 should
name this population and should say that "outside the model's decision" includes conventional flaws that are not specific to
agents (part a). The manuscript changes proposed for this are listed in the strengthening report. They are not applied here.

## Limits
- One AI auditor; no second human. Mechanism and category coding are judgements, recorded per case with reasons.
- Part (b) uses the saved source copies only. A source that changed later, or that was not saved, was not consulted.
- These are counts on the sample. The exploratory variants reuse the frozen estimator. They are not preregistered and support
  no confirmatory claim.
