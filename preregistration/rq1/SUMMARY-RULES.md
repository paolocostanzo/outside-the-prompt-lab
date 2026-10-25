# RQ1 case summaries — rules (written before any summary, 25 Oct 2026)

From §3 of the preregistration, D4(a), D14 point 3, D41 points 1–2 and D42. The summary is the only input of the model raters
and the main input of R0 (who also has the source link). It must let a reader decide where the first failure sits without
telling them.

1. **Source.** Written from the case's primary source (the earliest public advisory or write-up in `rq1-frame.csv` /
   `disclosure-dates.csv`), opened for this purpose; for a multi-record case, from every record's advisory. Every finding of the case must be covered by a reachable primary source:
   the repository advisory, the global GitHub advisory, the CVE record or the researcher write-up of that finding are equivalent
   for this purpose; coverage is recorded per finding. If any finding cannot be covered, no summary is written and the whole
   case is recorded as non-response (null in `rq1-r0.json`, D44 points 5–6); a subset of findings is never summarised.
2. **Content.** What the component is, in generic terms (e.g. "an MCP server that exposes a database to an agent", "a
   command-line coding agent"); what the flaw lets someone do; and **every precondition of exploitation** stated in the source
   (D14 point 3): configuration, version range only if it changes the conditions, network exposure, credentials or roles needed,
   user actions needed, what the agent or model must do.
3. **Who supplies the triggering input** (D41 point 2), always stated: an attacker who reaches the tool, endpoint or file directly;
   or content the model reads (a web page, a file, an issue, a tool result) that leads the model to call the tool or act; or both
   when the source says both are possible. Never inferred beyond the source; if the source does not say, write "the source does
   not say who supplies the input".
4. **Bundles** (D41 point 1): when the case has several findings, list each with its own preconditions and its own triggering
   input.
5. **Neutral words.** None of the class words of §3 ("before trust", "approval", "injection", "authority", "plumbing", "class";
   `classify.py` rejects them): paraphrase, e.g. "attacker-controlled text reaches a shell command" instead of "command injection",
   "instructions planted in content the agent reads" instead of "prompt injection". No product, vendor or project names, no CVE or
   GHSA ids, no dates, no severity scores, no vendor judgement of severity, no taxonomy terms of the study.
6. **No exploit detail.** No payloads, commands, request bodies or step-by-step procedures; describe the mechanism in one or two
   sentences.
7. **Length.** 50–150 words, plain English, present tense, no lists except for bundles.
8. **Record kept apart from the summary** (never shown to raters): case id, source URLs opened, the preconditions as a list, the
   triggering input as one of "direct attacker", "content the model reads", "both", "not stated", and any doubt.
9. **Check.** Codex (D42 point 2) checks every summary against its source for completeness of preconditions, correct triggering
   input, neutrality and the absence of names and class words, before R0 sees any summary. Every case gets one row in
   `summary-checks.csv`: case id, verdict (ok / corrected), corrections made (old and new text), a **pre-label flag** (yes/no)
   with its reason, and the final disposition. A case is flagged when, after the check, a precondition or the triggering input
   remains uncertain in the source, or the writer and the checker disagree on them. A flag is never removed by a later
   correction. Flagged case ids are written to `rq1-flags.json`, committed with the summaries before R0 starts; the analysis
   treats them as contested cases (D41 point 4) in the sensitivity analyses of D41 point 6.

## Clarification (25 Oct 2026, after the first drafts and before any check or label)
The first drafts showed two readings of rule 1. To make every summary use the same sources:
- **Source set of a case**: every advisory of its records (repository advisory, global GitHub advisory, CVE record, vendor
  bulletin) and every write-up by the reporter that an advisory links to (blog post, report, gist, document, or an issue opened
  by the reporter to describe the flaw). Other issues, pull requests and third-party pages are not used. The date of the case
  is unchanged (frame, D14 point 2): this concerns only what the summary may draw on.
- **Record metrics** (e.g. CVSS "privileges required", "user interaction", "attack vector") are part of the advisory and may be
  stated as preconditions, phrased as such ("the record lists user interaction as required"); severity scores stay out.
- All 120 drafts are revised under this clarification before the Codex check; the record of each case lists every source opened.
