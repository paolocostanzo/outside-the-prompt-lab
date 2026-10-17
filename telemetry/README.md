# Telemetry — Q4 (RQ5) lab, in preparation

What a defender can see, in default client logs and in standard host telemetry, of the events measured in parts 2 and 3. This
folder holds the collection side required by deviation D24; the event runs, the baseline and the detection rules come after D24 is
published.

| Path | What it is |
|---|---|
| `inventory/candidates.json` | Candidate default log locations per client (a superset; the inventory keeps what exists) |
| `inventory/inventory-20261017.json` | Inventory on the clean snapshot, 17 Oct 2026: files and bytes per candidate pattern (counts only; paths stay private because they name the lab account's connected services) |
| `scripts/vm_logs.py` | Runs inside the disposable VM: `inventory` lists existing candidate files; `collect` archives them with a manifest (size, mtime, SHA-256) |
| `scripts/q4_events.py` | Host side: the 36 event runs of D24 point 3 (three event types × six clients × two), random order fixed by a seed and written to `plan.json` first; per run: clean snapshot, cell, client-log archive, ground-truth logs, host telemetry, collection check. `--dry-run` prints the plan only |
| `scripts/baseline_session.py` | Runs inside the VM: one baseline session of scripted normal use (`baseline/tasks.json`), answering command and edit questions "allow once" (`baseline/clients.json`, provisional until the set-up sessions); writes `timeline.jsonl` with every action's time; a session in which the lab server served anything but definition A is invalid |
| `scripts/q4_baseline.py` | Host side: development sessions for every client in a seeded order, then holdout sessions in the same order, each at least 6 h after the same client's development session; same export as the event runs |
| `scripts/score.py` | Scoring of detection rules (D6, D13, D24 point 5): detection between the ground-truth event time and the end of the run; one-minute holdout windows; false-positive windows with Wilson 95% intervals and alerts per hour; "tells apart" = every scored run detected and ≤ 5% of holdout windows |
| `baseline/tasks.json`, `baseline/clients.json` | The fixed tasks, and the per-client "allow once" patterns (provisional) |
| `scripts/collection_check.py` | Host side: per session, export ok/failed and whether the client wrote, wrote nothing in the session, or has no default logs. Independent of detection: ground truth comes from the lab server's or the canary's log |
| `test/` | `python3 -m unittest discover -s telemetry/test` |

Safety boundary: read-only on the clients' stores; run only in a disposable VM.
