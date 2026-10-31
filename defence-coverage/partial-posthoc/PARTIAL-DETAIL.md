# RQ4: what "partial" means, tool by tool (post hoc, exploratory)

**Status.** This is a post hoc, exploratory analysis, written on 31 October 2026, after the census figures of RQ4 were published.
It does not change the census. `results-20261024/final-census.csv`, `adjudication.csv`, the readings and `COVERAGE.md` are unchanged
and remain the reported result. Any reclassification it suggests is kept in a separate, versioned file
(`RECLASSIFICATION-SUGGESTIONS-v1.md`) for the author to decide. **Coverage is not effectiveness:** nothing here measures whether a defence
resists an attack. It only records which returned text passes through which mechanism.

**Scope.** The six published servers only, at the census's pinned commits:
microsoft/azure-devops-mcp `ea8a7f6b378881c07525ab58cecec69dc13fdb46`; github/github-mcp-server `eb47a99ddb866ca2b8a162920e6bda9521f33ebb`;
getsentry/sentry-mcp `1d53ad86e8a47a1d31004fcb8bbd110a8311abbb`; awslabs/mcp `089b6b8a9ea25a369c92e308af96da71ef6a3a57`
(aws-iac, mssql, oracle). All 60 tools coded `partial` are covered, plus 7 contrast tools: 4 `full` and 3 `none`.

**Sources.** The census clones at the pinned commits. `git rev-parse HEAD` gives the pinned commit in each case. Nothing was cloned or fetched for
this analysis. File:line references are relative to each repository root; GitHub paths are under `pkg/`, Sentry paths under
`packages/mcp-core/src/`. The `evidence_basis` column of `PARTIAL-DETAIL.csv` says, for each row, whether the cited lines were read
again for this analysis ("verified here"), or are taken from reading 2 and checked on a sample ("reading 2, spot-checked"). Every
census `partial` appears exactly once in the CSV, and the script asserts this. Recomputing the census aggregates from
`final-census.csv` reproduces `COVERAGE.md` exactly (34.6/87.8 mean, 10.7/94.4 median, 53/138 and 113/138 pooled).

## Four mechanisms, kept distinct

Each row of the CSV has a column for each of the four mechanisms that D23 counts or mentions:
- **delimitation**: the text is enclosed between markers. A *random* nonce boundary (Azure, AWS DB) is recorded differently from a
  *fixed* tag (AWS IaC) and from a *bare* Markdown code fence or JSON quoting (Sentry). D23 counts delimiters only when they come with an
  instruction to treat the enclosed text as untrusted.
- **untrusted-data instruction**: in-band text telling the model not to follow the enclosed content.
- **provenance**: a marker of origin or trust. This can be in-band (Sentry `<seer_analysis>` tags), or out of band in the result's `_meta`
  (GitHub IFC labels, opt-in).
- **sanitisation (character hygiene)**: removal or neutralisation of characters. Invisible-Unicode and HTML filtering (GitHub
  `sanitize`, AWS IaC) is recorded separately from whitespace collapse (Sentry `\s+` to a space; CR/LF removal), which does not remove
  zero-width or tag characters.

## Results per server

### Azure DevOps (1 partial of 34)
`wit_work_item_attachment`: text attachments (`text/*`) are wrapped with a random-nonce delimiter plus an untrusted-content
instruction (`src/tools/work-items.ts:557`; `src/shared/content-safety.ts:21-36`). Every other MIME type is returned as a base64
`resource.blob` (work-items.ts:560-572). This includes `application/json`, `image/svg+xml`, `application/pdf` and files with an unknown
extension or no name (`getMimeType`, :1400-1424). The central wrapper only rewrites `text` blocks and `resource.text`
(content-safety.ts:50-58), so the blob stays outside it. Whoever can attach a file to the work item controls that content. Whether a
client decodes the blob and shows it to the model was not tested. For contrast, every other Azure tool goes through the central wrapper
(`src/tools.ts:61`), including error text.

### GitHub (41 partial of 60)
The server has two mechanisms, and they are independent:
1. **Character hygiene** (`pkg/sanitize/sanitize.go:22-51`: invisible characters, code-fence metadata, HTML policy), applied *per
   field* in the converters (for example `minimal_types.go:817-818, 928-929, 1087-1088, 1797`). There is no delimiter and no untrusted-data
   instruction. Visible text is returned unchanged.
2. **IFC provenance label** in the result's `_meta` (`ifc_labels.go:13-18`). It is attached only when the opt-in feature flag `ifc_labels` is on,
   and only to successful results (`ifc_labels.go:20-22`). The flag is in the user-allowed list but not among the insiders defaults
   (`feature_flags.go:46-66`). The label carries integrity (`trusted`/`untrusted`) and confidentiality. Its value depends on the
   tool, and for several tools on repository visibility: private-repository content is labelled `trusted`
   (`pkg/ifc/ifc.go:93-108, 135-152`).

The 41 partial tools fall into two groups:
- **T1, field-subset hygiene (17 tools)**: some prose fields are sanitised and others are not. Examples of text left out, all
  third-party writable: the raw PR diff (`pull_request_read`, `pullrequests.go:279`), file patches (`get_commit`, `minimal_types.go:1901`),
  fork repository descriptions (`list_pull_requests`, :1165), and workflow-run display titles (`actions_*`, :2072). In the sub-issue,
  issue-search, issue-field and project tools, the text left out (label/milestone descriptions, field values, project descriptions) is
  writable by repository writers, triagers or project members rather than by arbitrary outsiders. In `issue_dependency_write`, no
  third-party prose outside the defence was observed: titles go through `newMinimalIssueRef` (`minimal_types.go:646-649`) by way of
  `issue_dependencies.go:410-423`.
- **T2, provenance label only (24 tools)**: no field is sanitised, so the label is the only mechanism. In the default configuration (flag
  off), no defence applies to any text these tools return. In 18 of them the label says `untrusted`, at least for public repositories. Examples:
  file contents, job logs, gists, code search, security alerts, advisories. In 6 of them (`get_label`, `list_label`, `get_tag`,
  `list_issue_fields`, `list_issue_types`, `get_teams`) the label is always integrity `trusted` (`LabelRepoMetadata`, `ifc.go:154-172`;
  `LabelTeam`, :361-371). So the only mechanism does not mark that prose as untrusted data. That is the vendor's stated
  threat model: these objects need write access to create.

### Sentry (16 partial of 33)
The only mechanism that the code itself describes as an untrusted-data boundary is the `<seer_analysis>` provenance tag around
Seer (LLM-generated) analysis (`internal/tool-helpers/seer.ts:105-122`; `internal/formatting.ts:1958-1961`). The tag carries no in-band
instruction. The other partial labels rest on formatting:
- **T4, section-level provenance (2)**: `analyze_issue_with_seer` and `get_issue_details`. Seer sections are tagged. Left untagged:
  "Processing: <todo>" and retry error text (`analyze-issue-with-seer.ts:236-238, 275`); issue title, culprit and event body, and fallback Seer
  summaries (`get-issue-details.ts:247-252, 280-285`; `formatting.ts:1964-1971`). Event titles and messages come from the
  instrumented application and can carry end-user input. This is a general property of error reporting and was not tested here.
- **T5, inherited (2)**: `execute_sentry_tool` and `get_sentry_resource` return the target handler's output unchanged
  (`tools/special/execute-tool.ts:60-65, 138`). They therefore inherit the Seer tags of some targets, and the gaps of all of them.
- **T1-whitespace (6)**: `search_errors`, `search_events`, `search_issue_events`, `search_logs`, `search_traces`, `get_snapshot_image`.
  Whitespace is collapsed in field values (`tools/support/search-events/utils.ts:448-450, 552-564`; `snapshots/formatting.ts:157-160`).
  Headings built from titles or span descriptions, image descriptions and generated explanations are not collapsed.
- **T6, bare delimiters (6)**: `get_event_attachment` (text in a plain fence, binary non-image attachments as blobs;
  `get-event-attachment.ts:176-182, 212-216`), `get_event_stacktrace`, `get_span_details`, `get_trace_details` (JSON fences; span
  description outside, `get-trace-details.ts:900`), `get_uptime_monitor_details`, and `get_replay_details` (JSON.stringify quoting,
  `get-replay-details.ts:603-605`). None of these fences or quotes comes with an untrusted-data instruction.

### AWS IaC (0 partial of 9), SQL Server (1 of 1), Oracle (1 of 1)
The census figures are those agreed with AWS and are not discussed further here. In both `run_query` tools, the successful result is
wrapped in a random boundary with an untrusted-data instruction (mssql `server.py:111-124`, oracle `server.py:90-103`). The generic
exception branch returns the exception text unwrapped (mssql :203-207, oracle :214-218). Whether that text can contain stored data
was not tested ("not verifiable" from the code alone).

## Aggregates (after the per-server results; descriptive)

Of the 60 partial tools, by the mechanism that applies to the covered part:

| Mechanism on the covered part | Tools | Servers |
|---|---|---|
| random delimiter + untrusted-data instruction (another branch outside) | 3 | Azure 1, SQL Server 1, Oracle 1 |
| character hygiene on a subset of fields | 17 | GitHub |
| provenance label only (opt-in `_meta`, success only) | 24 (6 labelled `trusted`) | GitHub |
| in-band provenance tag on one section, or inherited | 4 | Sentry |
| whitespace collapse on a subset of fields | 6 | Sentry |
| bare fence or quoting only | 6 | Sentry |

Who can write the text left outside (column `third_party_controllable`): arbitrary third parties, or "likely", in 29 tools; mixed in 4;
only repository writers, administrators or project members in 19; vendor-curated in 2; indirectly (model output) in 2; unclear in 3;
none observed in 1. The categories rest on the code and on how the platforms work. None was tested.

## Limits
- The analysis reads the code statically. It ran no server and no client, so whether `_meta` labels or resource blobs reach the model is
  "not verifiable" here.
- For about a third of the rows the file:line evidence comes from reading 2 with spot checks, not from a full re-read. The CSV marks which.
- The classification of who can write each field (third party or writer) uses general knowledge of the platforms where the code does
  not settle it. Those rows say "likely", "unclear" or "general property, not tested".
