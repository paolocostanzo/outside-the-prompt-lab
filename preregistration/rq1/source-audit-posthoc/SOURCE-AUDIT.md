# RQ1 source audit — post hoc, exploratory (1 Nov 2026)

**Not preregistered, not an independent validation.** One AI coder (Claude, Opus 5.5), working alone, read the saved
primary sources of the 120 sampled cases and recorded, for each, whether the source documents an exploit chain that
needs the model to follow untrusted instructions. It is a second look at the same material by an AI system of the same
family as the models used elsewhere in the study; it can show where the sources are thin, not what the true share is.

## Method

- **Cases:** the 120 rows of `../rq1-sample.csv` with `sampled == yes`.
- **Material:** only the saved sources in `reports/a2-riassunti/sources/RQ1-xxxx/` (records, advisories, issues,
  bulletins; `index.json` maps URLs to files). No fallback to `../raw-20261025/` was needed: every case had a
  readable record. Text was extracted locally (record descriptions, advisory bodies, page text), duplicates across
  record copies removed, and the long advisories read in full where the first part did not settle the route.
- **Blinding:** the AI-written summaries, `rq1-r0.json`, model outputs, `../audit-posthoc/` and the flags were not
  opened until all 120 outcomes were written. The R0 file was opened only for the cross-tab below.
- **Outcomes:**
  - `A_no_model` — the source documents a sufficient chain with no model manipulation: attacker input reaches the
    flaw directly (network request, logged-in user, malicious server/client/file, local process, web page via DNS
    rebinding) or through a product step without the model following untrusted instructions.
  - `B_model` — the documented chain needs the model to follow untrusted instructions (prompt injection, poisoned
    content or memory the agent acts on, model-generated code or parameters driven by attacker text).
  - `C_undetermined` — the source does not allow a decision: one-line records; "an attacker can supply X" / "caller-
    controlled value" with no actor or route; or both a direct route and a prompt-injection route asserted without
    saying which is sufficient. C was used freely.
- **Decision rules adopted while coding (written down for reuse):**
  1. A user of the product acting through their own requests (including through the chat) against a missing
     authorization check is A: the model follows a principal, not third-party text (e.g. RQ1-0015, RQ1-0152).
  2. A direct write that only harms through the agent later acting on it (memory, vector store) is B (RQ1-0023,
     RQ1-0325).
  3. Cases where the agent itself performs the harmful action and the source does not say what leads it there are
     C (RQ1-0080, RQ1-0119).
  4. **Tool-caller A (generous):** when a report frames the attacker as the direct MCP caller ("an attacker who can
     invoke the tool", "a malicious MCP client", "an MCP caller can…") and mentions no model step, the case is A with
     `a_basis = tool_caller` (19 cases, mostly local stdio servers). This is the weakest A basis; a sensitivity line
     moves them to C. Reports that only say the value is "attacker-controlled" without naming the caller are C.
- **Per case:** outcome, evidence reference (folder/basename + SHA-256 prefix, 12 hex), one-line reason
  (`source-audit.csv`, public, no names/URLs). The decisive verbatim excerpt (≤ 30 words, checked mechanically against
  the source file) is only in `source-audit-PRIVATE.csv` — **lab-side only, may contain names, never publish** (listed
  in this folder's `.gitignore`).
- **Shares:** `../estimate.py` imported unmodified (`stratified_share`), stratum = product type, weights and bounds from
  the frame stratum sizes in `../rq1-sample-manifest.json` (agent client 100, MCP server or connector 210, SDK 20).
  `source_audit_summary.py` recomputes everything from `source-audit.csv` (`--r0` adds the cross-tab).

## Counts

| Stratum | M | n | A | B | C |
|---|---|---|---|---|---|
| agent client | 100 | 37 | 20 | 6 | 11 |
| MCP server or connector | 210 | 76 | 50 | 6 | 20 |
| SDK | 20 | 7 | 7 | 0 | 0 |
| **total** | 330 | 120 | **77** | **12** | **31** |

A basis: 58 direct, 19 tool_caller.

## Cross-tab with R0 (classes 1–3 vs class 4)

| Source audit \ R0 | 1–3 | 4 | total |
|---|---|---|---|
| A_no_model | 77 | 0 | 77 |
| B_model | 3 | 9 | 12 |
| C_undetermined | 28 | 3 | 31 |
| total | 108 | 12 | 120 |

- Every A case is R0 1–3. Agreement on the 89 decided cases: 86/89 (A↔1–3, B↔4).
- B but R0 1–3: RQ1-0023, RQ1-0130, RQ1-0285 (prompt-injection or memory-poisoning chains; R0 put the flaw in the
  non-model class, which is consistent with a taxonomy of *where the flaw sits* rather than *how it is reached*).
- C but R0 4: RQ1-0175, RQ1-0193, RQ1-0296.
- C cases are 28 R0 1–3 and 3 R0 4: the R0 1–3 share rests partly on cases whose sources do not document the route.

## Shares of A (stratified, 95% conservative intervals from estimate.py)

| Variant | Share | 95% interval |
|---|---|---|
| A among decided cases (A / A+B) | 86.2% | 70.0% – 94.5% |
| C counted against (C and B outside A) | 64.3% | 49.7% – 75.2% |
| C counted both ways (estimate.py convention for unlabelled) | 64.3% | 49.7% – 95.8% |
| Sensitivity: tool_caller A → C, decided only | 82.7% | 62.7% – 93.6% |
| Sensitivity: tool_caller A → C, C against | 48.4% | 34.5% – 60.3% |

Caveat for the "decided only" rows: estimate.py treats the decided cases as a random draw from each stratum; they are
not (C is not random), so that interval is descriptive only.

## B cases (12)

RQ1-0023, RQ1-0060, RQ1-0088, RQ1-0089, RQ1-0108, RQ1-0130, RQ1-0139, RQ1-0217, RQ1-0260, RQ1-0276, RQ1-0285,
RQ1-0325.

## C cases (31)

- One-line records, no chain detail (12): RQ1-0025, 0077, 0218, 0277, 0296, 0297, 0311, 0312, 0313, 0314, 0326; also
  RQ1-0292 (attacker content reaches the server through a user's interaction, relay not stated).
- Both a direct and a prompt-injection route asserted (7): RQ1-0039, 0066, 0074, 0163, 0255, 0258, 0299.
- Attacker-controlled / caller-controlled input with no actor or route (10): RQ1-0016, 0109, 0122, 0148, 0175, 0187,
  0193, 0196, 0201, 0208.
- Agent performs the harmful action, trigger not stated (2): RQ1-0080, 0119.

Reasons per case are in `source-audit.csv`.

## Frame side

See `frame-check.md`: no sampled pair found to be the same flaw; one conditional doubt on the counting unit (RQ1-0215 groups two
products from one bulletin; D41 point 1 permits cross-product bundles, so this is a concern only under a per-product unit), one pair worth checking for a shared root cause / incomplete fix (RQ1-0143 / RQ1-0302, with RQ1-0096), and
four eligibility suspicions (RQ1-0005, 0027, 0300, 0025).

## Files

- `source-audit.csv` — public: case_id, outcome, a_basis, evidence_ref, reason.
- `source-audit-PRIVATE.csv` — lab-side only: adds the verbatim excerpt.
- `frame-check.md` — duplicate/grouping and eligibility suspicions.
- `source_audit_summary.py` — recomputes counts, shares and (with `--r0`) the cross-tab.
