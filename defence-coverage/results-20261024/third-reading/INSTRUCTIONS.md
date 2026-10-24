# Third reading for the Q2 adjudication: proposed decisions

For each case of the assigned adjudication files, propose a decision for the author to check. Rules (preregistration D17 points 2–4):
- class: "A" if the tool returns free prose written by third parties (titles, descriptions, bodies, comments, messages, file
  contents, logs, commit messages); names and identifier-like strings, numbers, states, or the server's own text do not make it A;
  otherwise "not-A".
- protection (only for A): "full" if an output-side defence (sanitizing, escaping, fencing/marking as untrusted) applies to all the
  third-party prose the tool returns; "partial" if it applies to only some fields or some code paths; "none" if there is none. For
  not-A: "n-a".
- vendor_only: "true" if the only free prose is written by the server's vendor (documentation, curated advisories, official
  examples), "false" otherwise.
Base the proposal only on the two readings and the code cited in the case (the .md file shows it); if the cited code is not enough,
say so and propose the more conservative reading (the one with less protection), marking confidence "low".

Output: one JSON object per case, in a JSON list, written to the output file named in your task:
{"server": "...", "n": "<case number>", "class": "A|not-A", "protection": "full|partial|none|n-a", "vendor_only": "true|false",
 "confidence": "high|medium|low", "agree_with": "first|second|neither|both",
 "perche": "<2–3 short sentences IN ITALIAN, plain words, for a non-programmer: what the tool returns, and whether/where it is protected>",
 "riga": "<the one file:line that decides it, from the case>"}
