# Q4 (RQ5) evidence — public part

One folder per campaign, as the orchestrators wrote them, reduced to what can be published:
- `plan.json` (seed, clients, order, harness commit and trees), `host-log.jsonl` (every step of the campaign);
- per run or session: `run.json` (or `attempt.json` for an attempt that did not count), `collection-public.json` (counts per
  frozen log location, no paths), `harness-sha256.txt`, and from the VM's outputs `session.json`, `timeline.jsonl`,
  `command-bounds.json` and, for event runs, the ground-truth logs (`q3-server.log`, `canary-start.log`).

Campaigns: `pipeline-check` (D25), `events-dev` (rule development, D27), `events` (the 30 confirmatory event runs, D24, D29),
`setup-r1`…`setup-r7` (exploratory set-up sessions), `baseline`, `baseline-r2`, `baseline-r3` (attempts, D32, D33, D37) and
`baseline-r4` (the counted baseline: five development and five holdout sessions of 60 minutes).

`scores-20261024/` holds the scorer's input and output for the author's rules, the second author's and the host rules, the H5
verdict (`h5-author.json`) and the agreement between the two authors. They were produced with the frozen tools of
`../rules/FROZEN.md` after the freeze commit; every opening of the holdouts is in `../rules/holdout-access.md`.

Not here: the client-log archives (raw and redacted) and the screen captures. They hold account data of the lab's clients and stay
private; the counts above are computed from them by the published scripts.
