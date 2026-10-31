# Outside the Prompt — reproducible lab harness

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23300292.svg)](https://doi.org/10.5281/zenodo.23300292)

Companion code for the research series *Outside the Prompt* (https://paolocostanzo.github.io/) and its November 2026 preprint.
Author: Paolo Costanzo (ORCID 0009-0005-7205-5945), CoDe RTD, Turin.

**Safety boundary.** Every component here is a harmless canary or a read-only check: the canary MCP server only logs that it
started and answers a minimal handshake with one no-op tool; the generators write configuration that points at the canary; the
runners drive the clients and record screens and logs. There are no attack payloads and nothing that exfiltrates, modifies or
reaches the network. The matrix runners edit the clients' trust stores in `$HOME`: run them only in a disposable VM. The RQ1
data in `preregistration/rq1/` keep advisory identifiers, titles, dates, references and short factual notes; full advisory description texts,
which can describe exploitation, are not in the current tree or in the release archives; their SHA-256 hashes are published,
and the git history keeps the texts in the frame commit e62676b, which the reproduction reads.

| Folder | Measurement (preregistered RQ) | Article |
|---|---|---|
| `trusting-a-repo/` | Q5 (RQ2) — does a client start a repository-declared MCP server, and under which trust decision? Six terminal clients with the automated runner and two graphical clients by hand, 18 component tests, evidence with SHA-256 hashes | *Trusting a repo now means trusting its MCP servers* (13 Oct 2026) |
| `tool-change/` | Q3 (RQ3) — does a client notice when an approved tool's definition changes? Dual-era MCP server (2026-07-28 and legacy), 60-repetition matrix on six terminal clients, two editors by hand, rule-based coder, preregistered and additional (D22) coders, reader script `check-approvals`, 61 tests, evidence with SHA-256 hashes; the open-weight cells promised in part 2 (D39, exploratory: what four clients send to an open-weight model before and after the change), 23 Python tests, evidence in `evidence/open-weight-20261024/`; the per-client positive control added before any confirmatory data by deviation D12 point 5 and run after the fact (D52, exploratory: one rename cell per client, Cursor CLI excluded), evidence in `evidence/positive-control-20261028/` | *You approved the tool. Then it changed.* (20 Oct 2026); open-weight cells: *Would your logs have caught it?* (27 Oct 2026) |
| `defence-coverage/` | Q2 (RQ4) — in official MCP servers, which third-party-content tools pass through the vendor's own defence? Both readings, the third reading's proposals and the author's adjudication (D22, D38), the final census and coverage tables of the published servers (`results-20261024/`), scripts, 28 tests | *Would your logs have caught it?* (27 Oct 2026) |
| `telemetry/` | Q4 (RQ5) — what default client logs and host telemetry show for each event (D24–D37): inventory of default log locations, exporter run inside the VM, collection check, event and baseline orchestrators, quota observer, frozen detection rules of two authors, host rules, scoring and the H5 verdict, public evidence of every run and session, 221 tests | *Would your logs have caught it?* (27 Oct 2026) |
| `preregistration/` | RQ1 (confirmatory): deviations log D1–D54, frozen frame of 330 disclosures, stratified sample of 120, the author's labels (R0), canonical classifier, the confirmatory run of three open-weight model raters (`runs/rq1-confirmatory-20261027T142818Z/`) and its analysis (`…-rq1-analysis/RESULTS-RQ1.md`), the exploratory disagreement analysis and a sheet plus analysis for a second human rater (D51), ten-case pilot | preprint (November 2026) |

Each folder has its own README with requirements, how to reproduce, the test matrix and the limits of interpretation.

## Reproduce every reported analysis (one command, offline)
```bash
python3 reproduce.py            # re-runs every scripted analysis behind the paper's figures and compares with the committed outputs
python3 reproduce.py --tests    # also every test suite (stubs, a temporary HOME and loopback-only traffic)
```
The analyses write only to a temporary directory and never start a client, a VM, a model or a network call. Counts the paper
reads directly from evidence tables (RQ2 current-version re-checks, non-interactive and graphical cells; RQ3 graphical clients)
are not regenerated: their folders' READMEs give the counts and source files. Needs a git checkout (RQ1
reads the frozen frame from its commit). Model answers, human labels, client captures and the private RQ5 log archives are inputs,
not regenerated. SHA-256 manifests exist for the RQ1 advisory-query inputs (`preregistration/rq1/raw-20261025/`), the RQ2 evidence
(`trusting-a-repo/evidence/environment.json`) and the RQ3 evidence (`tool-change/evidence/SHA256SUMS` for the primary, conformance, set-up and graphical-client folders; the
exploratory folders `open-weight-20261024/` (D39) and `positive-control-20261028/` (D52) list every file's SHA-256 in the
`manifest` key of their `secret-gate.json`); the private RQ5 log
archives are not hashed here, except the package given to the second rule author (`telemetry/rules/second-author/package-SHA256SUMS`).

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
python3 -m unittest discover -s test -p 'test_*.py'   # 23 tests: the open-weight cells (D39): recording proxy, campaign guards
node scripts/check-approvals.mjs          # which MCP tools have I approved permanently, and in which file?
```

## Quick start (Q4 and Q2 components, no VM needed)
```bash
python3 -m unittest discover -s telemetry/test          # 221 tests, Python >= 3.11, no dependencies
python3 -m unittest discover -s defence-coverage/test   # 28 tests
python3 -m unittest discover -s preregistration/test    # 99 tests: RQ1 classifier, sampler, estimator, analysis
python3 telemetry/scripts/vm_logs.py inventory telemetry/inventory/candidates.json   # read-only: which agent logs are on this machine?
```
The event and baseline orchestrators run on the host and drive the disposable VM; the scripts that stop or reset clients refuse to
run outside it.

## Citing
Cite the concept DOI, which always resolves to the latest version: **https://doi.org/10.5281/zenodo.23300292**.
Version v0.2.0 (Q5 harness, 11 Oct 2026): https://doi.org/10.5281/zenodo.23300293. Version v0.2.1 (13 Oct 2026, corrections after an external review — see the release notes): https://doi.org/10.5281/zenodo.23341303. Version v0.3.0 (17 Oct 2026, Q3 harness and evidence for part 3): https://doi.org/10.5281/zenodo.23438372. Version v0.4.0 (24 Oct 2026, Q4 and Q2 harness, rules, census and evidence for part 4): https://doi.org/10.5281/zenodo.23616425. Version v0.4.1 (24 Oct 2026, the open-weight cells of D39 and their evidence): https://doi.org/10.5281/zenodo.23623265. Version v0.4.2 (24 Oct 2026, the D39 orchestrator takes the shared VM lock and refuses a mismatched resume; the analysis follows the plan): https://doi.org/10.5281/zenodo.23623381. Version v0.4.3 (25 Oct 2026, RQ1: deviations D40–D44, hardened classifier, frozen frame of 330 disclosures and the 120-case sample drawn with a public beacon): https://doi.org/10.5281/zenodo.23649529. See also `CITATION.cff`.

The study design (research questions, hypotheses, criteria, analysis plan, Q3 and Q4 protocols) was preregistered on
11 October 2026: https://doi.org/10.5281/zenodo.23300369

> Costanzo, P. (2026). *Outside the Prompt — reproducible lab harness* (v0.4.3) [Software]. Zenodo. https://doi.org/10.5281/zenodo.23300292

## License
MIT.
