# Telemetry — Q4 (RQ5) lab, in preparation

What a defender can see, in default client logs and in standard host telemetry, of the events measured in parts 2 and 3. This
folder holds the collection side required by deviation D24; the event runs, the baseline and the detection rules come after D24 is
published.

| Path | What it is |
|---|---|
| `inventory/candidates.json` | Candidate default log locations per client (a superset; the inventory keeps what exists) |
| `inventory/inventory-20261017.json` | Inventory on the clean snapshot, 17 Oct 2026: files and bytes per candidate pattern (counts only; paths stay private because they name the lab account's connected services) |
| `scripts/vm_logs.py` | Runs inside the disposable VM: `inventory` lists existing candidate files; `collect` archives them with a manifest (size, mtime, SHA-256) |
| `scripts/collection_check.py` | Host side: per session, export ok/failed and whether the client wrote, wrote nothing in the session, or has no default logs. Independent of detection: ground truth comes from the lab server's or the canary's log |
| `test/` | `python3 -m unittest discover -s telemetry/test` |

Safety boundary: read-only on the clients' stores; run only in a disposable VM.
