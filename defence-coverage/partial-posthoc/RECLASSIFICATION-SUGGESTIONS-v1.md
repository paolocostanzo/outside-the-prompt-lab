# RQ4 reclassification suggestions, v1 (31 Oct 2026; post hoc, exploratory; NOT applied)

These are suggestions only, for the author to decide. The census (`results-20261024/`) is unchanged. If any suggestion is adopted, it
needs a new deviation entry and a new derived file, and the original tables and their SHA-256 stay as they are. The AWS servers are
not touched: their figures stay as agreed with AWS. All figures below are recomputed from `final-census.csv` with only the listed rows
changed. The census baseline reproduces `COVERAGE.md` exactly.

## A. GitHub: the only mechanism is a label that says "trusted" (partial -> none), 6 tools
`get_label`, `list_label`, `get_tag`, `list_issue_fields`, `list_issue_types`, `get_teams`.
**Reason.** None of the returned text is sanitised. The only mechanism is the opt-in IFC `_meta` label, and for these tools it always
carries integrity `trusted` (`pkg/ifc/ifc.go:154-172` `LabelRepoMetadata`; `:361-371` `LabelTeam`; used at `labels.go:121,231`,
`repositories.go:2076`, `issue_fields.go:161,163`, `issues.go:1367,1395`, `context_tools.go:289`). D23 counts provenance marking
that marks content as data the model should not follow. A label stating that the content is trusted does not do that. The third
reading treated "an optional IFC label exists" as partial without looking at the label's value.
**Counter-argument (record it).** The vendor's model treats this text as written by trusted writers. The census's class rule (D17 point
2) still counts it as third-party prose.

## B. GitHub: issue_dependency_write (partial -> full), 1 tool
**Reason.** The third reading proposed partial with *low* confidence, because `issueToLegacyDependencyRef` was "not shown". At the
pinned commit it calls `issueToDependencyRef` and then `newMinimalIssueRef`, which applies `sanitize.PlainText` to the title
(`issue_dependencies.go:410-423, 193-203`; `minimal_types.go:646-649`). The only text left outside is the GitHub API error body
(`errors/error.go:283`), which other tools coded `full` also leave outside (e.g. `list_releases`). The change would make it consistent
with `issue_dependency_read` (full).

## C. Sentry: delimiters without an untrusted-data instruction (sensitivity under a strict reading of D23)
D23 was fixed on 17 October, before the D38 adjudication. Its rule: "delimiters that present the content as instructions to follow do
not count", and a delimitation counts only "together with an instruction to treat the delimited text as untrusted data". The third
reading's instructions (`third-reading/INSTRUCTIONS.md`) list D17 points 2-4 only, and they count "fencing" as a defence. Two
readings of the rule are possible:
- **C1 (fence or quoting only -> none), 6 tools:** `get_event_attachment`, `get_event_stacktrace`, `get_replay_details`,
  `get_span_details`, `get_trace_details`, `get_uptime_monitor_details`.
- **C2 (whitespace collapse not counted as character hygiene), 7 tools:** `get_snapshot_image`, `search_errors`, `search_events`,
  `search_issue_events`, `search_logs`, `search_traces` (partial -> none) and `get_issue_breadcrumbs` (full -> none). `\s+` and CR/LF
  collapse does not remove zero-width or tag characters (`search-events/utils.ts:448-450`; `tool-helpers/breadcrumbs.ts:98-102`).
The reading of the rule (D23 or the third-reading instruction) is the author's call. Note one inconsistency either way: `get_doc` and
`search_docs` (horizontal-rule and blockquote delimiters) were adjudicated `none`, while fenced tools were adjudicated `partial`.

## Effect (all tools; in brackets without vendor-only)

| Variant | GitHub F/P/N | Sentry F/P/N | Mean over servers, full / full+partial | Pooled full / full+partial |
|---|---|---|---|---|
| Census (unchanged) | 11/41/8 | 1/16/16 | 34.6% / 87.8% (33.2 / 86.8) | 53/138, 113/138 (49/130, 107/130) |
| A+B | 12/34/14 | 1/16/16 | 34.8% / 86.2% (33.5 / 85.1) | 54/138, 107/138 (50/130, 101/130) |
| A+B+C1 | 12/34/14 | 1/10/22 | 34.8% / 83.1% (33.5 / 81.9) | 54/138, 101/138 (50/130, 95/130) |
| A+B+C1+C2 | 12/34/14 | 0/4/29 | 34.3% / 79.6% (33.0 / 78.1) | 53/138, 94/138 (49/130, 88/130) |

Per server, full+partial: GitHub 86.7% -> 76.7% (A+B); Sentry 51.5% -> 33.3% (C1) -> 12.1% (C2). Medians over servers stay at
94.4% for full+partial in every variant. Azure DevOps, AWS IaC, SQL Server and Oracle are unchanged.
