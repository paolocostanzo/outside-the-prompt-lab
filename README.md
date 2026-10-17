# Outside the Prompt — reproducible lab harness

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23300292.svg)](https://doi.org/10.5281/zenodo.23300292)

Companion code for the research series *Outside the Prompt* (https://paolocostanzo.github.io/) and its November 2026 preprint.
Author: Paolo Costanzo (ORCID 0009-0005-7205-5945), CoDe RTD, Turin.

**Safety boundary.** Every component here is a harmless canary or a read-only check: the canary MCP server only logs that it
started and answers a minimal handshake with one no-op tool; the generators write configuration that points at the canary; the
runners drive the clients and record screens and logs. There are no attack payloads and nothing that exfiltrates, modifies or
reaches the network. The matrix runners edit the clients' trust stores in `$HOME`: run them only in a disposable VM.

| Folder | Measurement (preregistered RQ) | Article |
|---|---|---|
| `trusting-a-repo/` | Q5 (RQ2) — does a client start a repository-declared MCP server, and under which trust decision? Six terminal clients with the automated runner and two graphical clients by hand, 14 component tests, evidence with SHA-256 hashes | *Trusting a repo now means trusting its MCP servers* (13 Oct 2026) |
| `tool-change/` | Q3 (RQ3) — does a client notice when an approved tool's definition changes? Dual-era MCP server (2026-07-28 and legacy), 60-repetition matrix on six terminal clients, two editors by hand, rule-based coder, preregistered and additional (D22) coders, reader script `check-approvals`, 61 tests, evidence with SHA-256 hashes | *You approved the tool. Then it changed.* (20 Oct 2026) |
| `defence-coverage/` (scripts; census tables after adjudication) | Q2 (RQ4) — in official MCP servers, which third-party-content tools pass through the vendor's own defence? Second-reading and comparison scripts (D22), final census and coverage tables for an explicit list of servers (D17, D23), 28 tests | part 4 (27 Oct 2026) |
| `telemetry/` (in preparation, no run yet) | Q4 (RQ5) — what default client logs and host telemetry show for each event (D24, D25): inventory of default log locations, exporter run inside the VM, collection check, event and baseline orchestrators with set-up sessions and a pipeline check, quota observer, scoring, 105 tests | part 4 (27 Oct 2026) |
| `preregistration/` | deviations log, RQ1 classifier, ten-case pilot | preprint (November 2026) |

Each folder has its own README with requirements, how to reproduce, the test matrix and the limits of interpretation.

## Quick start (Q5 components, no VM needed)
```bash
cd trusting-a-repo
npm test                                  # 18 tests, Node >= 22, no dependencies
node scripts/check-repo.mjs path/to/repo  # which MCP servers would this repository ask my agent to run?
node scripts/check-trust.mjs              # which projects have I already trusted, client by client?
```

## Quick start (Q3 components, no VM needed)
```bash
cd tool-change
npm test                                  # 61 tests, Node >= 22 and Python >= 3.11, no dependencies
node scripts/check-approvals.mjs          # which MCP tools have I approved permanently, and in which file?
```

## Quick start (Q4 and Q2 components, no VM needed)
```bash
python3 -m unittest discover -s telemetry/test          # 105 tests, Python >= 3.11, no dependencies
python3 -m unittest discover -s defence-coverage/test   # 28 tests
python3 telemetry/scripts/vm_logs.py inventory telemetry/inventory/candidates.json   # read-only: which agent logs are on this machine?
```
The event and baseline orchestrators run on the host and drive the disposable VM; the scripts that stop or reset clients refuse to
run outside it.

## Citing
Cite the concept DOI, which always resolves to the latest version: **https://doi.org/10.5281/zenodo.23300292**.
Version v0.2.0 (Q5 harness, 11 Oct 2026): https://doi.org/10.5281/zenodo.23300293. Version v0.2.1 (13 Oct 2026, corrections after an external review — see the release notes): https://doi.org/10.5281/zenodo.23341303. Version v0.3.0 (17 Oct 2026, Q3 harness and evidence for part 3): https://doi.org/10.5281/zenodo.23438372. See also `CITATION.cff`.

The study design (research questions, hypotheses, criteria, analysis plan, Q3 and Q4 protocols) was preregistered on
11 October 2026: https://doi.org/10.5281/zenodo.23300369

> Costanzo, P. (2026). *Outside the Prompt — reproducible lab harness* (v0.3.0) [Software]. Zenodo. https://doi.org/10.5281/zenodo.23300292

## License
MIT.
