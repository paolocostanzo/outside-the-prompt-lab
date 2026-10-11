# Outside the Prompt — reproducible lab harness

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23300292.svg)](https://doi.org/10.5281/zenodo.23300292)

Companion code for the research series *Outside the Prompt* (https://paolocostanzo.github.io/) and its November 2026 preprint.
Author: Paolo Costanzo (ORCID 0009-0005-7205-5945), CoDe RTD, Turin.

**Safety boundary.** Every component here is a harmless canary or a read-only check: the canary MCP server only logs that it
started and answers a minimal handshake with one no-op tool; the generators write configuration that points at the canary; the
runners drive the clients and record screens and logs. There are no attack payloads and nothing that exfiltrates, modifies or
reaches the network. The matrix runners edit the clients' trust stores in `$HOME`: run them only in a disposable VM.

| Folder | Measurement | Article |
|---|---|---|
| `trusting-a-repo/` | Q5 — does a client start a repository-declared MCP server, and under which trust decision? Eight clients, 75 automated cells, 14 component tests, evidence with SHA-256 hashes | *Trusting a repo now means trusting its MCP servers* (13 Oct 2026) |
| `tool-change/` (coming) | Q3 — does a client notice when an approved tool's definition changes? | part 3 (20 Oct 2026) |
| `telemetry/` (coming) | Q4 — what default host telemetry shows for each event | part 5 (3 Nov 2026) |

Each folder has its own README with requirements, how to reproduce, the test matrix and the limits of interpretation.

## Quick start (Q5 components, no VM needed)
```bash
cd trusting-a-repo
npm test                                  # 14 tests, Node >= 22, no dependencies
node scripts/check-repo.mjs path/to/repo  # which MCP servers would this repository ask my agent to run?
node scripts/check-trust.mjs              # which projects have I already trusted, client by client?
```

## Citing
Cite the concept DOI, which always resolves to the latest version: **https://doi.org/10.5281/zenodo.23300292**.
Version v0.2.0 (Q5 harness): https://doi.org/10.5281/zenodo.23300293. See also `CITATION.cff`.

> Costanzo, P. (2026). *Outside the Prompt — reproducible lab harness* (v0.2.0) [Software]. Zenodo. https://doi.org/10.5281/zenodo.23300292

## License
MIT.
