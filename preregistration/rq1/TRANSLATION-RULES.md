# Italian translation of the RQ1 summaries and criteria (D46) — rules, written before any translation

1. Translate the English summary sentence by sentence into plain Italian. Same meaning, same order, same level of detail.
2. Keep every precondition, every condition word ("only", "if", "unless", "before", "after", "without") and the statement of who
   supplies the triggering input exactly as strong as in English; never add, drop, soften or strengthen a condition.
3. Do not explain, interpret or add context. Keep technical terms that Italian security people use in English (e.g. MCP, server,
   token, endpoint, path traversal, SSRF, shell, prompt, repository, tool) when an Italian word would be less precise.
4. Neutral words: none of the class words of §3 nor their Italian equivalents — not "approvazione/approvare" (use "autorizzare",
   "confermare" or "consentire" only if the English has "authorize", "confirm" or "permit"; otherwise keep the English verb's
   meaning with a neutral word), "iniezione", "autorità", "classe", "plumbing", "prima della fiducia". No product, vendor or
   project names, ids, dates or scores (the English has none).
5. The criteria text is translated in the same way; the class names stay in English next to the Italian
   ("1. Before trust (prima della decisione di fiducia)") because they are the names the models see.
6. Output keeps the case id; nothing else changes.
7. (added before any translation was checked) In the criteria the word "classe" is unavoidable, since the criteria define the
   classes; rule 4's ban applies to the summaries. "Approve" in the criteria ("asked to approve") is rendered "confermare" to keep
   the summaries' vocabulary neutral; the English criteria stay the reference.
