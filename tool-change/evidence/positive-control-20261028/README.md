# RQ3 positive control (D52, exploratory), 28 October 2026

D12 point 5 preregistered a positive control per client before the primary matrix; it was not run then (D50 point 2). D52
(`preregistration/DEVIATIONS.md`, design committed in 24163a8 before any cell) runs it afterwards, to check that the harness and
the coder capture and code a question when a client asks one after a change.

- Change: the tool is renamed (`q3_noop` → `q3_noop_renamed`, same description and schema), a tool the user never approved;
  signal `notifications/tools/list_changed`; phases 1–3 of D16 (call; change; call; reopen and call); the frozen prompt.
- Clients (snapshot `q4-base-20261023b`, the versions of the primary matrix): Gemini CLI 0.64.0 (first, alone, as the cost pilot),
  then Codex CLI 0.162.1, Goose 1.54.0, Qwen Code 0.25.1, Claude Code 2.1.300 in the order drawn from seed 20261028
  (`plan.json`). Cursor CLI excluded (no plan available). One cell each.
- Run by `scripts/q3_positive_host.py` with `scripts/q3-clients-positive.json` (the frozen `q3-clients.json` with Gemini's
  approval pattern widened to the renamed tool; the frozen pattern ends with `"q3_noop"` and would not match the new name) and
  the runner `run_q3_cell.py` as amended by D19 (609c880), which in the primary matrix ran 1 of the 60 cells (the other 59 used
  the D18 version). Server, flip script, coder and client versions are those of the primary matrix. Host events in
  `host-log.jsonl`; each cell's `harness-sha256.txt` records the exact files. The secret gate of D26 ran after every cell (rc 0 in
  `host-log.jsonl`); this folder, as published, was scanned again with the resulting fingerprints: `secret-gate.json` lists
  every file's SHA-256 and the result. Host telemetry (audit log, journal) stays in the private evidence.
- Launches: two launches (10:07 and 10:55 UTC) did not start, because the snapshot revert failed (libvirt could not load the
  VM's AppArmor profile, attributed to host memory fragmentation); no cell ran. After a host restart (11:02 UTC) the third launch
  ran all five cells. All three are in `host-log.jsonl`.
- Coded by `scripts/code_q3.py` → `coded.csv`.

| Client | Phase 2 (same session) | Phase 3 (after reopening) |
|---|---|---|
| Gemini CLI | notice "Tools updated for server: q3-lab", then asked for approval of `q3_noop_renamed` | asked again (session approvals end at restart, as in the primary) |
| Codex CLI | called the old name (unknown tool), no new list fetched | fetched B, asked for approval of `q3_noop_renamed` |
| Claude Code | fetched B 3 ms after the signal, called `q3_noop_renamed` without a question | the same; the model's reply mentions the substitution |
| Qwen Code | received the signal, called the old name at least three times (unknown; still working when the phase closed) | fetched B, called it without a question |
| Goose | signal not deliverable (no subscription); called the old name, got "Unknown tool", the model still replied "ok" | fetched B, called it without a question |

In `coded.csv` a question for the new name is coded `re-approval-required` (the coder's category; here it is the first approval
of a new name), and phase 2 of Codex CLI, Qwen Code and Goose is coded 6 (`error-no-call-timeout`): no successful call, because
the call went to the removed name and failed; there was no timeout.

Expected (D52 point 6, written before the cells): Codex CLI and Gemini CLI ask; Claude Code, Qwen Code and Goose, in their
default modes, do not. Both held in these cells: no approval question for this benign rename in the tested configurations. Those
modes can still ask in other conditions (D19 records Qwen Code asking when its classifier was unavailable). What this shows is limited: the question of Codex CLI (frozen pattern) and of
Gemini CLI (widened pattern) were captured and coded after a change; the patterns of Claude Code, Qwen Code and Cursor CLI were
not exercised after a change, and Goose has none. A rename tests the approval of a new name, not a second approval of a changed
definition. Limits: one cell per client, a later snapshot with the same versions but different credentials (D26, D35), no
Cursor CLI.
Cost: a few requests to the Gemini key's flash model (Gemini CLI, Qwen Code, Goose), well under one dollar.
