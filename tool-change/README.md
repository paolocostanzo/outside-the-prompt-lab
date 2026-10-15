# Tool change — MCP lab (Q3)

Companion laboratory for part 3 of *Outside the Prompt* (20 October 2026), preregistered research question RQ3.

The question: **after a user approves an MCP tool, the server changes the tool's definition. Does the client notice — does it tell
the user, ask for approval again, accept the change silently, or refuse the server?** The lab runs one harmless server whose single
no-op tool switches from definition A to definition B on a local control file, and records, message by message, what the client
asked for and what it was served.

**Status (15 October 2026): components written and tested; no client measured yet.** The procedure follows the frozen protocol as
amended by deviations D5, D12 and D16 (`../preregistration/DEVIATIONS.md`), all written before any RQ3 data.

## Safety boundary

- The server (`server/q3-server.mjs`) exposes one tool, `q3_noop`, that returns the word `ok` and appends one line to the server's
  own log. Definitions A and B describe that same behaviour in different words; neither contains instructions to the model, URLs,
  paths, data access or network access (test 15). The schema change adds one optional field that is ignored; the name change renames
  the tool. The server opens no network connection and writes no file other than its log (test 14).
- No third-party server, account or data is involved.
- `prepare_vm.py` and `run_q3_cell.py` edit the clients' MCP configuration and approvals in `$HOME`; `q3_host.py` restores and
  destroys a virtual machine. **Run them only in a disposable VM.**

## Contents

| Path | What it is |
|---|---|
| `server/q3-server.mjs` | Dual-era MCP server (stdio): modern 2026-07-28 and legacy (`initialize`) behaviour, logs every message in and out |
| `scripts/flip.mjs` | Writes the control file atomically (state A/B, signal level, kind of change) and logs each change |
| `scripts/prepare_vm.py` | Adds `q3-lab` to each client's user-level MCP configuration (with backups) and creates the test folder |
| `scripts/run_q3_cell.py` | Runs one repetition for one terminal client in tmux: call with A, change to B, call again, reopen, call again |
| `scripts/q3-clients.json` | Per-client screen patterns and keys, fixed in the set-up runs and frozen before the primary runs |
| `scripts/code_q3.py` | Rule-based provisional coder: outcome per phase from the server log and the runner's observations |
| `scripts/q3_host.py` | Host-side orchestration: clean snapshot per repetition, randomised blocked order, raw telemetry export |
| `test/` | `node:test` suite (server, coder with the real server, configuration writer, run plan) |

## How the server behaves

- **Modern (2026-07-28)**: any request carrying `_meta["io.modelcontextprotocol/protocolVersion"]` is served statelessly.
  `server/discover` returns the supported version, capabilities (`tools.listChanged: true`) and server info; an unsupported version
  gets `UnsupportedProtocolVersionError` (`-32022`) with the supported list; `tools/list` carries `resultType`, `ttlMs: 0` and
  `cacheScope`; `subscriptions/listen` is acknowledged first (`notifications/subscriptions/acknowledged`, subscription id in `_meta`),
  and list-changed notifications are sent only on subscriptions that asked for `toolsListChanged`.
- **Legacy**: `initialize` selects legacy semantics for the life of the process; the server negotiates the requested legacy revision
  (or 2025-11-25) and declares `tools.listChanged: true` — a server capability. After the change, at the `list_changed` level, it sends
  `notifications/tools/list_changed` on the initialized connection.
- Every `tools/list` is logged with the definition served (A or B) and its SHA-256; every `tools/call` with the name called, whether it
  exists, and the definition in force. At the `list_changed` level the server logs whether the signal could be delivered and on which
  channel (`signal-delivered`) or not (`signal-not-deliverable`, D16 point 1).

## Outcomes (D12, with precedence) and how they are coded

1 refused or disconnected · 2 re-approval required · 3 notified without re-approval · 4 silent accept (B served by a `tools/list` after
the change, call succeeded, nothing shown) · 5 stale (no `tools/list` after the change, A still in use) · 6 error, no call or timeout.
A repetition whose first call did not succeed with A is invalid. `code_q3.py` gives a provisional outcome; the two preregistered coders
classify the captures independently (D16 point 7). "Silent accept" is a protocol-level outcome: that B reached the model is claimed
only where a recording proxy shows it (local-engine cells).

## Requirements and tests

Node.js ≥ 22 and Python ≥ 3.11, no dependencies. `npm test` runs the suite (30 tests on 15 October 2026).

## Interpretation limits

- Measures client behaviour on a definition change, not what a model does with a changed description.
- Results are per client version; clients update themselves (Cursor CLI, Codex's background component).
- One OS (Debian 13 in a VM); graphical clients by hand.
- The server is configured at user level and the test folder is trusted beforehand (D16 point 2): repository trust is RQ2's question.
