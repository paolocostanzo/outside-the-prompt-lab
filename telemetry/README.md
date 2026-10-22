# Telemetry — Q4 (RQ5) lab, in preparation

What a defender can see, in default client logs and in standard host telemetry, of the events measured in parts 2 and 3. This
folder holds the collection side required by deviation D24; the event runs, the baseline and the detection rules come after D24 is
published.

| Path | What it is |
|---|---|
| `inventory/candidates.json` | Candidate default log locations per client (a superset; the inventory keeps what exists) |
| `inventory/inventory-20261017.json` | Inventory on the clean snapshot, 17 Oct 2026: files and bytes per candidate pattern (counts only; paths stay private because they name the lab account's connected services) |
| `inventory/sources.md` | Every default log source: format, retention, and how record times are read |
| `scripts/vm_logs.py` | Runs inside the disposable VM, read-only: `inventory` lists existing candidate files; `collect` archives them with a manifest (every frozen pattern with its match count, files with size, mtime, SHA-256, unreadable files, logging configuration, record time ranges where readable); SQLite databases travel with their `-wal`/`-shm` files and are also saved as consolidated copies opened from a private copy |
| `scripts/q4_events.py` | Host side: the 36 event runs of D24 point 3 (three event types × six clients × two), random order fixed by a seed and written to `plan.json` first; per run: clean snapshot, cell, client-log archive, ground-truth logs, host telemetry, collection check. `--dry-run` prints the plan only |
| `scripts/baseline_session.py` | Runs inside the VM: one baseline session of scripted normal use (`baseline/tasks.json`), answering command and edit questions "allow once" (`baseline/clients.json`, provisional until the set-up sessions); writes `timeline.jsonl` with every action's time; a session in which the lab server served anything but definition A is invalid |
| `scripts/q4_baseline.py` | Host side: development sessions for every client in a seeded order, then holdout sessions in the same order, each at least 6 h after the same client's development session; same export as the event runs |
| `scripts/score.py` | Scoring of detection rules (D6, D13, D24 point 5): detection between the ground-truth event time and the end of the run; one-minute holdout windows; false-positive windows with Wilson 95% intervals and alerts per hour; "tells apart" = every scored run detected and fewer than 5% of holdout windows (k/n < 0.05, D27 point 2) |
| `baseline/tasks.json`, `baseline/clients.json` | The fixed tasks, and the per-client "allow once" patterns (provisional) |
| `scripts/collection_check.py` | Host side: export ok/failed (manifest schema, every frozen pattern accounted for, candidates file hash, file hashes, unreadable files, databases readable), client logs wrote / wrote-nothing-in-session / no-default-logs, record coverage of the session window or "unknown" |
| `scripts/secret_gate.py` | Secret gate (D26): `fingerprints` runs inside the VM and records, for every lab secret, its length, first four characters and SHA-256, never the value; `scan` checks files, folders and archives by exact value and by known token formats; `scan-git` checks every blob, file name, commit message, annotated tag and ref name of a commit range before a push; `redact` writes copies with every match replaced by characters of the same length (archives rebuilt, every copy checked clean). Fails closed. The orchestrators run it on every run and session folder before anything else reads it: token-shaped data inside the private raw client-log archive is counted in `secret-marks.json`, everything else stops the campaign |
| `test/` | `python3 -m unittest discover -s telemetry/test` |

Safety boundary: read-only on the clients' stores; run only in a disposable VM.
